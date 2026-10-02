"""
ReNexa — Authentication Service Tests (Phase 9B)
================================================
Verifies authentication flows, JWT token handling, credential security,
and local guest mode fallback without requiring a live Supabase account.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from database.auth import AuthService, get_auth_service, AUTH_USER_KEY, AUTH_TOKEN_KEY


def test_auth_service_unconfigured_fallback():
    """Verify signup and login gracefully notify when Supabase credentials are missing."""
    with patch("database.auth.is_database_configured", return_value=False):
        service = AuthService()

        res_signup = service.signup("test@example.com", "secret123")
        assert res_signup["success"] is False
        assert "fallback" in res_signup["error"].lower() or "not configured" in res_signup["error"].lower()
        assert res_signup["user"] is None
        assert res_signup["token"] is None

        res_login = service.login("test@example.com", "secret123")
        assert res_login["success"] is False
        assert res_login["user"] is None
        assert res_login["token"] is None


def test_auth_validation_rejects_empty_inputs():
    """Verify email and minimum password length constraints."""
    with patch("database.auth.is_database_configured", return_value=True):
        service = AuthService()

        # Short password
        res = service.signup("test@example.com", "123")
        assert res["success"] is False
        assert "min 6 chars" in res["error"]

        # Missing email
        res2 = service.login("", "secret123")
        assert res2["success"] is False


def test_auth_mock_signup_success():
    """Verify successful sign-up parses user UUID and JWT token."""
    with patch("database.auth.is_database_configured", return_value=True), patch(
        "database.auth.get_supabase_config",
        return_value={"url": "https://testproj.supabase.co", "anon_key": "anon-key-123"},
    ), patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "mock-jwt-token-xyz",
            "user": {
                "id": "usr-uuid-1111",
                "email": "greenuser@renexa.org",
                "user_metadata": {"display_name": "Green Hero"},
            },
        }
        mock_post.return_value = mock_resp

        service = AuthService()
        res = service.signup("greenuser@renexa.org", "strongpass123", display_name="Green Hero")

        assert res["success"] is True
        assert res["token"] == "mock-jwt-token-xyz"
        assert res["user"]["id"] == "usr-uuid-1111"
        assert res["user"]["email"] == "greenuser@renexa.org"
        assert res["user"]["display_name"] == "Green Hero"

        # Verify password is NEVER in return structure
        assert "password" not in json.dumps(res)


def test_auth_mock_login_success():
    """Verify successful sign-in parses access token and user identity."""
    with patch("database.auth.is_database_configured", return_value=True), patch(
        "database.auth.get_supabase_config",
        return_value={"url": "https://testproj.supabase.co", "anon_key": "anon-key-123"},
    ), patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "login-token-456",
            "user": {
                "id": "usr-uuid-2222",
                "email": "eco@renexa.org",
                "user_metadata": {"display_name": "EcoWarrior"},
            },
        }
        mock_post.return_value = mock_resp

        service = AuthService()
        res = service.login("eco@renexa.org", "mypassword")

        assert res["success"] is True
        assert res["token"] == "login-token-456"
        assert res["user"]["id"] == "usr-uuid-2222"
        assert res["user"]["display_name"] == "EcoWarrior"


def test_auth_mock_login_invalid_credentials():
    """Verify failed login returns error message cleanly."""
    with patch("database.auth.is_database_configured", return_value=True), patch(
        "database.auth.get_supabase_config",
        return_value={"url": "https://testproj.supabase.co", "anon_key": "anon-key-123"},
    ), patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error_description": "Invalid login credentials"}
        mock_post.return_value = mock_resp

        service = AuthService()
        res = service.login("eco@renexa.org", "wrongpass")

        assert res["success"] is False
        assert "Invalid login credentials" in res["error"]
        assert res["user"] is None


def test_auth_get_user_from_token():
    """Verify fetching user profile from active JWT bearer token."""
    with patch("database.auth.is_database_configured", return_value=True), patch(
        "database.auth.get_supabase_config",
        return_value={"url": "https://testproj.supabase.co", "anon_key": "anon-key-123"},
    ), patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "usr-uuid-3333",
            "email": "recycle@renexa.org",
            "user_metadata": {"display_name": "RecycleChampion"},
        }
        mock_get.return_value = mock_resp

        service = AuthService()
        user = service.get_user_from_token("valid-jwt-token")

        assert user is not None
        assert user["id"] == "usr-uuid-3333"
        assert user["display_name"] == "RecycleChampion"


def test_singleton_getter():
    """Verify get_auth_service returns singleton instance."""
    s1 = get_auth_service()
    s2 = get_auth_service()
    assert s1 is s2
