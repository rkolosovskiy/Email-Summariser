"""
Gmail Authentication Module
Handles OAuth2 authentication with Gmail API
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailAuthenticator:
    """Handles Gmail API authentication"""

    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        """
        Initialize the authenticator

        Args:
            credentials_path: Path to the OAuth2 credentials JSON file
            token_path: Path to save/load the authentication token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None

    def authenticate(self):
        """
        Authenticate with Gmail API using OAuth2

        Returns:
            Google credentials object
        """
        # Check if we have valid credentials saved
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing expired credentials...")
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}\n"
                        f"Please download OAuth2 credentials from Google Cloud Console"
                    )

                print("Starting OAuth2 authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                print("Using fixed port 8080 for authentication...")
                # The credentials.json file might contain a different redirect_uri if not updated,
                # but we can try to force the redirect_uri that the user should have added to their console.
                flow.redirect_uri = 'http://localhost:8080/'
                
                # run_local_server will use this host and port
                self.creds = flow.run_local_server(port=8080, open_browser=False)
                
                print(f"Please open this URL in your browser: {flow.authorization_url()[0]}")

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            print("Authentication successful!")

        return self.creds

    def get_gmail_service(self):
        """
        Get an authenticated Gmail API service

        Returns:
            Gmail API service object
        """
        if not self.creds:
            self.authenticate()

        return build('gmail', 'v1', credentials=self.creds)
