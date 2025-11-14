"""Gmail API client for accessing emails."""

import os
import base64
import pickle
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email_classifier import RecruitingEmailClassifier
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
        """Search for emails matching the query with pagination support."""
        try:
            all_messages = []
            page_token = None
            
            while True:
                # Build request parameters
                request_params = {
                    'userId': 'me',
                    'q': query,
                    'maxResults': min(max_results, 500)  # Gmail API max is 500 per page
                }
                
                if page_token:
                    request_params['pageToken'] = page_token
                
                results = self.service.users().messages().list(**request_params).execute()
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                
                # Check if there are more pages
                page_token = results.get('nextPageToken')
                if not page_token or len(all_messages) >= max_results:
                    break
            
            # Limit to max_results if specified
            if max_results and len(all_messages) > max_results:
                all_messages = all_messages[:max_results]
            
            return all_messages
            
        except HttpError as error:
            print(f"Error searching emails: {error}")
            return []
    
    def get_job_application_emails(self, days_back=30):
        """
        Fetch recent emails and use Gemini AI to decide which ones are job-related.
        Removes all manual filters (no domain or subject lists).
        """
        classifier = RecruitingEmailClassifier()

        # Step 1: Pull all recent emails (unfiltered) - increase limit to 500
        query = f"newer_than:{days_back}d"
        print(f"📬 Fetching all emails from the past {days_back} days for AI classification...")
        messages = self.search_emails(query, max_results=500)
        if not messages:
            print("⚠️ No emails retrieved from Gmail.")
            return []

        job_emails = []

        # Step 2: Iterate and classify each email
        for msg in messages:
            if not isinstance(msg, dict) or "id" not in msg:
                print("⚠️ Skipping malformed Gmail message (missing 'id')")
                continue

            details = self.get_email_details(msg["id"])
            if not details:
                continue

            subject = details.get("subject", "No subject")
            try:
                if classifier.is_job_related(details):
                    print(f"✅ Job-related email detected: {subject[:80]}")
                    job_emails.append(details)
            except Exception as e:
                print(f"⚠️ Error during AI classification for '{subject}': {e}")
                continue

        print(f"\n📊 AI identified {len(job_emails)} job-related emails out of {len(messages)} total.")
        return job_emails

    
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
                            body = re.sub('<[^<]+?>', '', html_content)
                elif part['mimeType'].startswith('multipart/'):
                    # Recursively handle nested multipart messages
                    nested_body = self._extract_email_body(part)
                    if nested_body:
                        body += nested_body
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
                    body = re.sub('<[^<]+?>', '', html_content)
            elif payload['mimeType'].startswith('multipart/'):
                # Handle multipart messages
                nested_body = self._extract_email_body(payload)
                if nested_body:
                    body += nested_body
        
        return body.strip()
    
    def get_recent_job_emails(self, days_back=7):
        """
        Get recent job-related emails classified by Gemini.
        (No need to re-fetch by 'id' — they already contain all details.)
        """
        job_emails = self.get_job_application_emails(days_back)
        print(f"📦 Returning {len(job_emails)} fully parsed job emails.")
        return job_emails

