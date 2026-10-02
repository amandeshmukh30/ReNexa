"""
ReNexa — Recovery Knowledge Base Service
==========================================
Loads, validates, and queries structured recovery pathways from CSV.

Supports recovery pathways across 5 canonical types:
    - repair
    - reuse
    - upcycle
    - recycle
    - dispose

Design Principles:
- Material-level matching: Normalizes glass sub-labels ("brown-glass" -> "glass").
- No Ranking in Phase 4: Returns all candidate pathways for downstream feasibility evaluation.
- Pure Python/CSV: No database, vector embeddings, or LLM dependencies.
"""

import csv
import os

# Path to the recovery pathways dataset
DEFAULT_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "recovery_pathways.csv")
)

# Required columns in the CSV schema
REQUIRED_COLUMNS = [
    "pathway_id",
    "input_material",
    "input_item",
    "pathway_type",
    "title",
    "description",
    "condition_requirement",
    "min_quantity",
    "tools",
    "extra_materials",
    "budget",
    "time_required",
    "skill_level",
    "workspace",
    "safety_level",
    "steps",
    "expected_output",
    "fallback",
    "source",
    "verification_status",
    "last_reviewed",
]

# Canonical allowed pathway types
ALLOWED_PATHWAY_TYPES = {
    "repair",
    "reuse",
    "upcycle",
    "recycle",
    "dispose",
}

# Glass label normalisation set
GLASS_VARIANTS = {"brown-glass", "green-glass", "white-glass", "glass"}


def normalize_material_name(material):
    """
    Normalize raw or sub-class material name to canonical category.
    Example: 'brown-glass' -> 'glass', 'Plastic' -> 'plastic'.
    """
    if not material:
        return "unknown"
    mat = str(material).strip().lower()
    if mat in GLASS_VARIANTS:
        return "glass"
    return mat


def load_recovery_pathways(csv_path=None):
    """
    Read and validate recovery_pathways.csv.

    Args:
        csv_path: Optional custom path to CSV file.

    Returns:
        list[dict]: List of validated and normalized recovery pathway dicts.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing or values are invalid.
    """
    path = csv_path or DEFAULT_CSV_PATH

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Recovery pathways CSV not found at: {path}")

    pathways = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate required headers
        headers = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValueError(f"Recovery CSV missing required columns: {missing}")

        for row_idx, row in enumerate(reader, start=2):
            # Verify non-empty required fields
            pathway_id = (row.get("pathway_id") or "").strip()
            title = (row.get("title") or "").strip()
            raw_mat = (row.get("input_material") or "").strip()
            raw_type = (row.get("pathway_type") or "").strip().lower()

            if not title:
                raise ValueError(f"Row {row_idx}: 'title' must not be empty.")

            if raw_type not in ALLOWED_PATHWAY_TYPES:
                raise ValueError(
                    f"Row {row_idx}: invalid pathway_type '{raw_type}'. "
                    f"Must be one of {ALLOWED_PATHWAY_TYPES}"
                )

            # Parse numeric min_quantity safely
            try:
                min_qty = int(row.get("min_quantity", 1))
            except (ValueError, TypeError):
                min_qty = 1

            # Build standardized pathway dictionary
            entry = {
                "pathway_id": pathway_id,
                "input_material": normalize_material_name(raw_mat),
                "input_item": (row.get("input_item") or "Unknown").strip(),
                "pathway_type": raw_type,
                "title": title,
                "description": (row.get("description") or "").strip(),
                "condition_requirement": (row.get("condition_requirement") or "Any").strip(),
                "min_quantity": min_qty,
                "tools": (row.get("tools") or "None").strip(),
                "extra_materials": (row.get("extra_materials") or "None").strip(),
                "budget": (row.get("budget") or "0").strip(),
                "time_required": (row.get("time_required") or "Unknown").strip(),
                "skill_level": (row.get("skill_level") or "Beginner").strip(),
                "workspace": (row.get("workspace") or "Any").strip(),
                "safety_level": (row.get("safety_level") or "Low").strip(),
                "steps": (row.get("steps") or "").strip(),
                "expected_output": (row.get("expected_output") or "").strip(),
                "fallback": (row.get("fallback") or "").strip(),
                "source": (row.get("source") or "Internal prototype rule").strip(),
                "verification_status": (row.get("verification_status") or "prototype").strip(),
                "last_reviewed": (row.get("last_reviewed") or "").strip(),
            }
            pathways.append(entry)

    return pathways


def get_recovery_pathways(material=None, pathway_type=None, csv_path=None):
    """
    Query recovery pathways matching material and/or pathway type.

    Args:
        material: Normalized or raw material name (e.g. 'plastic', 'glass', 'brown-glass').
        pathway_type: Optional filter by type ('repair', 'reuse', 'upcycle', 'recycle', 'dispose').
        csv_path: Optional custom path to CSV.

    Returns:
        list[dict]: List of matching pathways. Returns empty list if no matches or unknown.
    """
    if material is not None and str(material).strip().lower() in ("unknown", "none", ""):
        return []

    all_pathways = load_recovery_pathways(csv_path=csv_path)
    target_mat = normalize_material_name(material) if material else None
    target_type = str(pathway_type).strip().lower() if pathway_type else None

    results = []
    for p in all_pathways:
        if target_mat and p["input_material"] != target_mat:
            continue
        if target_type and p["pathway_type"] != target_type:
            continue
        results.append(p)

    return results


def get_pathways_for_profile(waste_profile, csv_path=None):
    """
    Helper to fetch all matching pathways directly from a structured waste profile.

    Args:
        waste_profile: Waste profile dict containing at least 'material'.

    Returns:
        list[dict]: List of matching recovery pathways.
    """
    if not waste_profile or not isinstance(waste_profile, dict):
        return []
    material = waste_profile.get("material")
    return get_recovery_pathways(material=material, csv_path=csv_path)


def get_available_materials(csv_path=None):
    """Return a sorted list of unique materials present in the knowledge base."""
    all_pathways = load_recovery_pathways(csv_path=csv_path)
    return sorted(list({p["input_material"] for p in all_pathways}))
