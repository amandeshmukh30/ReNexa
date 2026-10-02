"""
ReNexa — Eligibility Engine Unit Tests
========================================
Tests for orchestration of safety + constraints into final eligibility decision.

Run with:
    python -m pytest tests/test_eligibility_service.py -v
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.eligibility_service import (
    evaluate_pathway_eligibility,
    evaluate_all_pathways,
    get_eligible_pathways_for_profile,
)


def test_eligible_pathway_when_safety_and_constraints_pass():
    """Eligible is True only when safety passes AND constraints pass."""
    pathway = {
        "pathway_id": "REC-PLA-001",
        "input_material": "plastic",
        "pathway_type": "reuse",
        "title": "Plastic Container Storage",
        "budget": "0",
        "time_required": "5 minutes",
        "tools": "None",
        "skill_level": "Beginner",
        "workspace": "Any",
        "min_quantity": 1,
        "condition_requirement": "Good",
    }
    user_constraints = {
        "budget": "₹100",
        "time": "15 minutes",
        "tools": [],
        "skill": "Beginner",
        "workspace": "Indoor",
    }
    waste_profile = {
        "material": "plastic",
        "condition": "Good",
        "confirmed_quantity": 1,
        "contamination": "Clean",
    }
    res = evaluate_pathway_eligibility(pathway, user_constraints, waste_profile)
    assert res["eligible"] is True
    assert res["safety_status"] == "ALLOW"
    assert res["constraint_status"] == "FEASIBLE"
    assert len(res["reasons"]) == 0


def test_safety_block_overrides_satisfied_constraints():
    """Safety BLOCK prevents eligibility even if all user constraints are 100% satisfied."""
    hazardous_pathway = {
        "pathway_id": "HAZ-BAT-001",
        "input_material": "battery",
        "pathway_type": "repair",  # Prohibited
        "title": "Battery Acid Refill",
        "budget": "0",
        "time_required": "5 minutes",
        "tools": "None",
        "skill_level": "Beginner",
        "workspace": "Indoor",
        "steps": "Open battery cell and add acid",
    }
    user_constraints = {
        "budget": "₹500+",
        "time": "2+ hours",
        "tools": ["Everything"],
        "skill": "Advanced",
        "workspace": "Indoor",
    }
    res = evaluate_pathway_eligibility(hazardous_pathway, user_constraints)
    assert res["eligible"] is False
    assert res["safety_status"] == "BLOCK"
    assert res["constraint_status"] == "NOT_EVALUATED"


def test_safety_warn_allows_eligibility_if_constraints_pass():
    """Safety WARN preserves eligibility while displaying safety warnings."""
    warn_pathway = {
        "pathway_id": "REC-GLA-003",
        "input_material": "glass",
        "pathway_type": "upcycle",
        "title": "Cut glass bottle planter",
        "tools": "Utility knife",
        "budget": "0",
        "time_required": "15 minutes",
        "skill_level": "Beginner",
        "workspace": "Indoor",
        "steps": "Score glass bottle carefully with knife",
    }
    user_constraints = {
        "budget": "₹100",
        "time": "30 minutes",
        "tools": ["Utility knife"],
        "skill": "Beginner",
        "workspace": "Indoor",
    }
    res = evaluate_pathway_eligibility(warn_pathway, user_constraints)
    assert res["safety_status"] in ("WARN", "ALLOW")
    if res["safety_status"] == "WARN":
        assert len(res["warnings"]) > 0
        assert res["eligible"] is True


def test_get_eligible_pathways_for_profile():
    """Full workflow: structured profile queries pathways and evaluates eligibility."""
    waste_profile = {
        "material": "paper",
        "condition": "Good",
        "confirmed_quantity": 2,
        "contamination": "Clean",
    }
    user_constraints = {
        "budget": "₹50",
        "time": "15 minutes",
        "tools": ["Scissors", "Binder clip"],
        "skill": "Beginner",
        "workspace": "Indoor",
    }
    results = get_eligible_pathways_for_profile(waste_profile, user_constraints)
    assert len(results) >= 2
    assert any(r["eligible"] is True for r in results)
