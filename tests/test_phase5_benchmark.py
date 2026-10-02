"""
ReNexa — Phase 5 Deterministic Benchmark Suite (100+ Scenarios)
================================================================
Evaluates Safety Engine, Constraint Engine, and Eligibility Engine
against >= 100 rigorously defined ground-truth test scenarios.

Calculates:
- Safety Compliance Rate (Target: >= 95%, 100% on hazardous operations)
- Constraint Agreement Rate (Target: >= 95%)
- Eligibility Agreement Rate (Target: >= 95%)
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.safety_service import evaluate_safety
from services.constraint_service import evaluate_constraints
from services.eligibility_service import evaluate_pathway_eligibility


def generate_100_benchmark_scenarios():
    """
    Generate 100 deterministic benchmark scenarios with clear expected outcomes.
    Returns list of scenario dicts.
    """
    scenarios = []

    # ── Group 1: Hazardous Operations (20 Scenarios) -> Expected Safety BLOCK, Eligible FALSE
    haz_materials = ["battery", "plastic", "glass", "metal", "biological"]
    for i in range(20):
        mat = haz_materials[i % len(haz_materials)]
        if mat == "battery":
            p = {
                "pathway_id": f"HAZ-BAT-{i:03d}",
                "input_material": "battery",
                "pathway_type": "repair" if i % 2 == 0 else "upcycle",
                "title": f"Battery DIY Cell Modification {i}",
                "tools": "Screwdriver, pliers",
                "steps": "Dismantle battery casing and replace lithium plate",
                "safety_level": "High",
                "budget": "0",
                "time_required": "10 minutes",
                "skill_level": "Beginner",
                "workspace": "Indoor",
            }
        elif mat == "plastic":
            p = {
                "pathway_id": f"HAZ-PLA-{i:03d}",
                "input_material": "plastic",
                "pathway_type": "upcycle",
                "title": f"Home Plastic Melting and Casting {i}",
                "tools": "Oven, mold",
                "steps": "Heat and melt plastic bottles in kitchen oven",
                "safety_level": "High",
                "budget": "0",
                "time_required": "15 minutes",
                "skill_level": "Beginner",
                "workspace": "Indoor",
            }
        else:
            p = {
                "pathway_id": f"HAZ-GEN-{i:03d}",
                "input_material": mat,
                "pathway_type": "upcycle",
                "title": f"Chemical Acid Treatment {i}",
                "tools": "Chemical acid bath",
                "steps": "Soak material in concentrated acid bath for stripping",
                "safety_level": "High",
                "budget": "0",
                "time_required": "20 minutes",
                "skill_level": "Intermediate",
                "workspace": "Indoor",
            }

        user_const = {
            "budget": "₹500+",
            "time": "2+ hours",
            "tools": ["Screwdriver", "Oven", "Pliers", "Chemical acid bath"],
            "skill": "Advanced",
            "workspace": "Indoor",
        }
        profile = {"material": mat, "condition": "Good", "confirmed_quantity": 2, "contamination": "Clean"}
        scenarios.append({
            "id": f"SCEN-HAZ-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "BLOCK",
            "expected_eligible": False,
        })

    # ── Group 2: Fully Feasible Pathways (25 Scenarios) -> Expected Safety ALLOW/WARN, Constraint FEASIBLE, Eligible TRUE
    safe_types = [
        ("plastic", "reuse", "Plastic Container Storage", "None", "0", "5 minutes", "Beginner", "Indoor", 1, "Good"),
        ("glass", "reuse", "Glass Jar Pantry Storage", "None", "0", "10 minutes", "Beginner", "Indoor", 1, "Good"),
        ("metal", "reuse", "Metal Tin Pen Stand", "None", "0", "5 minutes", "Beginner", "Indoor", 1, "Good"),
        ("paper", "reuse", "Scratchpad Notes", "Binder clip", "0", "5 minutes", "Beginner", "Indoor", 1, "Good"),
        ("cardboard", "reuse", "Cardboard Box Storage", "Tape", "0", "5 minutes", "Beginner", "Indoor", 1, "Good"),
    ]
    for i in range(25):
        mat, ptype, title, tools, budget, time_req, skill, ws, qty, cond = safe_types[i % len(safe_types)]
        p = {
            "pathway_id": f"FEAS-{i:03d}",
            "input_material": mat,
            "pathway_type": ptype,
            "title": f"{title} #{i+1}",
            "tools": tools,
            "budget": budget,
            "time_required": time_req,
            "skill_level": skill,
            "workspace": ws,
            "min_quantity": qty,
            "condition_requirement": cond,
            "steps": "Clean item thoroughly and use for dry storage.",
            "safety_level": "Low",
        }
        user_const = {
            "budget": "₹100",
            "time": "1 hour",
            "tools": ["Binder clip", "Tape", "Scissors"],
            "skill": "Intermediate",
            "workspace": "Indoor",
        }
        profile = {"material": mat, "condition": "Good", "confirmed_quantity": 2, "contamination": "Clean"}
        scenarios.append({
            "id": f"SCEN-FEAS-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "FEASIBLE",
            "expected_eligible": True,
        })

    # ── Group 3: Tool Shortage Infeasible Pathways (15 Scenarios) -> Expected Constraint INFEASIBLE, Eligible FALSE
    for i in range(15):
        p = {
            "pathway_id": f"TOOL-{i:03d}",
            "input_material": "cardboard",
            "pathway_type": "upcycle",
            "title": f"Cardboard Construction {i}",
            "tools": "Utility knife, PVA glue",
            "budget": "0",
            "time_required": "15 minutes",
            "skill_level": "Beginner",
            "workspace": "Indoor",
            "min_quantity": 1,
            "condition_requirement": "Any",
            "steps": "Cut panels and glue compartments.",
            "safety_level": "Low",
        }
        user_const = {
            "budget": "₹100",
            "time": "1 hour",
            "tools": ["Tape"],  # Missing Utility knife and PVA glue
            "skill": "Beginner",
            "workspace": "Indoor",
        }
        profile = {"material": "cardboard", "condition": "Good", "confirmed_quantity": 1}
        scenarios.append({
            "id": f"SCEN-TOOL-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "INFEASIBLE",
            "expected_eligible": False,
        })

    # ── Group 4: Budget Shortage Infeasible Pathways (10 Scenarios) -> Expected Constraint INFEASIBLE, Eligible FALSE
    for i in range(10):
        p = {
            "pathway_id": f"BUD-{i:03d}",
            "input_material": "clothes",
            "pathway_type": "repair",
            "title": f"Shoe or Textile Restoration {i}",
            "tools": "Needle",
            "budget": "100",  # Requires 100
            "time_required": "15 minutes",
            "skill_level": "Beginner",
            "workspace": "Indoor",
            "min_quantity": 1,
            "condition_requirement": "Any",
            "steps": "Mend fabric.",
            "safety_level": "Low",
        }
        user_const = {
            "budget": "₹0",  # Budget is 0
            "time": "1 hour",
            "tools": ["Needle"],
            "skill": "Beginner",
            "workspace": "Indoor",
        }
        profile = {"material": "clothes", "condition": "Used", "confirmed_quantity": 1}
        scenarios.append({
            "id": f"SCEN-BUD-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "INFEASIBLE",
            "expected_eligible": False,
        })

    # ── Group 5: Time Shortage Infeasible Pathways (10 Scenarios) -> Expected Constraint INFEASIBLE, Eligible FALSE
    for i in range(10):
        p = {
            "pathway_id": f"TIME-{i:03d}",
            "input_material": "metal",
            "pathway_type": "upcycle",
            "title": f"Multi-step Metal Assembly {i}",
            "tools": "Hammer",
            "budget": "0",
            "time_required": "1 hour",  # Requires 60 mins
            "skill_level": "Beginner",
            "workspace": "Indoor",
            "min_quantity": 1,
            "condition_requirement": "Any",
            "steps": "Punch holes and assemble.",
            "safety_level": "Low",
        }
        user_const = {
            "budget": "₹100",
            "time": "5 minutes",  # Only 5 mins
            "tools": ["Hammer"],
            "skill": "Beginner",
            "workspace": "Indoor",
        }
        profile = {"material": "metal", "condition": "Good", "confirmed_quantity": 1}
        scenarios.append({
            "id": f"SCEN-TIME-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "INFEASIBLE",
            "expected_eligible": False,
        })

    # ── Group 6: Skill Mismatch (5 Scenarios) -> Expected Constraint INFEASIBLE, Eligible FALSE
    for i in range(5):
        p = {
            "pathway_id": f"SKILL-{i:03d}",
            "input_material": "shoes",
            "pathway_type": "repair",
            "title": f"Advanced Footwear Re-soling {i}",
            "tools": "Shoe adhesive",
            "budget": "0",
            "time_required": "20 minutes",
            "skill_level": "Advanced",  # Requires Advanced
            "workspace": "Indoor",
            "min_quantity": 1,
            "condition_requirement": "Any",
            "steps": "Dismantle and stitch outsole.",
            "safety_level": "Low",
        }
        user_const = {
            "budget": "₹100",
            "time": "1 hour",
            "tools": ["Shoe adhesive"],
            "skill": "Beginner",  # Beginner user
            "workspace": "Indoor",
        }
        profile = {"material": "shoes", "condition": "Used", "confirmed_quantity": 1}
        scenarios.append({
            "id": f"SCEN-SKILL-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "INFEASIBLE",
            "expected_eligible": False,
        })

    # ── Group 7: Workspace Mismatch (5 Scenarios) -> Expected Constraint INFEASIBLE, Eligible FALSE
    for i in range(5):
        p = {
            "pathway_id": f"WS-{i:03d}",
            "input_material": "biological",
            "pathway_type": "recycle",
            "title": f"Outdoor Composting Pit {i}",
            "tools": "Trowel",
            "budget": "0",
            "time_required": "15 minutes",
            "skill_level": "Beginner",
            "workspace": "Outdoor",  # Requires Outdoor
            "min_quantity": 1,
            "condition_requirement": "Any",
            "steps": "Layer green and brown organic waste.",
            "safety_level": "Low",
        }
        user_const = {
            "budget": "₹100",
            "time": "1 hour",
            "tools": ["Trowel"],
            "skill": "Beginner",
            "workspace": "Indoor",  # Only Indoor
        }
        profile = {"material": "biological", "condition": "Good", "confirmed_quantity": 1}
        scenarios.append({
            "id": f"SCEN-WS-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "INFEASIBLE",
            "expected_eligible": False,
        })

    # ── Group 8: Condition & Quantity Mismatch (10 Scenarios) -> Expected Constraint INFEASIBLE, Eligible FALSE
    for i in range(10):
        if i % 2 == 0:
            # Condition mismatch
            p = {
                "pathway_id": f"COND-{i:03d}",
                "input_material": "glass",
                "pathway_type": "reuse",
                "title": f"Glass Jar Food Storage {i}",
                "tools": "None",
                "budget": "0",
                "time_required": "5 minutes",
                "skill_level": "Beginner",
                "workspace": "Indoor",
                "min_quantity": 1,
                "condition_requirement": "Good",  # Strictly Good
                "steps": "Store pantry spices in intact jar.",
                "safety_level": "Low",
            }
            user_const = {"budget": "₹100", "time": "1 hour", "tools": []}
            profile = {"material": "glass", "condition": "Damaged", "confirmed_quantity": 1}  # Damaged item
        else:
            # Quantity shortage
            p = {
                "pathway_id": f"QTY-{i:03d}",
                "input_material": "cardboard",
                "pathway_type": "upcycle",
                "title": f"Multi-Carton Shelving {i}",
                "tools": "Tape",
                "budget": "0",
                "time_required": "15 minutes",
                "skill_level": "Beginner",
                "workspace": "Indoor",
                "min_quantity": 3,  # Requires 3
                "condition_requirement": "Any",
                "steps": "Assemble 3 cartons together.",
                "safety_level": "Low",
            }
            user_const = {"budget": "₹100", "time": "1 hour", "tools": ["Tape"]}
            profile = {"material": "cardboard", "condition": "Good", "confirmed_quantity": 1}  # Only 1

        scenarios.append({
            "id": f"SCEN-MAT-COND-{i+1:03d}",
            "pathway": p,
            "user_constraints": user_const,
            "waste_profile": profile,
            "expected_safety": "ALLOW",
            "expected_constraint": "INFEASIBLE",
            "expected_eligible": False,
        })

    return scenarios


def test_phase5_100_scenario_benchmark_execution():
    """
    Run the 100-scenario deterministic benchmark.
    Verify Safety Compliance Rate, Constraint Agreement, and Eligibility Agreement >= 95%.
    Verify 100% correct blocking on hazardous operations.
    """
    scenarios = generate_100_benchmark_scenarios()
    assert len(scenarios) == 100, f"Expected exactly 100 scenarios, got {len(scenarios)}"

    total_scenarios = len(scenarios)
    safety_matches = 0
    constraint_matches = 0
    eligibility_matches = 0
    hazardous_blocked = 0
    hazardous_total = 0

    for sc in scenarios:
        res = evaluate_pathway_eligibility(
            pathway=sc["pathway"],
            user_constraints=sc["user_constraints"],
            waste_profile=sc["waste_profile"],
        )

        # 1. Safety check
        exp_safety = sc.get("expected_safety")
        if exp_safety:
            if exp_safety == "BLOCK":
                hazardous_total += 1
                if res["safety_status"] == "BLOCK":
                    hazardous_blocked += 1
                    safety_matches += 1
            elif res["safety_status"] in (exp_safety, "WARN", "ALLOW") and res["safety_status"] != "BLOCK":
                safety_matches += 1
        else:
            safety_matches += 1

        # 2. Constraint check
        exp_const = sc.get("expected_constraint")
        if exp_const:
            if res["constraint_status"] == exp_const:
                constraint_matches += 1
        else:
            # In hazardous block cases, constraint is NOT_EVALUATED
            if res["safety_status"] == "BLOCK" and res["constraint_status"] == "NOT_EVALUATED":
                constraint_matches += 1

        # 3. Overall eligibility check
        exp_elig = sc["expected_eligible"]
        if res["eligible"] == exp_elig:
            eligibility_matches += 1

    safety_rate = (safety_matches / total_scenarios) * 100
    constraint_rate = (constraint_matches / total_scenarios) * 100
    eligibility_rate = (eligibility_matches / total_scenarios) * 100
    hazardous_rate = (hazardous_blocked / hazardous_total) * 100 if hazardous_total > 0 else 100.0

    print(f"\n--- Phase 5 Benchmark Results ({total_scenarios} scenarios) ---")
    print(f"Safety Compliance Rate:       {safety_rate:.1f}% ({safety_matches}/{total_scenarios})")
    print(f"Hazardous Operations Blocked: {hazardous_rate:.1f}% ({hazardous_blocked}/{hazardous_total})")
    print(f"Constraint Agreement Rate:    {constraint_rate:.1f}% ({constraint_matches}/{total_scenarios})")
    print(f"Eligibility Agreement Rate:   {eligibility_rate:.1f}% ({eligibility_matches}/{total_scenarios})")

    assert safety_rate >= 95.0, f"Safety compliance rate {safety_rate:.1f}% is below 95%"
    assert hazardous_rate == 100.0, f"Hazardous block rate {hazardous_rate:.1f}% must be 100%"
    assert constraint_rate >= 95.0, f"Constraint agreement rate {constraint_rate:.1f}% is below 95%"
    assert eligibility_rate >= 95.0, f"Eligibility agreement rate {eligibility_rate:.1f}% is below 95%"
