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
import uuid
import datetime
from dotenv import load_dotenv
from ApiWork import gcal, gmail, gpeople, jira_slack

load_dotenv(override=True)
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
jira_client = jira_slack.get_jira_client()
slack_client = jira_slack.get_slack_client()
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

class CreateJiraIssueInput(BaseModel):
    summary: str = Field(description="Summary of the issue")
    description: str = Field(description="Description of the issue")

class UpdateJiraIssueInput(BaseModel):
    issue_id: str = Field(description="The ID of the issue to update")
    summary: Optional[str] = Field(default=None, description="The new summary of the issue")
    description: Optional[str] = Field(default=None, description="The new description of the issue")

# --- Tool Wrappers ---

def list_calendar_events_tool(time_min: str = None, time_max: str = None, max_results: int = 10, query: str = None):
    """
    List calendar events to check availability or existing events.
    """
    return gcal.list_events(calendar_service, time_min, time_max, max_results, query)

def read_emails_tool(query: str = None, max_results: int = 10):
    """
    Read emails to find relevant information.
    """
    return gmail.read_emails(gmail_service, query, max_results)

def get_contacts_tool(query: str = None):
    """
    Get contacts to find email addresses.
    """
    return gpeople.get_contacts(people_service, query)

def create_calendar_event_tool(summary: str, start_time: str, end_time: str, location: str = None, description: str = None, attendees: list[str] = None):
    """
    Propose creating a calendar event.
    """
    body = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "America/Detroit"},
        "end": {"dateTime": end_time, "timeZone": "America/Detroit"},
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
    if start_time: body["start"] = {"dateTime": start_time, "timeZone": "America/Detroit"}
    if end_time: body["end"] = {"dateTime": end_time, "timeZone": "America/Detroit"}
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

def create_jira_issue_tool(summary: str, description: str):
    """
    Propose creating a Jira issue.
    """
    return jira_slack.propose_create_jira_issue(summary, description)

def send_slack_message_tool(message: str):
    """
    Propose sending a Slack message.
    """
    return jira_slack.propose_send_slack_message(message)

def set_error(context, error_message):
    context["Status"] = 400
    context["Error"] = error_message
    print(f"Error occurred, error message is: {error_message}")

@app.route('/')
def index():
    return render_template('index.html')

# --- Action Management Endpoints ---

def add_proposed_action(data):
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
    return action_obj

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
    
    action_obj = add_proposed_action(data)
    return jsonify({"uuid": action_obj["uuid"], "status": "created"}), 201

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
        
        elif action_type == 'create_jira_issue':
            print(f"Executing Jira action {action_id}: {action_data}")
            result = jira_slack.execute_create_jira_issue(jira_client, action_data)

        elif action_type == 'send_slack_message':
            print(f"Executing Slack action {action_id}: {action_data}")
            result = jira_slack.execute_send_slack_message(slack_client, action_data)

        else:
            return jsonify({"error": f"Unknown action type: {action_type}"}), 400

        # Remove from pending list after successful execution
        del PROPOSED_ACTIONS[action_id]
        
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        print(f"Execution failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Existing Endpoints ---

def process_attention_item(client, tools, transcript_text, index, target_message):
    """
    Process a single attention item with its own chat session.
    """
    target_content = target_message.get('content', '')
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f'''
    You are a helpful assistant that can manage calendar events and emails.
    
    Here is the full conversation transcript:
    {transcript_text}
    
    Focus specifically on the message at index {index}: "Speaker {target_message.get('speaker', 'Unknown')}: {target_content}".
    This message (and its surrounding context) indicates that an action needs to be taken (e.g. creating a calendar event, sending an email).
    
    Be aware of the times that users give for action items. They may be relative to today's date, {today_date}.
    
    First, analyze the context around this message to understand the specific user need.
    If you need more information (e.g. checking calendar availability, finding an email address, or looking up an email), use the following tools:
    - list_calendar_events_tool
    - read_emails_tool
    - get_contacts_tool
    
    Then, propose the necessary action(s) using:
    - create_calendar_event_tool
    - update_calendar_event_tool
    - delete_calendar_event_tool
    - send_email_tool
    - create_jira_issue_tool
    - send_slack_message_tool
    
    CRITICAL: You MUST propose at least one action for this attention item.

    If you are missing information (like an email address), SEARCH for it using get_contacts_tool or read_emails_tool.
    If you still cannot find it after searching, use a placeholder like 'INSERT_EMAIL_HERE' or 'TBD' and PROPOSE THE ACTION ANYWAY.
    DO NOT stop to ask the user for information.
    '''
    
    # Create a chat session
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            tools=tools,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"
                )
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            )
        )
    )

    # Send initial message
    response = chat.send_message(prompt)

    proposed_actions = []
    
    # Manual loop for function calling
    max_turns = 10
    for _ in range(max_turns):
        if not response.function_calls:
            break
            
        print(f"Gemini requested function calls for index {index}: {response.function_calls}")
        
        function_responses = []
        for call in response.function_calls:
            tool_map = {
                "list_calendar_events_tool": list_calendar_events_tool,
                "read_emails_tool": read_emails_tool,
                "get_contacts_tool": get_contacts_tool,
                "create_calendar_event_tool": create_calendar_event_tool,
                "update_calendar_event_tool": update_calendar_event_tool,
                "delete_calendar_event_tool": delete_calendar_event_tool,
                "send_email_tool": send_email_tool,
                "create_jira_issue_tool": create_jira_issue_tool,
                "send_slack_message_tool": send_slack_message_tool
            }
            
            func = tool_map.get(call.name)
            if func:
                print(f"Executing tool: {call.name} with args: {call.args}")
                try:
                    # Execute the tool
                    result = func(**call.args)
                    
                    # If it's a proposal tool, register the action
                    if call.name in ["create_calendar_event_tool", "update_calendar_event_tool", "delete_calendar_event_tool", "send_email_tool", "create_jira_issue_tool", "send_slack_message_tool"]:
                        action_obj = add_proposed_action(result)
                        proposed_actions.append(action_obj)
                        # Return the action object (or just the result) to the model
                        function_responses.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=call.name,
                                response={"result": result}
                            )
                        ))
                    else:
                        # Read tool, just return result
                        function_responses.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=call.name,
                                response={"result": result}
                            )
                        ))
                except Exception as tool_error:
                    print(f"Error executing tool {call.name}: {tool_error}")
                    function_responses.append(types.Part(
                        function_response=types.FunctionResponse(
                            name=call.name,
                            response={"error": str(tool_error)}
                        )
                    ))
        
        # Send function responses back to the model
        if function_responses:
            print(f"Sending function responses back to Gemini for index {index}")
            response = chat.send_message(function_responses)
            print(f"Gemini response after function execution for index {index}: {response}")
        else:
            break
            
    return proposed_actions

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
        print(indices, messages)
        set_error(context, "Messages or indices contain invalid content")
        return jsonify(**context)
    
    # process messages and output it, for the time being just return the list of messages that are relevant
    client = genai.Client(api_key=API_KEY)

    tools = [
        list_calendar_events_tool,
        read_emails_tool,
        get_contacts_tool,
        create_calendar_event_tool,
        update_calendar_event_tool,
        delete_calendar_event_tool,
        send_email_tool,
        create_jira_issue_tool,
        send_slack_message_tool
    ]
    
    # Full transcript context
    transcript_text = "Full Conversation Transcript:\n" + '\n'.join([f"[{i}] Speaker {msg.get('speaker', 'Unknown')}: {msg.get('content', '')}" for i, msg in enumerate(messages)])
    print(transcript_text)
    
    try:
        all_proposed_actions = []
        
        for index in indices:
            if index >= len(messages): continue
            
            target_message = messages[index]
            print(f"Processing attention index {index}...")
            
            actions = process_attention_item(client, tools, transcript_text, index, target_message)
            all_proposed_actions.extend(actions)
        
        context["Todos"] = all_proposed_actions

    except Exception as error:
        set_error(context, f"Error: {error}")
        return jsonify(**context)

    return jsonify(**context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
