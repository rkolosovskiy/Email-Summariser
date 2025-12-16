
import os
from gmail_auth import GmailAuthenticator

def main():
    print("Loading local credentials to prepare for Cloud deployment...")
    
    # helper to load credentials using existing logic
    auth = GmailAuthenticator()
    creds = auth.authenticate()
    
    print("\n" + "="*60)
    print("CLOUD DEPLOYMENT CREDENTIALS")
    print("="*60)
    print("Copy these values to your Google Cloud Run Environment Variables:\n")
    
    print(f"GMAIL_CLIENT_ID={creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    
    print("\n" + "="*60)
    print("NOTE: If GMAIL_REFRESH_TOKEN is None, you might need to re-authenticate")
    print("by deleting token.pickle and running main.py again.")

if __name__ == "__main__":
    main()
