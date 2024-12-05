import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as google_request
import json
from datetime import datetime, timedelta, date

import traceback

from crud import get_user_by_username

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def init_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google_request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials2.json",
                SCOPES,
                redirect_uri="http://localhost:8501",
            )

            auth_url, _ = flow.authorization_url(access_type="offline")
            print(
                "Please go to this URL: {}".format(auth_url)
                # + "&redirect_uri=http://localhost:8501"
            )
            code = input("Enter the authorization code: ")
            creds = flow.fetch_token(code=code)

            x = json.dumps(creds)
            x = json.loads(x)

            x["client_id"] = flow.client_config["client_id"]
            x["client_secret"] = flow.client_config["client_secret"]

            json.dump(x, open("token.json", "w"))

            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    return build("calendar", "v3", credentials=creds)


def list_events(service, max_results=10, start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime.utcnow().date()  # today
    if end_date is None:
        end_date = start_date + timedelta(days=7)  # +7 days

    if isinstance(start_date, date):
        start_date = start_date.isoformat() + "T00:00:00Z"
    if isinstance(end_date, date):
        end_date = end_date.isoformat() + "T23:59:59Z"

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_date,
            timeMax=end_date,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])
    return events
    # return print("list_events done")


def add_event(service, event):
    """Add an event to the calendar."""
    event_result = (
        service.events().insert(calendarId="primary", body=event).execute()
    )
    return event_result


def delete_event(service, event_id):
    """Delete an event by its ID."""
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"Event {event_id} deleted."


def edit_event(service, event_id, updated_event):
    """Edit an existing event."""
    event_result = (
        service.events()
        .update(calendarId="primary", eventId=event_id, body=updated_event)
        .execute()
    )
    return event_result


def show_event(service, event_id):
    """Show details of a specific event."""
    event = (
        service.events().get(calendarId="primary", eventId=event_id).execute()
    )
    return event

"""
# def main():
#     service = init_service()

#     events = list_events(service)
#     for event in events:
#         start = event["start"].get("dateTime", event["start"].get("date"))
#         print(f"{start}: {event['summary']} (ID: {event['id']})")

#     new_event = {
#         "summary": "Test Event",
#         "location": "123 Test St.",
#         "description": "Trololo.",
#         "start": {
#             "dateTime": "2024-11-12T11:11:11-07:00",
#             "timeZone": "Europe/Moscow",
#         },
#         "end": {
#             "dateTime": "2024-11-12T11:11:11-07:00",
#             "timeZone": "Europe/Moscow",
#         },
#     }
#     added_event = add_event(service, new_event)
#     print(f"Added event: {added_event['summary']} (ID: {added_event['id']})")
"""

def check_token_for_valid(db, user):
    google_token = user.access_token
    refresh_token = user.refresh_token
    client_id = user.client_id
    client_secret = user.client_secret

    google_load = {
        "access_token": google_token,
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = None

    try:
        creds = Credentials.from_authorized_user_info(google_load, SCOPES)
        delta = timedelta(hours=4)
        creds.expiry += delta
        if creds and creds.valid:
            print("Token is valid.")
            print(creds.to_json())
            print(creds.expiry)
            user.need_google_token = False
        else:
            print(creds.to_json())
            print(type(creds.expiry))
            print("Token is invalid or expired.")
            raise Exception("Invalid credentials")
    except:
        print(traceback.format_exc())
        if not creds.valid:
            try:
                creds.refresh(google_request())

                x = json.dumps(creds)
                x = json.loads(x)

                user.access_token = x["access_token"]
                user.refresh_token = x["refresh_token"]
                user.need_google_token = False
                print("Token refreshed successfully.")
            except:
                user.need_google_token = True
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials2.json",
                    SCOPES,
                    redirect_uri="http://localhost:8501",
                )

                auth_url, _ = flow.authorization_url(access_type="offline")
                print()
                return {"message": "{}".format(auth_url)}
        else:
            user.need_google_token = True
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials2.json",
                SCOPES,
                redirect_uri="http://localhost:8501",
            )

            auth_url, _ = flow.authorization_url(access_type="offline")
            return {"message": "{}".format(auth_url)}
    db.commit()


def set_google_token_(db, user, google_token):

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials2.json",
        SCOPES,
        redirect_uri="http://localhost:8501",
    )
    creds = flow.fetch_token(code=google_token)
    x = json.dumps(creds)
    x = json.loads(x)

    x["client_id"] = flow.client_config["client_id"]
    x["client_secret"] = flow.client_config["client_secret"]

    user.access_token = x["access_token"]
    user.refresh_token = x["refresh_token"]
    user.client_id = x["client_id"]
    user.client_secret = x["client_secret"]
    user.need_google_token = False

    db.commit()


def return_service(db, user):
    google_token = user.access_token
    refresh_token = user.refresh_token
    client_id = user.client_id
    client_secret = user.client_secret

    google_load = {
        "access_token": google_token,
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = None

    try:
        creds = Credentials.from_authorized_user_info(google_load, SCOPES)

        if creds:
            print("Token is valid.")
            print(creds.to_json())
            user.need_google_token = False
            db.commit()
            return build("calendar", "v3", credentials=creds)
        else:
            print("Token is invalid or expired.")
            raise Exception("Invalid credentials")
    except:
        check_token_for_valid(db, user)
