"""Evaluation harness: precision/recall/F1 for discrepancy detection (Module 8)."""

from tradefin.evaluation.metrics import (
    CodeMetrics,
    EvalReport,
    evaluate_predictions,
)
from tradefin.evaluation.runner import build_eval_cases, evaluate_engine

__all__ = [
    "CodeMetrics",
    "EvalReport",
    "evaluate_predictions",
    "build_eval_cases",
    "evaluate_engine",
]
