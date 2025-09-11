#!/usr/bin/env python3
"""
Google Calendar Token Generator
Generates a fresh token.pickle file for Google Calendar API access
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

def generate_token():
    """Generate a fresh Google Calendar API token."""
    
    credentials_path = "./credentials.json"
    token_path = "./token.pickle"
    
    if not os.path.exists(credentials_path):
        print(f"❌ Error: {credentials_path} not found!")
        print("Please download your credentials.json file from Google Cloud Console")
        return False
    
    print("🔄 Starting OAuth flow...")
    print("This will open your browser for Google authentication...")
    
    # Create the flow using the client secrets file
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    
    # Run the flow to get credentials
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)
    
    print(f"✅ Token saved to {token_path}")
    return True

if __name__ == '__main__':
    print("🚀 Google Calendar Token Generator")
    print("=" * 40)
    
    success = generate_token()
    
    if success:
        print("✅ Success! Your Google Calendar token is ready.")
        print("Now restart your FastAPI server to use the new token.")
    else:
        print("❌ Failed to generate token.")