"""
ReNexa — Database Module (Phase 9A)
===================================
Provides database client abstraction, configuration management,
and local fallback persistence.
"""

from database.database import (
    get_database,
    is_database_configured,
    get_database_status,
    save_scan,
    save_waste_profile,
    save_recommendation,
    save_recommendations,
    save_execution_feedback,
    get_user_scans,
    get_scan_recommendations,
    get_user_recommendations,
    get_user_feedback,
    get_all_feedback,
    get_user_dashboard_metrics,
)
from database.auth import (
    AuthService,
    get_auth_service,
    AUTH_USER_KEY,
    AUTH_TOKEN_KEY,
)

__all__ = [
    "get_database",
    "is_database_configured",
    "get_database_status",
    "save_scan",
    "save_waste_profile",
    "save_recommendation",
    "save_recommendations",
    "save_execution_feedback",
    "get_user_scans",
    "get_scan_recommendations",
    "get_user_recommendations",
    "get_user_feedback",
    "get_all_feedback",
    "get_user_dashboard_metrics",
    "AuthService",
    "get_auth_service",
    "AUTH_USER_KEY",
    "AUTH_TOKEN_KEY",
]
