"""
ReNexa — Phase 8 Deterministic Outcome Benchmark Suite (50 Scenarios)
======================================================================
Evaluates the mathematical correctness and robustness of Phase 8
Outcome Analytics across 50 software validation benchmark test records.

Note:
These records are software/outcome-validation test cases used to verify the
analytics engine; they are not fabricated claims of real-world human performance.

Evaluates:
- Success and attempt counts
- Recovery Execution Success Rate (RESR)
- Partial Success Rate
- Failure Rate
- Resource Completeness Rate
- Safety Incident Rate
- Mean Absolute Time Error (MAE)
- Outcome-Validated Recipe Reliability (OVRR)
- Failure Reason Breakdown
- Per-Pathway Diagnostic Aggregations
"""

import sys
import os
import json
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.outcome_service import (
    load_outcome_feedback,
    calculate_outcome_metrics,
    summarize_failure_reasons,
    analyze_pathway_outcomes,
)

BENCHMARK_JSON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "phase8_benchmark.json")
)


def test_phase8_benchmark_execution():
    """
    Execute mathematical analytics benchmark across 50 deterministic validation records.
    Verifies 100% calculation accuracy against ground-truth mathematical derivations.
    """
    assert os.path.isfile(BENCHMARK_JSON_PATH), f"Benchmark file missing at: {BENCHMARK_JSON_PATH}"

    records = load_outcome_feedback(file_path=BENCHMARK_JSON_PATH)
    assert len(records) == 50, f"Expected exactly 50 benchmark records, got {len(records)}"

    metrics = calculate_outcome_metrics(records)

    # 1. Total counts
    assert metrics["total_recorded"] == 50
    assert metrics["not_attempted_count"] == 4
    assert metrics["total_attempted"] == 46
    assert metrics["successful_count"] == 30
    assert metrics["partial_count"] == 10
    assert metrics["failed_count"] == 6

    # 2. Key Outcome Feasibility Rates
    # RESR = 30 / 46 * 100 = 65.22%
    assert metrics["resr"] == pytest.approx(65.22, 0.01)

    # Partial Rate = 10 / 46 * 100 = 21.74%
    assert metrics["partial_rate"] == pytest.approx(21.74, 0.01)

    # Failure Rate = 6 / 46 * 100 = 13.04%
    assert metrics["failure_rate"] == pytest.approx(13.04, 0.01)

    # Resource Completeness Rate = 38 / 46 * 100 = 82.61%
    assert metrics["resource_completeness_rate"] == pytest.approx(82.61, 0.01)

    # Safety Issue Rate = 2 / 46 * 100 = 4.35%
    assert metrics["safety_issue_rate"] == pytest.approx(4.35, 0.01)

    # OVRR = 30 / 46 * 100 = 65.22%
    assert metrics["ovrr"] == pytest.approx(65.22, 0.01)

    # 3. Time MAE
    # Sum of abs diffs = 112 mins across 46 evaluated records -> MAE = 112 / 46 = 2.43 mins
    assert metrics["time_evaluated_count"] == 46
    assert metrics["time_mae"] == pytest.approx(2.43, 0.01)

    # 4. Failure Reason Breakdown
    failure_reasons = summarize_failure_reasons(records)
    assert failure_reasons["missing_tool"] == 4  # 034, 039 (partial), 041, 042 (failed) -> explicit reason/tools
    assert failure_reasons["missing_material"] == 4  # 031, 033, 035, 036
    assert failure_reasons["safety_issue"] == 2  # 043, 044
    assert failure_reasons["time_underestimated"] == 1  # 032
    assert failure_reasons["condition_problem"] == 2  # 037, 045
    assert failure_reasons["instruction_problem"] == 2  # 038, 046
    assert failure_reasons["other"] == 1  # 040

    # 5. Per-Pathway Breakdown Table
    pathway_table = analyze_pathway_outcomes(records)
    assert len(pathway_table) > 10
    # Pathways are sorted by attempts descending
    assert pathway_table[0]["attempts"] >= pathway_table[-1]["attempts"]

    print(f"\n==================================================================")
    print(f"--- Phase 8 Outcome Analytics Benchmark ({len(records)} test records) ---")
    print(f"Total Recorded:              {metrics['total_recorded']}")
    print(f"Total Attempted:             {metrics['total_attempted']}")
    print(f"Execution Success (RESR):    {metrics['resr']:.2f}% ({metrics['successful_count']}/{metrics['total_attempted']})")
    print(f"Partial Completion Rate:     {metrics['partial_rate']:.2f}% ({metrics['partial_count']}/{metrics['total_attempted']})")
    print(f"Execution Failure Rate:      {metrics['failure_rate']:.2f}% ({metrics['failed_count']}/{metrics['total_attempted']})")
    print(f"Resource Completeness Rate:  {metrics['resource_completeness_rate']:.2f}%")
    print(f"Safety Incident Rate:        {metrics['safety_issue_rate']:.2f}%")
    print(f"Recipe Reliability (OVRR):   {metrics['ovrr']:.2f}%")
    print(f"Time Estimation MAE:         {metrics['time_mae']:.2f} minutes")
    print(f"==================================================================")
