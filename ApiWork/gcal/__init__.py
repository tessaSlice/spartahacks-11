import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ApiWork.utils import SCOPES

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
                "ApiWork/credentials.json", SCOPES
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

def get_event(service, event_id):
    """Retrieves a single event by ID."""
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        return event
    except HttpError as error:
        if error.resp.status == 404:
            return None
        print(f"An error occurred fetching event {event_id}: {error}")
        return None

def propose_create_event(event_body):
    return {
        "action": "create",
        "body": event_body
    }

def propose_update_event(service, event_id, event_body):
    original_event = get_event(service, event_id)
    return {
        "action": "update",
        "id": event_id,
        "body": event_body,
        "original": original_event
    }

def propose_delete_event(service, event_id):
    original_event = get_event(service, event_id)
    return {
        "action": "delete",
        "id": event_id,
        "original": original_event
    }

def execute_create_event(service, data):
    """Creates a new calendar event."""
    body = data.get('body')
    print(f"Creating event: {body.get('summary', 'Unknown')}")
    return service.events().insert(calendarId='primary', body=body).execute()

def execute_update_event(service, data):
    """Updates an existing calendar event."""
    event_id = data.get('id')
    body = data.get('body')
    print(f"Updating event ID: {event_id}")
    return service.events().patch(
        calendarId='primary', 
        eventId=event_id, 
        body=body
    ).execute()

def execute_delete_event(service, data):
    """Deletes a calendar event."""
    event_id = data.get('id')
    print(f"Deleting event ID: {event_id}")
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return {"id": event_id, "status": "deleted"}

def list_events(service, time_min=None, time_max=None, max_results=10, query=None):
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
        
    print(f"Fetching events from {time_min} to {time_max if time_max else 'Future'} with query: {query}")
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            q=query
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
        return execute_create_event(service, action_data)
        
    elif action == "update":
        return execute_update_event(service, action_data)
        
    elif action == "delete":
        return execute_delete_event(service, action_data)
        
    return None