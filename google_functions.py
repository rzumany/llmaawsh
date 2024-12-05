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

from crud import get_user_by_username

SCOPES = ["https://www.googleapis.com/auth/calendar"]

with open("./credentials.json") as f:
    google_credentials = json.load(f)["web"]

CLIENT_ID = google_credentials["client_id"]
CLIENT_SECRET = google_credentials["client_secret"]
REDIRECT_URIS = google_credentials["redirect_uris"][0]
TOKEN_URI = google_credentials["token_uri"]


from datetime import datetime, timedelta, date


# def list_events(service, max_results=10, start_date=None, end_date=None):
#     if start_date is None:
#         start_date = datetime.utcnow().date()
#     else:
#         start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

#     if end_date is None:
#         end_date = start_date + timedelta(days=7)
#     else:
#         end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

#     start_date = (
#         datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
#     )
#     end_date = (
#         datetime.combine(end_date, datetime.max.time()).isoformat() + "Z"
#     )

#     events_result = (
#         service.events()
#         .list(
#             calendarId="primary",
#             timeMin=start_date,
#             timeMax=end_date,
#             maxResults=max_results,
#             singleEvents=True,
#             orderBy="startTime",
#         )
#         .execute()
#     )

#     events = events_result.get("items", [])
#     return events
#     # return print("list_events done")


def list_events(service, max_results=10, start=None, end=None):
    """
    Получает список предстоящих событий в пределах заданного периода с учетом московского времени.
    
    :param service: Google Calendar API service instance.
    :param max_results: Максимальное количество возвращаемых событий (по умолчанию 10).
    :param start: Дата и время начала периода поиска событий в формате YYYY-MM-DDTHH:MM:SS.
    :param end: Дата и время окончания периода поиска событий в формате YYYY-MM-DDTHH:MM:SS.
    :return: Список событий.
    """
    
    # Определяем московский часовой пояс
    msk_tz = pytz.timezone("Europe/Moscow")

    # Если start не задан, устанавливаем на текущий момент в Московском времени
    if start is None:
        start = datetime.now(msk_tz).isoformat()

    # Если end не задан, устанавливаем на 7 дней позже в Московском времени
    if end is None:
        end = (datetime.now(msk_tz) + timedelta(days=7)).isoformat()

    # Конвертируем start и end в строки в формате RFC3339 с часовым поясом
    start = datetime.fromisoformat(start).astimezone(msk_tz).isoformat()
    end = datetime.fromisoformat(end).astimezone(msk_tz).isoformat()

    # Запрашиваем события из календаря
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start,
            timeMax=end,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            timeZone="Europe/Moscow"  # Добавление временной зоны
        )
        .execute()
    )

    events = events_result.get("items", [])
    return events


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


def check_token_for_valid(db, user):
    """
    Проверяет токен на валидность, обновляет его при необходимости,
    и возвращает URL авторизации, если токен недействителен.
    """
    try:
        # Создаём объект Credentials из токенов пользователя
        creds = Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            token_uri=TOKEN_URI,
            client_id=user.client_id,
            client_secret=user.client_secret,
        )

        # Проверка и обновление токена
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
        # Если токен недействителен или обновить не удалось
        user.need_google_token = True
        db.commit()

        # Создание ссылки авторизации
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


# def check_token_for_valid(db, user):
#     google_token = user.access_token
#     refresh_token = user.refresh_token
#     client_id = user.client_id
#     client_secret = user.client_secret

#     google_load = {
#         "access_token": google_token,
#         "refresh_token": refresh_token,
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "token_uri": "https://oauth2.googleapis.com/token",
#     }
#     creds = None

#     try:
#         creds = Credentials.from_authorized_user_info(google_load, SCOPES)
#         delta = timedelta(hours=4)
#         creds.expiry += delta
#         if creds and creds.valid:
#             print("Token is valid.")
#             print(creds.to_json())
#             print(creds.expiry)
#             user.need_google_token = False
#         else:
#             print(creds.to_json())
#             print(type(creds.expiry))
#             print("Token is invalid or expired.")
#             raise Exception("Invalid credentials")
#     except:
#         print(traceback.format_exc())
#         if not creds.valid:
#             try:
#                 creds.refresh(google_request())

#                 x = json.dumps(creds)
#                 x = json.loads(x)

#                 user.access_token = x["access_token"]
#                 user.refresh_token = x["refresh_token"]
#                 user.need_google_token = False
#                 print("Token refreshed successfully.")
#             except:
#                 user.need_google_token = True
#                 flow = InstalledAppFlow.from_client_secrets_file(
#                     "credentials.json",
#                     SCOPES,
#                     redirect_uri="http://localhost:8501",
#                 )

#                 auth_url, _ = flow.authorization_url(access_type="offline")
#                 print()
#                 return {"message": "{}".format(auth_url)}
#         else:
#             user.need_google_token = True
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json",
#                 SCOPES,
#                 redirect_uri="http://localhost:8501",
#             )

#             auth_url, _ = flow.authorization_url(access_type="offline")
#             return {"message": "{}".format(auth_url)}
#     db.commit()


def set_google_token_(db, user, google_token) -> None:
    try:
        # Извлечение authorization code из строки
        auth_code = google_token

        # Обмен authorization code на токены
        token_request_data = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URIS,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(TOKEN_URI, data=token_request_data)
        token_response.raise_for_status()  # Проверка на успешность запроса

        # Парсинг ответа с токенами
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        # Установка данных в пользователя
        user.client_id = CLIENT_ID
        user.client_secret = CLIENT_SECRET
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.need_google_token = False

        # Сохранение изменений в базе данных
        db.commit()
    except Exception as e:
        print(f"Error setting Google token: {e}")
        db.rollback()


# def set_google_token_(db, user, google_token):

#     flow = InstalledAppFlow.from_client_secrets_file(
#         "credentials.json",
#         SCOPES,
#         redirect_uri="http://localhost:8501",
#     )
#     creds = flow.fetch_token(code=google_token, access_type="offline")
#     x = json.dumps(creds)
#     x = json.loads(x)
#     if "refresh_token" not in x:
#         x["refresh_token"] = ""

#     print(x)
#     x["client_id"] = flow.client_config["client_id"]
#     x["client_secret"] = flow.client_config["client_secret"]

#     user.access_token = x["access_token"]

#     user.refresh_token = x["refresh_token"]
#     user.client_id = x["client_id"]
#     user.client_secret = x["client_secret"]
#     user.need_google_token = False

#     db.commit()


# def return_service(db, user):
#     google_token = user.access_token
#     refresh_token = user.refresh_token
#     client_id = user.client_id
#     client_secret = user.client_secret

#     google_load = {
#         "access_token": google_token,
#         "refresh_token": refresh_token,
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "token_uri": "https://oauth2.googleapis.com/token",
#     }
#     creds = None

#     try:
#         creds = Credentials.from_authorized_user_info(google_load, SCOPES)

#         if creds:
#             print("Token is valid.")
#             print(creds.to_json())
#             user.need_google_token = False
#             db.commit()
#             return build("calendar", "v3", credentials=creds)
#         else:
#             print("Token is invalid or expired.")
#             raise Exception("Invalid credentials")
#     except:
#         check_token_for_valid(db, user)


def return_service(db, user):
    # Проверить токен

    check_token_for_valid(db, user)

    # Если токен всё ещё недействителен, выдать ошибку
    if user.need_google_token:
        raise ValueError("User needs to reauthenticate with Google")

    # Создать объект creds
    creds = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri=TOKEN_URI,
        client_id=user.client_id,
        client_secret=user.client_secret,
    )
    # Возврат сервиса Google Calendar
    service = build("calendar", "v3", credentials=creds)
    return service
