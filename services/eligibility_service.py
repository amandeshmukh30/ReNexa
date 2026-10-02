"""
ReNexa — Eligibility Engine Service
=====================================
Orchestration layer combining Safety Engine and Constraint Engine.

Core Decision Logic:
1. Evaluate Safety:
   - If Safety == BLOCK:
     - Pathway is strictly INELIGIBLE.
     - Constraint evaluation is marked NOT_EVALUATED (safety cannot be overridden).
2. Evaluate Constraints (if Safety != BLOCK):
   - Check budget, tools, skill, time, workspace, quantity, condition, contamination.
3. Determine Final Eligibility:
   - ELIGIBLE: Safety in {ALLOW, WARN} AND Constraint Status == FEASIBLE.
   - INELIGIBLE: Safety == BLOCK OR Constraint Status == INFEASIBLE.
"""

from services.safety_service import evaluate_safety
from services.constraint_service import evaluate_constraints
from services.recovery_service import get_recovery_pathways


def evaluate_pathway_eligibility(pathway, user_constraints=None, waste_profile=None):
    """
    Evaluate the end-to-end recovery eligibility of a single pathway.

    Args:
        pathway:          Dict containing pathway metadata.
        user_constraints: Dict of user-provided constraints.
        waste_profile:    Dict containing structured waste profile.

    Returns:
        dict:
            pathway_id: str
            pathway: dict
            safety_status: 'ALLOW' | 'WARN' | 'BLOCK'
            constraint_status: 'FEASIBLE' | 'INFEASIBLE' | 'NOT_EVALUATED'
            eligible: bool
            reasons: list[str] (blocking/infeasibility reasons)
            warnings: list[str] (safety or preference warnings)
            missing_tools: list[str]
            missing_materials: list[str]
            budget_gap: float | None
            time_gap: int | None
    """
    if not pathway or not isinstance(pathway, dict):
        return {
            "pathway_id": "UNKNOWN",
            "pathway": {},
            "safety_status": "BLOCK",
            "constraint_status": "NOT_EVALUATED",
            "eligible": False,
            "reasons": ["Invalid pathway definition."],
            "warnings": [],
            "missing_tools": [],
            "missing_materials": [],
            "budget_gap": None,
            "time_gap": None,
        }

    constraints = user_constraints or {}
    safety_pref = constraints.get("safety_preference")

    # 1. Evaluate Safety
    safety_result = evaluate_safety(
        pathway=pathway,
        waste_profile=waste_profile,
        safety_preference=safety_pref,
    )

    safety_status = safety_result["safety_status"]
    warnings = list(safety_result.get("warnings", []))
    reasons = list(safety_result.get("reasons", []))

    # 2. Safety BLOCK immediately disqualifies the pathway
    if safety_status == "BLOCK":
        return {
            "pathway_id": pathway.get("pathway_id", "UNKNOWN"),
            "pathway": pathway,
            "safety_status": "BLOCK",
            "constraint_status": "NOT_EVALUATED",
            "eligible": False,
            "reasons": reasons,
            "warnings": warnings,
            "missing_tools": [],
            "missing_materials": [],
            "budget_gap": None,
            "time_gap": None,
        }

    # 3. Evaluate Constraints
    constraint_result = evaluate_constraints(
        pathway=pathway,
        user_constraints=constraints,
        waste_profile=waste_profile,
    )

    constraint_status = constraint_result["constraint_status"]
    reasons.extend(constraint_result.get("reasons", []))
    is_eligible = (constraint_status == "FEASIBLE")

    return {
        "pathway_id": pathway.get("pathway_id", "UNKNOWN"),
        "pathway": pathway,
        "safety_status": safety_status,
        "constraint_status": constraint_status,
        "eligible": is_eligible,
        "reasons": reasons,
        "warnings": warnings,
        "missing_tools": constraint_result.get("missing_tools", []),
        "missing_materials": constraint_result.get("missing_materials", []),
        "budget_gap": constraint_result.get("budget_gap"),
        "time_gap": constraint_result.get("time_gap"),
    }


def evaluate_all_pathways(pathways, user_constraints=None, waste_profile=None):
    """
    Evaluate eligibility for a list of candidate pathways.

    Returns:
        list[dict]: List of evaluated pathway eligibility records.
    """
    if not pathways:
        return []
    return [
        evaluate_pathway_eligibility(
            pathway=p,
            user_constraints=user_constraints,
            waste_profile=waste_profile,
        )
        for p in pathways
    ]


def get_eligible_pathways_for_profile(waste_profile, user_constraints=None):
    """
    Find and evaluate all candidate pathways matching a waste profile.

    Args:
        waste_profile: Structured waste profile dict.
        user_constraints: User constraints dict.

    Returns:
        list[dict]: Evaluated eligibility records for all candidate pathways.
    """
    if not waste_profile or not isinstance(waste_profile, dict):
        return []

    material = waste_profile.get("material")
    candidate_pathways = get_recovery_pathways(material=material)
    return evaluate_all_pathways(
        pathways=candidate_pathways,
        user_constraints=user_constraints,
        waste_profile=waste_profile,
    )
