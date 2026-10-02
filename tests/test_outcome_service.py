"""
ReNexa — Phase 8 Outcome Service Unit Tests
============================================
Comprehensive unit tests for outcome feedback persistence, metric calculations
(RESR, OVRR, Time MAE, Resource Completeness, Safety Incident Rate),
failure reason analysis, and per-pathway diagnostics.

Run with:
    python -m pytest tests/test_outcome_service.py -v
"""

import sys
import os
import json
import tempfile
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.outcome_service import (
    load_outcome_feedback,
    save_outcome_feedback,
    calculate_outcome_metrics,
    summarize_failure_reasons,
    analyze_pathway_outcomes,
    normalize_attempt_status,
    parse_numeric_minutes,
)


@pytest.fixture
def temp_feedback_file():
    """Create a temporary JSON file for isolated testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("[]")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_save_and_load_feedback(temp_feedback_file):
    """Save a feedback record and verify it loads correctly."""
    record = {
        "pathway_id": "REC-PLA-001",
        "pathway_title": "Plastic Container Storage",
        "attempt_status": "Successfully completed",
        "actual_time_minutes": 5,
        "estimated_time_minutes": 5,
        "missing_tools": False,
        "missing_materials": False,
        "safety_issue": False,
    }
    assert save_outcome_feedback(record, file_path=temp_feedback_file) is True
    loaded = load_outcome_feedback(file_path=temp_feedback_file)
    assert len(loaded) == 1
    assert loaded[0]["pathway_id"] == "REC-PLA-001"
    assert loaded[0]["attempt_status"] == "successful"


def test_multiple_records_preserved(temp_feedback_file):
    """Multiple feedback entries are appended without overwriting previous history."""
    save_outcome_feedback({"pathway_id": "REC-PLA-001", "attempt_status": "successful"}, file_path=temp_feedback_file)
    save_outcome_feedback({"pathway_id": "REC-GLA-001", "attempt_status": "partial"}, file_path=temp_feedback_file)
    save_outcome_feedback({"pathway_id": "REC-MET-001", "attempt_status": "failed"}, file_path=temp_feedback_file)

    loaded = load_outcome_feedback(file_path=temp_feedback_file)
    assert len(loaded) == 3
    assert [r["pathway_id"] for r in loaded] == ["REC-PLA-001", "REC-GLA-001", "REC-MET-001"]


def test_empty_file_handled(temp_feedback_file):
    """Empty JSON file returns empty list gracefully."""
    with open(temp_feedback_file, "w") as f:
        f.write("")
    assert load_outcome_feedback(file_path=temp_feedback_file) == []


def test_malformed_file_handled(temp_feedback_file):
    """Corrupted JSON returns empty list without raising unhandled exceptions."""
    with open(temp_feedback_file, "w") as f:
        f.write("{corrupted_json_content::")
    assert load_outcome_feedback(file_path=temp_feedback_file) == []


def test_attempt_status_counts():
    """Verify accurate counting of successful, partial, and failed attempts."""
    records = [
        {"attempt_status": "successful"},
        {"attempt_status": "successful"},
        {"attempt_status": "partial"},
        {"attempt_status": "failed"},
        {"attempt_status": "not_attempted"},
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["total_recorded"] == 5
    assert metrics["total_attempted"] == 4
    assert metrics["successful_count"] == 2
    assert metrics["partial_count"] == 1
    assert metrics["failed_count"] == 1
    assert metrics["not_attempted_count"] == 1


def test_not_attempted_excluded_from_metrics():
    """'Not attempted' entries must not dilute execution success rates."""
    records = [
        {"attempt_status": "successful"},
        {"attempt_status": "not_attempted"},
        {"attempt_status": "not_attempted"},
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["total_attempted"] == 1
    assert metrics["resr"] == 100.0


def test_resr_formula():
    """RESR = (successful / total_attempted) * 100."""
    records = [
        {"attempt_status": "successful"},
        {"attempt_status": "successful"},
        {"attempt_status": "successful"},
        {"attempt_status": "failed"},
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["resr"] == 75.0


def test_failure_rate_formula():
    """Failure Rate = (failed / total_attempted) * 100."""
    records = [
        {"attempt_status": "successful"},
        {"attempt_status": "failed"},
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["failure_rate"] == 50.0


def test_resource_completeness_formula():
    """Resource completeness measures attempts with zero missing tools and materials."""
    records = [
        {"attempt_status": "successful", "missing_tools": False, "missing_materials": False},
        {"attempt_status": "successful", "missing_tools": True, "missing_materials": False},
        {"attempt_status": "partial", "missing_tools": False, "missing_materials": True},
        {"attempt_status": "successful", "missing_tools": False, "missing_materials": False},
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["resource_completeness_rate"] == 50.0  # 2 of 4


def test_safety_issue_rate_formula():
    """Safety issue rate = (reported safety issues / total attempted) * 100."""
    records = [
        {"attempt_status": "successful", "safety_issue": False},
        {"attempt_status": "failed", "safety_issue": True},
        {"attempt_status": "successful", "safety_issue": False},
        {"attempt_status": "partial", "safety_issue": False},
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["safety_issue_rate"] == 25.0  # 1 of 4


def test_time_mae_formula():
    """Time MAE = mean(|actual - estimated|)."""
    records = [
        {"attempt_status": "successful", "estimated_time_minutes": 10, "actual_time_minutes": 15},  # diff = 5
        {"attempt_status": "successful", "estimated_time_minutes": 20, "actual_time_minutes": 15},  # diff = 5
        {"attempt_status": "successful", "estimated_time_minutes": 5, "actual_time_minutes": 5},    # diff = 0
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["time_mae"] == pytest.approx(3.33, 0.01)
    assert metrics["time_evaluated_count"] == 3


def test_missing_actual_time_handled_safely():
    """Records with missing actual time are safely excluded from MAE without crash."""
    records = [
        {"attempt_status": "successful", "estimated_time_minutes": 10, "actual_time_minutes": None},
        {"attempt_status": "successful", "estimated_time_minutes": 10, "actual_time_minutes": 12},  # diff = 2
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["time_mae"] == 2.0
    assert metrics["time_evaluated_count"] == 1


def test_ovrr_formula():
    """OVRR = (successful AND no missing resources AND no safety issue) / total_attempted * 100."""
    records = [
        {"attempt_status": "successful", "missing_tools": False, "missing_materials": False, "safety_issue": False},  # OVRR clean
        {"attempt_status": "successful", "missing_tools": True, "missing_materials": False, "safety_issue": False},   # Missing tool
        {"attempt_status": "successful", "missing_tools": False, "missing_materials": False, "safety_issue": True},    # Safety incident
        {"attempt_status": "failed", "missing_tools": False, "missing_materials": False, "safety_issue": False},        # Failed
    ]
    metrics = calculate_outcome_metrics(records)
    assert metrics["ovrr"] == 25.0  # 1 of 4


def test_failure_reason_summary():
    """Failure reasons are categorized accurately."""
    records = [
        {"attempt_status": "failed", "failure_reason": "missing_tool"},
        {"attempt_status": "failed", "failure_reason": "missing_tool"},
        {"attempt_status": "failed", "failure_reason": "missing_material"},
        {"attempt_status": "failed", "failure_reason": "safety_issue"},
    ]
    summary = summarize_failure_reasons(records)
    assert summary["missing_tool"] == 2
    assert summary["missing_material"] == 1
    assert summary["safety_issue"] == 1
    assert summary["time_underestimated"] == 0


def test_per_pathway_analysis():
    """Per-pathway analytics aggregate attempts and success rates accurately."""
    records = [
        {"pathway_id": "REC-PLA-001", "pathway_title": "Plastic Storage", "attempt_status": "successful", "estimated_time_minutes": 5, "actual_time_minutes": 5},
        {"pathway_id": "REC-PLA-001", "pathway_title": "Plastic Storage", "attempt_status": "successful", "estimated_time_minutes": 5, "actual_time_minutes": 7},
        {"pathway_id": "REC-CAR-001", "pathway_title": "Cardboard Box", "attempt_status": "failed", "estimated_time_minutes": 10, "actual_time_minutes": 15},
    ]
    table = analyze_pathway_outcomes(records)
    assert len(table) == 2
    p_pla = next(r for r in table if r["pathway_id"] == "REC-PLA-001")
    assert p_pla["attempts"] == 2
    assert p_pla["successful"] == 2
    assert p_pla["success_rate"] == "100.0%"
    assert p_pla["avg_time_error_mins"] == "1.0 mins"


def test_deterministic_outcome_metrics():
    """Outcome metric calculations are completely deterministic across repeated evaluations."""
    records = [
        {"attempt_status": "successful", "estimated_time_minutes": 5, "actual_time_minutes": 6, "missing_tools": False, "missing_materials": False, "safety_issue": False},
        {"attempt_status": "partial", "estimated_time_minutes": 10, "actual_time_minutes": 15, "missing_tools": True, "missing_materials": False, "safety_issue": False},
        {"attempt_status": "failed", "estimated_time_minutes": 15, "actual_time_minutes": 20, "missing_tools": False, "missing_materials": True, "safety_issue": True},
    ]
    m1 = calculate_outcome_metrics(records)
    m2 = calculate_outcome_metrics(records)
    assert m1 == m2


def test_no_fabricated_outcomes_on_empty_data():
    """Empty datasets report 0 counts and None MAE without fabricating dummy success rates."""
    metrics = calculate_outcome_metrics([])
    assert metrics["total_recorded"] == 0
    assert metrics["total_attempted"] == 0
    assert metrics["resr"] == 0.0
    assert metrics["ovrr"] == 0.0
    assert metrics["time_mae"] is None
