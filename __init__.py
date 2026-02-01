# receive POST request, parse it, output to agentic AI model that will run TODOs
# Hosting on DigitalOcean would work but it costs money. At the very minimum it would cost $5/month as of the time of writing: https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-app-using-gunicorn-to-app-platform

"""
parse post request, which is structured like so: 
"session_id": string
"attention_indices": array of ints
"messages": array of {"content": string, "speaker": int}
"""

from flask import Flask, jsonify, request, render_template
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import sys
import uuid
import json
import datetime
from dotenv import load_dotenv

sys.path.append(os.path.abspath("API work"))
import gcal
import gmail
import gpeople

load_dotenv()
API_KEY = os.getenv("API_KEY")

# create a Flask server
app = Flask(__name__)

# In-memory store for proposed actions
# Structure: { uuid: { uuid: str, data: dict, status: 'pending' } }
PROPOSED_ACTIONS: Dict[str, Any] = {}

# Initialize Services
calendar_service = gcal.get_calendar_service()
gmail_service = gmail.get_services()
people_service = gpeople.get_services()

# --- Structured Inputs (Pydantic Models) ---

class CreateCalendarEventInput(BaseModel):
    summary: str = Field(description="The title of the event")
    start_time: str = Field(description="Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")
    end_time: str = Field(description="End time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")
    location: Optional[str] = Field(default=None, description="Location of the event")
    description: Optional[str] = Field(default=None, description="Description of the event")
    attendees: Optional[List[str]] = Field(default=None, description="List of attendee email addresses")

class UpdateCalendarEventInput(BaseModel):
    event_id: str = Field(description="The ID of the event to update")
    summary: Optional[str] = Field(default=None, description="The new title of the event")
    start_time: Optional[str] = Field(default=None, description="New start time in ISO 8601 format")
    end_time: Optional[str] = Field(default=None, description="New end time in ISO 8601 format")
    location: Optional[str] = Field(default=None, description="New location")
    description: Optional[str] = Field(default=None, description="New description")
    attendees: Optional[List[str]] = Field(default=None, description="New list of attendee email addresses")

class DeleteCalendarEventInput(BaseModel):
    event_id: str = Field(description="The ID of the event to delete")

class SendEmailInput(BaseModel):
    recipient: str = Field(description="Email address of the recipient")
    subject: str = Field(description="Subject of the email")
    body: str = Field(description="Body content of the email")

# --- Tool Wrappers ---

def create_calendar_event_tool(summary: str, start_time: str, end_time: str, location: str = None, description: str = None, attendees: list[str] = None):
    """
    Propose creating a calendar event.
    """
    body = {
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    if location: body["location"] = location
    if description: body["description"] = description
    if attendees: body["attendees"] = [{"email": email} for email in attendees]
    
    return gcal.propose_create_event(body)

def update_calendar_event_tool(event_id: str, summary: str = None, start_time: str = None, end_time: str = None, location: str = None, description: str = None, attendees: list[str] = None):
    """
    Propose updating a calendar event.
    """
    body = {}
    if summary: body["summary"] = summary
    if start_time: body["start"] = {"dateTime": start_time}
    if end_time: body["end"] = {"dateTime": end_time}
    if location: body["location"] = location
    if description: body["description"] = description
    if attendees: body["attendees"] = [{"email": email} for email in attendees]
    
    return gcal.propose_update_event(calendar_service, event_id, body)

def delete_calendar_event_tool(event_id: str):
    """
    Propose deleting a calendar event.
    """
    return gcal.propose_delete_event(calendar_service, event_id)

def send_email_tool(recipient: str, subject: str, body: str):
    """
    Propose sending an email.
    """
    return gmail.propose_send_email(recipient, subject, body)

# TODO: consider adding more attributes if requested
class ToDoList(BaseModel):
    todo_items: List[str]

def set_error(context, error_message):
    context["Status"] = 400
    context["Error"] = error_message
    print(f"Error occurred, error message is: {error_message}")

@app.route('/')
def index():
    return render_template('index.html')

# --- Action Management Endpoints ---

@app.route('/actions', methods=['GET'])
def get_actions():
    """Get all pending actions."""
    return jsonify(list(PROPOSED_ACTIONS.values()))

@app.route('/actions', methods=['POST'])
def create_action():
    """
    Propose a new action.
    Expected JSON body: The action definition (output of define_event_alternation)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    action_id = str(uuid.uuid4())
    action_obj = {
        "uuid": action_id,
        "data": data,
        "status": "pending",
        "created_at": str(datetime.datetime.now()) if 'datetime' in globals() else None
    }
    
    if data and 'original' in data:
        action_obj['existing_data'] = data['original']

    PROPOSED_ACTIONS[action_id] = action_obj
    print(f"Action proposed: {action_id}")
    return jsonify({"uuid": action_id, "status": "created"}), 201

@app.route('/actions/<action_id>', methods=['PUT'])
def update_action(action_id):
    """Update an action's data."""
    if action_id not in PROPOSED_ACTIONS:
        return jsonify({"error": "Action not found"}), 404
    
    data = request.get_json()
    if 'data' in data:
        PROPOSED_ACTIONS[action_id]['data'] = data['data']
        return jsonify({"status": "updated"})
    return jsonify({"error": "Invalid update data"}), 400

@app.route('/actions/<action_id>', methods=['DELETE'])
def delete_action(action_id):
    """Delete/Dismiss an action."""
    if action_id in PROPOSED_ACTIONS:
        del PROPOSED_ACTIONS[action_id]
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Action not found"}), 404

@app.route('/actions/<action_id>/execute', methods=['POST'])
def execute_action(action_id):
    """Execute the action."""
    if action_id not in PROPOSED_ACTIONS:
        return jsonify({"error": "Action not found"}), 404
    
    action = PROPOSED_ACTIONS[action_id]
    # Allow client to send updated data in the execute request
    req_data = request.get_json()
    if req_data and 'data' in req_data:
        action['data'] = req_data['data']

    action_data = action['data']
    action_type = action_data.get('action')

    try:
        result = None
        if action_type in ['create', 'update', 'delete']:
            print(f"Executing Calendar action {action_id}: {action_data}")
            result = gcal.execute_action(calendar_service, action_data)
        
        elif action_type == 'send_email':
            print(f"Executing Email action {action_id}: {action_data}")
            # The body of the action contains the draft structure
            email_body = action_data.get('body')
            result = gmail.execute_send_email(gmail_service, email_body)
        
        else:
            return jsonify({"error": f"Unknown action type: {action_type}"}), 400

        # Remove from pending list after successful execution
        del PROPOSED_ACTIONS[action_id]
        
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        print(f"Execution failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Existing Endpoints ---

@app.route('/GetTodos', methods=["POST"])
def get_todos():
    print("Received request")
    data = request.get_json(force=False, silent=False)
    context = {
        "Status": 200,
        "Error": "",
    }

    # process the POST request data
    if 'attention_indices' not in data or 'messages' not in data:
        set_error(context, "Improperly formatted request, attention_indices or messages is not included in JSON payload")
        return jsonify(**context)
        
    indices = data['attention_indices']
    messages = data['messages']

    if not indices or not messages or indices[-1] >= len(messages):
        set_error(context, "Messages or indices contain invalid content")
        return jsonify(**context)
    
    # process messages and output it, for the time being just return the list of messages that are relevant
    client = genai.Client(api_key=API_KEY)

    tools = types.Tool(function_declarations=[
        create_calendar_event_tool,
        update_calendar_event_tool,
        delete_calendar_event_tool,
        send_email_tool
    ])
    config = types.GenerateContentConfig(tools=[tools])

    try:
        highlighted_messages = [messages[index] for index in indices]
        context_text = "Conversation context:\n" + '\n'.join([f"- {msg.get('content', '')}" for msg in highlighted_messages])
        
        prompt = '''
        You are a helpful assistant that can 
        - create, update, delete calendar events
        - send emails
        You are given a conversation context and a list of attention indices.
        You need to create a list of proposed actions based on the conversation context and the attention indices.
        The attention indices are the indices where a user indicated that the conversation context around that index is relevant to the user's needs.
        
        Solve the user's problems, outputting only the following tool calls:
        - create_calendar_event_tool
        - update_calendar_event_tool
        - delete_calendar_event_tool
        - send_email_tool
        The tool calls are to be returned in the form of a list of dictionaries.
        '''

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=context_text,
            config=config,
        )

        proposed_actions = []
        
        # Handle tool calls
        if response.function_calls:
            for call in response.function_calls:
                tool_map = {
                    "create_calendar_event_tool": create_calendar_event_tool,
                    "update_calendar_event_tool": update_calendar_event_tool,
                    "delete_calendar_event_tool": delete_calendar_event_tool,
                    "send_email_tool": send_email_tool
                }
                
                func = tool_map.get(call.name)
                if func:
                    # Execute the wrapper to get the proposal
                    proposal = func(**call.args)
                    proposed_actions.append(proposal)


    except Exception as e:
        set_error(context, f"Gemini error: {e}")
        return jsonify(**context)

    return jsonify(**context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
