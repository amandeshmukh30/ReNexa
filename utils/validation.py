"""
ReNexa — Validation Helpers

Simple validation functions for file uploads and constraint inputs.
"""

# Allowed image extensions (lowercase)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Maximum upload size in bytes (5 MB)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def is_valid_extension(filename):
    """
    Check whether the file extension is in the allowed set.

    Args:
        filename: Name of the uploaded file (string).

    Returns:
        True if extension is allowed, False otherwise.
    """
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


def is_valid_size(size_bytes):
    """
    Check whether the file size is within the allowed limit.

    Args:
        size_bytes: File size in bytes (int).

    Returns:
        True if within limit, False otherwise.
    """
    return 0 < size_bytes <= MAX_UPLOAD_BYTES


def format_file_size(size_bytes):
    """Return a human-readable file-size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


# ── Default constraint values ──────────────────────────────────────────────

DEFAULT_CONSTRAINTS = {
    "budget": "₹0",
    "tools": [],
    "skill": "Beginner",
    "time": "15 minutes",
    "workspace": "Small",
    "quantity": 1,
    "recovery_goal": "No preference",
    "safety_preference": "Only low-risk options",
}


def get_default_constraints():
    """Return a copy of the default constraint dictionary."""
    return dict(DEFAULT_CONSTRAINTS)
