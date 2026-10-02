"""
ReNexa — Recovery Knowledge Base Tests
========================================
Tests for loading, querying, and validating recovery pathways from CSV.

Run with:
    python -m pytest tests/test_recovery_service.py -v
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.recovery_service import (
    DEFAULT_CSV_PATH,
    REQUIRED_COLUMNS,
    ALLOWED_PATHWAY_TYPES,
    load_recovery_pathways,
    get_recovery_pathways,
    get_pathways_for_profile,
    get_available_materials,
    normalize_material_name,
)


# ============================================================
# Phase 4 Mandatory Test Cases (TEST 1 – TEST 14)
# ============================================================

def test_phase4_test1_csv_exists():
    """TEST 1: Recovery pathways CSV file exists on disk."""
    assert os.path.isfile(DEFAULT_CSV_PATH), f"CSV not found at {DEFAULT_CSV_PATH}"


def test_phase4_test2_csv_contains_all_required_columns():
    """TEST 2: CSV contains all required columns in header."""
    import csv
    with open(DEFAULT_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for col in REQUIRED_COLUMNS:
            assert col in header, f"Missing required column '{col}' in CSV header"


def test_phase4_test3_csv_loads_successfully():
    """TEST 3: CSV loads into a non-empty list of dictionary records."""
    pathways = load_recovery_pathways()
    assert isinstance(pathways, list)
    assert len(pathways) > 0
    assert all(isinstance(p, dict) for p in pathways)


def test_phase4_test4_plastic_pathways_retrieved():
    """TEST 4: Plastic pathways can be queried and retrieved."""
    pathways = get_recovery_pathways("plastic")
    assert len(pathways) >= 3
    assert all(p["input_material"] == "plastic" for p in pathways)


def test_phase4_test5_glass_pathways_retrieved():
    """TEST 5: Glass pathways can be queried and retrieved."""
    pathways = get_recovery_pathways("glass")
    assert len(pathways) >= 3
    assert all(p["input_material"] == "glass" for p in pathways)


def test_phase4_test6_metal_pathways_retrieved():
    """TEST 6: Metal pathways can be queried and retrieved."""
    pathways = get_recovery_pathways("metal")
    assert len(pathways) >= 2
    assert all(p["input_material"] == "metal" for p in pathways)


def test_phase4_test7_paper_pathways_retrieved():
    """TEST 7: Paper pathways can be queried and retrieved."""
    pathways = get_recovery_pathways("paper")
    assert len(pathways) >= 2
    assert all(p["input_material"] == "paper" for p in pathways)


def test_phase4_test8_cardboard_pathways_retrieved():
    """TEST 8: Cardboard pathways can be queried and retrieved."""
    pathways = get_recovery_pathways("cardboard")
    assert len(pathways) >= 3
    assert all(p["input_material"] == "cardboard" for p in pathways)


def test_phase4_test9_clothes_pathways_retrieved():
    """TEST 9: Clothes pathways can be queried and retrieved."""
    pathways = get_recovery_pathways("clothes")
    assert len(pathways) >= 2
    assert all(p["input_material"] == "clothes" for p in pathways)


def test_phase4_test10_unknown_material_returns_empty():
    """TEST 10: Unknown material or unrecognized string returns empty list."""
    assert get_recovery_pathways("Unknown") == []
    assert get_recovery_pathways("unsupported_alien_material") == []
    assert get_recovery_pathways("") == []
    assert get_recovery_pathways(None) != []  # None returns all pathways


def test_phase4_test11_all_pathway_types_valid():
    """TEST 11: All pathway types belong to allowed canonical set."""
    pathways = load_recovery_pathways()
    for p in pathways:
        assert p["pathway_type"] in ALLOWED_PATHWAY_TYPES, (
            f"Pathway '{p['pathway_id']}' has invalid type '{p['pathway_type']}'"
        )


def test_phase4_test12_no_pathway_empty_title():
    """TEST 12: No pathway has an empty or whitespace-only title."""
    pathways = load_recovery_pathways()
    for p in pathways:
        assert p["title"] and len(p["title"].strip()) > 0, (
            f"Pathway '{p['pathway_id']}' has an empty title"
        )


def test_phase4_test13_no_pathway_fake_source():
    """TEST 13: No pathway has fake or placeholder source links."""
    pathways = load_recovery_pathways()
    for p in pathways:
        source = p.get("source", "")
        assert source and len(source.strip()) > 0
        assert not source.startswith("http://fake")
        assert not source.startswith("www.example.com")


def test_phase4_test14_material_normalization():
    """TEST 14: Material normalization works for sub-classes (brown-glass -> glass)."""
    assert normalize_material_name("brown-glass") == "glass"
    assert normalize_material_name("green-glass") == "glass"
    assert normalize_material_name("white-glass") == "glass"

    # Querying with 'brown-glass' should return 'glass' pathways
    brown_glass_pathways = get_recovery_pathways("brown-glass")
    glass_pathways = get_recovery_pathways("glass")
    assert len(brown_glass_pathways) > 0
    assert brown_glass_pathways == glass_pathways


# ============================================================
# Additional Knowledge Base Helper Tests
# ============================================================

def test_get_pathways_for_profile():
    """get_pathways_for_profile should extract material and return matches."""
    profile = {
        "material": "plastic",
        "item": "Unknown",
        "condition": "Good",
        "quantity": 2,
    }
    pathways = get_pathways_for_profile(profile)
    assert len(pathways) > 0
    assert all(p["input_material"] == "plastic" for p in pathways)

    # Empty profile returns empty list
    assert get_pathways_for_profile(None) == []
    assert get_pathways_for_profile({}) == []


def test_get_available_materials_list():
    """get_available_materials returns list of unique materials."""
    materials = get_available_materials()
    assert isinstance(materials, list)
    assert len(materials) >= 8
    assert "plastic" in materials
    assert "glass" in materials
    assert "metal" in materials
