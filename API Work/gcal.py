import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils import SCOPES

def get_calendar_service():
    """Shows basic usage of the Google Calendar API.
    Returns the service object.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not set(SCOPES).issubset(set(creds.scopes or [])):
            print("Existing token lacks required scopes, re-running OAuth flow...")
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "API work/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def create_event(service, event_body):
    """Creates a new calendar event."""
    print(f"Creating event: {event_body.get('summary', 'Unknown')}")
    return service.events().insert(calendarId='primary', body=event_body).execute()

def update_event(service, event_id, event_body):
    """Updates an existing calendar event."""
    print(f"Updating event ID: {event_id}")
    return service.events().patch(
        calendarId='primary', 
        eventId=event_id, 
        body=event_body
    ).execute()

def delete_event(service, event_id):
    """Deletes a calendar event."""
    print(f"Deleting event ID: {event_id}")
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return {"id": event_id, "status": "deleted"}

def list_events(service, time_min=None, time_max=None, max_results=10):
    """
    Returns a list of events within the specified time range.
    Defaults to upcoming 10 events if no range specified.
    """
    if not time_min:
        time_min = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    
    # Convert datetime objects to ISO format string if needed
    if isinstance(time_min, datetime.datetime):
        time_min = time_min.isoformat()
    if isinstance(time_max, datetime.datetime):
        time_max = time_max.isoformat()
        
    print(f"Fetching events from {time_min} to {time_max if time_max else 'Future'}")
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])

def execute_action(service, action_data):
    """
    Dispatcher for calendar actions.
    """
    if not action_data:
        return None
        
    action = action_data.get("action")
    
    if action == "create":
        return create_event(service, action_data.get('body'))
        
    elif action == "update":
        return update_event(service, action_data.get('id'), action_data.get('body'))
        
    elif action == "delete":
        return delete_event(service, action_data.get('id'))
        
    return None

# Alias for backward compatibility if needed, but we will update __init__.py
execute_event_alternation = execute_action
