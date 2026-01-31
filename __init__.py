# receive POST request, parse it, output to agentic AI model that will run TODOs

"""
TODO:
1. Host it locally on Flask to confirm the POST request works, output the TODO requests (but in reality we just want to call whatever function that the agentic AI model performs)
2. Figure out how to host it on DigitalOcean with a tutorial located here: https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-app-using-gunicorn-to-app-platform (consider using ngrok if digitalocean doesn't end up working out)

parse post request, which is structured like so: 
"session_id": string
"attention_indices": array of ints
"messages": array of {"content": string, "speaker": int}
"""

from flask import Flask, jsonify, request
from google import genai
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY")

# TODO: consider adding more attributes if requested
class ToDoList(BaseModel):
    todo_items: List[str]

def set_error(context, error_message):
    context["Status"] = 400
    context["Error"] = error_message

# create a Flask server
app = Flask(__name__)

@app.route('/GetTodos', methods=["POST"])
def get_todos():
    data = request.get_json(force=False, silent=False)
    context = {
        "Status": 200,
        "Error": "",
        # list of strings
        "Todos": []
    }

    # process the POST request data
    if 'attention_indices' not in data or 'messages' not in data:
        set_error("Improperly formatted request, attention_indices or messages is not included in JSON payload")
        return jsonify(**context)
        
    indices = data['attention_indices']
    messages = data['messages']

    if not indices or not messages or indices[-1] >= len(messages):
        set_error("Messages or indices contain invalid content")
        return jsonify(**context)
    
    # process messages and output it, for the time being just return the list of messages that are relevant
    # TODO: create new API key through GEMINI studio
    client = genai.Client(api_key=API_KEY)
    response = ""

    # NOTE: we use structured outputs. Docs: https://ai.google.dev/gemini-api/docs/structured-output?example=recipe
    try:
        highlighted_messages = [messages[index] for index in indices]
        bulleted_list = '\n'.join(["- " + substr for substr in highlighted_messages])
        prompt = f"Based on the bullet points I've provided below, construct a TODO list: \n{bulleted_list}"
        response = client.models.generate_content(
            # TODO: choose a model
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ToDoList.model_json_schema(),
            },
        )
    except Exception as e:
        set_error("Gemini error, likely the token limits have been exceeded")
        return jsonify(**context)
    if not response:
        set_error("No response received from Gemini")
        return jsonify(**context)

    # TODO: do something with the formatted response output (that is a dictionary)
    # todo_items is just a list of strings
    todo_items = response['todo_items']

    # TODO: do something with the todo items with the agent
    context["Todos"] = todo_items

    return jsonify(**context)
