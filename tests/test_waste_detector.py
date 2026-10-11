"""
ReNexa — Waste Detector & Structured Profile Tests
====================================================
Tests for WasteDetector inference, glass label normalisation,
Phase 3 Structured Waste Profile creation, condition/contamination
assessment, validation rules, and no-detection handling.

Run with:
    python -m pytest tests/test_waste_detector.py -v
"""

import sys
import os

# Make project root importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from ai.model_config import (
    MODEL_PATH,
    GLASS_LABELS,
    MATERIAL_OPTIONS,
    ALLOWED_CONDITIONS,
    ALLOWED_CONTAMINATIONS,
)
from ai.waste_detector import WasteDetector
from ai.waste_profile import (
    create_waste_profile,
    update_profile_user_fields,
    validate_waste_profile,
    is_valid_waste_profile,
    normalize_condition,
    normalize_contamination,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def detector():
    """Load the detector once for all tests in this module."""
    return WasteDetector()


@pytest.fixture(scope="module")
def sample_image_path():
    """
    Path to an existing TrashNet cardboard image for integration tests.
    This file should already exist in the dataset.
    """
    path = os.path.join(
        PROJECT_ROOT,
        "data", "raw", "trashnet", "dataset-resized", "cardboard", "cardboard1.jpg",
    )
    return path


# ============================================================
# Section 1: Model Loading Tests
# ============================================================

def test_model_loads(detector):
    """The WasteDetector should load the YOLO model without error."""
    assert detector.model is not None


def test_model_has_class_names(detector):
    """The loaded YOLO26s model should report exactly 7 trained classes with exact IDs."""
    expected_classes = {
        0: "cardboard",
        1: "glass",
        2: "metal",
        3: "organic",
        4: "other",
        5: "paper",
        6: "plastic",
    }
    assert len(detector.class_names) == 7
    assert detector.model.names == expected_classes



def test_model_path_exists():
    """The configured model file should exist on disk."""
    assert os.path.isfile(MODEL_PATH), f"Model not found at {MODEL_PATH}"


# ============================================================
# Section 2: Detector Return Structure Tests
# ============================================================

def test_detect_returns_dict(detector, sample_image_path):
    """detect() should return a plain Python dict."""
    if not os.path.isfile(sample_image_path):
        pytest.skip("Sample image not available")
    result = detector.detect(sample_image_path)
    assert isinstance(result, dict)


def test_result_has_expected_keys(detector, sample_image_path):
    """The result dict should contain all required keys."""
    if not os.path.isfile(sample_image_path):
        pytest.skip("Sample image not available")
    result = detector.detect(sample_image_path)
    expected_keys = {"detected", "label", "model_label", "confidence", "all_detections"}
    assert expected_keys.issubset(result.keys())


def test_confidence_is_float(detector, sample_image_path):
    """Confidence should be a float between 0 and 1."""
    if not os.path.isfile(sample_image_path):
        pytest.skip("Sample image not available")
    result = detector.detect(sample_image_path)
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


def test_all_detections_is_list(detector, sample_image_path):
    """all_detections should always be a list."""
    if not os.path.isfile(sample_image_path):
        pytest.skip("Sample image not available")
    result = detector.detect(sample_image_path)
    assert isinstance(result["all_detections"], list)


# ============================================================
# Section 3: Glass Label Normalisation Tests
# ============================================================

def test_glass_normalisation_brown():
    """brown-glass should normalise to glass."""
    assert WasteDetector._normalize_label("brown-glass") == "glass"


def test_glass_normalisation_green():
    """green-glass should normalise to glass."""
    assert WasteDetector._normalize_label("green-glass") == "glass"


def test_glass_normalisation_white():
    """white-glass should normalise to glass."""
    assert WasteDetector._normalize_label("white-glass") == "glass"


def test_non_glass_passes_through():
    """Non-glass labels should not be changed."""
    assert WasteDetector._normalize_label("plastic") == "plastic"
    assert WasteDetector._normalize_label("metal") == "metal"
    assert WasteDetector._normalize_label("cardboard") == "cardboard"


def test_glass_labels_config():
    """The GLASS_LABELS config should contain exactly 3 glass types."""
    assert GLASS_LABELS == {"brown-glass", "green-glass", "white-glass"}


# ============================================================
# Section 4: Phase 3 Dedicated Profile & Validation Tests
# ============================================================

def test_phase3_test1_basic_profile_creation():
    """TEST 1: Basic profile creation with required fields."""
    detection = {
        "detected": True,
        "label": "plastic",
        "model_label": "plastic",
        "confidence": 0.85,
        "count": 1,
        "material_counts": {"plastic": 1},
        "all_detections": [{"label": "plastic", "confidence": 0.85, "box": [0, 0, 10, 10]}],
    }
    profile = create_waste_profile(detection)
    assert "material" in profile and profile["material"] == "plastic"
    assert "item" in profile and profile["item"] == "Unknown"
    assert "confirmed_quantity" in profile and profile["confirmed_quantity"] == 1
    assert "detected_object_count" in profile and profile["detected_object_count"] == 1


def test_phase3_test2_plastic_material():
    """TEST 2: Plastic material detection maintains material != item."""
    detection = {
        "detected": True,
        "label": "plastic",
        "model_label": "plastic",
        "confidence": 0.82,
        "count": 1,
        "material_counts": {"plastic": 1},
        "all_detections": [],
    }
    profile = create_waste_profile(detection)
    assert profile["material"] == "plastic"
    assert profile["item"] == "Unknown"
    assert profile["item"] != "plastic bottle"
    assert profile["item"] != "plastic"


def test_phase3_test3_glass_normalization():
    """TEST 3: Glass normalization preserves model_label and sets material to glass."""
    detection = {
        "detected": True,
        "label": "glass",
        "model_label": "brown-glass",
        "confidence": 0.91,
        "count": 1,
        "material_counts": {"glass": 1},
        "all_detections": [],
    }
    profile = create_waste_profile(detection)
    assert profile["material"] == "glass"
    assert profile["model_label"] == "brown-glass"


def test_phase3_test4_multiple_materials():
    """TEST 4: Multiple materials counted correctly in material_counts."""
    detection = {
        "detected": True,
        "label": "plastic",
        "model_label": "plastic",
        "confidence": 0.88,
        "count": 4,
        "material_counts": {"plastic": 2, "glass": 1, "metal": 1},
        "all_detections": [
            {"label": "plastic", "model_label": "plastic", "confidence": 0.88, "box": [0, 0, 10, 10]},
            {"label": "plastic", "model_label": "plastic", "confidence": 0.80, "box": [10, 10, 20, 20]},
            {"label": "glass", "model_label": "green-glass", "confidence": 0.75, "box": [20, 20, 30, 30]},
            {"label": "metal", "model_label": "metal", "confidence": 0.70, "box": [30, 30, 40, 40]},
        ],
    }
    profile = create_waste_profile(detection)
    assert profile["material_counts"] == {"plastic": 2, "glass": 1, "metal": 1}
    assert profile["detected_object_count"] == 4


def test_phase3_test5_detected_count():
    """TEST 5: Detected count reflects number of valid AI detections."""
    detection = {
        "detected": True,
        "label": "cardboard",
        "model_label": "cardboard",
        "confidence": 0.85,
        "count": 3,
        "material_counts": {"cardboard": 3},
        "all_detections": [{}, {}, {}],
    }
    profile = create_waste_profile(detection)
    assert profile["detected_object_count"] == 3


def test_phase3_test6_confirmed_quantity_defaults_to_detected_count():
    """TEST 6: Confirmed quantity defaults to detected count."""
    detection = {
        "detected": True,
        "label": "metal",
        "model_label": "metal",
        "confidence": 0.90,
        "count": 4,
        "material_counts": {"metal": 4},
        "all_detections": [],
    }
    profile = create_waste_profile(detection)
    assert profile["detected_object_count"] == 4
    assert profile["confirmed_quantity"] == 4


def test_phase3_test7_manual_quantity_override():
    """TEST 7: Manual quantity override updates confirmed_quantity while keeping detected_object_count."""
    detection = {
        "detected": True,
        "label": "paper",
        "model_label": "paper",
        "confidence": 0.80,
        "count": 5,
        "material_counts": {"paper": 5},
        "all_detections": [],
    }
    profile = create_waste_profile(detection)
    assert profile["detected_object_count"] == 5
    assert profile["confirmed_quantity"] == 5

    # User adjusts confirmed quantity to 3
    updated = update_profile_user_fields(profile, confirmed_quantity=3, confirmed=True)
    assert updated["detected_object_count"] == 5
    assert updated["confirmed_quantity"] == 3
    assert updated["quantity"] == 3


def test_phase3_test8_condition_allowed_values():
    """TEST 8: Condition accepts Good, Used, Damaged, Heavily Damaged, Unknown."""
    detection = {
        "detected": True,
        "label": "plastic",
        "model_label": "plastic",
        "confidence": 0.85,
        "count": 1,
        "all_detections": [],
    }
    for cond in ALLOWED_CONDITIONS:
        profile = create_waste_profile(detection)
        updated = update_profile_user_fields(profile, condition=cond, confirmed=True)
        assert updated["condition"] == cond
        valid, errors = validate_waste_profile(updated)
        assert valid, f"Condition {cond} failed validation: {errors}"


def test_phase3_test9_contamination_allowed_values():
    """TEST 9: Contamination accepts Clean, Slightly Contaminated, Heavily Contaminated, Unknown."""
    detection = {
        "detected": True,
        "label": "glass",
        "model_label": "glass",
        "confidence": 0.85,
        "count": 1,
        "all_detections": [],
    }
    for cont in ALLOWED_CONTAMINATIONS:
        profile = create_waste_profile(detection)
        updated = update_profile_user_fields(profile, contamination=cont, confirmed=True)
        assert updated["contamination"] == cont
        valid, errors = validate_waste_profile(updated)
        assert valid, f"Contamination {cont} failed validation: {errors}"


def test_phase3_test10_invalid_quantity_rejected():
    """TEST 10: Negative quantity is rejected by validation."""
    profile = {
        "material": "plastic",
        "item": "Unknown",
        "detected_object_count": 2,
        "confirmed_quantity": -1,  # invalid negative
        "condition": "Good",
        "contamination": "Clean",
        "confidence": 0.8,
        "material_counts": {"plastic": 2},
    }
    is_valid, errors = validate_waste_profile(profile)
    assert is_valid is False
    assert any("quantity" in err.lower() for err in errors)


def test_phase3_test11_invalid_confidence_rejected():
    """TEST 11: Confidence outside 0–1 is rejected by validation."""
    profile_high = {
        "material": "plastic",
        "item": "Unknown",
        "detected_object_count": 1,
        "confirmed_quantity": 1,
        "condition": "Good",
        "contamination": "Clean",
        "confidence": 1.5,  # invalid > 1.0
        "material_counts": {"plastic": 1},
    }
    is_valid, errors = validate_waste_profile(profile_high)
    assert is_valid is False
    assert any("confidence" in err.lower() for err in errors)

    profile_neg = dict(profile_high, confidence=-0.2)
    is_valid_neg, errors_neg = validate_waste_profile(profile_neg)
    assert is_valid_neg is False


def test_phase3_test12_no_detection():
    """TEST 12: No detection returns material = Unknown, item = Unknown, detected_object_count = 0."""
    no_detect = {
        "detected": False,
        "label": None,
        "model_label": None,
        "confidence": 0.0,
        "count": 0,
        "all_detections": [],
    }
    profile = create_waste_profile(no_detect)
    assert profile["material"] == "Unknown"
    assert profile["item"] == "Unknown"
    assert profile["detected_object_count"] == 0
    assert profile["confirmed_quantity"] == 0
    assert profile["user_confirmed"] is False

    # Also test with None
    profile_none = create_waste_profile(None)
    assert profile_none["material"] == "Unknown"
    assert profile_none["item"] == "Unknown"
    assert profile_none["detected_object_count"] == 0


def test_phase3_test13_no_fake_item_inference():
    """TEST 13: Plastic must NOT automatically become plastic bottle."""
    detection = {
        "detected": True,
        "label": "plastic",
        "model_label": "plastic",
        "confidence": 0.88,
        "count": 1,
        "material_counts": {"plastic": 1},
        "all_detections": [],
    }
    profile = create_waste_profile(detection)
    assert profile["item"] != "bottle"
    assert profile["item"] != "plastic bottle"
    assert profile["item"] == "Unknown"


# ============================================================
# Section 5: Backward Compatibility Tests
# ============================================================

def test_profile_from_detection():
    """create_waste_profile should build a correct profile dict."""
    mock_detection = {
        "detected": True,
        "label": "plastic",
        "model_label": "plastic",
        "confidence": 0.88,
        "count": 3,
        "material_counts": {"plastic": 3},
        "all_detections": [
            {"label": "plastic", "model_label": "plastic", "confidence": 0.88, "box": [10.0, 20.0, 100.0, 200.0]},
            {"label": "plastic", "model_label": "plastic", "confidence": 0.82, "box": [110.0, 20.0, 200.0, 200.0]},
            {"label": "plastic", "model_label": "plastic", "confidence": 0.75, "box": [210.0, 20.0, 300.0, 200.0]},
        ],
    }
    profile = create_waste_profile(mock_detection)
    assert profile["material"] == "plastic"
    assert profile["item"] == "Unknown"
    assert profile["model_label"] == "plastic"
    assert profile["confidence"] == 0.88
    assert profile["quantity"] == 3
    assert profile["confirmed_quantity"] == 3
    assert profile["detected_count"] == 3
    assert profile["detected_object_count"] == 3
    assert profile["material_counts"] == {"plastic": 3}
    assert profile["condition"] == "Unknown"
    assert profile["contamination"] == "Unknown"
    assert profile["user_confirmed"] is False


def test_profile_update():
    """update_profile_user_fields should correctly set all fields."""
    mock_detection = {
        "detected": True,
        "label": "metal",
        "model_label": "metal",
        "confidence": 0.75,
        "count": 1,
        "material_counts": {"metal": 1},
        "all_detections": [],
    }
    profile = create_waste_profile(mock_detection)
    updated = update_profile_user_fields(
        profile,
        material="metal",
        condition="Good",
        quantity=3,
        contamination="Clean",
        confirmed=True,
    )
    assert updated["material"] == "metal"
    assert updated["condition"] == "Good"
    assert updated["quantity"] == 3
    assert updated["confirmed_quantity"] == 3
    assert updated["contamination"] == "Clean"
    assert updated["user_confirmed"] is True


def test_empty_result_structure():
    """An empty result from the detector should have valid structure."""
    empty = WasteDetector._empty_result()
    assert empty["detected"] is False
    assert empty["label"] is None
    assert empty["confidence"] == 0.0
    assert empty["all_detections"] == []


def test_profile_from_no_detection():
    """create_waste_profile should handle a no-detection dict safely."""
    no_detect = {
        "detected": False,
        "label": None,
        "model_label": None,
        "confidence": 0.0,
        "all_detections": [],
    }
    profile = create_waste_profile(no_detect)
    assert profile["item"] == "Unknown"
    assert profile["material"] == "Unknown"
    assert profile["user_confirmed"] is False


def test_profile_from_none():
    """create_waste_profile should handle None input without crashing."""
    profile = create_waste_profile(None)
    assert profile["item"] == "Unknown"
    assert profile["material"] == "Unknown"
    assert profile["user_confirmed"] is False


def test_invalid_image_returns_empty(detector):
    """Passing a non-existent path should return an empty result, not crash."""
    result = detector.detect("this_file_does_not_exist.jpg")
    assert result["detected"] is False
    assert result["all_detections"] == []


def test_material_options_list():
    """MATERIAL_OPTIONS should be a non-empty list of strings."""
    assert isinstance(MATERIAL_OPTIONS, list)
    assert len(MATERIAL_OPTIONS) > 0
    assert all(isinstance(m, str) for m in MATERIAL_OPTIONS)
    assert "glass" in MATERIAL_OPTIONS
    assert "brown-glass" not in MATERIAL_OPTIONS
