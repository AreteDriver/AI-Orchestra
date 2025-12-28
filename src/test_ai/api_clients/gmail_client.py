"""Gmail API client wrapper."""
from typing import Optional, List, Dict
from test_ai.config import get_settings


class GmailClient:
    """Wrapper for Gmail API."""
    
    def __init__(self):
        settings = get_settings()
        self.credentials_path = settings.gmail_credentials_path
        self.service = None
    
    def is_configured(self) -> bool:
        """Check if Gmail client is configured."""
        return self.credentials_path is not None
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        if not self.is_configured():
            return False
        
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import os.path
            import pickle
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            creds = None
            
            token_path = 'token.pickle'
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception:
            return False
    
    def list_messages(
        self,
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict]:
        """List Gmail messages."""
        if not self.service:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query or ''
            ).execute()
            
            messages = results.get('messages', [])
            return messages
        except Exception:
            return []
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """Get a specific message."""
        if not self.service:
            return None
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            return message
        except Exception:
            return None
    
    def extract_email_body(self, message: Dict) -> str:
        """Extract email body from message."""
        try:
            import base64
            
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = message['payload']['body'].get('data', '')
                return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception:
            return ""
