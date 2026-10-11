"""
ReNexa — Safety Service Unit Tests
====================================
Tests for rule-based safety evaluation (ALLOW, WARN, BLOCK).

Run with:
    python -m pytest tests/test_safety_service.py -v
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.safety_service import (
    load_safety_rules,
    evaluate_safety,
    normalize_material,
)


def test_safety_rules_load_successfully():
    """Safety rules CSV loads into valid rule dictionaries."""
    rules = load_safety_rules()
    assert isinstance(rules, list)
    assert len(rules) >= 15
    assert all("rule_id" in r and "status" in r for r in rules)


def test_battery_diy_repair_is_blocked():
    """Batteries must strictly BLOCK repair, reuse, and upcycle operations."""
    pathway = {
        "pathway_id": "TEST-BAT-001",
        "input_material": "battery",
        "pathway_type": "repair",
        "title": "Battery DIY Repair",
        "tools": "Screwdriver, pliers",
        "steps": "Open battery cell and replace electrolyte",
        "safety_level": "High",
    }
    result = evaluate_safety(pathway)
    assert result["safety_status"] == "BLOCK"
    assert len(result["reasons"]) > 0


def test_battery_safe_disposal_is_allowed():
    """Battery disposal into designated collection bins is allowed."""
    pathway = {
        "pathway_id": "REC-BAT-001",
        "input_material": "battery",
        "pathway_type": "dispose",
        "title": "Designated Battery E-Waste Drop-off",
        "tools": "Electrical tape",
        "steps": "Tape terminals and drop into e-waste bin",
        "safety_level": "High",
    }
    result = evaluate_safety(pathway)
    # Allowed with safety guidance
    assert result["safety_status"] in ("ALLOW", "WARN")


def test_plastic_thermal_melting_is_blocked():
    """Plastic thermal melting or burning must strictly BLOCK."""
    pathway = {
        "pathway_id": "TEST-PLA-BURN",
        "input_material": "plastic",
        "pathway_type": "upcycle",
        "title": "Melt plastic in oven",
        "tools": "Oven, mold",
        "steps": "Heat and melt plastic bottles in home oven",
        "safety_level": "High",
    }
    result = evaluate_safety(pathway)
    assert result["safety_status"] == "BLOCK"
    assert any("toxic" in r.lower() or "melt" in r.lower() or "dioxin" in r.lower() for r in result["reasons"])


def test_glass_cutting_triggers_warn():
    """Glass cutting or piercing triggers WARN with laceration precaution."""
    pathway = {
        "pathway_id": "TEST-GLA-CUT",
        "input_material": "glass",
        "pathway_type": "upcycle",
        "title": "Cut glass bottle into cup",
        "tools": "Utility knife, blade",
        "steps": "Score and snap glass bottle",
        "safety_level": "Medium",
    }
    result = evaluate_safety(pathway)
    assert result["safety_status"] in ("WARN", "BLOCK")
    assert len(result["warnings"]) > 0 or len(result["reasons"]) > 0


def test_standard_plastic_reuse_is_allowed():
    """Standard mechanical plastic storage reuse is ALLOW."""
    pathway = {
        "pathway_id": "REC-PLA-001",
        "input_material": "plastic",
        "pathway_type": "reuse",
        "title": "Plastic Container Storage",
        "tools": "None",
        "steps": "Wash container and store dry goods",
        "safety_level": "Low",
    }
    result = evaluate_safety(pathway)
    assert result["safety_status"] == "ALLOW"
    assert len(result["reasons"]) == 0


def test_material_normalization_in_safety():
    """Glass sub-label (brown-glass) normalizes and matches glass safety rules."""
    pathway = {
        "pathway_id": "REC-GLA-001",
        "input_material": "brown-glass",
        "pathway_type": "reuse",
        "title": "Glass Jar Storage",
        "tools": "None",
        "steps": "Wash jar and store pantry items",
        "safety_level": "Low",
    }
    result = evaluate_safety(pathway)
    assert result["safety_status"] == "ALLOW"


def test_safety_preference_flagging():
    """User strict low-risk preference flags medium-risk pathways with notice."""
    pathway = {
        "pathway_id": "REC-MET-002",
        "input_material": "metal",
        "pathway_type": "upcycle",
        "title": "Hanging Herb Planter",
        "tools": "Hammer",
        "steps": "Punch holes in metal tin with hammer and nail",
        "safety_level": "Medium",
    }
    result = evaluate_safety(pathway, safety_preference="Only low-risk options")
    assert any("safety level" in w.lower() or "preference" in w.lower() for w in result["warnings"])

def test_chipped_glass_is_blocked_for_household_upcycling():
    """Chipped glass must not be recommended for household upcycling."""
    pathway = {
        "pathway_id": "TEST-GLA-CHIPPED",
        "input_material": "glass",
        "pathway_type": "upcycle",
        "title": "Glass Candle Holder or Planter",
        "tools": "Towel, small pebbles",
        "steps": "Clean glass jar and add pebbles",
        "safety_level": "Low",
    }
    profile = {
        "material": "glass",
        "condition": "Chipped",
        "contamination": "Clean",
    }

    result = evaluate_safety(pathway, waste_profile=profile)

    assert result["safety_status"] == "BLOCK"
    assert len(result["reasons"]) > 0


def test_metal_tin_hole_punching_is_blocked():
    """DIY hole punching in a metal tin must be blocked due to sharp-burr risk."""
    pathway = {
        "pathway_id": "TEST-MET-HOLE",
        "input_material": "metal",
        "pathway_type": "upcycle",
        "title": "Hanging Herb Planter",
        "tools": "Hammer, nail, twine",
        "steps": "Punch drainage holes in a metal tin with a hammer and nail",
        "safety_level": "Medium",
    }

    result = evaluate_safety(pathway)

    assert result["safety_status"] == "BLOCK"
    assert len(result["reasons"]) > 0
