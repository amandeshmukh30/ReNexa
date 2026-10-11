"""
ReNexa — Recovery Expansion & Coverage Regression Tests
======================================================
Validates expanded recovery pathways, detector class coverage,
safety constraints, and tutorial matching.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.recovery_service import (
    load_recovery_pathways,
    get_recovery_pathways,
    get_available_materials,
    get_tutorials_for_pathway,
    get_tutorials,
    normalize_material_name,
)
from services.safety_service import evaluate_safety, load_safety_rules
from services.ranking_service import get_ranked_recommendations_for_profile
from services.execution_service import get_execution_guide
from utils.validation import get_default_constraints


def test_pathway_count_expanded():
    """Verify that pathways knowledge base has been expanded beyond baseline 29."""
    pathways = load_recovery_pathways()
    assert len(pathways) >= 50, f"Expected at least 50 pathways, got {len(pathways)}"


def test_unique_pathway_ids():
    """Ensure no duplicate pathway IDs exist in recovery_pathways.csv."""
    pathways = load_recovery_pathways()
    ids = [p["pathway_id"] for p in pathways]
    duplicates = [pid for pid in set(ids) if ids.count(pid) > 1]
    assert len(duplicates) == 0, f"Duplicate pathway IDs found: {duplicates}"


def test_all_detector_classes_covered():
    """Verify that all 7 YOLO detector classes have catalogued recovery pathways."""
    detector_classes = ["cardboard", "glass", "metal", "organic", "other", "paper", "plastic"]
    for det_class in detector_classes:
        norm_mat = normalize_material_name(det_class)
        matching = get_recovery_pathways(material=norm_mat)
        assert len(matching) > 0, f"No pathways catalogued for detector class '{det_class}' (normalized: '{norm_mat}')"


def test_other_material_pathways_present():
    """Verify that 'other' material now has distinct pathways."""
    other_pws = get_recovery_pathways(material="other")
    assert len(other_pws) >= 4, f"Expected at least 4 pathways for 'other', got {len(other_pws)}"
    types = {p["pathway_type"] for p in other_pws}
    assert "upcycle" in types
    assert "repair" in types
    assert "recycle" in types


def test_biological_material_pathways_expanded():
    """Verify that 'biological' material has expanded home recovery pathways."""
    bio_pws = get_recovery_pathways(material="biological")
    assert len(bio_pws) >= 4, f"Expected at least 4 pathways for biological, got {len(bio_pws)}"


def test_all_seven_detector_classes_rank_feasible_recommendations():
    """Verify that every detector class returns at least one feasible recommendation with default constraints."""
    defaults = get_default_constraints()
    detector_classes = ["cardboard", "glass", "metal", "organic", "other", "paper", "plastic"]

    for det_class in detector_classes:
        norm_mat = normalize_material_name(det_class)
        profile = {
            "material": norm_mat,
            "item": f"Sample {det_class} item",
            "condition": "Good",
            "contamination": "Clean",
            "confirmed_quantity": 1,
        }
        ranked = get_ranked_recommendations_for_profile(profile, defaults, top_k=3)
        assert len(ranked) > 0, f"Zero feasible recommendations for detector class '{det_class}'"
        assert all(r["eligible"] for r in ranked)


def test_safety_rules_for_new_materials():
    """Verify safety rules properly evaluate 'other' and 'biological' operations."""
    rules = load_safety_rules()
    materials = {r["material"] for r in rules}
    assert "other" in materials
    assert "biological" in materials

    # Cutting cork with utility knife should trigger WARN
    cork_eval = evaluate_safety({
        "input_material": "other",
        "pathway_type": "upcycle",
        "tools": "Utility knife",
        "steps": "Slice corks with sharp knife.",
    })
    assert cork_eval["safety_status"] == "WARN"

    # Standard miscellaneous reuse should be ALLOW
    other_reuse = evaluate_safety({
        "input_material": "other",
        "pathway_type": "reuse",
        "tools": "None",
        "steps": "Clean and store.",
    })
    assert other_reuse["safety_status"] == "ALLOW"


def test_verified_tutorials_matched_for_expanded_pathways():
    """Verify that newly added pathways match existing verified tutorials."""
    # Plastic self-watering planter
    p5_tuts = get_tutorials_for_pathway("REC-PLA-005", verified_only=True)
    assert len(p5_tuts) > 0
    assert any("planter" in t["product_name"].lower() for t in p5_tuts)

    # Cork trivet
    cork_tuts = get_tutorials_for_pathway("REC-OTH-001", verified_only=True)
    assert len(cork_tuts) > 0
    assert any("trivet" in t["product_name"].lower() or "cork" in t["raw_material"].lower() for t in cork_tuts)

    # Paper seed pots
    pot_tuts = get_tutorials_for_pathway("REC-PAP-004", verified_only=True)
    assert len(pot_tuts) > 0
    assert any("seed" in t["product_name"].lower() or "pot" in t["product_name"].lower() for t in pot_tuts)
