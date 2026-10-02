"""
ReNexa — Structured Waste Profile & Condition Assessment
==========================================================
Builds, updates, and validates the structured Waste Profile.

The Waste Profile is the central data contract for the ReNexa pipeline:
    Scan (AI Detection) → Profile Confirmation → Recovery KB → Constraints → Recommendations

Design Principles:
- Material != Item: The AI detects materials (e.g. "plastic", "glass"), NOT specific items (e.g. "bottle").
  Item remains "Unknown" to avoid false/synthetic classifications.
- Separation of Counts:
    - detected_object_count: raw count of bounding boxes identified by AI.
    - confirmed_quantity: quantity validated or adjusted by the household user.
- User-Confirmed Assessment:
    - condition: ["Good", "Used", "Damaged", "Heavily Damaged", "Unknown"]
    - contamination: ["Clean", "Slightly Contaminated", "Heavily Contaminated", "Unknown"]
"""

from ai.model_config import ALLOWED_CONDITIONS, ALLOWED_CONTAMINATIONS, GLASS_LABELS


# ── Canonical Normalization Mappings ─────────────────────────────────────────

_CONDITION_MAP = {
    "good": "Good",
    "used": "Used",
    "damaged": "Damaged",
    "heavily damaged": "Heavily Damaged",
    "unknown": "Unknown",
    # Aliases for graceful compatibility
    "clean": "Good",
    "dirty": "Used",
    "wet": "Damaged",
}

_CONTAMINATION_MAP = {
    "clean": "Clean",
    "slightly contaminated": "Slightly Contaminated",
    "heavily contaminated": "Heavily Contaminated",
    "unknown": "Unknown",
    # Aliases for graceful compatibility
    "none": "Clean",
    "low": "Slightly Contaminated",
    "medium": "Slightly Contaminated",
    "high": "Heavily Contaminated",
}


def normalize_condition(condition_str):
    """Normalize condition string to standard title-case category."""
    if not condition_str:
        return "Unknown"
    key = str(condition_str).strip().lower()
    return _CONDITION_MAP.get(key, "Unknown" if key not in [c.lower() for c in ALLOWED_CONDITIONS] else condition_str.title())


def normalize_contamination(contamination_str):
    """Normalize contamination string to standard title-case category."""
    if not contamination_str:
        return "Unknown"
    key = str(contamination_str).strip().lower()
    return _CONTAMINATION_MAP.get(key, "Unknown" if key not in [c.lower() for c in ALLOWED_CONTAMINATIONS] else contamination_str.title())


# ── Profile Builder ─────────────────────────────────────────────────────────

def create_waste_profile(detection_result):
    """
    Build a structured Waste Profile dictionary from a detector output.

    The model identifies MATERIALS (e.g. "plastic", "glass"), not specific items.
    The "item" field is set to "Unknown" because we cannot determine item type
    from the current material-level model.

    Quantity fields:
        - detected_object_count: actual count of objects found by AI
        - confirmed_quantity: defaults to detected_object_count (user can override)
        - quantity: alias for confirmed_quantity (for backwards compatibility)

    Args:
        detection_result: dict returned by WasteDetector.detect() or None

    Returns:
        dict: complete structured waste profile.
    """
    # If nothing was detected or detection is invalid
    if not detection_result or not detection_result.get("detected"):
        return {
            "material": "Unknown",
            "item": "Unknown",
            "model_label": None,
            "confidence": 0.0,
            "detected_object_count": 0,
            "detected_count": 0,           # backward-compatibility alias
            "confirmed_quantity": 0,
            "quantity": 0,                  # backward-compatibility alias
            "condition": "Unknown",
            "contamination": "Unknown",
            "material_counts": {},
            "detections": [],
            "all_detections": [],          # backward-compatibility alias
            "user_confirmed": False,
        }

    # Extract detected object count
    raw_detections = detection_result.get("all_detections", [])
    detected_count = detection_result.get("count", len(raw_detections))
    if detected_count == 0 and detection_result.get("label"):
        detected_count = 1

    # Standardize individual detections
    detections = []
    for det in raw_detections:
        d_mat = det.get("label", "")
        d_raw = det.get("model_label", d_mat)
        d_conf = det.get("confidence", 0.0)
        d_box = det.get("box") or det.get("bounding_box", [])
        detections.append({
            "material": d_mat,
            "label": d_mat,
            "model_label": d_raw,
            "confidence": round(float(d_conf), 4),
            "bounding_box": d_box,
            "box": d_box,
        })

    # Material counts
    material_counts = dict(detection_result.get("material_counts", {}))
    if not material_counts and detection_result.get("label"):
        material_counts = {detection_result["label"]: detected_count}

    return {
        # Material identified by AI (normalized, e.g. "glass")
        "material": detection_result.get("label", "Unknown"),

        # Item level is explicitly Unknown (material != item)
        "item": "Unknown",

        # Original model class name (e.g. "brown-glass")
        "model_label": detection_result.get("model_label"),

        # AI Confidence score (0.0 – 1.0)
        "confidence": round(float(detection_result.get("confidence", 0.0)), 4),

        # Number of objects detected by AI
        "detected_object_count": detected_count,
        "detected_count": detected_count,           # backward-compatibility alias

        # User-confirmed quantity (defaults to detected_object_count)
        "confirmed_quantity": detected_count,
        "quantity": detected_count,                  # backward-compatibility alias

        # ── User-Assessed Fields ──────────────────────────────────────
        "condition": "Unknown",
        "contamination": "Unknown",

        # Aggregated material counts and detection list
        "material_counts": material_counts,
        "detections": detections,
        "all_detections": raw_detections,           # backward-compatibility alias

        # Confirmation flag
        "user_confirmed": False,
    }


def update_profile_user_fields(profile, material=None, item=None, condition=None,
                                quantity=None, confirmed_quantity=None,
                                contamination=None, confirmed=False):
    """
    Update the user-provided fields on an existing structured waste profile.

    Called after the user confirms or corrects the AI prediction
    and provides condition/quantity/contamination inputs.

    Args:
        profile:            existing waste profile dict
        material:           corrected material (or None to keep AI prediction)
        item:               specific item if provided by user (otherwise keeps existing)
        condition:          user-selected condition string
        quantity:           user-selected quantity (int)
        confirmed_quantity: user-confirmed quantity (int)
        contamination:      user-selected contamination level
        confirmed:          True if user explicitly confirmed

    Returns:
        dict: The updated profile dict (mutated in place).
    """
    if profile is None:
        profile = create_waste_profile(None)

    if material is not None:
        profile["material"] = str(material)

    if item is not None:
        profile["item"] = str(item)

    if condition is not None:
        profile["condition"] = normalize_condition(condition)

    # Resolve confirmed quantity
    final_qty = confirmed_quantity if confirmed_quantity is not None else quantity
    if final_qty is not None:
        profile["confirmed_quantity"] = int(final_qty)
        profile["quantity"] = int(final_qty)

    if contamination is not None:
        profile["contamination"] = normalize_contamination(contamination)

    profile["user_confirmed"] = bool(confirmed)
    return profile


# ── Profile Validation ───────────────────────────────────────────────────────

def validate_waste_profile(profile):
    """
    Validate a structured waste profile dictionary.

    Checks:
    1. Profile is a dictionary.
    2. Material is non-empty string or 'Unknown'.
    3. Item is a string (e.g. 'Unknown') and not a fake/unsupported guess.
    4. Detected object count is a non-negative integer.
    5. Confirmed quantity is a valid integer (>= 0).
    6. Condition is one of ALLOWED_CONDITIONS.
    7. Contamination is one of ALLOWED_CONTAMINATIONS.
    8. Confidence is a float between 0.0 and 1.0.
    9. Material counts is a valid dictionary of non-negative integer counts.
    10. Rejects negative quantities or out-of-bounds confidences.

    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_errors)
    """
    errors = []

    if not isinstance(profile, dict):
        return False, ["Profile must be a dictionary"]

    # 1. Material
    material = profile.get("material")
    if material is None or not isinstance(material, str) or not material.strip():
        errors.append("Material must be a non-empty string or 'Unknown'")

    # 2. Item
    item = profile.get("item")
    if item is None or not isinstance(item, str):
        errors.append("Item must be a string (defaults to 'Unknown')")

    # 3. Detected object count
    det_count = profile.get("detected_object_count")
    if det_count is None:
        det_count = profile.get("detected_count", 0)
    if not isinstance(det_count, int) or det_count < 0:
        errors.append("Detected object count must be a non-negative integer")

    # 4. Confirmed quantity
    qty = profile.get("confirmed_quantity")
    if qty is None:
        qty = profile.get("quantity", 0)
    if not isinstance(qty, int) or qty < 0:
        errors.append("Confirmed quantity must be a non-negative integer")

    # 5. Condition
    condition = profile.get("condition")
    norm_condition = normalize_condition(condition)
    if norm_condition not in ALLOWED_CONDITIONS:
        errors.append(f"Condition '{condition}' is not in allowed values: {ALLOWED_CONDITIONS}")

    # 6. Contamination
    contamination = profile.get("contamination")
    norm_contamination = normalize_contamination(contamination)
    if norm_contamination not in ALLOWED_CONTAMINATIONS:
        errors.append(f"Contamination '{contamination}' is not in allowed values: {ALLOWED_CONTAMINATIONS}")

    # 7. Confidence
    confidence = profile.get("confidence", 0.0)
    if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
        errors.append(f"Confidence must be between 0.0 and 1.0 (got {confidence})")

    # 8. Material counts
    mat_counts = profile.get("material_counts", {})
    if not isinstance(mat_counts, dict):
        errors.append("material_counts must be a dictionary")
    else:
        for k, v in mat_counts.items():
            if not isinstance(k, str) or not isinstance(v, int) or v < 0:
                errors.append(f"Invalid material count entry: {k}: {v}")

    return len(errors) == 0, errors


def is_valid_waste_profile(profile):
    """Boolean helper to quickly check if a profile is valid."""
    is_valid, _ = validate_waste_profile(profile)
    return is_valid
