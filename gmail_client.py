"""Gmail API client for accessing emails."""

import os
import base64
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, MAX_EMAILS_PER_CHECK

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailClient:
    """Gmail API client for reading emails."""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(GMAIL_TOKEN_FILE):
            with open(GMAIL_TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {GMAIL_CREDENTIALS_FILE}\n"
                        "Please download your OAuth2 credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    GMAIL_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(GMAIL_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail API authenticated successfully!")
    
    def search_emails(self, query, max_results=MAX_EMAILS_PER_CHECK):
        """Search for emails matching the query."""
        try:
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return messages
            
        except HttpError as error:
            print(f"Error searching emails: {error}")
            return []
    
    def get_job_application_emails(self, days_back=30):
        """Get emails that might be job application confirmations."""
        from config import JOB_PLATFORM_PATTERNS, JOB_EMAIL_SUBJECT_PATTERNS
        
        # Build search query
        query_parts = []
        
        # Search for job platform emails
        for platform in JOB_PLATFORM_PATTERNS:
            query_parts.append(f"from:{platform}")
        
        # Search for job-related subjects
        for subject_pattern in JOB_EMAIL_SUBJECT_PATTERNS:
            query_parts.append(f'subject:"{subject_pattern}"')
        
        # Combine with OR logic and date filter
        query = f"({' OR '.join(query_parts)}) newer_than:{days_back}d"
        
        print(f"Searching for job emails with query: {query}")
        return self.search_emails(query)
    
    def get_email_details(self, message_id):
        """Get detailed information about a specific email."""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_email_message(message)
            
        except HttpError as error:
            print(f"Error getting email details: {error}")
            return None
    
    def _parse_email_message(self, message):
        """Parse Gmail message into structured data."""
        headers = message['payload'].get('headers', [])
        
        # Extract headers
        email_data = {
            'message_id': message['id'],
            'thread_id': message['threadId'],
            'date': None,
            'subject': None,
            'from': None,
            'to': None,
            'body': None
        }
        
        # Parse headers
        for header in headers:
            name = header['name'].lower()
            value = header['value']
            
            if name == 'date':
                email_data['date'] = value
            elif name == 'subject':
                email_data['subject'] = value
            elif name == 'from':
                email_data['from'] = value
            elif name == 'to':
                email_data['to'] = value
        
        # Extract body
        email_data['body'] = self._extract_email_body(message['payload'])
        
        return email_data
    
    def _extract_email_body(self, payload):
        """Extract email body text from payload."""
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    # Prefer plain text, but use HTML if no plain text
                    if not body:
                        data = part['body'].get('data')
                        if data:
                            html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Simple HTML tag removal (you might want to use BeautifulSoup for better parsing)
                            import re
                            body = re.sub('<[^<]+?>', '', html_content)
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                    import re
                    body = re.sub('<[^<]+?>', '', html_content)
        
        return body.strip()
    
    def get_recent_job_emails(self, days_back=7):
        """Get recent job application emails."""
        messages = self.get_job_application_emails(days_back)
        email_details = []
        
        for message in messages:
            details = self.get_email_details(message['id'])
            if details:
                email_details.append(details)
        
        return email_details
