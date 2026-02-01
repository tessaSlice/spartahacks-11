import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ApiWork.utils import SCOPES

def get_services():
    """Returns the Gmail service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not set(SCOPES).issubset(set(creds.scopes or [])):
            print("Existing token lacks required scopes, re-running OAuth flow...")
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "ApiWork/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        gmail_service = build("gmail", "v1", credentials=creds)
        return gmail_service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def read_emails(gmail_service, query=None, max_results=10):
    """
    Reads a range of emails matching the query.
    
    Args:
        gmail_service: Gmail service instance.
        query (str): Search query (e.g., 'is:unread').
        max_results (int): Max number of emails to return.
        
    Returns:
        list: List of email dictionaries with id, subject, sender, snippet.
    """
    try:
        results = gmail_service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        email_data = []
        for msg in messages:
            msg_detail = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_detail.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            snippet = msg_detail.get('snippet', '')
            
            email_data.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'snippet': snippet
            })
            
        return email_data
    except HttpError as error:
        print(f"An error occurred reading emails: {error}")
        return []

def propose_send_email(recipient, subject, body):
    """
    Creates a draft structure for the frontend/agent to review.
    Returns the full action proposal dictionary.
    """
    return {
        "action": "send_email",
        "body": {
            "recipient": recipient,
            "subject": subject,
            "body": body
        }
    }

def execute_send_email(service, draft_structure):
    """
    Sends an email based on the draft structure.
    
    Args:
        service: Gmail service instance.
        draft_structure (dict): Dictionary with recipient, subject, body.
    """
    try:
        message = EmailMessage()
        message.set_content(draft_structure['body'])
        message['To'] = draft_structure['recipient']
        message['Subject'] = draft_structure['subject']
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {
            'raw': encoded_message
        }
        
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f"Message Id: {send_message['id']}")
        return send_message
    except HttpError as error:
        print(f"An error occurred sending email: {error}")
        return None