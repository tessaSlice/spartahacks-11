import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# we want to CRUD
# Create events
# Read events
# Update events
# Delete events

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
  # verify credentials
  # they are created during the first authentication pass through
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  # calendar functions
  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API (service is the calendar service)
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()  # get the current day
    print("Getting the upcoming 10 events")
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])
      
    # create event
    # event = {
    #   'summary': 'Home',
    #   'location': '1760 Broadway St., Ann Arbor, MI 48105',
    #   'description': 'Cry in the corner',
    #   'start': {
    #     'dateTime': '2026-02-14T09:00:00-07:00',
    #     'timeZone': 'America/New_York',
    #   },
    #   'end': {
    #     'dateTime': '2026-02-14T17:00:00-07:00',
    #     'timeZone': 'America/New_York',
    #   },
    #   'recurrence': [
    #     'RRULE:FREQ=DAILY;COUNT=2'
    #   ],
    #   'reminders': {
    #     'useDefault': False,
    #     'overrides': [
    #       {'method': 'email', 'minutes': 24 * 60},
    #       {'method': 'popup', 'minutes': 10},
    #     ],
    #   },
    # }
    # event = service.events().insert(calendarId='primary', body=event).execute()
    # print('Event created: %s' % (event.get('htmlLink')))
    
    # 'service' is an authorized Google Calendar API service instance
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=20, singleEvents=True,
            orderBy="startTime",).execute()
    events = events_result.get('items', [])

    print(f'event size {len(events)}')

    if not events:
        print(f'No upcoming events found.')
    for event in events:
      # Print the event ID
      print(f"Summary: {event['summary']}\n Start Date: {event['start']} Event ID: {event['id']}\n")
    
    # EVENT_ID = events[0]['id']
    # CALENDAR_ID = 'primary'
    # TIMEZONE = "America/New_York"  # Use an IANA time zone name (e.g., "America/Detroit")
    # # print(f"{events[0]['summary']}")
    # # Define the updates you want to make in a dictionary
    # event_update_body = {
    #     'summary': 'Happy Birthday!',
    #   #   'location': 'New Address, New City',
    #   #   'start': {
    #   #   'dateTime': '2026-02-14T09:00:00-07:00',
    #   #   'timeZone': 'America/New_York',
    #   # },
    #   # 'end': {
    #   #   'dateTime': '2026-02-14T17:00:00-07:00',
    #   #   'timeZone': 'America/New_York',
    #   # },
    # }

    # # Call the events().patch() method
    # updated_event = service.events().patch(
    #     calendarId=CALENDAR_ID,
    #     eventId=EVENT_ID,
    #     body=event_update_body,
    #     sendUpdates='all'  # Optional: determines if guests receive notifications ('all', 'externalOnly', or 'none')
    # ).execute()
    
    # delete event
    service.events().delete(calendarId='primary', eventId=events[0]['id']).execute()

    # print(f"Event updated: {updated_event.get('htmlLink')}")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
