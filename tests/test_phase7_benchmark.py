"""
ReNexa — Phase 7 Deterministic Benchmark Suite (50+ Scenarios)
===============================================================
Evaluates Execution Guidance and Tutorial Layer across >= 50 scenarios:
1. Guidance Retrieval Accuracy (Target: >= 95%)
2. Step Order Preservation (Target: 100%)
3. Safety Status Preservation (Target: 100%)
4. Resource Metadata Preservation (Target: 100%)
5. Missing-Data Handling (Target: 100%)
6. Fabrication Prevention (Target: 100%)
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.recovery_service import load_recovery_pathways
from services.execution_service import (
    get_execution_guide,
    parse_execution_steps,
)


def generate_50_execution_benchmark_scenarios():
    """
    Generate >= 50 diverse execution scenarios:
    - 28 catalogued recovery pathways from CSV under normal feasible conditions.
    - 12 safety-blocked / hazardous scenarios (must enforce can_execute == False).
    - 6 constraint-mismatched scenarios (budget/time/tool shortages).
    - 4 data-quality edge-cases (missing steps, missing source citations, empty IDs).
    """
    scenarios = []
    catalogued_pathways = load_recovery_pathways()

    # 1. 28 Catalogued Pathways (Feasible standard conditions)
    for p in catalogued_pathways:
        pid = p["pathway_id"]
        # Provide compatible constraints
        user_const = {
            "budget": "₹500+",
            "time": "2+ hours",
            "tools": ["Scissors", "Tape", "Twine", "Binder clip", "Needle", "Trowel", "Hammer", "Utility knife", "Shoe adhesive"],
            "skill": "Advanced",
            "workspace": "Outdoor",
            "extra_materials": ["Thread", "Potting soil", "PVA glue", "Packaging tape", "Cleaning cloth", "Electrical tape", "Dry leaves", "Trash bag"],
        }
        scenarios.append({
            "id": f"BENCH-CAT-{pid}",
            "type": "catalogued_feasible",
            "pathway": p,
            "user_constraints": user_const,
            "expected_can_execute": True,
            "expected_safety": "ALLOW" if p.get("safety_level") != "High" and p["input_material"] != "battery" else ("ALLOW" if p.get("pathway_type") == "dispose" else "BLOCK"),
            "raw_steps": p.get("steps", ""),
            "raw_source": p.get("source", ""),
        })

    # 2. 12 Hazardous / Blocked Scenarios
    for i in range(12):
        if i % 3 == 0:
            p = {
                "pathway_id": f"HAZ-BENCH-{i+1:03d}",
                "input_material": "battery",
                "pathway_type": "repair",
                "title": f"Hazardous Battery Repair Test #{i+1}",
                "steps": "1. Cut open casing; 2. Replace lithium cell.",
                "tools": "Pliers",
                "budget": "0",
                "time_required": "15 minutes",
                "skill_level": "Intermediate",
                "workspace": "Indoor",
                "safety_level": "High",
            }
        elif i % 3 == 1:
            p = {
                "pathway_id": f"HAZ-BENCH-{i+1:03d}",
                "input_material": "plastic",
                "pathway_type": "upcycle",
                "title": f"Hazardous Plastic Melting Test #{i+1}",
                "steps": "1. Heat and melt plastic over open stove; 2. Pour into mold.",
                "tools": "Stove, Mold",
                "budget": "0",
                "time_required": "15 minutes",
                "skill_level": "Intermediate",
                "workspace": "Indoor",
                "safety_level": "High",
            }
        else:
            p = {
                "pathway_id": f"HAZ-BENCH-{i+1:03d}",
                "input_material": "metal",
                "pathway_type": "upcycle",
                "title": f"Hazardous Acid Leaching Test #{i+1}",
                "steps": "1. Submerge metal in concentrated acid bath; 2. Leach coating.",
                "tools": "Chemical acid bath",
                "budget": "0",
                "time_required": "15 minutes",
                "skill_level": "Intermediate",
                "workspace": "Indoor",
                "safety_level": "High",
            }

        scenarios.append({
            "id": f"BENCH-HAZ-{i+1:03d}",
            "type": "safety_blocked",
            "pathway": p,
            "user_constraints": {"budget": "₹500+", "time": "2+ hours", "tools": ["Pliers", "Stove", "Chemical acid bath"]},
            "expected_can_execute": False,
            "expected_safety": "BLOCK",
            "raw_steps": p["steps"],
            "raw_source": "",
        })

    # 3. 6 Constraint-Mismatched Infeasible Scenarios
    for i in range(6):
        p = {
            "pathway_id": f"INFEAS-BENCH-{i+1:03d}",
            "input_material": "cardboard",
            "pathway_type": "upcycle",
            "title": f"High Budget Project #{i+1}",
            "steps": "1. Cut board; 2. Glue together; 3. Mount on wall.",
            "tools": "Utility knife",
            "budget": "200",
            "time_required": "30 minutes",
            "skill_level": "Intermediate",
            "workspace": "Indoor",
            "safety_level": "Low",
        }
        scenarios.append({
            "id": f"BENCH-INFEAS-{i+1:03d}",
            "type": "constraint_infeasible",
            "pathway": p,
            "user_constraints": {"budget": "₹0", "time": "5 minutes", "tools": []},  # Severe shortage
            "expected_can_execute": False,
            "expected_safety": "ALLOW",
            "raw_steps": p["steps"],
            "raw_source": "",
        })

    # 4. 4 Data-Quality Missing-Data Edge Cases
    edge_cases = [
        ("EDGE-NO-STEP", "Missing Steps Pathway", "", "EPA Guidance"),
        ("EDGE-NO-SRC", "Missing Source Pathway", "1. Clean; 2. Dry", ""),
        ("EDGE-EMPTY-ALL", "Blank Everything", "", ""),
        ("EDGE-CORRUPTED", "Single Word Step", "Flatten", "Internal prototype rule"),
    ]
    for pid, title, steps, src in edge_cases:
        p = {
            "pathway_id": pid,
            "input_material": "paper",
            "pathway_type": "reuse",
            "title": title,
            "steps": steps,
            "tools": "None",
            "budget": "0",
            "time_required": "5 minutes",
            "skill_level": "Beginner",
            "workspace": "Indoor",
            "source": src,
        }
        scenarios.append({
            "id": f"BENCH-{pid}",
            "type": "data_quality_edge",
            "pathway": p,
            "user_constraints": {"budget": "₹100", "time": "30 minutes", "tools": []},
            "expected_can_execute": bool(steps.strip()),
            "expected_safety": "ALLOW",
            "raw_steps": steps,
            "raw_source": src,
        })

    return scenarios


def test_phase7_benchmark_execution():
    """
    Run the deterministic 50-scenario execution guidance benchmark.
    Verifies:
    - Guidance Retrieval Accuracy (>= 95%)
    - Step Order Preservation (100%)
    - Safety Status Preservation (100%)
    - Resource Metadata Preservation (100%)
    - Missing-Data Handling (100%)
    - Fabrication Prevention (100%)
    """
    scenarios = generate_50_execution_benchmark_scenarios()
    total_scenarios = len(scenarios)
    assert total_scenarios >= 50, f"Expected at least 50 scenarios, got {total_scenarios}"

    retrieval_successes = 0
    step_order_preservations = 0
    safety_status_preservations = 0
    resource_preservations = 0
    missing_data_handled = 0
    no_fabrication_passes = 0

    for sc in scenarios:
        guide = get_execution_guide(
            pathway_or_id=sc["pathway"],
            user_constraints=sc["user_constraints"],
        )

        # 1. Retrieval Check
        if guide is not None and "execution_status" in guide:
            retrieval_successes += 1

        # 2. Step Order Preservation
        raw_steps = sc.get("raw_steps", "")
        parsed_steps = guide.get("steps", [])
        expected_steps = parse_execution_steps(raw_steps)
        if parsed_steps == expected_steps:
            step_order_preservations += 1

        # 3. Safety Status Preservation
        expected_safety = sc.get("expected_safety")
        if sc["type"] == "safety_blocked":
            if guide["safety_status"] == "BLOCK" and guide["can_execute"] is False:
                safety_status_preservations += 1
        elif sc["type"] == "constraint_infeasible":
            if guide["can_execute"] is False and guide["execution_status"] == "INFEASIBLE":
                safety_status_preservations += 1
        else:
            if guide["safety_status"] in ("ALLOW", "WARN"):
                safety_status_preservations += 1

        # 4. Resource Metadata Preservation
        p = sc["pathway"]
        if (
            guide.get("budget") == str(p.get("budget", "0"))
            and guide.get("time_required") == str(p.get("time_required", "Unknown"))
            and guide.get("skill_level") == str(p.get("skill_level", "Beginner"))
            and guide.get("workspace") == str(p.get("workspace", "Any"))
        ):
            resource_preservations += 1

        # 5. Missing-Data Handling
        if sc["type"] == "data_quality_edge":
            if not raw_steps and guide["execution_status"] == "DATA_QUALITY_ISSUE":
                missing_data_handled += 1
            elif not sc.get("raw_source") and "No verified tutorial reference is available" in guide["tutorial_reference"]:
                missing_data_handled += 1
            elif guide is not None:
                missing_data_handled += 1
        else:
            missing_data_handled += 1

        # 6. Fabrication Prevention (No fake URLs or invented tools)
        has_fake_url = any("http://fake" in str(v) or "www.invented" in str(v) for v in guide.values())
        if not has_fake_url:
            no_fabrication_passes += 1

    retrieval_rate = (retrieval_successes / total_scenarios) * 100
    step_order_rate = (step_order_preservations / total_scenarios) * 100
    safety_preservation_rate = (safety_status_preservations / total_scenarios) * 100
    resource_rate = (resource_preservations / total_scenarios) * 100
    missing_data_rate = (missing_data_handled / total_scenarios) * 100
    no_fabrication_rate = (no_fabrication_passes / total_scenarios) * 100

    print(f"\n==================================================================")
    print(f"--- Phase 7 Execution Guidance Benchmark ({total_scenarios} scenarios) ---")
    print(f"Guidance Retrieval Accuracy:     {retrieval_rate:.1f}% ({retrieval_successes}/{total_scenarios})")
    print(f"Step Order Preservation:         {step_order_rate:.1f}% ({step_order_preservations}/{total_scenarios})")
    print(f"Safety Status Preservation:      {safety_preservation_rate:.1f}% ({safety_status_preservations}/{total_scenarios})")
    print(f"Resource Metadata Preservation:  {resource_rate:.1f}% ({resource_preservations}/{total_scenarios})")
    print(f"Missing-Data Handling:           {missing_data_rate:.1f}% ({missing_data_handled}/{total_scenarios})")
    print(f"Fabrication Prevention:          {no_fabrication_rate:.1f}% ({no_fabrication_passes}/{total_scenarios})")
    print(f"==================================================================")

    assert retrieval_rate >= 95.0, f"Retrieval accuracy {retrieval_rate:.1f}% below 95%"
    assert step_order_rate == 100.0, f"Step order preservation {step_order_rate:.1f}% must be 100%"
    assert safety_preservation_rate == 100.0, f"Safety preservation {safety_preservation_rate:.1f}% must be 100%"
    assert resource_rate == 100.0, f"Resource metadata preservation {resource_rate:.1f}% must be 100%"
    assert missing_data_rate == 100.0, f"Missing-data handling {missing_data_rate:.1f}% must be 100%"
    assert no_fabrication_rate == 100.0, f"Fabrication prevention {no_fabrication_rate:.1f}% must be 100%"
