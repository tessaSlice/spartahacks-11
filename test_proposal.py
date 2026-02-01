import requests
import datetime
import sys
import os
import random

# Add API Work to path
sys.path.append(os.path.abspath("API Work"))
import gmail
import calendar
import contacts

# Define the endpoint
URL = "http://localhost:8080/actions"

def propose_email_draft():
    print("Authenticating with Gmail/People API...")
    gmail_service = gmail.get_services()
    people_service = contacts.get_services()

    contacts = contacts.get_contacts(people_service)
    
    if not contacts:
        print("No contacts found. Using a dummy contact.")
        selected_contact = {"name": "Test User", "email": "test@example.com"}
    else:
        selected_contact = random.choice(contacts)
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
    try:
        response = requests.post(URL, json=action_proposal)
        if response.status_code == 201:
            print(f"Success! Action ID: {response.json()['uuid']}")
        else:
            print(f"Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to localhost:8080. Is the server running?")

def propose_calendar_event():
    print("Authenticating with Calendar API...")
    calendar_service = calendar.get_calendar_service()

    # Example 1: Create a new event
    create_event_data = {
        "action": "create",
        "body": {
            "summary": "AI Proposed Meeting",
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
    }

    action_proposal = {
        "action": "create",
        "body": create_event_data
    }

    print("Proposing CREATE_EVENT action...")
    try:
        response = requests.post(URL, json=action_proposal)
        if response.status_code == 201:
            print(f"Success! Action ID: {response.json()['uuid']}")
        else:
            print(f"Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to localhost:8080. Is the server running?")

if __name__ == "__main__":
    propose_email_draft()
