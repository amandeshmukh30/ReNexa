"""
ReNexa — Database Service (Phase 9A)
====================================
Provides transparent data access for scans, waste profiles,
recommendations, and outcome validation feedback.

Features:
- Detects Supabase credentials (SUPABASE_URL, SUPABASE_ANON_KEY).
- Seamlessly falls back to structured local JSON storage when Supabase is unconfigured.
- Prevents credential leakage in logs and exception messages.
- Fully compatible with Phase 8 outcome validation structures.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import requests

from database.models import (
    create_scan_record,
    create_waste_profile_record,
    create_recommendation_record,
    create_feedback_record,
)

logger = logging.getLogger("renexa.database")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

LOCAL_FILES = {
    "scans": os.path.join(DATA_DIR, "scans.json"),
    "waste_profiles": os.path.join(DATA_DIR, "waste_profiles.json"),
    "recommendations": os.path.join(DATA_DIR, "recommendations.json"),
    "execution_feedback": os.path.join(DATA_DIR, "outcome_feedback.json"),
}


def _load_env_file_if_present():
    """Lightweight loader for .env key-values if not in os.environ."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


_load_env_file_if_present()


def get_supabase_config() -> Dict[str, Optional[str]]:
    """Retrieve Supabase URL and anon key safely from environment or Streamlit Secrets."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()

    if not url or not anon_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if not url and "SUPABASE_URL" in st.secrets:
                    url = str(st.secrets["SUPABASE_URL"]).strip()
                if not anon_key and "SUPABASE_ANON_KEY" in st.secrets:
                    anon_key = str(st.secrets["SUPABASE_ANON_KEY"]).strip()
        except Exception:
            pass

    return {
        "url": url if url else None,
        "anon_key": anon_key if anon_key else None,
    }


def is_database_configured() -> bool:
    """Check whether valid Supabase credentials are configured."""
    cfg = get_supabase_config()
    return bool(cfg["url"] and cfg["anon_key"])


def get_database_status() -> Dict[str, Any]:
    """
    Get current database operational status for diagnostics.
    Never exposes raw secrets or keys.
    """
    cfg = get_supabase_config()
    configured = is_database_configured()
    masked_url = None
    if cfg["url"]:
        # Mask middle of URL for secure display
        parts = cfg["url"].split("//")
        scheme = parts[0] + "//" if len(parts) > 1 else "https://"
        domain = parts[-1]
        if len(domain) > 12:
            masked_url = f"{scheme}{domain[:6]}...{domain[-6:]}"
        else:
            masked_url = f"{scheme}{domain}"

    return {
        "configured": configured,
        "mode": "supabase_postgresql" if configured else "local_fallback",
        "url_masked": masked_url,
        "storage_target": "Supabase Cloud" if configured else "Local JSON Data Store",
    }


# ------------------------------------------------------------------------------
# LOCAL FALLBACK HELPERS
# ------------------------------------------------------------------------------

def _read_local_json(file_path: str) -> List[Dict[str, Any]]:
    """Read a local JSON file safely, returning an empty list on error."""
    if not os.path.isfile(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning(f"Error reading local file {os.path.basename(file_path)}: {e}")
        return []


def _append_local_json(file_path: str, record: Dict[str, Any]) -> bool:
    """Append a record to a local JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    records = _read_local_json(file_path)
    records.append(record)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to append record to {file_path}: {e}")
        return False


# ------------------------------------------------------------------------------
# SUPABASE REST CLIENT
# ------------------------------------------------------------------------------

class SupabaseClient:
    """Lightweight REST client for Supabase PostgreSQL tables."""

    def __init__(self, url: str, anon_key: str, token: Optional[str] = None, timeout: int = 10):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.token = token
        self.timeout = timeout
        self.headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.token}" if self.token else f"Bearer {self.anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def insert(self, table: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a single record into table."""
        endpoint = f"{self.url}/rest/v1/{table}"
        try:
            resp = requests.post(
                endpoint,
                headers=self.headers,
                json=record,
                timeout=self.timeout,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return data[0] if isinstance(data, list) and len(data) > 0 else record
            else:
                logger.warning(f"Supabase insert error on {table}: HTTP {resp.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Supabase connection error inserting to {table}: {e}")
            return None

    def query(self, table: str, params: Optional[Dict[str, str]] = None) -> Optional[List[Dict[str, Any]]]:
        """Query records from table."""
        endpoint = f"{self.url}/rest/v1/{table}"
        try:
            resp = requests.get(
                endpoint,
                headers=self.headers,
                params=params or {},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            logger.warning(f"Supabase query error on {table}: {e}")
            return None


def get_database(token: Optional[str] = None) -> Optional[SupabaseClient]:
    """Get active Supabase client instance if configured, else None."""
    cfg = get_supabase_config()
    if cfg["url"] and cfg["anon_key"]:
        return SupabaseClient(url=cfg["url"], anon_key=cfg["anon_key"], token=token)
    return None


# ------------------------------------------------------------------------------
# HIGH-LEVEL PERSISTENCE API
# ------------------------------------------------------------------------------

def save_scan(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist scan metadata to Supabase (if configured) or local fallback.
    """
    if not isinstance(scan_data, dict):
        scan_data = {}

    record = create_scan_record(
        detected_material=scan_data.get("detected_material") or scan_data.get("material", "Unknown"),
        model_label=scan_data.get("model_label"),
        confidence=scan_data.get("confidence"),
        detected_object_count=scan_data.get("detected_object_count") or scan_data.get("detected_count", 1),
        confirmed_quantity=scan_data.get("confirmed_quantity") or scan_data.get("quantity", 1),
        image_filename=scan_data.get("image_filename"),
        session_id=scan_data.get("session_id"),
        user_id=scan_data.get("user_id"),
        scan_id=scan_data.get("id"),
    )

    client = get_database()
    if client:
        res = client.insert("scans", record)
        if res:
            # Also keep local copy for sync
            _append_local_json(LOCAL_FILES["scans"], record)
            return res

    _append_local_json(LOCAL_FILES["scans"], record)
    return record


def save_waste_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist structured waste profile assessment.
    """
    if not isinstance(profile_data, dict):
        profile_data = {}

    record = create_waste_profile_record(
        scan_id=profile_data.get("scan_id", ""),
        material=profile_data.get("material", "Unknown"),
        condition=profile_data.get("condition", "clean"),
        contamination=profile_data.get("contamination", "none"),
        confirmed_quantity=profile_data.get("confirmed_quantity", 1),
        item=profile_data.get("item", "Unknown"),
        user_confirmed=profile_data.get("user_confirmed", True),
        material_breakdown=profile_data.get("material_counts") or profile_data.get("material_breakdown"),
        profile_id=profile_data.get("id"),
    )

    client = get_database()
    if client:
        res = client.insert("waste_profiles", record)
        if res:
            _append_local_json(LOCAL_FILES["waste_profiles"], record)
            return res

    _append_local_json(LOCAL_FILES["waste_profiles"], record)
    return record


def save_recommendation(rec_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a single ranked recommendation.
    """
    if not isinstance(rec_data, dict):
        rec_data = {}

    record = create_recommendation_record(
        scan_id=rec_data.get("scan_id", ""),
        pathway_id=rec_data.get("pathway_id", ""),
        pathway_title=rec_data.get("pathway_title") or rec_data.get("title", ""),
        pathway_type=rec_data.get("pathway_type", "reuse"),
        rank=rec_data.get("rank", 1),
        mcda_score=rec_data.get("mcda_score") or rec_data.get("score", 0.0),
        criterion_scores=rec_data.get("criterion_scores"),
        why_this=rec_data.get("why_this"),
        why_not_this=rec_data.get("why_not_this"),
        warnings=rec_data.get("warnings"),
        recommendation_id=rec_data.get("id"),
    )

    client = get_database()
    if client:
        res = client.insert("recommendations", record)
        if res:
            _append_local_json(LOCAL_FILES["recommendations"], record)
            return res

    _append_local_json(LOCAL_FILES["recommendations"], record)
    return record


def save_recommendations(rec_list: List[Dict[str, Any]], scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Persist a list of ranked recommendations."""
    if not isinstance(rec_list, list):
        return []

    saved = []
    for r in rec_list:
        if isinstance(r, dict):
            r_copy = dict(r)
            if scan_id and not r_copy.get("scan_id"):
                r_copy["scan_id"] = scan_id
            saved.append(save_recommendation(r_copy))
    return saved


def save_execution_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist outcome validation feedback record.
    """
    if not isinstance(feedback_data, dict):
        feedback_data = {}

    record = create_feedback_record(
        pathway_id=feedback_data.get("pathway_id", ""),
        pathway_title=feedback_data.get("pathway_title") or feedback_data.get("title", ""),
        attempt_status=feedback_data.get("attempt_status", "not_attempted"),
        material=feedback_data.get("material"),
        item=feedback_data.get("item"),
        condition=feedback_data.get("condition"),
        contamination=feedback_data.get("contamination"),
        quantity=feedback_data.get("quantity", 1),
        predicted_rank=feedback_data.get("predicted_rank"),
        predicted_score=feedback_data.get("predicted_score"),
        estimated_time_minutes=feedback_data.get("estimated_time_minutes"),
        actual_time_minutes=feedback_data.get("actual_time_minutes"),
        time_accuracy=feedback_data.get("time_accuracy"),
        missing_tools=feedback_data.get("missing_tools", False),
        missing_tools_details=feedback_data.get("missing_tools_details"),
        missing_materials=feedback_data.get("missing_materials", False),
        missing_materials_details=feedback_data.get("missing_materials_details"),
        safety_issue=feedback_data.get("safety_issue", False),
        safety_issue_details=feedback_data.get("safety_issue_details"),
        failure_reason=feedback_data.get("failure_reason"),
        user_rating=feedback_data.get("user_rating"),
        would_try_again=feedback_data.get("would_try_again"),
        notes=feedback_data.get("notes"),
        scan_id=feedback_data.get("scan_id"),
        recommendation_id=feedback_data.get("recommendation_id"),
        user_id=feedback_data.get("user_id"),
        feedback_id=feedback_data.get("id"),
    )

    client = get_database()
    if client:
        res = client.insert("execution_feedback", record)
        if res:
            _append_local_json(LOCAL_FILES["execution_feedback"], record)
            return res

    _append_local_json(LOCAL_FILES["execution_feedback"], record)
    return record


def get_user_scans(
    user_id: Optional[str] = None,
    token: Optional[str] = None,
    material: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve recent scans with optional user and material filtering."""
    client = get_database(token=token)
    if client:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        if material and material.lower() != "all":
            params["detected_material"] = f"eq.{material.lower()}"
        records = client.query("scans", params=params)
        if records is not None:
            return records

    records = _read_local_json(LOCAL_FILES["scans"])
    if user_id:
        records = [r for r in records if r.get("user_id") == user_id]
    if material and material.lower() != "all":
        records = [r for r in records if str(r.get("detected_material", "")).lower() == material.lower()]
    records.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    return records[:limit]


def get_scan_recommendations(scan_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve saved recommendations for a given scan."""
    if not scan_id:
        return []

    client = get_database(token=token)
    if client:
        records = client.query("recommendations", params={"scan_id": f"eq.{scan_id}", "order": "rank.asc"})
        if records is not None:
            return records

    records = _read_local_json(LOCAL_FILES["recommendations"])
    matched = [r for r in records if r.get("scan_id") == scan_id]
    matched.sort(key=lambda x: int(x.get("rank", 99)))
    return matched


def get_user_recommendations(
    user_id: Optional[str] = None,
    token: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve recommendations evaluated for the user."""
    client = get_database(token=token)
    if client:
        params = {"order": "created_at.desc", "limit": str(limit)}
        records = client.query("recommendations", params=params)
        if records is not None:
            return records

    # In local storage, if user_id is provided, find scans owned by user
    all_recs = _read_local_json(LOCAL_FILES["recommendations"])
    if user_id:
        user_scans = {s["id"] for s in get_user_scans(user_id=user_id)}
        all_recs = [r for r in all_recs if r.get("scan_id") in user_scans]
    all_recs.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    return all_recs[:limit]


def get_user_feedback(
    user_id: Optional[str] = None,
    token: Optional[str] = None,
    status_filter: Optional[str] = None,
    material_filter: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve feedback entries for a user with optional status and material filtering."""
    client = get_database(token=token)
    if client:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        if status_filter and status_filter.lower() != "all":
            params["attempt_status"] = f"eq.{status_filter.lower()}"
        if material_filter and material_filter.lower() != "all":
            params["material"] = f"eq.{material_filter.lower()}"
        records = client.query("execution_feedback", params=params)
        if records is not None:
            return records

    records = _read_local_json(LOCAL_FILES["execution_feedback"])
    if user_id:
        records = [r for r in records if r.get("user_id") == user_id]
    if status_filter and status_filter.lower() != "all":
        records = [r for r in records if str(r.get("attempt_status", "")).lower() == status_filter.lower()]
    if material_filter and material_filter.lower() != "all":
        records = [r for r in records if str(r.get("material", "")).lower() == material_filter.lower()]
    records.sort(key=lambda x: str(x.get("created_at", "") or x.get("timestamp", "")), reverse=True)
    return records[:limit]


def get_all_feedback() -> List[Dict[str, Any]]:
    """Retrieve all execution feedback records (local fallback / global view)."""
    client = get_database()
    if client:
        records = client.query("execution_feedback", params={"order": "created_at.desc"})
        if records is not None and len(records) > 0:
            return records

    return _read_local_json(LOCAL_FILES["execution_feedback"])


def get_user_dashboard_metrics(
    user_id: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute summary dashboard statistics strictly from genuine user records.
    Never injects synthetic benchmark cases.
    """
    scans = get_user_scans(user_id=user_id, token=token, limit=100)
    recs = get_user_recommendations(user_id=user_id, token=token, limit=100)
    feedback = get_user_feedback(user_id=user_id, token=token, limit=100)

    total_scans = len(scans)
    total_recs = len(recs)

    attempted = [f for f in feedback if str(f.get("attempt_status", "")).lower() in ("successful", "partial", "failed")]
    successful = [f for f in attempted if str(f.get("attempt_status", "")).lower() == "successful"]
    partial = [f for f in attempted if str(f.get("attempt_status", "")).lower() == "partial"]
    failed = [f for f in attempted if str(f.get("attempt_status", "")).lower() == "failed"]
    safety_issues = [f for f in attempted if f.get("safety_issue")]

    total_attempts = len(attempted)
    resr = round((len(successful) / total_attempts * 100.0), 1) if total_attempts > 0 else 0.0

    return {
        "total_scans": total_scans,
        "total_recommendations": total_recs,
        "total_attempts": total_attempts,
        "successful_executions": len(successful),
        "partial_executions": len(partial),
        "failed_executions": len(failed),
        "safety_issues_count": len(safety_issues),
        "resr": resr,
        "recent_scans": scans[:5],
        "recent_feedback": feedback[:5],
    }
