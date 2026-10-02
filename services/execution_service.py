"""
ReNexa — Execution Guidance Service
====================================
Prepares safe, step-by-step physical execution guidance for verified recovery pathways.

Core Architecture:
    Waste Profile -> Recovery Knowledge Base -> Safety -> Constraints -> Eligibility
    -> MCDA Ranking -> Selected Pathway -> Execution Guidance & Tutorial Layer

Guiding Principles:
- Grounded Data: All execution steps, tools, materials, budget, and sources derive directly from data/recovery_pathways.csv.
- Hard Safety Enforcement: Inherits authoritative Phase 5 Safety evaluation. Safety BLOCK strictly prevents execution guide display.
- Constraint Awareness: Verifies that user constraints still support the selected pathway before enabling execution.
- No Fabrication: If steps or tutorial references are missing, returns explicit data quality notices without inventing instructions.
"""

from services.recovery_service import load_recovery_pathways
from services.eligibility_service import evaluate_pathway_eligibility


def parse_execution_steps(raw_steps):
    """
    Parse formatted pathway steps into a clean, ordered list of step instructions.

    Args:
        raw_steps: Semicolon or newline-separated step text (e.g. '1. Clean; 2. Dry; 3. Store').

    Returns:
        list[str]: Clean list of sequential steps preserving exact original order.
    """
    if not raw_steps or not isinstance(raw_steps, str):
        return []

    text = raw_steps.strip()
    if not text:
        return []

    # Split primarily by semicolon if present, otherwise newline
    if ";" in text:
        chunks = text.split(";")
    elif "\n" in text:
        chunks = text.split("\n")
    else:
        chunks = [text]

    steps = []
    for chunk in chunks:
        cleaned = chunk.strip()
        if cleaned:
            steps.append(cleaned)

    return steps


def get_pathway_by_id(pathway_id, csv_path=None):
    """
    Retrieve a raw pathway dictionary from the knowledge base by its unique pathway ID.

    Returns:
        dict | None: The pathway record or None if not found.
    """
    if not pathway_id:
        return None

    target_id = str(pathway_id).strip().upper()
    all_pathways = load_recovery_pathways(csv_path=csv_path)

    for p in all_pathways:
        if str(p.get("pathway_id", "")).strip().upper() == target_id:
            return p

    return None


def get_execution_guide(pathway_or_id, user_constraints=None, waste_profile=None, csv_path=None):
    """
    Retrieve and prepare execution guidance for a specific recovery pathway.

    Args:
        pathway_or_id:    Pathway dict or string pathway_id (e.g. 'REC-PLA-001').
        user_constraints: Dict of current household constraints.
        waste_profile:    Dict of active structured waste profile.
        csv_path:         Optional custom path to CSV.

    Returns:
        dict: Structured execution guide containing parsed steps, safety status,
              resource requirements, expected output, fallback, and tutorial citations.
    """
    if not pathway_or_id:
        return {
            "pathway_id": "UNKNOWN",
            "title": "Unknown Pathway",
            "can_execute": False,
            "execution_status": "NOT_FOUND",
            "reasons": ["No pathway provided."],
            "warnings": [],
            "steps": [],
            "tools": [],
            "extra_materials": [],
            "tutorial_available": False,
            "tutorial_reference": "No verified tutorial reference is available.",
        }

    # Resolve pathway record
    if isinstance(pathway_or_id, dict):
        pathway = pathway_or_id
    else:
        pathway = get_pathway_by_id(str(pathway_or_id), csv_path=csv_path)

    if not pathway:
        return {
            "pathway_id": str(pathway_or_id),
            "title": "Pathway Not Found",
            "can_execute": False,
            "execution_status": "NOT_FOUND",
            "reasons": [f"Pathway '{pathway_or_id}' does not exist in the knowledge base."],
            "warnings": [],
            "steps": [],
            "tools": [],
            "extra_materials": [],
            "tutorial_available": False,
            "tutorial_reference": "No verified tutorial reference is available.",
        }

    # Authoritative Phase 5 Eligibility Check
    eligibility_result = evaluate_pathway_eligibility(
        pathway=pathway,
        user_constraints=user_constraints,
        waste_profile=waste_profile,
    )

    safety_status = eligibility_result.get("safety_status", "ALLOW")
    constraint_status = eligibility_result.get("constraint_status", "FEASIBLE")
    is_eligible = eligibility_result.get("eligible", False)
    warnings = list(eligibility_result.get("warnings", []))
    reasons = list(eligibility_result.get("reasons", []))

    # Parse raw steps into clean list
    raw_steps = pathway.get("steps", "")
    steps_list = parse_execution_steps(raw_steps)

    # Determine execution feasibility state
    if safety_status == "BLOCK":
        can_execute = False
        execution_status = "BLOCKED"
    elif not is_eligible or constraint_status == "INFEASIBLE":
        can_execute = False
        execution_status = "INFEASIBLE"
    elif not steps_list:
        can_execute = False
        execution_status = "DATA_QUALITY_ISSUE"
        reasons.append("No step-by-step instructions catalogued for this pathway.")
    else:
        can_execute = True
        execution_status = "READY"

    # Format tools and extra materials lists
    raw_tools = str(pathway.get("tools", "None")).strip()
    if raw_tools.lower() in ("none", "n/a", ""):
        tools_list = []
    else:
        tools_list = [t.strip() for t in raw_tools.split(",") if t.strip()]

    raw_mat = str(pathway.get("extra_materials", "None")).strip()
    if raw_mat.lower() in ("none", "n/a", ""):
        materials_list = []
    else:
        materials_list = [m.strip() for m in raw_mat.split(",") if m.strip()]

    # Tutorial & Reference Source
    source_str = str(pathway.get("source", "")).strip()
    has_valid_source = bool(source_str and source_str.lower() not in ("none", "unknown", ""))
    tutorial_ref = source_str if has_valid_source else "No verified tutorial reference is available."

    return {
        "pathway_id": pathway.get("pathway_id", "UNKNOWN"),
        "title": pathway.get("title", "Unnamed Pathway"),
        "pathway_type": pathway.get("pathway_type", "reuse"),
        "input_material": pathway.get("input_material", "unknown"),
        "description": pathway.get("description", ""),
        "can_execute": can_execute,
        "execution_status": execution_status,
        "eligible": is_eligible,
        "safety_status": safety_status,
        "constraint_status": constraint_status,
        "warnings": warnings,
        "reasons": reasons,
        "tools": tools_list,
        "extra_materials": materials_list,
        "budget": str(pathway.get("budget", "0")),
        "time_required": str(pathway.get("time_required", "Unknown")),
        "skill_level": str(pathway.get("skill_level", "Beginner")),
        "workspace": str(pathway.get("workspace", "Any")),
        "safety_level": str(pathway.get("safety_level", "Low")),
        "condition_requirement": str(pathway.get("condition_requirement", "Any")),
        "min_quantity": int(pathway.get("min_quantity", 1)),
        "steps": steps_list,
        "expected_output": str(pathway.get("expected_output", "Restored or repurposed item.")),
        "fallback": str(pathway.get("fallback", "Municipal waste segregation")),
        "source": source_str,
        "verification_status": str(pathway.get("verification_status", "prototype")),
        "last_reviewed": str(pathway.get("last_reviewed", "Unknown")),
        "tutorial_available": has_valid_source,
        "tutorial_reference": tutorial_ref,
    }
