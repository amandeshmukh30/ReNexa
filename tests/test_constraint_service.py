"""
ReNexa — Constraint Service Unit Tests
========================================
Tests for deterministic constraint evaluation.

Run with:
    python -m pytest tests/test_constraint_service.py -v
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.constraint_service import (
    evaluate_constraints,
    parse_budget_amount,
    parse_time_in_minutes,
    parse_tool_list,
)


@pytest.fixture
def sample_pathway():
    return {
        "pathway_id": "REC-CAR-003",
        "input_material": "cardboard",
        "title": "Desk Document Organizer",
        "budget": "50",
        "time_required": "30 minutes",
        "tools": "Utility knife, PVA glue",
        "extra_materials": "PVA glue",
        "skill_level": "Intermediate",
        "workspace": "Indoor",
        "min_quantity": 2,
        "condition_requirement": "Good",
    }


def test_fully_feasible_pathway(sample_pathway):
    """When all constraints are met, status is FEASIBLE."""
    user_constraints = {
        "budget": "₹100",
        "time": "1 hour",
        "tools": ["Utility knife", "PVA glue", "Scissors"],
        "extra_materials": ["PVA glue"],
        "skill": "Intermediate",
        "workspace": "Indoor",
    }
    waste_profile = {
        "material": "cardboard",
        "condition": "Good",
        "confirmed_quantity": 3,
        "contamination": "Clean",
    }
    result = evaluate_constraints(sample_pathway, user_constraints, waste_profile)
    assert result["constraint_status"] == "FEASIBLE"
    assert len(result["reasons"]) == 0
    assert result["missing_tools"] == []
    assert result["budget_gap"] is None


def test_insufficient_budget(sample_pathway):
    """Insufficient budget triggers infeasibility and calculates budget gap."""
    user_constraints = {
        "budget": "₹0",  # Requires ₹50
        "time": "1 hour",
        "tools": ["Utility knife", "PVA glue"],
        "skill": "Advanced",
        "workspace": "Indoor",
    }
    result = evaluate_constraints(sample_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert result["budget_gap"] == 50.0
    assert any("budget" in r.lower() for r in result["reasons"])


def test_missing_tool(sample_pathway):
    """Missing tool marks pathway infeasible and reports missing tool."""
    user_constraints = {
        "budget": "₹100",
        "time": "1 hour",
        "tools": ["Scissors"],  # Missing Utility knife and PVA glue
        "skill": "Intermediate",
        "workspace": "Indoor",
    }
    result = evaluate_constraints(sample_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert len(result["missing_tools"]) >= 1
    assert any("tool" in r.lower() for r in result["reasons"])


def test_missing_extra_material(sample_pathway):
    """Missing consumable material reports missing materials."""
    user_constraints = {
        "budget": "₹100",
        "time": "1 hour",
        "tools": ["Utility knife", "PVA glue"],
        "extra_materials": ["Tape"],  # Missing PVA glue
        "skill": "Intermediate",
        "workspace": "Indoor",
    }
    result = evaluate_constraints(sample_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert "Pva Glue" in result["missing_materials"] or "pva glue" in [m.lower() for m in result["missing_materials"]]


def test_insufficient_time(sample_pathway):
    """Insufficient time triggers infeasibility and calculates time gap."""
    user_constraints = {
        "budget": "₹100",
        "time": "15 minutes",  # Requires 30 mins
        "tools": ["Utility knife", "PVA glue"],
        "skill": "Intermediate",
        "workspace": "Indoor",
    }
    result = evaluate_constraints(sample_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert result["time_gap"] == 15
    assert any("time" in r.lower() for r in result["reasons"])


def test_insufficient_skill_level(sample_pathway):
    """Beginner user attempting Intermediate pathway triggers skill mismatch."""
    user_constraints = {
        "budget": "₹100",
        "time": "1 hour",
        "tools": ["Utility knife", "PVA glue"],
        "skill": "Beginner",  # Requires Intermediate
        "workspace": "Indoor",
    }
    result = evaluate_constraints(sample_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert any("skill" in r.lower() for r in result["reasons"])


def test_wrong_workspace():
    """Outdoor pathway requested in strictly indoor space triggers workspace mismatch."""
    outdoor_pathway = {
        "pathway_id": "REC-MET-002",
        "budget": "0",
        "time_required": "10 minutes",
        "tools": "None",
        "skill_level": "Beginner",
        "workspace": "Outdoor",
        "min_quantity": 1,
    }
    user_constraints = {
        "workspace": "Indoor",
        "budget": "₹500+",
        "time": "1 hour",
    }
    result = evaluate_constraints(outdoor_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert any("workspace" in r.lower() for r in result["reasons"])


def test_quantity_below_minimum(sample_pathway):
    """User having 1 item when pathway requires 2 items triggers quantity mismatch."""
    user_constraints = {
        "budget": "₹100",
        "time": "1 hour",
        "tools": ["Utility knife", "PVA glue"],
        "skill": "Intermediate",
        "workspace": "Indoor",
    }
    waste_profile = {
        "material": "cardboard",
        "confirmed_quantity": 1,  # Requires 2
        "condition": "Good",
    }
    result = evaluate_constraints(sample_pathway, user_constraints, waste_profile)
    assert result["constraint_status"] == "INFEASIBLE"
    assert any("quantity" in r.lower() for r in result["reasons"])


def test_waste_condition_mismatch(sample_pathway):
    """Damaged item when pathway requires 'Good' condition triggers condition mismatch."""
    user_constraints = {
        "budget": "₹100",
        "time": "1 hour",
        "tools": ["Utility knife", "PVA glue"],
        "skill": "Intermediate",
        "workspace": "Indoor",
    }
    waste_profile = {
        "material": "cardboard",
        "confirmed_quantity": 2,
        "condition": "Damaged",  # Pathway requires 'Good'
    }
    result = evaluate_constraints(sample_pathway, user_constraints, waste_profile)
    assert result["constraint_status"] == "INFEASIBLE"
    assert any("condition" in r.lower() for r in result["reasons"])


def test_multiple_failure_reasons(sample_pathway):
    """Multiple constraint failures are all captured simultaneously."""
    user_constraints = {
        "budget": "₹0",         # Short by 50
        "time": "5 minutes",     # Short by 25
        "tools": [],             # Missing knife and glue
        "skill": "Beginner",     # Mismatch
        "workspace": "Indoor",
    }
    result = evaluate_constraints(sample_pathway, user_constraints)
    assert result["constraint_status"] == "INFEASIBLE"
    assert len(result["reasons"]) >= 3
    assert result["budget_gap"] is not None
    assert result["time_gap"] is not None
    assert len(result["missing_tools"]) >= 1
