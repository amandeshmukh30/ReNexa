"""
ReNexa — Constraint Engine Service
====================================
Deterministic evaluation of household-specific constraints against recovery pathways.

Evaluates:
- Budget (user available budget >= pathway cost)
- Available Tools (all mandatory pathway tools available)
- Extra Consumable Materials (tracks missing materials)
- DIY Skill Level (Beginner < Intermediate < Advanced)
- Dedicated Time (user time >= pathway time)
- Workspace Compatibility (Indoor / Outdoor / Any)
- Item Quantity (user quantity >= min_quantity)
- Waste Condition & Contamination (material state matches requirement)
"""

import re

# Skill hierarchy mapping
SKILL_RANKS = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}

# Workspace compatibility mapping
WORKSPACE_RANKS = {
    "very small": 1,
    "small": 2,
    "medium": 3,
    "large": 4,
}


def parse_budget_amount(val):
    """Parse numeric budget amount from string or number."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace("₹", "").replace("$", "").replace("+", "").replace(",", "").strip()
    try:
        return float(val_str)
    except ValueError:
        # Check for regex numbers
        match = re.search(r"(\d+(\.\d+)?)", val_str)
        if match:
            return float(match.group(1))
        return 0.0


def parse_time_in_minutes(val):
    """
    Parse duration in minutes from various human-readable formats.
    e.g. '5 minutes' -> 5, '1 hour' -> 60, '2+ hours' -> 120.
    """
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    val_str = str(val).lower().strip()
    if "hour" in val_str:
        match = re.search(r"(\d+(\.\d+)?)", val_str)
        if match:
            return int(float(match.group(1)) * 60)
        return 60
    if "min" in val_str:
        match = re.search(r"(\d+)", val_str)
        if match:
            return int(match.group(1))
        return 15
    try:
        return int(val_str)
    except ValueError:
        return 15


def parse_tool_list(tools_input):
    """Standardize tool list to lowercase set, ignoring 'None' and empty entries."""
    if not tools_input:
        return set()
    if isinstance(tools_input, (list, set, tuple)):
        items = [str(t).strip().lower() for t in tools_input]
    else:
        items = [str(t).strip().lower() for t in str(tools_input).split(",")]
    return {t for t in items if t and t not in ("none", "other", "n/a")}


def parse_material_list(materials_input):
    """Standardize consumable extra materials to lowercase set."""
    if not materials_input:
        return set()
    if isinstance(materials_input, (list, set, tuple)):
        items = [str(m).strip().lower() for m in materials_input]
    else:
        items = [str(m).strip().lower() for m in str(materials_input).split(",")]
    # Water and basic household air/sun are universally available
    ignore_items = {"none", "water", "clean water", "warm water", "dish soap", "soap"}
    return {m for m in items if m and m not in ignore_items}


def evaluate_constraints(pathway, user_constraints=None, waste_profile=None):
    """
    Evaluate user constraints against a single recovery pathway.

    Args:
        pathway:          Dict containing pathway metadata.
        user_constraints: Dict of user-provided constraints (budget, tools, skill, time, workspace, etc.).
        waste_profile:    Optional structured waste profile dict.

    Returns:
        dict with:
            constraint_status: 'FEASIBLE' | 'INFEASIBLE'
            reasons: list of constraint violation explanation strings
            missing_tools: list of missing tools
            missing_materials: list of missing materials
            budget_gap: numeric budget shortage (or None)
            time_gap: numeric minutes shortage (or None)
    """
    if not pathway or not isinstance(pathway, dict):
        return {
            "constraint_status": "INFEASIBLE",
            "reasons": ["Invalid pathway metadata."],
            "missing_tools": [],
            "missing_materials": [],
            "budget_gap": None,
            "time_gap": None,
        }

    constraints = user_constraints or {}
    reasons = []
    missing_tools = []
    missing_materials = []
    budget_gap = None
    time_gap = None

    # ── 1. Budget Constraint ────────────────────────────────────────────────
    pathway_cost = parse_budget_amount(pathway.get("budget", 0))
    user_budget = parse_budget_amount(constraints.get("budget", 500.0 if not constraints else 0.0))
    if user_budget < pathway_cost:
        budget_gap = round(pathway_cost - user_budget, 2)
        reasons.append(f"Insufficient budget: requires ₹{pathway_cost:g}, but available is ₹{user_budget:g} (gap: ₹{budget_gap:g})")

    # ── 2. Time Constraint ──────────────────────────────────────────────────
    pathway_time = parse_time_in_minutes(pathway.get("time_required", "15 minutes"))
    user_time = parse_time_in_minutes(constraints.get("time", "120 minutes" if not constraints else "15 minutes"))
    if user_time < pathway_time:
        time_gap = pathway_time - user_time
        reasons.append(f"Insufficient time: requires {pathway.get('time_required')}, but only {user_time} mins available (gap: {time_gap} mins)")

    # ── 3. Tool Availability Constraint ─────────────────────────────────────
    pathway_tools = parse_tool_list(pathway.get("tools"))
    user_tools = parse_tool_list(constraints.get("tools"))
    for req_tool in pathway_tools:
        # Check if user has this tool (or a closely matched keyword)
        has_tool = any(req_tool in u_tool or u_tool in req_tool for u_tool in user_tools)
        if not has_tool:
            missing_tools.append(req_tool.title())

    if missing_tools:
        reasons.append(f"Missing required tool(s): {', '.join(missing_tools)}")

    # ── 4. Extra Materials Constraint ───────────────────────────────────────
    pathway_materials = parse_material_list(pathway.get("extra_materials"))
    user_materials = parse_material_list(constraints.get("extra_materials") or constraints.get("materials"))
    # If user provided a specific materials list and something mandatory is missing
    if constraints.get("extra_materials") is not None or constraints.get("materials") is not None:
        for req_mat in pathway_materials:
            has_mat = any(req_mat in u_mat or u_mat in req_mat for u_mat in user_materials)
            if not has_mat:
                missing_materials.append(req_mat.title())
        if missing_materials:
            reasons.append(f"Missing extra material(s): {', '.join(missing_materials)}")

    # ── 5. Skill Level Constraint ───────────────────────────────────────────
    req_skill = str(pathway.get("skill_level", "Beginner")).strip().lower()
    user_skill = str(constraints.get("skill", "Beginner")).strip().lower()
    req_rank = SKILL_RANKS.get(req_skill, 1)
    user_rank = SKILL_RANKS.get(user_skill, 1)
    if user_rank < req_rank:
        reasons.append(f"Skill level mismatch: requires '{pathway.get('skill_level')}', but user is '{user_skill.capitalize()}'")

    # ── 6. Workspace Constraint ─────────────────────────────────────────────
    req_ws = str(pathway.get("workspace", "Any")).strip().lower()
    user_ws = str(constraints.get("workspace", "Any")).strip().lower()
    if req_ws == "outdoor" and user_ws in ("indoor", "very small"):
        reasons.append("Workspace mismatch: pathway requires outdoor space for proper ventilation/safety")

    # ── 7. Quantity Constraint ──────────────────────────────────────────────
    min_qty = int(pathway.get("min_quantity", 1))
    user_qty = 1
    if waste_profile and isinstance(waste_profile, dict):
        user_qty = int(waste_profile.get("confirmed_quantity", waste_profile.get("quantity", 1)))
    elif "quantity" in constraints:
        try:
            user_qty = int(str(constraints.get("quantity")).replace("+", ""))
        except ValueError:
            user_qty = 1

    if user_qty < min_qty:
        reasons.append(f"Insufficient quantity: requires at least {min_qty} item(s), but only {user_qty} available")

    # ── 8. Waste Condition & Contamination Constraints ──────────────────────
    if waste_profile and isinstance(waste_profile, dict):
        cond_req = str(pathway.get("condition_requirement", "Any")).strip()
        waste_cond = str(waste_profile.get("condition", "Unknown")).strip()
        waste_contam = str(waste_profile.get("contamination", "Unknown")).strip()

        # Check condition requirement (case-insensitive)
        if cond_req.lower() != "any":
            allowed_conditions = [c.strip().lower() for c in cond_req.split(",")]
            if waste_cond.lower() not in ("unknown", "") and waste_cond.lower() not in allowed_conditions:
                reasons.append(f"Condition requirement not met: pathway requires '{cond_req}', but item condition is '{waste_cond}'")

        # Heavy contamination blocks direct clean reuse and repair
        if waste_contam.lower() == "heavily contaminated" and pathway.get("pathway_type") in ("reuse", "repair"):
            reasons.append("Contamination mismatch: item is heavily contaminated for direct reuse/repair")

    # Final status determination
    status = "FEASIBLE" if len(reasons) == 0 else "INFEASIBLE"

    return {
        "constraint_status": status,
        "reasons": reasons,
        "missing_tools": missing_tools,
        "missing_materials": missing_materials,
        "budget_gap": budget_gap,
        "time_gap": time_gap,
    }
