"""
ReNexa — Multi-Criteria Decision Analysis (MCDA) Ranking Service
==================================================================
Deterministic, transparent ranking of eligible household waste-recovery pathways.

Research Pipeline:
    Waste Profile -> Recovery Pathways -> Safety Engine -> Constraint Engine
    -> Eligible Pathways Only -> MCDA Ranking -> Sorted Top-K Recommendations

MCDA Direct Criteria Weight Distribution (Total = 100%):
    - budget_fit:          20.0%  (Out-of-pocket financial cost & remaining budget margin)
    - time_fit:            20.0%  (Task duration & remaining available time margin)
    - tool_fit:            15.0%  (Tool accessibility and readiness)
    - recovery_value:      15.0%  (Circular economy recovery hierarchy priority)
    - extra_material_fit:  10.0%  (Consumable material availability)
    - skill_fit:           10.0%  (Skill match / user capability)
    - condition_fit:       10.0%  (Suitability for waste item condition)

Methodology Note on Orthogonality:
    All 7 criteria are mutually direct and orthogonal.
    `practical_fit` is calculated as an informative aggregate summary metric
    (mean of budget, time, tools, materials, skill fits) for reporting and secondary
    tie-breaking, but is NOT part of the linear weighted sum, eliminating double-counting.

Hard Gate Constraint:
    Only pathways with `eligible == True` are scored and ranked.
    Safety BLOCK and Constraint INFEASIBLE options are NEVER ranked.
"""

from services.constraint_service import (
    parse_budget_amount,
    parse_time_in_minutes,
    parse_tool_list,
    parse_material_list,
    SKILL_RANKS,
)
from services.eligibility_service import get_eligible_pathways_for_profile

# ── MCDA Direct Criteria Named Weights (Total = 100.0) ───────────────────────
WEIGHT_BUDGET_FIT = 20.0
WEIGHT_TIME_FIT = 20.0
WEIGHT_TOOL_FIT = 15.0
WEIGHT_RECOVERY_VALUE = 15.0
WEIGHT_EXTRA_MATERIAL_FIT = 10.0
WEIGHT_SKILL_FIT = 10.0
WEIGHT_CONDITION_FIT = 10.0

TOTAL_WEIGHT = (
    WEIGHT_BUDGET_FIT
    + WEIGHT_TIME_FIT
    + WEIGHT_TOOL_FIT
    + WEIGHT_RECOVERY_VALUE
    + WEIGHT_EXTRA_MATERIAL_FIT
    + WEIGHT_SKILL_FIT
    + WEIGHT_CONDITION_FIT
)

# ── Circular Economy Hierarchy Recovery Values (0 to 100) ────────────────────
# Standard waste hierarchy: Repair > Reuse > Upcycle > Recycle > Dispose
RECOVERY_VALUES = {
    "repair": 100.0,
    "reuse": 90.0,
    "upcycle": 80.0,
    "recycle": 60.0,
    "dispose": 30.0,
}


def score_budget_fit(pathway, user_constraints):
    """
    Score budget margin (0 to 100).
    Higher remaining budget margin yields a higher score.
    Zero-cost pathways score 100.0.
    """
    pathway_cost = parse_budget_amount(pathway.get("budget", 0))
    user_budget = parse_budget_amount((user_constraints or {}).get("budget", 0))

    if pathway_cost == 0:
        return 100.0

    if user_budget <= 0:
        return 100.0 if pathway_cost == 0 else 0.0

    # Margin ratio: 0.0 when pathway uses entire budget, 1.0 when cost is 0
    budget_used_ratio = min(1.0, max(0.0, pathway_cost / user_budget))
    # Score scales from 50 (at 100% budget spent) to 100 (at 0% budget spent)
    return round(100.0 - (budget_used_ratio * 50.0), 2)


def score_time_fit(pathway, user_constraints):
    """
    Score time margin (0 to 100).
    Faster pathways that consume a smaller fraction of user time score higher.
    """
    pathway_time = parse_time_in_minutes(pathway.get("time_required", "15 minutes"))
    user_time = parse_time_in_minutes((user_constraints or {}).get("time", "60 minutes"))

    if user_time <= 0:
        user_time = 15

    if pathway_time <= 0:
        return 100.0

    time_used_ratio = min(1.0, max(0.0, pathway_time / user_time))
    return round(100.0 - (time_used_ratio * 50.0), 2)


def score_tool_fit(pathway, user_constraints):
    """
    Score tool availability (0 to 100).
    If no special tools are needed, scores 100.0.
    If required tools are all available, scores 100.0.
    """
    pathway_tools = parse_tool_list(pathway.get("tools"))
    user_tools = parse_tool_list((user_constraints or {}).get("tools"))

    if not pathway_tools:
        return 100.0

    matched = sum(
        1 for req in pathway_tools if any(req in u or u in req for u in user_tools)
    )
    return round((matched / len(pathway_tools)) * 100.0, 2)


def score_extra_material_fit(pathway, user_constraints):
    """
    Score extra consumable materials availability (0 to 100).
    If no extra materials are needed, scores 100.0.
    """
    pathway_materials = parse_material_list(pathway.get("extra_materials"))
    user_materials = parse_material_list(
        (user_constraints or {}).get("extra_materials")
        or (user_constraints or {}).get("materials")
    )

    if not pathway_materials:
        return 100.0

    matched = sum(
        1 for req in pathway_materials if any(req in u or u in req for u in user_materials)
    )
    return round((matched / len(pathway_materials)) * 100.0, 2)


def score_skill_fit(pathway, user_constraints):
    """
    Score skill level compatibility (0 to 100).
    Uses the hierarchy: Beginner (1) < Intermediate (2) < Advanced (3).
    A user with equal or higher skill than required is not penalized.
    """
    req_skill = str(pathway.get("skill_level", "Beginner")).strip().lower()
    user_skill = str((user_constraints or {}).get("skill", "Beginner")).strip().lower()

    req_rank = SKILL_RANKS.get(req_skill, 1)
    user_rank = SKILL_RANKS.get(user_skill, 1)

    if user_rank == req_rank:
        return 100.0
    elif user_rank > req_rank:
        # User has more skill than required (task is very easy for them)
        return 95.0
    else:
        # User has less skill than required (infeasible in Phase 5, but gracefully bounded)
        gap = req_rank - user_rank
        return max(0.0, 100.0 - (gap * 40.0))


def score_condition_fit(pathway, waste_profile):
    """
    Score waste item condition fit (0 to 100).
    Exact condition matches or 'Any' condition requirement score 100.0.
    """
    cond_req = str(pathway.get("condition_requirement", "Any")).strip()
    waste_cond = str((waste_profile or {}).get("condition", "Unknown")).strip()

    if cond_req.lower() == "any" or waste_cond.lower() in ("unknown", ""):
        return 100.0

    req_list = [c.strip().lower() for c in cond_req.split(",")]
    if waste_cond.lower() in req_list:
        return 100.0

    # Good item used for Used/Damaged pathway
    if waste_cond.lower() == "good":
        return 90.0

    return 60.0


def score_recovery_value(pathway):
    """
    Score circular economy recovery ladder value (0 to 100).
    Repair (100) > Reuse (90) > Upcycle (80) > Recycle (60) > Dispose (30).
    """
    ptype = str(pathway.get("pathway_type", "")).strip().lower()
    return RECOVERY_VALUES.get(ptype, 50.0)


def score_practical_fit(budget_s, time_s, tool_s, material_s, skill_s):
    """
    Compute aggregate practical user fit (0 to 100) from component resource fits.
    Used for diagnostic reporting and secondary tie-breaking.
    """
    avg = (budget_s + time_s + tool_s + material_s + skill_s) / 5.0
    return round(avg, 2)


def calculate_mcda_scores(pathway, user_constraints=None, waste_profile=None):
    """
    Compute individual direct criterion scores and total orthogonal weighted MCDA score.

    Returns:
        tuple: (final_score, criterion_scores_dict)
    """
    b_fit = score_budget_fit(pathway, user_constraints)
    t_fit = score_time_fit(pathway, user_constraints)
    tool_fit = score_tool_fit(pathway, user_constraints)
    mat_fit = score_extra_material_fit(pathway, user_constraints)
    s_fit = score_skill_fit(pathway, user_constraints)
    cond_fit = score_condition_fit(pathway, waste_profile)
    rec_val = score_recovery_value(pathway)
    p_fit = score_practical_fit(b_fit, t_fit, tool_fit, mat_fit, s_fit)

    criterion_scores = {
        "practical_fit": p_fit,
        "budget_fit": b_fit,
        "time_fit": t_fit,
        "tool_fit": tool_fit,
        "extra_material_fit": mat_fit,
        "skill_fit": s_fit,
        "condition_fit": cond_fit,
        "recovery_value": rec_val,
    }

    # Direct orthogonal weighted sum without double-counting practical_fit
    weighted_sum = (
        (b_fit * WEIGHT_BUDGET_FIT)
        + (t_fit * WEIGHT_TIME_FIT)
        + (tool_fit * WEIGHT_TOOL_FIT)
        + (rec_val * WEIGHT_RECOVERY_VALUE)
        + (mat_fit * WEIGHT_EXTRA_MATERIAL_FIT)
        + (s_fit * WEIGHT_SKILL_FIT)
        + (cond_fit * WEIGHT_CONDITION_FIT)
    )

    final_score = round(weighted_sum / TOTAL_WEIGHT, 2)
    # Clamp safely between 0 and 100
    final_score = max(0.0, min(100.0, final_score))

    return final_score, criterion_scores


def generate_why_this(pathway, criterion_scores, rank=1):
    """
    Generate transparent, grounded reasons why this pathway scored highly.
    """
    reasons = []
    ptype = str(pathway.get("pathway_type", "")).strip().capitalize()
    cost = parse_budget_amount(pathway.get("budget", 0))
    time_req = pathway.get("time_required", "15 minutes")

    if criterion_scores.get("recovery_value", 0) >= 90:
        reasons.append(f"High circular economy value: {ptype} extends material life directly.")
    elif criterion_scores.get("recovery_value", 0) >= 80:
        reasons.append(f"Creative upcycling: converts waste into functional utility.")
    elif ptype.lower() == "recycle":
        reasons.append("Standard circular recovery: prepares material for municipal recycling.")

    if cost == 0:
        reasons.append("Zero additional financial expense (₹0 budget required).")
    elif criterion_scores.get("budget_fit", 0) >= 85:
        reasons.append(f"Low cost implementation (₹{cost:g} required).")

    if criterion_scores.get("time_fit", 0) >= 85:
        reasons.append(f"Quick execution: requires only {time_req}.")

    if criterion_scores.get("tool_fit", 0) == 100:
        tools = pathway.get("tools", "None")
        if tools.lower() in ("none", ""):
            reasons.append("No specialized household tools required.")
        else:
            reasons.append("All required tools are readily available.")

    if criterion_scores.get("skill_fit", 0) >= 95:
        reasons.append(f"Comfortably matches your skill level ({pathway.get('skill_level')}).")

    if not reasons:
        reasons.append("Meets all baseline household feasibility criteria.")

    return reasons


def generate_why_not_this(pathway, criterion_scores):
    """
    Generate transparent explanations for why a pathway ranked lower than Top-1.
    """
    notes = []
    cost = parse_budget_amount(pathway.get("budget", 0))
    ptype = str(pathway.get("pathway_type", "")).lower()

    if criterion_scores.get("recovery_value", 0) <= 60:
        if ptype == "dispose":
            notes.append("Lowest recovery tier: residual waste disposal rather than reuse or recycling.")
        elif ptype == "recycle":
            notes.append("Lower recovery value tier compared to direct repair or reuse.")

    if cost > 0 and criterion_scores.get("budget_fit", 0) < 90:
        notes.append(f"Requires higher budget allocation (₹{cost:g}).")

    if criterion_scores.get("time_fit", 0) < 80:
        notes.append(f"Requires longer duration ({pathway.get('time_required')}).")

    if criterion_scores.get("skill_fit", 0) < 90:
        notes.append(f"Requires higher crafting skill ({pathway.get('skill_level')}).")

    return notes


def get_ranked_pathways(eligibility_records, user_constraints=None, waste_profile=None, top_k=3):
    """
    Filter for eligible pathways, compute MCDA multi-criteria scores,
    and return deterministically sorted recommendations.

    Args:
        eligibility_records: list of dicts from Phase 5 eligibility evaluation.
        user_constraints:    user constraint dictionary.
        waste_profile:       waste profile dictionary.
        top_k:               maximum number of ranked results to return (None for all).

    Returns:
        list[dict]: Ranked recommendation records with scores, rankings, and explanations.
    """
    if not eligibility_records:
        return []

    # HARD FILTER: Only pathways that passed Phase 5 (eligible == True)
    eligible_records = [
        rec for rec in eligibility_records
        if rec.get("eligible") is True
        and rec.get("safety_status") != "BLOCK"
        and rec.get("constraint_status") == "FEASIBLE"
    ]

    if not eligible_records:
        return []

    scored_items = []
    for rec in eligible_records:
        pathway = rec.get("pathway") or {}
        p_id = pathway.get("pathway_id") or rec.get("pathway_id") or "UNKNOWN"
        title = pathway.get("title") or "Unnamed Pathway"

        final_score, crit_scores = calculate_mcda_scores(
            pathway=pathway,
            user_constraints=user_constraints,
            waste_profile=waste_profile,
        )

        scored_items.append({
            "pathway_id": p_id,
            "title": title,
            "pathway": pathway,
            "eligible": True,
            "score": final_score,
            "criterion_scores": crit_scores,
            "warnings": rec.get("warnings", []),
            "reasons": rec.get("reasons", []),
            "required_tools": pathway.get("tools", "None"),
            "extra_materials": pathway.get("extra_materials", "None"),
            "budget": pathway.get("budget", "0"),
            "time_required": pathway.get("time_required", "Unknown"),
            "skill_level": pathway.get("skill_level", "Beginner"),
            "workspace": pathway.get("workspace", "Any"),
            "pathway_type": pathway.get("pathway_type", "reuse"),
            "expected_output": pathway.get("expected_output", ""),
            "steps": pathway.get("steps", ""),
        })

    # Deterministic Tie Breaking:
    # 1. Higher final score
    # 2. Higher recovery_value (circular economy hierarchy)
    # 3. Higher practical_fit (resource convenience)
    # 4. Higher budget_fit
    # 5. Higher time_fit
    # 6. Alphabetical pathway_id
    def sort_key(item):
        cs = item["criterion_scores"]
        return (
            -item["score"],
            -cs["recovery_value"],
            -cs["practical_fit"],
            -cs["budget_fit"],
            -cs["time_fit"],
            item["pathway_id"],
        )

    scored_items.sort(key=sort_key)

    # Assign ranks and explanations
    ranked_results = []
    for idx, item in enumerate(scored_items, start=1):
        item["rank"] = idx
        item["why_this"] = generate_why_this(item["pathway"], item["criterion_scores"], rank=idx)
        item["why_not_this"] = generate_why_not_this(item["pathway"], item["criterion_scores"])
        ranked_results.append(item)

    if top_k is not None and top_k > 0:
        return ranked_results[:top_k]

    return ranked_results


def get_ranked_recommendations_for_profile(waste_profile, user_constraints=None, top_k=3, csv_path=None):
    """
    End-to-end convenience function:
    Profile -> Candidate Pathways -> Phase 5 Eligibility -> MCDA Ranking -> Top-K.

    Args:
        waste_profile:    structured waste profile dictionary.
        user_constraints: user constraint dictionary.
        top_k:            number of recommendations to return (default 3).
        csv_path:         optional custom CSV path.

    Returns:
        list[dict]: Ranked top-K recommendations.
    """
    if not waste_profile or not isinstance(waste_profile, dict):
        return []

    # Run Phase 5 Eligibility
    eligibility_records = get_eligible_pathways_for_profile(
        waste_profile=waste_profile,
        user_constraints=user_constraints,
        csv_path=csv_path,
    )

    # Run Phase 6 MCDA Ranking
    return get_ranked_pathways(
        eligibility_records=eligibility_records,
        user_constraints=user_constraints,
        waste_profile=waste_profile,
        top_k=top_k,
    )
