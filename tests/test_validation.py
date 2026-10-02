"""
ReNexa — Basic Tests
=====================
Simple tests for validation helpers and default constraints.

Run with:
    python -m pytest tests/test_validation.py -v
"""

import sys
import os

# Make project root importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.validation import (
    is_valid_extension,
    is_valid_size,
    format_file_size,
    get_default_constraints,
    MAX_UPLOAD_BYTES,
    ALLOWED_EXTENSIONS,
)


# ── Extension validation tests ────────────────────────────────────────────

def test_valid_jpg_extension():
    assert is_valid_extension("photo.jpg") is True


def test_valid_jpeg_extension():
    assert is_valid_extension("photo.jpeg") is True


def test_valid_png_extension():
    assert is_valid_extension("photo.png") is True


def test_valid_webp_extension():
    assert is_valid_extension("photo.webp") is True


def test_valid_uppercase_extension():
    assert is_valid_extension("photo.JPG") is True


def test_valid_mixed_case_extension():
    assert is_valid_extension("photo.Png") is True


def test_invalid_gif_extension():
    assert is_valid_extension("photo.gif") is False


def test_invalid_bmp_extension():
    assert is_valid_extension("photo.bmp") is False


def test_invalid_pdf_extension():
    assert is_valid_extension("document.pdf") is False


def test_invalid_exe_extension():
    assert is_valid_extension("malware.exe") is False


def test_invalid_no_extension():
    assert is_valid_extension("noextension") is False


def test_invalid_empty_filename():
    assert is_valid_extension("") is False


def test_invalid_none_filename():
    assert is_valid_extension(None) is False


# ── Size validation tests ─────────────────────────────────────────────────

def test_valid_small_size():
    assert is_valid_size(1024) is True  # 1 KB


def test_valid_exact_limit():
    assert is_valid_size(MAX_UPLOAD_BYTES) is True  # exactly 5 MB


def test_valid_just_under_limit():
    assert is_valid_size(MAX_UPLOAD_BYTES - 1) is True


def test_invalid_over_limit():
    assert is_valid_size(MAX_UPLOAD_BYTES + 1) is False


def test_invalid_way_over_limit():
    assert is_valid_size(10 * 1024 * 1024) is False  # 10 MB


def test_invalid_zero_size():
    assert is_valid_size(0) is False


def test_invalid_negative_size():
    assert is_valid_size(-100) is False


# ── Format file size tests ────────────────────────────────────────────────

def test_format_bytes():
    assert format_file_size(500) == "500 B"


def test_format_kilobytes():
    result = format_file_size(2048)
    assert "KB" in result


def test_format_megabytes():
    result = format_file_size(3 * 1024 * 1024)
    assert "MB" in result


# ── Default constraints tests ─────────────────────────────────────────────

def test_default_constraints_returns_dict():
    defaults = get_default_constraints()
    assert isinstance(defaults, dict)


def test_default_budget():
    defaults = get_default_constraints()
    assert defaults["budget"] == "₹0"


def test_default_tools_empty():
    defaults = get_default_constraints()
    assert defaults["tools"] == []


def test_default_skill():
    defaults = get_default_constraints()
    assert defaults["skill"] == "Beginner"


def test_default_time():
    defaults = get_default_constraints()
    assert defaults["time"] == "15 minutes"


def test_default_workspace():
    defaults = get_default_constraints()
    assert defaults["workspace"] == "Small"


def test_default_quantity():
    defaults = get_default_constraints()
    assert defaults["quantity"] == 1


def test_default_recovery_goal():
    defaults = get_default_constraints()
    assert defaults["recovery_goal"] == "No preference"


def test_default_safety_preference():
    defaults = get_default_constraints()
    assert defaults["safety_preference"] == "Only low-risk options"


def test_default_constraints_returns_copy():
    """Ensure modifying the returned dict doesn't affect the original."""
    defaults1 = get_default_constraints()
    defaults1["budget"] = "₹500+"
    defaults2 = get_default_constraints()
    assert defaults2["budget"] == "₹0"


# ── Allowed extensions constant test ──────────────────────────────────────

def test_allowed_extensions_set():
    assert ALLOWED_EXTENSIONS == {"jpg", "jpeg", "png", "webp"}
