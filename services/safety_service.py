"""
ReNexa — Safety Engine Service
================================
Deterministic, rule-based safety evaluation for household waste recovery pathways.

Safety Decision Hierarchy:
    BLOCK: The operation is inherently hazardous (e.g. dismantling batteries, melting plastics, chemical leaching).
           Pathway is strictly ineligible regardless of user constraints.
    WARN:  The operation is permissible but requires specific safety precautions (e.g. sharp blades, adhesive fumes, eye protection).
    ALLOW: The operation has standard low risk and is fully safe for household execution.

Design Principles:
- 100% Deterministic: No generative or unverified guessing.
- Grounded in Safety Rules: Driven by data/safety_rules.csv with official safety citations.
- Glass & Sub-label Normalization: Unifies material classes.
"""

import csv
import os

# Paths to the safety rules dataset (check knowledge dir first, then fallback to data dir)
_KNOWLEDGE_SAFETY_CSV = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "safety_rules.csv")
)
_FALLBACK_SAFETY_CSV = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "safety_rules.csv")
)
DEFAULT_SAFETY_CSV = (
    _KNOWLEDGE_SAFETY_CSV if os.path.isfile(_KNOWLEDGE_SAFETY_CSV) else _FALLBACK_SAFETY_CSV
)

GLASS_VARIANTS = {"brown-glass", "green-glass", "white-glass", "glass"}
MATERIAL_ALIASES = {
    "organic": "biological",
    "bio": "biological",
    "food": "biological",
}


def normalize_material(material):
    """Normalize material string for rule matching."""
    if not material:
        return "any"
    mat = str(material).strip().lower()
    if mat in GLASS_VARIANTS:
        return "glass"
    if mat in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[mat]
    return mat


def load_safety_rules(csv_path=None):
    """
    Load safety rules from CSV file.

    Returns:
        list[dict]: List of safety rule records.
    """
    path = csv_path or DEFAULT_SAFETY_CSV
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Safety rules CSV not found at: {path}")

    rules = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append({
                "rule_id": (row.get("rule_id") or "").strip(),
                "material": normalize_material(row.get("material")),
                "operation": (row.get("operation") or "any").strip().lower(),
                "status": (row.get("status") or "ALLOW").strip().upper(),
                "warning": (row.get("warning") or "").strip(),
                "reason": (row.get("reason") or "").strip(),
                "source": (row.get("source") or "Internal safety rule").strip(),
                "verification_status": (row.get("verification_status") or "prototype").strip(),
                "last_reviewed": (row.get("last_reviewed") or "").strip(),
            })
    return rules


def evaluate_safety(pathway, waste_profile=None, safety_preference=None, csv_path=None):
    """
    Evaluate the safety of a given recovery pathway.

    Args:
        pathway:           Dict containing pathway metadata (input_material, pathway_type, tools, steps, etc.)
        waste_profile:     Optional structured waste profile dict.
        safety_preference: Optional user preference string (e.g. 'Only low-risk options').
        csv_path:          Optional custom path to safety rules CSV.

    Returns:
        dict with:
            safety_status: 'ALLOW' | 'WARN' | 'BLOCK'
            warnings: list of warning strings
            reasons: list of blocking reason strings
            rules_triggered: list of triggered rule IDs
    """
    if not pathway or not isinstance(pathway, dict):
        return {
            "safety_status": "BLOCK",
            "warnings": [],
            "reasons": ["Invalid or missing pathway definition."],
            "rules_triggered": [],
        }

    rules = load_safety_rules(csv_path=csv_path)

    # Determine material and operation
    p_mat = normalize_material(pathway.get("input_material"))
    if waste_profile and isinstance(waste_profile, dict) and waste_profile.get("material"):
        profile_mat = normalize_material(waste_profile.get("material"))
        if profile_mat != "unknown":
            p_mat = profile_mat

    p_type = str(pathway.get("pathway_type") or "").strip().lower()
    p_safety_level = str(pathway.get("safety_level") or "Low").strip().capitalize()
    p_steps = str(pathway.get("steps") or "").lower()
    p_tools = str(pathway.get("tools") or "").lower()

    warnings = []
    reasons = []
    rules_triggered = []
    final_status = "ALLOW"

    # ── Rule-based evaluation ───────────────────────────────────────────────
    for rule in rules:
        r_mat = rule["material"]
        r_op = rule["operation"]
        r_status = rule["status"]

        # Material matching: rule matches if rule applies to 'any' or exact material
        if r_mat not in ("any", p_mat):
            continue

        # Operation matching
        op_matches = False
        if r_op in ("any", p_type):
            op_matches = True
        elif r_op == "cutting" and any(k in p_tools for k in ["knife", "scissors", "utility knife", "blade", "hammer"]):
            op_matches = True
        elif r_op == "compost" and p_type == "recycle" and p_mat == "biological":
            op_matches = True
        elif r_op == "thermal_processing" and any(k in p_steps for k in ["heat", "melt", "burn", "flame"]):
            op_matches = True
        elif r_op == "chemical_treatment" and any(k in p_steps for k in ["acid", "bleach", "solvent", "leach"]):
            op_matches = True

        if op_matches:
            rules_triggered.append(rule["rule_id"])
            if r_status == "BLOCK":
                final_status = "BLOCK"
                reasons.append(f"[{rule['rule_id']}] {rule['reason']}")
            elif r_status == "WARN":
                if final_status != "BLOCK":
                    final_status = "WARN"
                if rule["warning"]:
                    warnings.append(f"[{rule['rule_id']}] {rule['warning']}")

    # ── Pathway-level inherent safety check ──────────────────────────────────
    # Conservative check for damaged glass used in household recovery.
    p_condition = (
        str(waste_profile.get("condition") or "").strip().lower()
        if isinstance(waste_profile, dict)
        else ""
    )

    if (
        p_mat == "glass"
        and p_type in ("reuse", "upcycle", "repair")
        and any(term in p_condition for term in (
            "chip", "crack", "broken", "shatter", "damaged"
        ))
    ):
        final_status = "BLOCK"
        reasons.append(
            "[SAF-GLA-DAMAGED] Chipped, cracked, broken, or damaged glass "
            "must not be used for household reuse or upcycling. "
            "Choose an appropriate glass collection or recycling option."
        )

    # Block the known risky household method: punching tin with a hammer and nail.
    metal_method = f"{p_steps} {p_tools}"
    if (
        p_mat == "metal"
        and p_type == "upcycle"
        and "punch" in metal_method
        and "hole" in metal_method
        and "hammer" in metal_method
        and "nail" in metal_method
    ):
        final_status = "BLOCK"
        reasons.append(
            "[SAF-MET-HOLE-PUNCH] Hammer-and-nail hole punching can leave "
            "sharp metal burrs. Do not recommend this household method; "
            "choose a safer ready-made container or recycling alternative."
        )

    # Check if pathway explicitly declares High risk or has battery DIY
    if p_mat == "battery" and p_type in ("repair", "upcycle", "reuse"):
        final_status = "BLOCK"
        reasons.append("[SAFETY-BATTERY-CRITICAL] DIY repair or upcycling of batteries is strictly prohibited.")

    if p_safety_level == "High" and final_status != "BLOCK" and p_type != "dispose":
        final_status = "WARN"
        warnings.append("[SAFETY-HIGH-RISK] Pathway involves high-hazard operations. Proceed only with certified protective equipment.")

    # ── User Safety Preference Check ─────────────────────────────────────────
    if safety_preference == "Only low-risk options" and p_safety_level in ("Medium", "High"):
        warnings.append(f"[PREFERENCE-NOTICE] Option has '{p_safety_level}' safety level while your preference is set to 'Only low-risk options'.")

    return {
        "safety_status": final_status,
        "warnings": list(dict.fromkeys(warnings)),  # deduplicate preserving order
        "reasons": list(dict.fromkeys(reasons)),
        "rules_triggered": list(dict.fromkeys(rules_triggered)),
    }
