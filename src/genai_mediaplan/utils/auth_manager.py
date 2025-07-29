import json
import os
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64

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
        # Try current directory first
        current_path = os.path.join(os.getcwd(), self.CLIENT_SECRET_FILE)
        if os.path.exists(current_path):
            return current_path
        
        # Try project root directory (2 levels up from src/genai_mediaplan)
        project_root = os.path.join(os.getcwd(), '..', '..', self.CLIENT_SECRET_FILE)
        if os.path.exists(project_root):
            return project_root
        
        # Try absolute path from project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(script_dir, '..', '..', '..', self.CLIENT_SECRET_FILE)
        if os.path.exists(project_root):
            return project_root
        
        return None
    
    def _check_oauth_setup(self):
        """Check if OAuth credentials are properly set up"""
        client_secret_path = self._get_client_secret_path()
        if not client_secret_path:
            print(f"⚠️  Warning: {self.CLIENT_SECRET_FILE} not found.")
            print("   OAuth authentication features will be disabled.")
            print("   To enable OAuth:")
            print("   1. Go to Google Cloud Console")
            print("   2. Create OAuth 2.0 credentials")
            print("   3. Download and rename to client_secret_drive.json")
            print("   4. Place in project root directory")
        else:
            print(f"✅ OAuth credentials found at: {client_secret_path}")
    
    def create_auth_url(self, user_id: str, redirect_uri: str, state: str = None) -> str:
        """Create OAuth authorization URL for a user"""
        try:
            client_secret_path = self._get_client_secret_path()
            if not client_secret_path:
                raise Exception(
                    f"OAuth credentials file '{self.CLIENT_SECRET_FILE}' not found. "
                    "Please download your OAuth credentials from Google Cloud Console "
                    "and place them in the project root directory."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, 
                self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Store flow for later use
            if not hasattr(self, '_flows'):
                self._flows = {}
            self._flows[user_id] = flow
            
            # Create authorization URL with state
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
            
            # Get credentials
            creds = flow.credentials
            
            # Store credentials
            self.user_credentials[user_id] = creds
            
            # Create services
            self._create_services_for_user(user_id, creds)
            
            # Return token info
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
    
    def set_user_credentials(self, user_id: str, credentials_data: Dict):
        """Set user credentials from stored data"""
        try:
            creds = Credentials(
                token=credentials_data.get("access_token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret"),
                scopes=credentials_data.get("scopes", self.SCOPES)
            )
            
            # Refresh if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            self.user_credentials[user_id] = creds
            self._create_services_for_user(user_id, creds)
            
        except Exception as e:
            raise Exception(f"Failed to set user credentials: {str(e)}")
    
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
    
    def refresh_user_token(self, user_id: str):
        """Refresh user's access token"""
        if user_id not in self.user_credentials:
            raise Exception(f"No credentials found for user {user_id}")
        
        creds = self.user_credentials[user_id]
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._create_services_for_user(user_id, creds)
    
    def remove_user(self, user_id: str):
        """Remove user's credentials and services"""
        if user_id in self.user_credentials:
            del self.user_credentials[user_id]
        if user_id in self.user_services:
            del self.user_services[user_id]
        if hasattr(self, '_flows') and user_id in self._flows:
            del self._flows[user_id]
    
    def is_oauth_available(self) -> bool:
        """Check if OAuth credentials are available"""
        return self._get_client_secret_path() is not None

# Global instance
auth_manager = GoogleAuthManager() 