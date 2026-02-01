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
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import sys
import uuid
import json
import datetime
from dotenv import load_dotenv

sys.path.append(os.path.abspath("API work"))
import calendar
import gmail
import contacts

load_dotenv()
API_KEY = os.getenv("API_KEY")

# create a Flask server
app = Flask(__name__)

# In-memory store for proposed actions
# Structure: { uuid: { uuid: str, data: dict, status: 'pending' } }
PROPOSED_ACTIONS: Dict[str, Any] = {}

# Initialize Calendar Service
calendar_service = None
if quickstart:
    calendar_service = quickstart.get_calendar_service()

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
    """Execute the action using quickstart.py."""
    if action_id not in PROPOSED_ACTIONS:
        return jsonify({"error": "Action not found"}), 404
    
    action = PROPOSED_ACTIONS[action_id]
    # Allow client to send updated data in the execute request
    req_data = request.get_json()
    if req_data and 'data' in req_data:
        action['data'] = req_data['data']

    if not quickstart or not calendar_service:
        return jsonify({"error": "Calendar service not available"}), 500

    try:
        print(f"Executing action {action_id}: {action['data']}")
        result = quickstart.execute_event_alternation(calendar_service, action['data'])
        
        # Remove from pending list after successful execution
        del PROPOSED_ACTIONS[action_id]
        
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        print(f"Execution failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Existing Endpoints ---

@app.route('/GetTodos', methods=["GET", "POST"])
def get_todos():
    print("Received request")
    data = request.get_json(force=False, silent=False)
    context = {
        "Status": 200,
        "Error": "",
        # list of strings
        "Todos": []
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
    # TODO: create new API key through GEMINI studio
    # client = genai.Client(api_key=API_KEY)
    # response = ""
    # # NOTE: we use structured outputs. Docs: https://ai.google.dev/gemini-api/docs/structured-output?example=recipe
    # try:
    #     highlighted_messages = [messages[index] for index in indices]
    #     bulleted_list = '\n'.join(["- " + substr for substr in highlighted_messages])
    #     prompt = f"Based on the bullet points I've provided below, construct a TODO list: \n{bulleted_list}"
    #     response = client.models.generate_content(
    #         # TODO: choose a model
    #         model="gemini-2.0-flash",
    #         contents=prompt,
    #         config={
    #             "response_mime_type": "application/json",
    #             "response_json_schema": ToDoList.model_json_schema(),
    #         },
    #     )
    # except Exception as e:
    #     set_error("Gemini error, likely the token limits have been exceeded")
    #     return jsonify(**context)
    # if not response:
    #     set_error("No response received from Gemini")
    #     return jsonify(**context)

    # TODO: do something with the formatted response output (that is a dictionary)
    # todo_items is just a list of strings
    # todo_items = response['todo_items']

    # TODO: do something with the todo items with the agent
    todo_items = ["temporary", "fix", "this"]
    context["Todos"] = todo_items

    return jsonify(**context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
