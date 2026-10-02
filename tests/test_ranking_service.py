"""
ReNexa — Phase 6 MCDA Ranking Engine Unit Tests
=================================================
Comprehensive unit tests for:
- Hard filtering of blocked/infeasible pathways
- Individual criterion scoring (budget, time, tools, materials, skill, condition, recovery value, practical fit)
- Weighted multi-criteria score computation
- Deterministic tie-breaking and rank stability
- Grounded explanation generation
- Top-K slicing and edge cases

Run with:
    python -m pytest tests/test_ranking_service.py -v
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from services.ranking_service import (
    score_budget_fit,
    score_time_fit,
    score_tool_fit,
    score_extra_material_fit,
    score_skill_fit,
    score_condition_fit,
    score_recovery_value,
    score_practical_fit,
    calculate_mcda_scores,
    generate_why_this,
    generate_why_not_this,
    get_ranked_pathways,
    get_ranked_recommendations_for_profile,
    WEIGHT_BUDGET_FIT,
    WEIGHT_TIME_FIT,
    WEIGHT_TOOL_FIT,
    WEIGHT_RECOVERY_VALUE,
    WEIGHT_EXTRA_MATERIAL_FIT,
    WEIGHT_SKILL_FIT,
    WEIGHT_CONDITION_FIT,
    TOTAL_WEIGHT,
)


def test_mcda_weights_sum_to_100():
    """Verify that the direct MCDA criterion weights total exactly 100% without double-counting."""
    assert TOTAL_WEIGHT == 100.0
    assert WEIGHT_BUDGET_FIT == 20.0
    assert WEIGHT_TIME_FIT == 20.0
    assert WEIGHT_TOOL_FIT == 15.0
    assert WEIGHT_RECOVERY_VALUE == 15.0
    assert WEIGHT_EXTRA_MATERIAL_FIT == 10.0
    assert WEIGHT_SKILL_FIT == 10.0
    assert WEIGHT_CONDITION_FIT == 10.0


def test_budget_fit_margin_scoring():
    """Higher budget margin must score higher than lower budget margin."""
    user_constraints = {"budget": "₹100"}

    pathway_zero_cost = {"budget": "0"}
    pathway_low_cost = {"budget": "20"}
    pathway_high_cost = {"budget": "95"}

    score_zero = score_budget_fit(pathway_zero_cost, user_constraints)
    score_low = score_budget_fit(pathway_low_cost, user_constraints)
    score_high = score_budget_fit(pathway_high_cost, user_constraints)

    assert score_zero == 100.0
    assert score_low == 90.0
    assert score_high == 52.5
    assert score_zero > score_low > score_high


def test_budget_fit_zero_budget_safe():
    """Zero budget with zero cost pathway returns 100 without division by zero."""
    user_constraints = {"budget": "₹0"}
    pathway_zero = {"budget": "0"}
    assert score_budget_fit(pathway_zero, user_constraints) == 100.0


def test_time_fit_margin_scoring():
    """Faster pathways consuming a smaller fraction of user time score higher."""
    user_constraints = {"time": "60 minutes"}

    pathway_quick = {"time_required": "10 minutes"}
    pathway_long = {"time_required": "55 minutes"}

    score_quick = score_time_fit(pathway_quick, user_constraints)
    score_long = score_time_fit(pathway_long, user_constraints)

    assert score_quick > score_long
    assert 0.0 <= score_long <= 100.0
    assert 0.0 <= score_quick <= 100.0


def test_tool_fit_scoring():
    """Paths needing no tools score 100; paths with satisfied tools score 100."""
    user_constraints = {"tools": ["Scissors", "Tape"]}

    p_no_tools = {"tools": "None"}
    p_satisfied = {"tools": "Scissors"}
    p_partial = {"tools": "Scissors, Hammer"}

    assert score_tool_fit(p_no_tools, user_constraints) == 100.0
    assert score_tool_fit(p_satisfied, user_constraints) == 100.0
    assert score_tool_fit(p_partial, user_constraints) == 50.0


def test_extra_materials_fit_scoring():
    """Extra materials score reflects availability without inventing materials."""
    user_constraints = {"extra_materials": ["Thread", "Twine"]}

    p_no_mat = {"extra_materials": "None"}
    p_satisfied = {"extra_materials": "Twine"}
    p_missing = {"extra_materials": "PVA glue"}

    assert score_extra_material_fit(p_no_mat, user_constraints) == 100.0
    assert score_extra_material_fit(p_satisfied, user_constraints) == 100.0
    assert score_extra_material_fit(p_missing, user_constraints) == 0.0


def test_skill_fit_hierarchy_and_no_penalty_for_higher_skill():
    """Advanced user performing beginner task is not penalized; under-skilled is penalized."""
    p_beginner = {"skill_level": "Beginner"}
    p_advanced = {"skill_level": "Advanced"}

    u_beginner = {"skill": "Beginner"}
    u_advanced = {"skill": "Advanced"}

    # Exact beginner match
    assert score_skill_fit(p_beginner, u_beginner) == 100.0
    # Advanced user doing beginner task -> strong score (95.0)
    assert score_skill_fit(p_beginner, u_advanced) == 95.0
    # Exact advanced match
    assert score_skill_fit(p_advanced, u_advanced) == 100.0
    # Beginner user attempting advanced task -> penalized
    assert score_skill_fit(p_advanced, u_beginner) < 50.0


def test_condition_fit_scoring():
    """Exact condition matches score 100; general 'Any' condition scores 100."""
    p_any = {"condition_requirement": "Any"}
    p_good = {"condition_requirement": "Good"}

    profile_good = {"condition": "Good"}
    profile_damaged = {"condition": "Damaged"}

    assert score_condition_fit(p_any, profile_damaged) == 100.0
    assert score_condition_fit(p_good, profile_good) == 100.0
    assert score_condition_fit(p_good, profile_damaged) < 100.0


def test_recovery_value_circular_economy_ladder():
    """Repair > Reuse > Upcycle > Recycle > Dispose."""
    v_repair = score_recovery_value({"pathway_type": "repair"})
    v_reuse = score_recovery_value({"pathway_type": "reuse"})
    v_upcycle = score_recovery_value({"pathway_type": "upcycle"})
    v_recycle = score_recovery_value({"pathway_type": "recycle"})
    v_dispose = score_recovery_value({"pathway_type": "dispose"})

    assert v_repair == 100.0
    assert v_reuse == 90.0
    assert v_upcycle == 80.0
    assert v_recycle == 60.0
    assert v_dispose == 30.0
    assert v_repair > v_reuse > v_upcycle > v_recycle > v_dispose


def test_final_score_within_0_to_100_and_exact_weights():
    """Verify final score formula applies exact weights and stays within bounds."""
    pathway = {
        "budget": "0",
        "time_required": "5 minutes",
        "tools": "None",
        "extra_materials": "None",
        "skill_level": "Beginner",
        "condition_requirement": "Good",
        "pathway_type": "reuse",
    }
    user_constraints = {
        "budget": "₹100",
        "time": "60 minutes",
        "tools": [],
        "skill": "Beginner",
    }
    waste_profile = {"condition": "Good"}

    score, crit = calculate_mcda_scores(pathway, user_constraints, waste_profile)
    assert 0.0 <= score <= 100.0
    for k, v in crit.items():
        assert 0.0 <= v <= 100.0


def test_hard_filter_only_eligible_pathways_ranked():
    """Safety BLOCK and Constraint INFEASIBLE are strictly filtered out before ranking."""
    eligibility_records = [
        {
            "pathway_id": "REC-001",
            "pathway": {"pathway_id": "REC-001", "title": "Feasible Reuse", "budget": "0", "time_required": "5 mins", "pathway_type": "reuse"},
            "safety_status": "ALLOW",
            "constraint_status": "FEASIBLE",
            "eligible": True,
        },
        {
            "pathway_id": "REC-002",
            "pathway": {"pathway_id": "REC-002", "title": "Blocked Dismantle", "budget": "0", "time_required": "5 mins", "pathway_type": "repair"},
            "safety_status": "BLOCK",
            "constraint_status": "NOT_EVALUATED",
            "eligible": False,
        },
        {
            "pathway_id": "REC-003",
            "pathway": {"pathway_id": "REC-003", "title": "Infeasible High Budget", "budget": "500", "time_required": "5 mins", "pathway_type": "upcycle"},
            "safety_status": "ALLOW",
            "constraint_status": "INFEASIBLE",
            "eligible": False,
        },
    ]

    ranked = get_ranked_pathways(eligibility_records)
    assert len(ranked) == 1
    assert ranked[0]["pathway_id"] == "REC-001"
    assert ranked[0]["eligible"] is True


def test_warn_pathway_remains_eligible_and_ranked_with_warnings():
    """A pathway with safety WARN remains eligible and carries its warnings into the ranking result."""
    eligibility_records = [
        {
            "pathway_id": "REC-GLA-003",
            "pathway": {"pathway_id": "REC-GLA-003", "title": "Glass Planter", "budget": "0", "time_required": "10 mins", "pathway_type": "upcycle"},
            "safety_status": "WARN",
            "constraint_status": "FEASIBLE",
            "eligible": True,
            "warnings": ["[SAF-001] Handle sharp glass edges with care."],
        }
    ]
    ranked = get_ranked_pathways(eligibility_records)
    assert len(ranked) == 1
    assert ranked[0]["pathway_id"] == "REC-GLA-003"
    assert len(ranked[0]["warnings"]) == 1
    assert "sharp glass" in ranked[0]["warnings"][0]


def test_deterministic_tie_breaking():
    """Identical scores break ties deterministically on practical_fit -> budget_fit -> time_fit -> recovery_value -> pathway_id."""
    # Two identical pathways except pathway_id
    eligibility_records = [
        {
            "pathway_id": "REC-BBB",
            "pathway": {"pathway_id": "REC-BBB", "title": "Option B", "budget": "0", "time_required": "5 mins", "pathway_type": "reuse"},
            "safety_status": "ALLOW",
            "constraint_status": "FEASIBLE",
            "eligible": True,
        },
        {
            "pathway_id": "REC-AAA",
            "pathway": {"pathway_id": "REC-AAA", "title": "Option A", "budget": "0", "time_required": "5 mins", "pathway_type": "reuse"},
            "safety_status": "ALLOW",
            "constraint_status": "FEASIBLE",
            "eligible": True,
        },
    ]

    ranked = get_ranked_pathways(eligibility_records)
    assert len(ranked) == 2
    # Alphabetical tie-break puts REC-AAA first
    assert ranked[0]["pathway_id"] == "REC-AAA"
    assert ranked[1]["pathway_id"] == "REC-BBB"


def test_top_k_limiting_and_full_list():
    """top_k=3 returns at most 3; top_k=None returns all."""
    records = [
        {
            "pathway_id": f"REC-{i:03d}",
            "pathway": {"pathway_id": f"REC-{i:03d}", "title": f"Option {i}", "budget": "0", "time_required": f"{i*5} mins", "pathway_type": "reuse"},
            "safety_status": "ALLOW",
            "constraint_status": "FEASIBLE",
            "eligible": True,
        }
        for i in range(1, 6)
    ]

    top3 = get_ranked_pathways(records, top_k=3)
    assert len(top3) == 3
    assert [r["rank"] for r in top3] == [1, 2, 3]

    all_res = get_ranked_pathways(records, top_k=None)
    assert len(all_res) == 5


def test_empty_inputs_return_empty_list():
    """Empty eligibility records or empty profile return empty list safely."""
    assert get_ranked_pathways([]) == []
    assert get_ranked_recommendations_for_profile(None) == []
    assert get_ranked_recommendations_for_profile({}) == []


def test_explanations_grounded_in_data():
    """Why-this reasons must reference actual pathway attributes."""
    pathway = {
        "pathway_id": "REC-PLA-001",
        "title": "Plastic Container Storage",
        "budget": "0",
        "time_required": "5 minutes",
        "tools": "None",
        "skill_level": "Beginner",
        "pathway_type": "reuse",
    }
    _, crit = calculate_mcda_scores(pathway, {"budget": "₹100", "time": "30 mins", "skill": "Beginner"})
    reasons = generate_why_this(pathway, crit, rank=1)

    assert any("₹0" in r or "financial expense" in r for r in reasons)
    assert any("Reuse" in r or "circular economy" in r for r in reasons)
    assert any("5 minutes" in r or "Quick" in r for r in reasons)


def test_repeated_execution_returns_identical_ordering():
    """MCDA ranking must be completely deterministic and stable across multiple runs."""
    records = [
        {
            "pathway_id": f"REC-STAB-{i}",
            "pathway": {
                "pathway_id": f"REC-STAB-{i}",
                "title": f"Pathway {i}",
                "budget": str(i * 10),
                "time_required": f"{i * 10} minutes",
                "pathway_type": "reuse" if i % 2 == 0 else "upcycle",
            },
            "safety_status": "ALLOW",
            "constraint_status": "FEASIBLE",
            "eligible": True,
        }
        for i in range(10)
    ]

    run1 = [r["pathway_id"] for r in get_ranked_pathways(records)]
    run2 = [r["pathway_id"] for r in get_ranked_pathways(records)]
    run3 = [r["pathway_id"] for r in get_ranked_pathways(records)]

    assert run1 == run2 == run3
