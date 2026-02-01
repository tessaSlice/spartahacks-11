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
    """Returns the People services."""
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
        people_service = build("people", "v1", credentials=creds)
        return people_service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def get_contacts(people_service, query=None):
    """
    Gets contacts and recommended recipients (other contacts).
    
    Args:
        people_service: The People API service instance.
        query (str): Optional search query to filter contacts.
    
    Returns:
        list: List of contact dictionaries with name, email, type.
    """
    contacts = []
    
    try:
        # Get 'connections' (my contacts)
        results = people_service.people().connections().list(
            resourceName='people/me',
            pageSize=100,
            personFields='names,emailAddresses'
        ).execute()
        connections = results.get('connections', [])
        
        for person in connections:
            names = person.get('names', [])
            emails = person.get('emailAddresses', [])
            if names and emails:
                name = names[0].get('displayName')
                email = emails[0].get('value')
                
                # Filter if query is provided
                if query:
                    if query.lower() in name.lower() or query.lower() in email.lower():
                        contacts.append({
                            'name': name,
                            'email': email,
                            'type': 'contact'
                        })
                else:
                    contacts.append({
                        'name': name,
                        'email': email,
                        'type': 'contact'
                    })

        # Get 'other contacts' (frequently contacted)
        # Note: searchContacts is better but requires different setup, so we filter locally for now
        other_results = people_service.otherContacts().list(
            pageSize=100,
            readMask='names,emailAddresses'
        ).execute()
        other_contacts = other_results.get('otherContacts', [])
        
        for person in other_contacts:
            names = person.get('names', [])
            emails = person.get('emailAddresses', [])
            if emails:
                 name = names[0].get('displayName') if names else 'Unknown'
                 email = emails[0].get('value')
                 
                 # Filter if query is provided
                 if query:
                     if query.lower() in name.lower() or query.lower() in email.lower():
                        contacts.append({
                            'name': name,
                            'email': email,
                            'type': 'other'
                        })
                 else:
                     contacts.append({
                        'name': name,
                        'email': email,
                        'type': 'other'
                    })
                
        return contacts
    except HttpError as error:
        print(f"An error occurred fetching contacts: {error}")
        return []