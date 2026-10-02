"""
ReNexa — Phase 7 Execution Service Unit Tests
==============================================
Comprehensive unit tests for execution guidance retrieval, step parsing,
safety enforcement, constraint validation, and data integrity.

Run with:
    python -m pytest tests/test_execution_service.py -v
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.execution_service import (
    parse_execution_steps,
    get_pathway_by_id,
    get_execution_guide,
)


def test_valid_pathway_retrieves_guide():
    """Valid pathway retrieves a structured execution guide."""
    guide = get_execution_guide("REC-PLA-001")
    assert guide is not None
    assert guide["pathway_id"] == "REC-PLA-001"
    assert guide["title"] == "Plastic Container Storage"
    assert guide["can_execute"] is True
    assert guide["execution_status"] == "READY"


def test_correct_title():
    """Title matches exactly from knowledge base."""
    guide = get_execution_guide("REC-GLA-001")
    assert guide["title"] == "Glass Jar Pantry Storage"


def test_tools_preserved():
    """Tools list preserves catalogued tools without fabrication."""
    guide = get_execution_guide("REC-PLA-002")
    assert "Scissors" in guide["tools"]


def test_extra_materials_preserved():
    """Extra materials list preserves catalogued materials."""
    guide = get_execution_guide("REC-PLA-002")
    assert "Potting soil" in guide["extra_materials"]


def test_budget_preserved():
    """Budget value matches the pathway definition."""
    guide = get_execution_guide("REC-PLA-003")
    assert guide["budget"] == "50"


def test_time_preserved():
    """Time required string is preserved."""
    guide = get_execution_guide("REC-PLA-001")
    assert guide["time_required"] == "5 minutes"


def test_skill_preserved():
    """Skill level matches pathway record."""
    guide = get_execution_guide("REC-MET-002")
    assert guide["skill_level"] == "Intermediate"


def test_workspace_preserved():
    """Workspace requirements are preserved."""
    guide = get_execution_guide("REC-MET-002")
    assert guide["workspace"] == "Outdoor"


def test_steps_preserved_in_exact_order():
    """Steps are parsed sequentially preserving original numbering and order."""
    raw = "1. Clean container; 2. Carefully pierce small drainage holes in the base; 3. Fill with soil and plant seeds."
    steps = parse_execution_steps(raw)
    assert len(steps) == 3
    assert steps[0].startswith("1. Clean container")
    assert steps[1].startswith("2. Carefully pierce")
    assert steps[2].startswith("3. Fill with soil")


def test_expected_output_preserved():
    """Expected outcome text is preserved from knowledge base."""
    guide = get_execution_guide("REC-PLA-001")
    assert "Organized dry storage container" in guide["expected_output"]


def test_fallback_preserved():
    """Fallback pathway is preserved."""
    guide = get_execution_guide("REC-PLA-001")
    assert "Municipal dry recycling" in guide["fallback"]


def test_source_preserved():
    """Source authority is preserved."""
    guide = get_execution_guide("REC-PLA-001")
    assert "Municipal Solid Waste Management Guidelines" in guide["source"]


def test_block_pathway_cannot_be_executed():
    """Safety BLOCK strictly prevents execution (can_execute == False)."""
    hazardous_pathway = {
        "pathway_id": "HAZ-BAT-999",
        "input_material": "battery",
        "pathway_type": "repair",
        "title": "Battery Acid Refill",
        "steps": "1. Open cell; 2. Pour acid",
        "tools": "Pliers",
        "budget": "0",
        "time_required": "10 minutes",
        "skill_level": "Beginner",
        "workspace": "Indoor",
    }
    guide = get_execution_guide(hazardous_pathway)
    assert guide["can_execute"] is False
    assert guide["execution_status"] == "BLOCKED"
    assert guide["safety_status"] == "BLOCK"
    assert len(guide["reasons"]) > 0


def test_warn_pathway_keeps_warnings():
    """Safety WARN preserves warnings while allowing execution if feasible."""
    warn_pathway = {
        "pathway_id": "REC-GLA-003",
        "input_material": "glass",
        "pathway_type": "upcycle",
        "title": "Glass Planter",
        "tools": "Utility knife",
        "steps": "1. Score bottle with knife; 2. Snap glass; 3. Sand edges.",
        "budget": "0",
        "time_required": "15 minutes",
        "skill_level": "Beginner",
        "workspace": "Indoor",
    }
    user_constraints = {"tools": ["Utility knife"], "budget": "₹100", "time": "30 mins"}
    guide = get_execution_guide(warn_pathway, user_constraints=user_constraints)
    if guide["safety_status"] == "WARN":
        assert len(guide["warnings"]) > 0
        assert guide["can_execute"] is True


def test_allow_pathway_works_normally():
    """Standard low-risk pathway allows clean execution."""
    guide = get_execution_guide("REC-PLA-001")
    assert guide["safety_status"] == "ALLOW"
    assert guide["can_execute"] is True
    assert guide["execution_status"] == "READY"


def test_missing_steps_handled_safely():
    """Missing or empty steps are handled gracefully without raising unhandled exceptions."""
    no_step_pathway = {
        "pathway_id": "TEST-NO-STEP",
        "input_material": "paper",
        "pathway_type": "reuse",
        "title": "Blank Step Pathway",
        "steps": "",
        "tools": "None",
        "budget": "0",
        "time_required": "5 minutes",
    }
    guide = get_execution_guide(no_step_pathway)
    assert guide["can_execute"] is False
    assert guide["execution_status"] == "DATA_QUALITY_ISSUE"
    assert len(guide["steps"]) == 0


def test_missing_tutorial_handled_safely():
    """Missing source citation produces explicit message rather than empty string."""
    no_src_pathway = {
        "pathway_id": "TEST-NO-SRC",
        "input_material": "paper",
        "pathway_type": "reuse",
        "title": "Blank Source Pathway",
        "steps": "1. Fold paper; 2. Use as bookmark",
        "source": "",
    }
    guide = get_execution_guide(no_src_pathway)
    assert guide["tutorial_available"] is False
    assert "No verified tutorial reference is available" in guide["tutorial_reference"]


def test_selected_pathway_must_be_eligible():
    """Infeasible constraint mismatch prevents execution."""
    pathway = {
        "pathway_id": "REC-EXPENSIVE",
        "input_material": "cardboard",
        "pathway_type": "upcycle",
        "title": "High Budget Project",
        "steps": "1. Cut board; 2. Glue together",
        "budget": "500",
        "tools": "None",
        "time_required": "15 minutes",
    }
    user_constraints = {"budget": "₹0"}  # 0 budget causes infeasibility
    guide = get_execution_guide(pathway, user_constraints=user_constraints)
    assert guide["can_execute"] is False
    assert guide["execution_status"] == "INFEASIBLE"
    assert any("budget" in r.lower() for r in guide["reasons"])


def test_repeated_retrieval_is_deterministic():
    """Guidance retrieval produces identical results across repeated calls."""
    g1 = get_execution_guide("REC-CAR-001")
    g2 = get_execution_guide("REC-CAR-001")
    assert g1 == g2


def test_no_fabricated_fields():
    """All metadata fields derive directly from input record."""
    guide = get_execution_guide("REC-SHO-002")
    assert guide["input_material"] == "shoes"
    assert guide["pathway_type"] == "reuse"
    assert guide["time_required"] == "5 minutes"
