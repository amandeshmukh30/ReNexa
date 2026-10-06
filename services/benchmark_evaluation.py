"""
ReNexa — Benchmark Evaluation Service
======================================
Computes empirical accuracy, classification reports, and confusion matrices
using scikit-learn for both:
1. ReNexa Decision Chain / Pathway Recommendation Benchmark (100 scenarios)
2. Computer Vision Waste Classification (YOLOv8 on test datasets)
"""

import os
import sys
from typing import Dict, Any, List, Optional
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.ranking_service import get_ranked_recommendations_for_profile
from tests.test_phase6_benchmark import generate_100_independent_scenarios


def evaluate_benchmarks() -> Dict[str, Any]:
    """
    Evaluate the 100 independently validated benchmark scenarios across
    multiple waste categories (battery, biological, cardboard, clothes, glass, metal, paper, plastic).
    
    Returns:
        dict containing:
            - "overall_accuracy": float
            - "classification_report": dict (from sklearn classification_report)
            - "classification_report_str": formatted text representation
            - "confusion_matrix": 2D list
            - "classes": list of unique classes
            - "by_category": dict of per-material performance
            - "raw_results": list of per-scenario predictions
    """
    scenarios = generate_100_independent_scenarios()
    
    results = []
    y_true = []
    y_pred = []
    categories = []
    
    for sc in scenarios:
        ranked = get_ranked_recommendations_for_profile(
            waste_profile=sc["waste_profile"],
            user_constraints=sc["user_constraints"],
            top_k=3,
        )
        predicted_top1 = ranked[0]["pathway_id"] if ranked else "NONE"
        expected_top1 = sc["expected_top1"]
        material = sc["waste_profile"]["material"]
        
        y_true.append(expected_top1)
        y_pred.append(predicted_top1)
        categories.append(material)
        
        results.append({
            "scenario_id": sc["id"],
            "material": material,
            "ground_truth_type": sc["ground_truth_type"],
            "expected_pathway": expected_top1,
            "predicted_pathway": predicted_top1,
            "is_correct": expected_top1 == predicted_top1,
            "top3_predicted": [r["pathway_id"] for r in ranked[:3]]
        })
        
    unique_classes = sorted(list(set(y_true + y_pred)))
    
    # ── Global Sklearn Metrics ────────────────────────────────────────────────
    overall_acc = float(accuracy_score(y_true, y_pred))
    report_dict = classification_report(y_true, y_pred, labels=unique_classes, output_dict=True, zero_division=0)
    report_text = classification_report(y_true, y_pred, labels=unique_classes, zero_division=0)
    conf_matrix = confusion_matrix(y_true, y_pred, labels=unique_classes).tolist()
    
    # ── Breakdown per material category ───────────────────────────────────────
    metrics_by_material = {}
    for mat in sorted(list(set(categories))):
        mat_indices = [i for i, c in enumerate(categories) if c == mat]
        mat_true = [y_true[i] for i in mat_indices]
        mat_pred = [y_pred[i] for i in mat_indices]
        
        mat_acc = float(accuracy_score(mat_true, mat_pred))
        mat_report = classification_report(mat_true, mat_pred, output_dict=True, zero_division=0)
        
        metrics_by_material[mat] = {
            "samples": len(mat_indices),
            "accuracy": mat_acc,
            "report": mat_report
        }
        
    return {
        "overall_accuracy": overall_acc,
        "classification_report": report_dict,
        "classification_report_str": report_text,
        "confusion_matrix": conf_matrix,
        "classes": unique_classes,
        "by_category": metrics_by_material,
        "raw_results": results,
    }


if __name__ == "__main__":
    metrics = evaluate_benchmarks()
    print("=" * 68)
    print(f"ReNexa Benchmark Evaluation (scikit-learn)")
    print(f"Overall Accuracy: {metrics['overall_accuracy']:.4f} ({metrics['overall_accuracy']*100:.2f}%)")
    print("=" * 68)
    print("\nClassification Report (per Recovery Pathway):")
    print(metrics["classification_report_str"])
    print("\nPerformance by Waste Material:")
    for mat, info in metrics["by_category"].items():
        print(f"  - {mat.capitalize():<12}: Samples={info['samples']:<2} | Accuracy={info['accuracy']*100:.1f}%")
