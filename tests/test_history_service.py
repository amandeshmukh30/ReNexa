"""
ReNexa — User History & Dashboard Service Tests (Phase 9C)
===========================================================
Verifies personalized history retrieval, user-data isolation, multi-field filtering,
guest mode fallback, and dashboard metrics calculations without live database requirements.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from database.database import (
    save_scan,
    save_recommendation,
    save_execution_feedback,
    get_user_scans,
    get_user_recommendations,
    get_user_feedback,
    get_user_dashboard_metrics,
    LOCAL_FILES,
)


@pytest.fixture
def mock_isolated_storage():
    """Create isolated temporary JSON storage files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_scans = os.path.join(tmpdir, "scans.json")
        test_recs = os.path.join(tmpdir, "recommendations.json")
        test_feedback = os.path.join(tmpdir, "outcome_feedback.json")

        with patch.dict(
            LOCAL_FILES,
            {
                "scans": test_scans,
                "recommendations": test_recs,
                "execution_feedback": test_feedback,
            },
        ), patch("database.database.is_database_configured", return_value=False):
            yield {
                "scans_file": test_scans,
                "recs_file": test_recs,
                "feedback_file": test_feedback,
            }


def test_authenticated_user_sees_own_scans_and_isolates_others(mock_isolated_storage):
    """Verify user A only sees user A's scans and never user B's."""
    user_a = "user-uuid-aaaa"
    user_b = "user-uuid-bbbb"

    # Save scan for user A
    save_scan({"user_id": user_a, "detected_material": "plastic", "confirmed_quantity": 2})
    save_scan({"user_id": user_a, "detected_material": "glass", "confirmed_quantity": 1})

    # Save scan for user B
    save_scan({"user_id": user_b, "detected_material": "metal", "confirmed_quantity": 5})

    # User A query
    scans_a = get_user_scans(user_id=user_a)
    assert len(scans_a) == 2
    assert all(s["user_id"] == user_a for s in scans_a)
    assert not any(s["detected_material"] == "metal" for s in scans_a)

    # User B query
    scans_b = get_user_scans(user_id=user_b)
    assert len(scans_b) == 1
    assert scans_b[0]["user_id"] == user_b
    assert scans_b[0]["detected_material"] == "metal"


def test_guest_fallback_mode_retrieves_all_local_records(mock_isolated_storage):
    """Verify guest mode (user_id=None) retrieves local session records without error."""
    save_scan({"detected_material": "paper", "confirmed_quantity": 3})
    save_scan({"detected_material": "cardboard", "confirmed_quantity": 1})

    guest_scans = get_user_scans(user_id=None)
    assert len(guest_scans) == 2


def test_material_and_status_filtering(mock_isolated_storage):
    """Verify filtering by material and outcome attempt status."""
    user_id = "user-filter-123"

    # Populate scans with different materials
    save_scan({"user_id": user_id, "detected_material": "plastic"})
    save_scan({"user_id": user_id, "detected_material": "glass"})
    save_scan({"user_id": user_id, "detected_material": "plastic"})

    # Filter scans by plastic
    plastic_scans = get_user_scans(user_id=user_id, material="plastic")
    assert len(plastic_scans) == 2
    assert all(s["detected_material"] == "plastic" for s in plastic_scans)

    # Filter scans by glass
    glass_scans = get_user_scans(user_id=user_id, material="glass")
    assert len(glass_scans) == 1
    assert glass_scans[0]["detected_material"] == "glass"

    # Populate feedback
    save_execution_feedback({"user_id": user_id, "pathway_id": "REC-PLA-001", "attempt_status": "successful", "material": "plastic"})
    save_execution_feedback({"user_id": user_id, "pathway_id": "REC-GLA-001", "attempt_status": "failed", "material": "glass"})

    # Filter feedback by status
    success_fb = get_user_feedback(user_id=user_id, status_filter="successful")
    assert len(success_fb) == 1
    assert success_fb[0]["attempt_status"] == "successful"

    failed_fb = get_user_feedback(user_id=user_id, status_filter="failed")
    assert len(failed_fb) == 1
    assert failed_fb[0]["attempt_status"] == "failed"


def test_empty_history_handled_cleanly(mock_isolated_storage):
    """Verify empty history queries return empty lists without exceptions."""
    assert get_user_scans(user_id="non-existent-user") == []
    assert get_user_recommendations(user_id="non-existent-user") == []
    assert get_user_feedback(user_id="non-existent-user") == []

    metrics = get_user_dashboard_metrics(user_id="non-existent-user")
    assert metrics["total_scans"] == 0
    assert metrics["total_recommendations"] == 0
    assert metrics["total_attempts"] == 0
    assert metrics["successful_executions"] == 0
    assert metrics["resr"] == 0.0


def test_user_dashboard_metrics_calculation(mock_isolated_storage):
    """Verify accurate calculation of personal dashboard statistics."""
    uid = "user-metrics-999"

    # 3 Scans
    s1 = save_scan({"user_id": uid, "detected_material": "plastic"})
    s2 = save_scan({"user_id": uid, "detected_material": "clothes"})
    s3 = save_scan({"user_id": uid, "detected_material": "metal"})

    # 2 Recommendations for scan 1
    save_recommendation({"scan_id": s1["id"], "pathway_id": "REC-PLA-001", "rank": 1, "score": 92.0})
    save_recommendation({"scan_id": s1["id"], "pathway_id": "REC-PLA-002", "rank": 2, "score": 84.0})

    # 3 Feedback entries: 2 successful, 1 failed (Total attempted = 3 -> RESR = 66.7%)
    save_execution_feedback({"user_id": uid, "pathway_id": "REC-PLA-001", "attempt_status": "successful"})
    save_execution_feedback({"user_id": uid, "pathway_id": "REC-PLA-002", "attempt_status": "successful"})
    save_execution_feedback({"user_id": uid, "pathway_id": "REC-MET-001", "attempt_status": "failed", "safety_issue": True})

    metrics = get_user_dashboard_metrics(user_id=uid)
    assert metrics["total_scans"] == 3
    assert metrics["total_recommendations"] == 2
    assert metrics["total_attempts"] == 3
    assert metrics["successful_executions"] == 2
    assert metrics["failed_executions"] == 1
    assert metrics["safety_issues_count"] == 1
    assert metrics["resr"] == pytest.approx(66.7, 0.1)


def test_synthetic_benchmark_is_never_mixed_with_user_history(mock_isolated_storage):
    """Verify synthetic Phase 8 benchmark file records are never mixed into live user history."""
    uid = "real-user-123"
    save_scan({"user_id": uid, "detected_material": "plastic"})
    save_execution_feedback({"user_id": uid, "pathway_id": "REC-PLA-001", "attempt_status": "successful"})

    user_records = get_user_feedback(user_id=uid)
    assert len(user_records) == 1
    assert not any("OUT-BENCH" in str(r.get("id", "")) for r in user_records)
