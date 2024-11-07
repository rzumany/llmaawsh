import os
import json
import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_httplib2 import AuthorizedHttp


SCOPES = ['https://www.googleapis.com/auth/calendar']


def init_service():
    creds = None
    if os.path.exists('credentials.json') and os.path.exists('token.json'):
        credentials = None
        access_token = None
        with open('credentials.json', 'r') as file:
            credentials = json.load(file)
        with open('token.json', 'r') as file:
            access_token = json.load(file)
        with open('creds.json', 'w') as file:
            json.dump({
                'token': access_token['access_token'],
                'refresh_token': access_token['refresh_token'],
                'token_uri': credentials['installed']['token_uri'],
                'client_id': credentials['installed']['client_id'],
                'client_secret': credentials['installed']['client_secret'],
                'scopes': access_token['scope'],
            }, file)
        creds = Credentials.from_authorized_user_file('creds.json')
    if not creds:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES, redirect_uri='http://localhost:8000')
            # Get the authorization URL
            auth_url, _ = flow.authorization_url(access_type='offline')
            print('Please go to this URL: {}'.format(auth_url))
            code = input('Enter the authorization code: ')  # Prompt for authorization code
            creds = flow.fetch_token(code=code)  # Exchange code for token
            # Save the credentials for future use
            with open('token.json', 'w') as token:
                token.write(json.dumps(creds))
    return build('calendar', 'v3', http=AuthorizedHttp(creds))


def list_events(service, max_results=10):
    """List the upcoming events."""
    events_result = service.events().list(
        calendarId='primary',
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events


def list_events(service, max_results=10,
                start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime.datetime.utcnow().date()  # today
    if end_date is None:
        end_date = start_date + datetime.timedelta(days=7)  # +7 days

    if isinstance(start_date, datetime.date):
        start_date = start_date.isoformat() + 'T00:00:00Z'
    if isinstance(end_date, datetime.date):
        end_date = end_date.isoformat() + 'T23:59:59Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_date,
        timeMax=end_date,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime').execute()

    events = events_result.get('items', [])
    return events


def add_event(service, event):
    """Add an event to the calendar."""
    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return event_result


def delete_event(service, event_id):
    """Delete an event by its ID."""
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return f'Event {event_id} deleted.'


def edit_event(service, event_id, updated_event):
    """Edit an existing event."""
    event_result = service.events().update(calendarId='primary', eventId=event_id, body=updated_event).execute()
    return event_result


def show_event(service, event_id):
    """Show details of a specific event."""
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    return event


def main():
    service = init_service()

    # Example of list_events
    print("Listing events:")
    events = list_events(service)
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start}: {event['summary']} (ID: {event['id']})")
    events = list_events(service,
                start_date=datetime.date(2024, 11, 1),
                end_date=datetime.date(2024, 11, 30))
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start}: {event['summary']} (ID: {event['id']})")

    # Example of adding an event
    new_event = {
        'summary': 'Test Event',
        'location': '123 Test St.',
        'description': 'A test the API.',
        'start': {
            'dateTime': '2024-11-11T11:11:11-07:00',
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': '2024-11-11T11:11:11-07:00',
            'timeZone': 'America/Los_Angeles',
        },
    }
    added_event = add_event(service, new_event)
    print(f"Added event: {added_event['summary']} (ID: {added_event['id']})")

    new_event['summary'] = new_event['summary'] + '(edited)'
    edited_event = edit_event(service, added_event['id'], new_event)
    print(f"Edited event: {edited_event['summary']} (ID: {edited_event['id']})")
