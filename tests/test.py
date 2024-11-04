import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/calendar']


def init_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Get the authorization URL
            auth_url, _ = flow.authorization_url(access_type='offline')
            print('Please go to this URL: {}'.format(auth_url) + '&redirect_uri=http://localhost:8000')
            code = input('Enter the authorization code: ')  # Prompt for authorization code
            creds = flow.fetch_token(code=code)  # Exchange code for token
            # Save the credentials for future use
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def list_events(service, max_results=10):
    """List the upcoming events."""
    events_result = service.events().list(calendarId='primary', maxResults=max_results, singleEvents=True, orderBy='startTime').execute()
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

  events = list_events(service)
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start}: {event['summary']} (ID: {event['id']})")

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
