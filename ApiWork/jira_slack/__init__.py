from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from jira import JIRA
import os
from dotenv import load_dotenv
load_dotenv(override=True)
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

JIRA_SERVER = 'https://grantow.atlassian.net'
JIRA_USER = 'grantow@umich.edu'

# returns the slack web client
def get_slack_client():
    return WebClient(token=SLACK_API_TOKEN)

def propose_send_slack_message(message):
    return {
        "action": "send_slack_message",
        "body": {
            "message": message
        }
    }

# inputs slack web client and message, sends it to all hackathon channel
def execute_send_slack_message(client, data):
    message = data.get('body', {}).get('message')
    try:
        response = client.chat_postMessage(
            channel="#all-hackathon",
            text=message
        )
        return {"status": "success", "ts": response['ts']}
    except SlackApiError as e:
        print(f"Error sending message: {e}")
        return {"status": "error", "message": str(e)}

# returns the jira web client
def get_jira_client():
    return JIRA(
        options={'server': JIRA_SERVER},
        basic_auth=(JIRA_USER, JIRA_API_TOKEN)
    )

def propose_create_jira_issue(summary, description):
    return {
        "action": "create_jira_issue",
        "body": {
            "summary": summary,
            "description": description
        }
    }

# inputs jira web client, summary, and description, creates an issue
def execute_create_jira_issue(client, data):
    summary = data.get('body', {}).get('summary')
    description = data.get('body', {}).get('description')
    try:
        new_issue = client.create_issue(project='SCRUM', summary=summary,
                                description=description, issuetype={'id': 10001})
        return {"status": "success", "key": new_issue.key, "id": new_issue.id}
    except Exception as e:
        print(f"Error creating issue: {e}")
        return {"status": "error", "message": str(e)}

