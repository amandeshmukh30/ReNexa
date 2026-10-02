"""
ReNexa — Feedback & Outcome Validation Service
=================================================
Validates whether recovery pathways predicted as feasible by ReNexa
can be successfully executed in real-world household environments.

Core Research Question:
    "How often does a pathway predicted as feasible by ReNexa result in
     successful real-world execution?"

Standard Metrics:
    - RESR (Recovery Execution Success Rate): % of attempts resulting in complete success.
    - Partial Success Rate: % of attempts partially completed.
    - Failure Rate: % of attempts that could not be completed.
    - Time Estimation MAE: Mean absolute difference between estimated and actual minutes.
    - Resource Completeness Rate: % of attempts where all needed tools/materials were present.
    - Safety Issue Rate: % of attempts reporting unexpected safety or hazard concerns.
    - OVRR (Outcome-Validated Recipe Reliability): % of attempts that were fully successful,
      required no missing resources, and encountered zero safety incidents.
"""

import json
import os
from datetime import datetime

DEFAULT_FEEDBACK_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "outcome_feedback.json")
)

# Canonical attempt statuses
ATTEMPT_STATUSES = {
    "not_attempted",
    "successful",
    "partial",
    "failed",
}

# Standardized failure reason categories
FAILURE_REASONS = {
    "missing_tool",
    "missing_material",
    "time_underestimated",
    "condition_problem",
    "instruction_problem",
    "safety_issue",
    "other",
}


def normalize_attempt_status(val):
    """Normalize human-readable attempt string to canonical status key."""
    if not val:
        return "not_attempted"
    v = str(val).strip().lower()
    if "success" in v:
        return "successful"
    if "part" in v:
        return "partial"
    if "could not" in v or "fail" in v or "unable" in v:
        return "failed"
    if "not yet" in v or "not_attempted" in v:
        return "not_attempted"
    return "not_attempted"


def parse_numeric_minutes(val):
    """Safely parse minutes integer from int, float, or string."""
    if val is None or val == "":
        return None
    try:
        num = float(str(val).replace("mins", "").replace("minutes", "").replace("min", "").strip())
        return int(round(num))
    except (ValueError, TypeError):
        return None


def is_truthy_flag(val):
    """Check whether a boolean or string flag indicates True / Yes."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    if isinstance(val, str):
        v = val.strip().lower()
        return v in ("yes", "true", "1", "y", "reported")
    return False


def load_outcome_feedback(file_path=None):
    """
    Read outcome feedback records from storage (Supabase or local JSON fallback).

    Args:
        file_path: Optional custom path to JSON file.

    Returns:
        list[dict]: List of feedback records. Returns empty list if missing or malformed.
    """
    if file_path is None:
        try:
            from database.database import get_database, is_database_configured, get_all_feedback
            if is_database_configured():
                db_records = get_all_feedback()
                if db_records:
                    return db_records
        except Exception:
            pass

    path = file_path or DEFAULT_FEEDBACK_FILE
    if not os.path.isfile(path):
        return []

    try:
        with open(path, mode="r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_outcome_feedback(record, file_path=None):
    """
    Append a new structured outcome feedback record to storage.
    Persists to Supabase when configured, and always maintains local JSON file.

    Args:
        record:    Feedback record dict.
        file_path: Optional custom storage path.

    Returns:
        bool: True on success, False on invalid input.
    """
    if not record or not isinstance(record, dict):
        return False

    path = file_path or DEFAULT_FEEDBACK_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Ensure standardized timestamp
    formatted_record = dict(record)
    if "timestamp" not in formatted_record or not formatted_record["timestamp"]:
        formatted_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Normalize attempt status
    formatted_record["attempt_status"] = normalize_attempt_status(
        formatted_record.get("attempt_status")
    )

    # Parse numeric times
    formatted_record["actual_time_minutes"] = parse_numeric_minutes(
        formatted_record.get("actual_time_minutes")
    )
    formatted_record["estimated_time_minutes"] = parse_numeric_minutes(
        formatted_record.get("estimated_time_minutes")
    )

    # Load existing history safely
    history = load_outcome_feedback(file_path=path)
    history.append(formatted_record)

    try:
        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError:
        return False

    # Also persist to cloud database if available and using default storage
    if file_path is None:
        try:
            from database.database import is_database_configured, save_execution_feedback as db_save_feedback
            if is_database_configured():
                db_save_feedback(formatted_record)
        except Exception:
            pass

    return True


def clear_outcome_feedback(file_path=None):
    """Clear feedback storage (useful for isolated unit testing)."""
    path = file_path or DEFAULT_FEEDBACK_FILE
    if os.path.isfile(path):
        try:
            with open(path, mode="w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except OSError:
            return False
    return True


def calculate_outcome_metrics(records):
    """
    Compute comprehensive research analytics from feedback records.

    Calculates:
    - total_recorded: Total number of submitted feedback entries.
    - total_attempted: Number of attempts (successful + partial + failed), excluding not_attempted.
    - successful_count: Successful executions.
    - partial_count: Partially completed executions.
    - failed_count: Incomplete / failed executions.
    - not_attempted_count: User submitted feedback before physical execution.
    - resr: Recovery Execution Success Rate (successful / total_attempted * 100).
    - partial_rate: Partial completion rate (% of attempts).
    - failure_rate: Failure rate (% of attempts).
    - time_mae: Mean Absolute Error between estimated and actual duration.
    - resource_completeness_rate: % of attempts with no missing tools or materials.
    - safety_issue_rate: % of attempts that reported safety concerns.
    - ovrr: Outcome-Validated Recipe Reliability (% successful with complete resources and 0 safety issues).

    Returns:
        dict: Standardized outcome metrics dictionary.
    """
    if not records or not isinstance(records, list):
        return {
            "total_recorded": 0,
            "total_attempted": 0,
            "successful_count": 0,
            "partial_count": 0,
            "failed_count": 0,
            "not_attempted_count": 0,
            "resr": 0.0,
            "partial_rate": 0.0,
            "failure_rate": 0.0,
            "time_mae": None,
            "time_evaluated_count": 0,
            "resource_completeness_rate": 0.0,
            "safety_issue_rate": 0.0,
            "ovrr": 0.0,
        }

    total_recorded = len(records)
    not_attempted_count = 0
    successful_count = 0
    partial_count = 0
    failed_count = 0

    time_diffs = []
    resource_complete_count = 0
    safety_issue_count = 0
    ovrr_clean_success_count = 0

    attempted_records = []
    for r in records:
        status = normalize_attempt_status(r.get("attempt_status"))
        if status == "not_attempted":
            not_attempted_count += 1
            continue

        attempted_records.append(r)
        if status == "successful":
            successful_count += 1
        elif status == "partial":
            partial_count += 1
        elif status == "failed":
            failed_count += 1

        # Check time error
        act_t = parse_numeric_minutes(r.get("actual_time_minutes"))
        est_t = parse_numeric_minutes(r.get("estimated_time_minutes"))
        if act_t is not None and est_t is not None:
            time_diffs.append(abs(act_t - est_t))

        # Check resource completeness (no missing tools and no missing materials reported)
        has_missing_tools = is_truthy_flag(r.get("missing_tools"))
        has_missing_materials = is_truthy_flag(r.get("missing_materials"))
        has_resource_gap = has_missing_tools or has_missing_materials
        if not has_resource_gap:
            resource_complete_count += 1

        # Check safety incident
        has_safety_issue = is_truthy_flag(r.get("safety_issue"))
        if has_safety_issue:
            safety_issue_count += 1

        # OVRR: Fully successful AND 0 missing resources AND 0 safety issues
        if status == "successful" and not has_resource_gap and not has_safety_issue:
            ovrr_clean_success_count += 1

    total_attempted = len(attempted_records)

    if total_attempted == 0:
        return {
            "total_recorded": total_recorded,
            "total_attempted": 0,
            "successful_count": 0,
            "partial_count": 0,
            "failed_count": 0,
            "not_attempted_count": not_attempted_count,
            "resr": 0.0,
            "partial_rate": 0.0,
            "failure_rate": 0.0,
            "time_mae": None,
            "time_evaluated_count": 0,
            "resource_completeness_rate": 0.0,
            "safety_issue_rate": 0.0,
            "ovrr": 0.0,
        }

    resr = round((successful_count / total_attempted) * 100.0, 2)
    partial_rate = round((partial_count / total_attempted) * 100.0, 2)
    failure_rate = round((failed_count / total_attempted) * 100.0, 2)
    res_comp_rate = round((resource_complete_count / total_attempted) * 100.0, 2)
    safety_rate = round((safety_issue_count / total_attempted) * 100.0, 2)
    ovrr = round((ovrr_clean_success_count / total_attempted) * 100.0, 2)

    time_mae = round(sum(time_diffs) / len(time_diffs), 2) if time_diffs else None

    return {
        "total_recorded": total_recorded,
        "total_attempted": total_attempted,
        "successful_count": successful_count,
        "partial_count": partial_count,
        "failed_count": failed_count,
        "not_attempted_count": not_attempted_count,
        "resr": resr,
        "partial_rate": partial_rate,
        "failure_rate": failure_rate,
        "time_mae": time_mae,
        "time_evaluated_count": len(time_diffs),
        "resource_completeness_rate": res_comp_rate,
        "safety_issue_rate": safety_rate,
        "ovrr": ovrr,
    }


def summarize_failure_reasons(records):
    """
    Summarize failure and challenge reasons across feedback entries.

    Returns:
        dict[str, int]: Counts per categorized failure reason.
    """
    counts = {k: 0 for k in FAILURE_REASONS}
    if not records:
        return counts

    for r in records:
        status = normalize_attempt_status(r.get("attempt_status"))
        reason = str(r.get("failure_reason", "")).strip().lower()

        # Check explicit failure reason
        if reason in counts:
            counts[reason] += 1
        elif is_truthy_flag(r.get("safety_issue")):
            counts["safety_issue"] += 1
        elif is_truthy_flag(r.get("missing_tools")):
            counts["missing_tool"] += 1
        elif is_truthy_flag(r.get("missing_materials")):
            counts["missing_material"] += 1
        elif status in ("partial", "failed") and reason:
            counts["other"] += 1

    return counts


def analyze_pathway_outcomes(records):
    """
    Perform per-pathway aggregation to observe reliability across individual recipes.

    Returns:
        list[dict]: Table of performance records grouped by pathway_id.
    """
    if not records:
        return []

    groups = {}
    for r in records:
        pid = str(r.get("pathway_id", "UNKNOWN")).strip().upper()
        if not pid or pid == "UNKNOWN":
            continue

        if pid not in groups:
            groups[pid] = {
                "pathway_id": pid,
                "pathway_title": r.get("pathway_title") or r.get("title") or pid,
                "attempts": 0,
                "successful": 0,
                "partial": 0,
                "failed": 0,
                "time_diffs": [],
            }

        status = normalize_attempt_status(r.get("attempt_status"))
        if status == "not_attempted":
            continue

        groups[pid]["attempts"] += 1
        if status == "successful":
            groups[pid]["successful"] += 1
        elif status == "partial":
            groups[pid]["partial"] += 1
        elif status == "failed":
            groups[pid]["failed"] += 1

        act_t = parse_numeric_minutes(r.get("actual_time_minutes"))
        est_t = parse_numeric_minutes(r.get("estimated_time_minutes"))
        if act_t is not None and est_t is not None:
            groups[pid]["time_diffs"].append(abs(act_t - est_t))

    results = []
    for pid, g in groups.items():
        if g["attempts"] == 0:
            continue
        s_rate = round((g["successful"] / g["attempts"]) * 100.0, 1)
        mae = round(sum(g["time_diffs"]) / len(g["time_diffs"]), 1) if g["time_diffs"] else None
        results.append({
            "pathway_id": pid,
            "title": g["pathway_title"],
            "attempts": g["attempts"],
            "successful": g["successful"],
            "partial": g["partial"],
            "failed": g["failed"],
            "success_rate": f"{s_rate:.1f}%",
            "avg_time_error_mins": f"{mae:.1f} mins" if mae is not None else "N/A",
        })

    # Sort by attempts descending
    results.sort(key=lambda x: -x["attempts"])
    return results
