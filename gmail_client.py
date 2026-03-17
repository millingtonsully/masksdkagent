import os
import io
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailClient:
    """A minimal client for interacting with the Gmail API."""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Handle the OAuth2 flow and caching of credentials."""
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "The 'credentials.json' file is missing. "
                        "Please download it from the Google Cloud Console "
                        "and place it in the root directory."
                    )
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
        except HttpError as error:
            print(f"An error occurred during build: {error}")

    def send_email(self, to_email: str, subject: str, body: str) -> str:
        """Constructs and sends an email via the Gmail API."""
        if not self.service:
             return "Error: Gmail client not authenticated."
             
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        
        # The Gmail API requires the email to be base64url encoded
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        create_message = {'raw': raw_message}

        try:
            send_message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            print(f"\n[Gmail API] Email successfully sent to '{to_email}' (Message ID: {send_message['id']})")
            return f"Successfully sent email to {to_email}."
        except HttpError as error:
            print(f"An error occurred sending the email: {error}")
            return f"Failed to send email to {to_email}: {error}"

# For standalone testing
if __name__ == '__main__':
    client = GmailClient()
    print("GmailClient initialized successfully.")
