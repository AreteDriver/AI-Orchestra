"""Token-based authentication."""

from datetime import datetime, timedelta
from typing import Optional

from test_ai.config import get_settings


class TokenAuth:
    """Simple token-based authentication."""

    def __init__(self):
        self.settings = get_settings()
        self._tokens = {}

    def create_token(self, user_id: str) -> str:
        """Create a new access token."""
        token = f"token_{user_id}_{datetime.now().timestamp()}"
        expiry = datetime.now() + timedelta(
            minutes=self.settings.access_token_expire_minutes
        )
        self._tokens[token] = {"user_id": user_id, "expiry": expiry}
        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Verify token and return user_id if valid."""
        if token not in self._tokens:
            return None

        token_data = self._tokens[token]
        if datetime.now() > token_data["expiry"]:
            del self._tokens[token]
            return None

        return token_data["user_id"]

    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False


# Global instance
_auth = TokenAuth()


def create_access_token(user_id: str) -> str:
    """Create an access token for a user."""
    return _auth.create_token(user_id)


def verify_token(token: str) -> Optional[str]:
    """Verify a token and return user_id if valid."""
    return _auth.verify_token(token)
