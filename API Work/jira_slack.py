from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from jira import JIRA

JIRA_SERVER = 'https://grantow.atlassian.net'
JIRA_USER = 'grantow@umich.edu'

# returns the slack web client
def get_slack_client():
    return WebClient(token=SLACK_API_TOKEN)

# inputs slack web client and message, sends it to all hackathon channel
def send_slack_message(client, message):
    client.chat_postMessage(
    channel="#all-hackathon",
    text=message
    )

# returns the jira web client
def get_jira_client():
    return JIRA(
    options={'server': JIRA_SERVER},
    basic_auth=(JIRA_USER, JIRA_API_TOKEN)
    )

# inputs jira web client, summary, and description, creates an issue
def create_jira_issue(client, summary, description):
    new_issue = client.create_issue(project='SCRUM', summary=summary,
                              description=description, issuetype={'id': 10001})
