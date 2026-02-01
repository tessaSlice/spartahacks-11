import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# this assumes that the type of calendar is primary, we could test secondary but I don't think that's incredibly useful

# if modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Creates an event
# bodyJson: the content of the event to insert
def createEvent(bodyJson, service):
    # create event with parameters
    event = service.events().insert(calendarId='primary', body=bodyJson).execute()

# @returns a list of calendar events
# timeStart: the date to start parsing
# numResults: the number of results to return
# service: the service variable for the calendar
def readEvent(timeStart, numResults, service):
    # For read event, we will use the number of events to return and the start/end
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=timeStart,
            maxResults=numResults,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result

# Updates a specified event with the provided json
# event_to_change: the event ID to change
# event_update_body: the content of the new event in json form
def updateEvent(event_to_change, event_update_body):
    # Call the events().patch() method
    updated_event = service.events().patch(
        calendarId='primary',
        eventId=event_to_change,
        body=event_update_body,
        sendUpdates='all'  # Optional: determines if guests receive notifications ('all', 'externalOnly', or 'none')
    ).execute()

# Deletes a specified event
# event_to_delete: ID of the event to delete
def deleteEvent(event_to_delete):
    # delete event
    service.events().delete(calendarId='primary', eventId=event_to_delete).execute()

# TODO in main
# # Get credentials from the token.json credential file
# creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# Build the calendar service
# service = build("calendar", "v3", credentials=creds)
# Get the current date for reference (not necessary but can do)
# now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()  # get the current day