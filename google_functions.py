import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as google_request

import json
from datetime import datetime, timedelta, date
import pytz

import traceback
import requests
import logging

from crud import get_user_by_username

SCOPES = ["https://www.googleapis.com/auth/calendar"]

with open("./credentials.json") as f:
    google_credentials = json.load(f)["web"]

CLIENT_ID = google_credentials["client_id"]
CLIENT_SECRET = google_credentials["client_secret"]
REDIRECT_URIS = google_credentials["redirect_uris"][0]
TOKEN_URI = google_credentials["token_uri"]


from datetime import datetime, timedelta, date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("google_calendar_agent.log"),
        logging.StreamHandler(),
    ],
)


def list_events(service, max_results=10, start=None, end=None):
    """Получает список предстоящих событий в пределах заданного периода с учетом московского времени."""
    try:
        logging.info("Fetching events list.")
        msk_tz = pytz.timezone("Europe/Moscow")

        if start is None:
            start = datetime.now(msk_tz).isoformat()

        if end is None:
            end = (datetime.now(msk_tz) + timedelta(days=7)).isoformat()

        start = datetime.fromisoformat(start).astimezone(msk_tz).isoformat()
        end = datetime.fromisoformat(end).astimezone(msk_tz).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start,
                timeMax=end,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
                timeZone="Europe/Moscow",
            )
            .execute()
        )

        events = events_result.get("items", [])
        logging.info(f"Fetched {len(events)} events.")
        return events
    except Exception as e:
        logging.error(f"Error fetching events: {e}")
        raise


def add_event(service, event):
    """Добавляет новое событие в календарь."""
    try:
        logging.info(f"Adding event: {event['summary']}")
        event_result = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
            )
            .execute()
        )
        logging.info(f"Event added: {event_result['id']}")
        return event_result
    except Exception as e:
        logging.error(f"Error adding event: {e}")
        raise


def delete_event(service, event_id):
    """Удаляет событие по его идентификатору."""
    try:
        logging.info(f"Deleting event with ID: {event_id}")
        service.events().delete(
            calendarId="primary",
            eventId=event_id,
        ).execute()
        logging.info(f"Event {event_id} deleted.")
        return f"Event {event_id} deleted."
    except Exception as e:
        logging.error(f"Error deleting event {event_id}: {e}")
        raise


def edit_event(service, event_id, updated_event):
    """Редактирует существующее событие."""
    try:
        logging.info(f"Editing event {event_id} with new details.")
        event_result = (
            service.events()
            .update(
                calendarId="primary",
                eventId=event_id,
                body=updated_event,
            )
            .execute()
        )
        logging.info(f"Event {event_id} updated.")
        return event_result
    except Exception as e:
        logging.error(f"Error editing event {event_id}: {e}")
        raise


def show_event(service, event_id):
    """Показывает детали конкретного события по его идентификатору."""
    try:
        logging.info(f"Fetching details for event ID: {event_id}")
        event = (
            service.events()
            .get(
                calendarId="primary",
                eventId=event_id,
            )
            .execute()
        )
        logging.info(f"Event details: {event}")
        return event
    except Exception as e:
        logging.error(f"Error fetching event {event_id}: {e}")
        raise


def check_token_for_valid(db, user):
    """
    Проверяет токен на валидность, обновляет его при необходимости,
    и возвращает URL авторизации, если токен недействителен.
    """
    try:
        creds = Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            token_uri=TOKEN_URI,
            client_id=user.client_id,
            client_secret=user.client_secret,
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(google_request())
            user.access_token = creds.token
            user.refresh_token = creds.refresh_token
            user.need_google_token = False
            db.commit()
            return {"message": "Token is valid and refreshed."}

        elif not creds.valid:
            raise ValueError("Token is invalid or missing.")

    except Exception as e:
        user.need_google_token = True
        db.commit()

        flow = InstalledAppFlow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": TOKEN_URI,
                    "redirect_uris": [REDIRECT_URIS],
                }
            },
            SCOPES,
        )
        flow.redirect_uri = REDIRECT_URIS
        auth_url, _ = flow.authorization_url(
            access_type="offline", prompt="consent"
        )
        return {
            "message": f"Token invalid. Reauthorize using this URL: {auth_url}"
        }


def set_google_token_(db, user, google_token) -> None:
    try:
        auth_code = google_token

        token_request_data = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URIS,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(TOKEN_URI, data=token_request_data)
        token_response.raise_for_status()

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        user.client_id = CLIENT_ID
        user.client_secret = CLIENT_SECRET
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.need_google_token = False

        db.commit()
    except Exception as e:
        print(f"Error setting Google token: {e}")
        db.rollback()


def return_service(db, user):
    check_token_for_valid(db, user)
    if user.need_google_token:
        raise ValueError("User needs to reauthenticate with Google")

    creds = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri=TOKEN_URI,
        client_id=user.client_id,
        client_secret=user.client_secret,
    )

    service = build("calendar", "v3", credentials=creds)
    return service


def list_calendars(service):
    """
    Получает список всех доступных календарей.

    :param service: Google Calendar API service instance.
    :return: Список календарей.
    """
    try:
        logging.info("Fetching list of calendars.")
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])
        logging.info(f"Fetched {len(calendars)} calendars.")
        return calendars
    except Exception as e:
        logging.error(f"Error fetching calendars: {e}")
        raise


def get_event_by_summary(service, summary, start=None, end=None):
    """
    Получает событие по названию (summary) в заданный период времени.

    :param service: Google Calendar API service instance.
    :param summary: Название события для поиска.
    :param start: Дата и время начала периода поиска событий в формате YYYY-MM-DDTHH:MM:SS.
    :param end: Дата и время окончания периода поиска событий в формате YYYY-MM-DDTHH:MM:SS.
    :return: Найденное событие или None, если событие не найдено.
    """
    try:
        logging.info(f"Searching for event with summary '{summary}'.")
        msk_tz = pytz.timezone("Europe/Moscow")

        if start is None:
            start = datetime.now(msk_tz).isoformat()

        if end is None:
            end = (datetime.now(msk_tz) + timedelta(days=7)).isoformat()

        start = datetime.fromisoformat(start).astimezone(msk_tz).isoformat()
        end = datetime.fromisoformat(end).astimezone(msk_tz).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                q=summary,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
                timeZone="Europe/Moscow",
            )
            .execute()
        )

        events = events_result.get("items", [])
        logging.info(
            f"Found {len(events)} events matching summary '{summary}'."
        )
        return events[0] if events else None
    except Exception as e:
        logging.error(
            f"Error searching for event with summary '{summary}': {e}"
        )
        raise


def list_events_by_calendar(service, calendar_id, max_results=10):
    """
    Получает список событий из конкретного календаря.

    :param service: Google Calendar API service instance.
    :param calendar_id: ID календаря, из которого нужно получить события.
    :param max_results: Максимальное количество возвращаемых событий (по умолчанию 10).
    :return: Список событий.
    """
    try:
        logging.info(f"Fetching events from calendar '{calendar_id}'.")
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        logging.info(
            f"Fetched {len(events)} events from calendar '{calendar_id}'."
        )
        return events
    except Exception as e:
        logging.error(
            f"Error fetching events from calendar '{calendar_id}': {e}"
        )
        raise
