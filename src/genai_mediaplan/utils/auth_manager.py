import json
import os
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GoogleAuthManager:
    """Manages Google OAuth authentication for multiple users"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    CLIENT_SECRET_FILE = 'client_secret_drive.json'
    
    def __init__(self):
        self.user_credentials: Dict[str, Credentials] = {}
        self.user_services: Dict[str, Dict] = {}
        self._check_oauth_setup()
    
    def _get_client_secret_path(self):
        """Get the path to the client secret file"""
        current_path = os.path.join(os.getcwd(), self.CLIENT_SECRET_FILE)
        if os.path.exists(current_path):
            return current_path
        return None
    
    def _check_oauth_setup(self):
        """Check if OAuth credentials are properly set up"""
        client_secret_path = self._get_client_secret_path()
        if not client_secret_path:
            print(f"⚠️  Warning: {self.CLIENT_SECRET_FILE} not found.")
        else:
            print(f"✅ OAuth credentials found at: {client_secret_path}")
    
    def create_auth_url(self, user_id: str, redirect_uri: str, state: str = None) -> str:
        """Create OAuth authorization URL for a user"""
        try:
            client_secret_path = self._get_client_secret_path()
            if not client_secret_path:
                raise Exception("OAuth credentials file not found.")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, 
                self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            if not hasattr(self, '_flows'):
                self._flows = {}
            self._flows[user_id] = flow
            
            auth_url, _ = flow.authorization_url(state=state)
            return auth_url
        except Exception as e:
            raise Exception(f"Failed to create auth URL: {str(e)}")
    
    def exchange_code_for_token(self, user_id: str, authorization_code: str) -> Dict:
        """Exchange authorization code for access token"""
        try:
            if user_id not in self._flows:
                raise Exception("No authorization flow found for user")
            
            flow = self._flows[user_id]
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            self.user_credentials[user_id] = creds
            self._create_services_for_user(user_id, creds)
            
            return {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes
            }
        except Exception as e:
            raise Exception(f"Failed to exchange code for token: {str(e)}")
    
    def _create_services_for_user(self, user_id: str, creds: Credentials):
        """Create Google services for a user"""
        try:
            self.user_services[user_id] = {
                'drive': build('drive', 'v3', credentials=creds),
                'slides': build('slides', 'v1', credentials=creds),
                'sheets': build('sheets', 'v4', credentials=creds)
            }
        except Exception as e:
            raise Exception(f"Failed to create services for user: {str(e)}")
    
    def get_user_services(self, user_id: str) -> Dict:
        """Get Google services for a user"""
        if user_id not in self.user_services:
            raise Exception(f"No services found for user {user_id}")
        return self.user_services[user_id]
    
    def is_user_authenticated(self, user_id: str) -> bool:
        """Check if user is authenticated"""
        return user_id in self.user_credentials and user_id in self.user_services
    
    def is_oauth_available(self) -> bool:
        """Check if OAuth credentials are available"""
        return self._get_client_secret_path() is not None

# Global instance
auth_manager = GoogleAuthManager() 