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


def define_event_alternation(current_event, new_event_data):
    """
    Defines an alternation of a calendar event (CRUD format).
    
    Scenarios:
    1. nil -> x (Create): current_event is None, new_event_data is valid.
    2. x -> y (Update): current_event is valid, new_event_data is valid.
    3. x -> nil (Delete): current_event is valid, new_event_data is None.
    
    Args:
        current_event (dict): The existing event object (or None).
        new_event_data (dict): The desired event data (or None).
        
    Returns:
        dict: A dictionary containing the 'action' and necessary data/ID.
        Returns None if no action is required (nil -> nil).
    """
    if current_event is None and new_event_data is not None:
        # Create (nil -> x)
        return {"action": "create", "body": new_event_data}
    
    elif current_event is not None and new_event_data is not None:
        # Update (x -> y)
        # We need the ID from current_event to update it
        return {"action": "update", "id": current_event['id'], "body": new_event_data}
        
    elif current_event is not None and new_event_data is None:
        # Delete (x -> nil)
        return {"action": "delete", "id": current_event['id']}
        
    else:
        # nil -> nil (No-op)
        return None


def execute_event_alternation(service, alternation_def):
    """
    Executes the creation, update, or deletion of an event based on the definition.
    
    Args:
        service: The authenticated Google Calendar service instance.
        alternation_def (dict): The output from define_event_alternation.
        
    Returns:
        The result of the API call (event object for create/update, empty for delete),
        or None if no action was taken.
    """
    if not alternation_def:
        return None
        
    action = alternation_def.get("action")
    
    if action == "create":
        body = alternation_def.get('body')
        print(f"Creating event: {body.get('summary', 'Unknown')}")

        return service.events().insert(calendarId='primary', body=body).execute()
        
    elif action == "update":
        body = alternation_def.get('body')
        print(f"Updating event ID: {alternation_def['id']}")
        
        # Validate body (Update might be partial, but usually follows resource semantics)
        # For patch, we might not need strict validation of all fields, but let's check basics if provided
        if 'start' in body or 'end' in body:
             # If one is provided, usually both should be checked or at least valid
             pass

        return service.events().patch(
            calendarId='primary', 
            eventId=alternation_def['id'], 
            body=body
        ).execute()
        
    elif action == "delete":
        print(f"Deleting event ID: {alternation_def['id']}")
        service.events().delete(calendarId='primary', eventId=alternation_def['id']).execute()
        return {"id": alternation_def['id'], "status": "deleted"}
        
    return None


def get_events_in_range(service, time_min, time_max):
    """
    Returns a list of events within the specified time range.
    
    Args:
        service: The authenticated Google Calendar service instance.
        time_min (str or datetime): Start time (inclusive).
        time_max (str or datetime): End time (inclusive).
        
    Returns:
        list: List of event objects.
    """
    # Convert datetime objects to ISO format string if needed
    if isinstance(time_min, datetime.datetime):
        time_min = time_min.isoformat()
    if isinstance(time_max, datetime.datetime):
        time_max = time_max.isoformat()
        
    print(f"Fetching events from {time_min} to {time_max}")
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])
