"""
ReNexa — Database Data Models (Phase 9A)
========================================
Defines standardized data dictionaries and validation structures
for persistence across local storage and PostgreSQL/Supabase.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


def generate_uuid() -> str:
    """Generate a RFC 4122 compliant UUID string."""
    return str(uuid.uuid4())


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.utcnow().isoformat() + "Z"


def create_scan_record(
    detected_material: str,
    model_label: Optional[str] = None,
    confidence: Optional[float] = None,
    detected_object_count: int = 1,
    confirmed_quantity: int = 1,
    image_filename: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    scan_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardized scan record."""
    return {
        "id": scan_id or generate_uuid(),
        "user_id": user_id,
        "created_at": get_utc_timestamp(),
        "detected_material": str(detected_material or "Unknown").strip().lower(),
        "model_label": str(model_label) if model_label else None,
        "confidence": float(confidence) if confidence is not None else None,
        "detected_object_count": max(1, int(detected_object_count or 1)),
        "confirmed_quantity": max(1, int(confirmed_quantity or 1)),
        "image_filename": image_filename,
        "session_id": session_id,
    }


def create_waste_profile_record(
    scan_id: str,
    material: str,
    condition: str,
    contamination: str,
    confirmed_quantity: int = 1,
    item: str = "Unknown",
    user_confirmed: bool = True,
    material_breakdown: Optional[Dict[str, int]] = None,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardized waste profile record linked to a scan."""
    return {
        "id": profile_id or generate_uuid(),
        "scan_id": scan_id,
        "created_at": get_utc_timestamp(),
        "material": str(material or "Unknown").strip().lower(),
        "item": str(item or "Unknown").strip(),
        "condition": str(condition or "clean").strip().lower(),
        "contamination": str(contamination or "none").strip().lower(),
        "confirmed_quantity": max(1, int(confirmed_quantity or 1)),
        "user_confirmed": bool(user_confirmed),
        "material_breakdown": material_breakdown or {},
    }


def create_recommendation_record(
    scan_id: str,
    pathway_id: str,
    pathway_title: str,
    pathway_type: str,
    rank: int,
    mcda_score: float,
    criterion_scores: Optional[Dict[str, float]] = None,
    why_this: Optional[List[str]] = None,
    why_not_this: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    recommendation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardized recommendation record linked to a scan."""
    return {
        "id": recommendation_id or generate_uuid(),
        "scan_id": scan_id,
        "created_at": get_utc_timestamp(),
        "pathway_id": str(pathway_id).strip().upper(),
        "pathway_title": str(pathway_title).strip(),
        "pathway_type": str(pathway_type).strip().lower(),
        "rank": int(rank),
        "mcda_score": round(float(mcda_score), 2),
        "criterion_scores": criterion_scores or {},
        "why_this": why_this or [],
        "why_not_this": why_not_this or [],
        "warnings": warnings or [],
    }


def create_feedback_record(
    pathway_id: str,
    pathway_title: str,
    attempt_status: str,
    material: Optional[str] = None,
    item: Optional[str] = None,
    condition: Optional[str] = None,
    contamination: Optional[str] = None,
    quantity: int = 1,
    predicted_rank: Optional[int] = None,
    predicted_score: Optional[float] = None,
    estimated_time_minutes: Optional[int] = None,
    actual_time_minutes: Optional[int] = None,
    time_accuracy: Optional[str] = None,
    missing_tools: bool = False,
    missing_tools_details: Optional[str] = None,
    missing_materials: bool = False,
    missing_materials_details: Optional[str] = None,
    safety_issue: bool = False,
    safety_issue_details: Optional[str] = None,
    failure_reason: Optional[str] = None,
    user_rating: Optional[int] = None,
    would_try_again: Optional[str] = None,
    notes: Optional[str] = None,
    scan_id: Optional[str] = None,
    recommendation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    feedback_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardized outcome feedback record."""
    return {
        "id": feedback_id or generate_uuid(),
        "user_id": user_id,
        "scan_id": scan_id,
        "recommendation_id": recommendation_id,
        "pathway_id": str(pathway_id).strip().upper(),
        "pathway_title": str(pathway_title).strip(),
        "created_at": get_utc_timestamp(),
        "attempt_status": str(attempt_status).strip().lower(),
        "material": str(material).strip().lower() if material else None,
        "item": str(item).strip() if item else None,
        "condition": str(condition).strip().lower() if condition else None,
        "contamination": str(contamination).strip().lower() if contamination else None,
        "quantity": max(1, int(quantity or 1)),
        "predicted_rank": int(predicted_rank) if predicted_rank is not None else None,
        "predicted_score": float(predicted_score) if predicted_score is not None else None,
        "estimated_time_minutes": int(estimated_time_minutes) if estimated_time_minutes is not None else None,
        "actual_time_minutes": int(actual_time_minutes) if actual_time_minutes is not None else None,
        "time_accuracy": str(time_accuracy).strip().lower() if time_accuracy else None,
        "missing_tools": bool(missing_tools),
        "missing_tools_details": str(missing_tools_details).strip() if missing_tools_details else None,
        "missing_materials": bool(missing_materials),
        "missing_materials_details": str(missing_materials_details).strip() if missing_materials_details else None,
        "safety_issue": bool(safety_issue),
        "safety_issue_details": str(safety_issue_details).strip() if safety_issue_details else None,
        "failure_reason": str(failure_reason).strip().lower() if failure_reason else None,
        "user_rating": int(user_rating) if user_rating is not None else None,
        "would_try_again": str(would_try_again).strip().lower() if would_try_again else None,
        "notes": str(notes).strip() if notes else None,
    }
