import requests
import datetime

# Define the endpoint
URL = "http://localhost:8080/actions"

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

print("Proposing CREATE action...")
try:
    response = requests.post(URL, json=create_event_data)
    if response.status_code == 201:
        print(f"Success! Action ID: {response.json()['uuid']}")
    else:
        print(f"Failed: {response.text}")
except requests.exceptions.ConnectionError:
    print("Could not connect to localhost:8080. Is the server running?")

# Example 2: Update an existing event (mock ID)
update_event_data = {
    "action": "update",
    "id": "mock_event_id_12345",
    "body": {
        "summary": "Updated Meeting Title"
    }
}

print("\nProposing UPDATE action...")
try:
    response = requests.post(URL, json=update_event_data)
    if response.status_code == 201:
        print(f"Success! Action ID: {response.json()['uuid']}")
    else:
        print(f"Failed: {response.text}")
except requests.exceptions.ConnectionError:
    pass
