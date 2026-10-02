"""
ReNexa — Authentication Service (Phase 9B)
===========================================
Provides user sign-up, sign-in, session management, and JWT token handling
with Supabase Auth over standard REST APIs, with safe local guest fallback.

Security Principles:
- Uses ONLY the public anon key.
- Never logs, saves, or stores plain text passwords.
- Binds user UUIDs directly to database ownership.
- Falls back safely to local guest mode when unconfigured.
"""

import os
import logging
from typing import Dict, Any, Optional
import requests

from database.database import get_supabase_config, is_database_configured

logger = logging.getLogger("renexa.auth")

# Session state keys for Streamlit integration
AUTH_USER_KEY = "renexa_auth_user"
AUTH_TOKEN_KEY = "renexa_auth_token"


class AuthService:
    """Supabase Auth REST client handler."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        cfg = get_supabase_config()
        anon_key = cfg["anon_key"] or ""
        headers = {
            "apikey": anon_key,
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            headers["Authorization"] = f"Bearer {anon_key}"
        return headers

    def signup(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user account with Supabase Auth.
        Never stores or logs the password.
        """
        if not is_database_configured():
            return {
                "success": False,
                "error": "Supabase credentials are not configured. Operating in local fallback mode.",
                "user": None,
                "token": None,
            }

        if not email or not password or len(password) < 6:
            return {
                "success": False,
                "error": "Valid email and password (min 6 chars) required.",
                "user": None,
                "token": None,
            }

        cfg = get_supabase_config()
        endpoint = f"{cfg['url'].rstrip('/')}/auth/v1/signup"

        payload = {
            "email": email.strip().lower(),
            "password": password,
            "data": {
                "display_name": display_name.strip() if display_name else email.split("@")[0]
            },
        }

        try:
            resp = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                user = data.get("user") or data
                token = data.get("access_token")
                return {
                    "success": True,
                    "user": {
                        "id": user.get("id"),
                        "email": user.get("email"),
                        "display_name": user.get("user_metadata", {}).get("display_name")
                        or email.split("@")[0],
                    },
                    "token": token,
                    "error": None,
                }
            else:
                err_msg = "Signup failed"
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("msg") or err_json.get("error_description") or err_json.get("message") or err_msg
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": f"{err_msg} (HTTP {resp.status_code})",
                    "user": None,
                    "token": None,
                }
        except Exception as e:
            logger.warning(f"Signup network exception: {e}")
            return {
                "success": False,
                "error": "Network error reaching authentication server.",
                "user": None,
                "token": None,
            }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate an existing user with email and password.
        """
        if not is_database_configured():
            return {
                "success": False,
                "error": "Supabase credentials are not configured. Operating in local fallback mode.",
                "user": None,
                "token": None,
            }

        if not email or not password:
            return {
                "success": False,
                "error": "Email and password are required.",
                "user": None,
                "token": None,
            }

        cfg = get_supabase_config()
        endpoint = f"{cfg['url'].rstrip('/')}/auth/v1/token?grant_type=password"

        payload = {
            "email": email.strip().lower(),
            "password": password,
        }

        try:
            resp = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                user = data.get("user", {})
                token = data.get("access_token")
                return {
                    "success": True,
                    "user": {
                        "id": user.get("id"),
                        "email": user.get("email"),
                        "display_name": user.get("user_metadata", {}).get("display_name")
                        or email.split("@")[0],
                    },
                    "token": token,
                    "error": None,
                }
            else:
                err_msg = "Invalid email or password"
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error_description") or err_json.get("msg") or err_msg
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": f"{err_msg} (HTTP {resp.status_code})",
                    "user": None,
                    "token": None,
                }
        except Exception as e:
            logger.warning(f"Login network exception: {e}")
            return {
                "success": False,
                "error": "Network error reaching authentication server.",
                "user": None,
                "token": None,
            }

    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token and fetch user identity."""
        if not is_database_configured() or not token:
            return None

        cfg = get_supabase_config()
        endpoint = f"{cfg['url'].rstrip('/')}/auth/v1/user"

        try:
            resp = requests.get(
                endpoint,
                headers=self._get_headers(token=token),
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                user = resp.json()
                return {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "display_name": user.get("user_metadata", {}).get("display_name")
                    or user.get("email", "").split("@")[0],
                }
            return None
        except Exception:
            return None


# Global singleton
_auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get global AuthService instance."""
    return _auth_service
