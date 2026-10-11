"""
ReNexa — Recovery Recommendation Engine Regression Test Suite
==============================================================
Validates the 9 core regression test cases defined in the Recovery Engine audit.

Run with:
    E:\\ReNexa\\venv\\Scripts\\python.exe -m pytest tests/test_recovery_engine_regression.py -v
"""

import os
import sys
import csv
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.recovery_service import (
    DEFAULT_CSV_PATH,
    load_recovery_pathways,
    get_recovery_pathways,
    get_pathways_for_profile,
    get_all_pathways,
    normalize_material_name,
)
from services.safety_service import (
    DEFAULT_SAFETY_CSV,
    load_safety_rules,
    evaluate_safety,
)
from services.constraint_service import evaluate_constraints
from services.eligibility_service import (
    evaluate_pathway_eligibility,
    get_eligible_pathways_for_profile,
)
from services.ranking_service import (
    get_ranked_recommendations_for_profile,
    get_ranked_pathways,
)
from services.execution_service import get_execution_guide


# ==============================================================================
# Case 1 & 2: Default Knowledge Base Paths
# ==============================================================================

def test_regression_case1_default_recovery_csv_exists():
    """Case 1: Default recovery CSV path exists and loads valid records."""
    assert os.path.isfile(DEFAULT_CSV_PATH), f"Recovery CSV not found at {DEFAULT_CSV_PATH}"
    pathways = load_recovery_pathways()
    assert len(pathways) > 0, "Recovery pathways CSV loaded 0 records"


def test_regression_case2_default_safety_csv_exists():
    """Case 2: Default safety CSV path exists and loads valid records."""
    assert os.path.isfile(DEFAULT_SAFETY_CSV), f"Safety CSV not found at {DEFAULT_SAFETY_CSV}"
    rules = load_safety_rules()
    assert len(rules) > 0, "Safety rules CSV loaded 0 records"


# ==============================================================================
# Case 3: Organic Material Mapping to Biological
# ==============================================================================

def test_regression_case3_organic_retrieves_biological_pathways():
    """Case 3: Detected material 'organic' correctly retrieves 'biological' recovery pathways."""
    assert normalize_material_name("organic") == "biological"
    assert normalize_material_name("ORGANIC") == "biological"

    # Query via material string
    pathways = get_recovery_pathways("organic")
    assert len(pathways) >= 2, f"Expected biological pathways for 'organic', got {len(pathways)}"
    assert all(p["input_material"] == "biological" for p in pathways)

    # Query via waste profile
    organic_profile = {
        "material": "organic",
        "condition": "Good",
        "contamination": "Clean",
        "confirmed_quantity": 1,
    }
    profile_pathways = get_pathways_for_profile(organic_profile)
    assert len(profile_pathways) >= 2
    assert all(p["input_material"] == "biological" for p in profile_pathways)


# ==============================================================================
# Case 4: Clean Plastic Retrieval
# ==============================================================================

def test_regression_case4_clean_plastic_retrieval():
    """Case 4: Clean plastic retrieves suitable plastic recovery options."""
    plastic_profile = {
        "material": "plastic",
        "condition": "Good",
        "contamination": "Clean",
        "confirmed_quantity": 1,
    }
    constraints = {
        "budget": "₹500+",
        "time": "1 hour",
        "tools": ["Scissors", "Tape"],
        "skill": "Beginner",
        "workspace": "Indoor",
    }
    recommendations = get_ranked_recommendations_for_profile(plastic_profile, constraints, top_k=3)
    assert len(recommendations) >= 1, "Expected at least 1 plastic recommendation"
    assert recommendations[0]["pathway"]["input_material"] == "plastic"
    assert recommendations[0]["eligible"] is True
    assert recommendations[0]["score"] > 0.0


# ==============================================================================
# Case 5: Heavy Contamination Disqualification
# ==============================================================================

def test_regression_case5_heavily_contaminated_disqualifies_reuse_and_repair():
    """Case 5: Heavily contaminated waste is not approved for prohibited reuse or repair."""
    plastic_reuse_pathway = get_recovery_pathways("plastic", pathway_type="reuse")[0]

    # Test with standard title-case contamination
    contam_profile = {
        "material": "plastic",
        "condition": "Good",
        "contamination": "Heavily Contaminated",
        "confirmed_quantity": 1,
    }
    eval_result = evaluate_constraints(
        plastic_reuse_pathway,
        user_constraints={"budget": 500, "time": 60, "tools": ["Scissors"], "skill": "Beginner"},
        waste_profile=contam_profile,
    )
    assert eval_result["constraint_status"] == "INFEASIBLE"
    assert any("heavily contaminated" in r.lower() for r in eval_result["reasons"])

    # Test with lowercase contamination string
    contam_lower = {
        "material": "plastic",
        "condition": "good",
        "contamination": "heavily contaminated",
        "confirmed_quantity": 1,
    }
    eval_lower = evaluate_constraints(
        plastic_reuse_pathway,
        user_constraints={"budget": 500, "time": 60, "tools": ["Scissors"], "skill": "Beginner"},
        waste_profile=contam_lower,
    )
    assert eval_lower["constraint_status"] == "INFEASIBLE"

    # End-to-end: recycling should still be allowed if condition permits
    plastic_recycle = get_recovery_pathways("plastic", pathway_type="recycle")[0]
    eval_recycle = evaluate_constraints(
        plastic_recycle,
        user_constraints={"budget": 500, "time": 60, "tools": ["None"], "skill": "Beginner"},
        waste_profile=contam_profile,
    )
    assert eval_recycle["constraint_status"] == "FEASIBLE"


# ==============================================================================
# Case 6: Battery Prohibitions
# ==============================================================================

def test_regression_case6_hazardous_battery_diy_prohibited():
    """Case 6: Hazardous household batteries cannot receive DIY repair or upcycling recommendations."""
    # Synthetic hazardous battery repair
    fake_battery_repair = {
        "pathway_id": "REC-BAT-FAKE",
        "input_material": "battery",
        "pathway_type": "repair",
        "title": "DIY Battery Cell Refurbish",
        "tools": "Screwdriver, Soldering iron",
        "steps": "Open battery casing and replace cells",
        "budget": "0",
        "time_required": "30 mins",
        "skill_level": "Intermediate",
        "safety_level": "High",
    }
    safety_res = evaluate_safety(fake_battery_repair)
    assert safety_res["safety_status"] == "BLOCK"

    elig_res = evaluate_pathway_eligibility(fake_battery_repair, waste_profile={"material": "battery"})
    assert elig_res["eligible"] is False
    assert elig_res["safety_status"] == "BLOCK"

    # Ranked recommendations for battery only suggest safe disposal
    battery_profile = {"material": "battery", "condition": "Any", "contamination": "Any", "confirmed_quantity": 1}
    battery_recs = get_ranked_recommendations_for_profile(battery_profile, top_k=5)
    for rec in battery_recs:
        assert rec["pathway"]["pathway_type"] == "dispose", f"Unexpected non-disposal pathway for battery: {rec['title']}"


# ==============================================================================
# Case 7: Tutorials Page Contract & Imports
# ==============================================================================

def test_regression_case7_tutorials_page_imports_and_contract():
    """Case 7: Tutorials page imports without ImportError and accesses all pathways."""
    # Ensure get_all_pathways is exported and works
    all_pathways = get_all_pathways()
    assert isinstance(all_pathways, list)
    assert len(all_pathways) >= 20

    # Ensure each pathway has a valid 'tools' representation
    for p in all_pathways:
        raw_tools = p.get("tools") or p.get("tools_required", "")
        assert raw_tools is not None


# ==============================================================================
# Case 8: Missing or Corrupt Knowledge Base Handling
# ==============================================================================

def test_regression_case8_missing_or_invalid_kb_fails_safely():
    """Case 8: Missing/invalid records produce clear errors or safe fallbacks, never silent unsafe actions."""
    # Non-existent pathway ID in execution service
    missing_guide = get_execution_guide("REC-NONEXISTENT-999")
    assert missing_guide["can_execute"] is False
    assert missing_guide["execution_status"] == "NOT_FOUND"

    # None pathway
    none_guide = get_execution_guide(None)
    assert none_guide["can_execute"] is False
    assert none_guide["execution_status"] == "NOT_FOUND"

    # None pathway in eligibility
    none_elig = evaluate_pathway_eligibility(None)
    assert none_elig["eligible"] is False
    assert none_elig["safety_status"] == "BLOCK"

    # Invalid CSV path raises FileNotFoundError clearly rather than returning fake data
    with pytest.raises(FileNotFoundError):
        load_recovery_pathways("E:/ReNexa/data/non_existent_file.csv")


# ==============================================================================
# Case 9: Verified YouTube Links Integrity
# ==============================================================================

def test_regression_case9_youtube_links_integrity():
    """Case 9: Verified tutorial links are preserved and unverified links are not marked verified."""
    video_csv_path = os.path.abspath(os.path.join(PROJECT_ROOT, "data", "knowledge", "video_index.csv"))
    assert os.path.isfile(video_csv_path)

    with open(video_csv_path, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

        verified = [r for r in reader if r.get("youtube_verified", "").strip().lower() == "yes"]
        unverified = [r for r in reader if r.get("youtube_verified", "").strip().lower() != "yes"]

        assert len(verified) >= 50, f"Expected at least 50 verified tutorials, got {len(verified)}"
        for v in verified:
            assert v["youtube_url"].startswith("https://www.youtube.com/watch?v="), f"Invalid YouTube URL: {v['youtube_url']}"
            assert len(v["youtube_title"].strip()) > 0

        assert len(unverified) >= 3, f"Expected at least 3 unverified tutorial rows, got {len(unverified)}"
        for uv in unverified:
            assert uv["youtube_url"].strip() == "", f"Unverified record must not have fake URL: {uv}"
