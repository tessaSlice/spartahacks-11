import requests
import datetime
import sys
import os
import random

# Add API Work to path
sys.path.append(os.path.abspath("API work"))
import gmail
import gcal
import gpeople

# Define the endpoint
URL = "http://localhost:8080/actions"

def send_proposal(data):
    try:
        response = requests.post(URL, json=data)
        if response.status_code == 201:
            print(f"Success! Proposal ID: {response.json()['uuid']}")
        else:
            print(f"Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to localhost:8080. Is the server running?")

def propose_email_draft():
    print("\n=== Email Proposal Test ===")
    print("Authenticating with Gmail/People API...")
    gmail_service = gmail.get_services()
    people_service = gpeople.get_services()

    people = gpeople.get_contacts(people_service)
    
    if not people:
        print("No contacts found. Using a dummy contact.")
        selected_contact = {"name": "Test User", "email": "test@example.com"}
    else:
        selected_contact = random.choice(people)
        print(f"Randomly selected contact: {selected_contact.get('name')} ({selected_contact.get('email')})")

    recipient_email = selected_contact.get('email')
    subject = "Hello from AI Agent"
    body = f"Hi {selected_contact.get('name', 'Friend')},\n\nThis is a drafted email proposed by the AI agent. It was randomly targeted to you from the user's contacts.\n\nBest,\nAI Agent"

    draft_structure = gmail.create_draft_structure(recipient_email, subject, body)
    
    # Wrap in our action format
    action_proposal = {
        "action": "send_email",
        "body": draft_structure
    }

    print("Proposing SEND_EMAIL action...")
    send_proposal(action_proposal)

def propose_calendar_event():
    print("\n=== Calendar Proposal Test ===")
    print("Authenticating with Calendar API...")
    calendar_service = gcal.get_calendar_service()

    # 1. Propose a CREATE action
    print("\n--- 1. Proposing CREATE Action ---")
    create_body = {
        "summary": "AI Proposed Meeting (To Be Created)",
        "description": "This meeting was proposed by the AI agent.",
        "start": {
            "dateTime": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(),
            "timeZone": "America/New_York",
        },
        "end": {
            "dateTime": (datetime.datetime.now() + datetime.timedelta(days=1, hours=1)).isoformat(),
            "timeZone": "America/New_York",
        },
    }
    
    create_proposal = {
        "action": "create",
        "body": create_body
    }
    send_proposal(create_proposal)

    # 2. Find an existing event to Update/Delete
    print("\n--- Looking for existing events to Update/Delete ---")
    # List upcoming events
    events = gcal.list_events(calendar_service, max_results=5)
    
    if not events:
        print("No existing events found. Skipping Update/Delete proposals.")
        return

    # Pick the first one (hopefully it's one we created or is safe to modify)
    # Ideally, we'd filter for "AI Proposed" events, but for this test we'll just take the first one.
    target_event = events[0]
    event_id = target_event['id']
    print(f"Found event: {target_event.get('summary')} (ID: {event_id})")

    # 3. Propose UPDATE on this event
    print("\n--- 2. Proposing UPDATE Action ---")
    update_body = {
        "summary": f"{target_event.get('summary')} (UPDATED)",
        "description": "This description was added via AI proposal.",
        # Keep existing times if possible, or just send what we have. 
        # For patch, we only need to send what changes, but let's be safe.
        # Actually, for this test let's just update summary/description.
    }
    update_proposal = {
        "action": "update",
        "id": event_id,
        "body": update_body
    }
    send_proposal(update_proposal)

    # 4. Propose DELETE on this event
    print("\n--- 3. Proposing DELETE Action ---")
    delete_proposal = {
        "action": "delete",
        "id": event_id
    }
    send_proposal(delete_proposal)

if __name__ == "__main__":
    propose_email_draft()
    propose_calendar_event()
