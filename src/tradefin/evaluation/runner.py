"""
Build a labelled evaluation set and score the compliance engine on it.

By default we evaluate the *deterministic compliance engine* on ground-truth
documents. That isolates the engine's reasoning from LLM extraction noise: it
answers "given correctly-read documents, does the engine flag the right
discrepancies?". (Extraction accuracy against a live LLM is a separate, harder
evaluation that needs a model + RAM; this harness is structured so that a
pipeline-based predictor could be dropped in later.)
"""

from __future__ import annotations

import random

from tradefin.compliance import check_case
from tradefin.evaluation.metrics import EvalReport, evaluate_predictions
from tradefin.generation import Discrepancy, build_case

ALL_CODES = [d.value for d in Discrepancy]


def build_eval_cases(n: int = 60, seed: int = 2024):
    """Deterministically build n cases with a mix of clean and flawed ones."""
    rng = random.Random(seed)
    all_discrepancies = list(Discrepancy)
    cases = []
    for _ in range(n):
        case_seed = rng.randrange(1, 99999)
        if rng.random() < 0.5:
            discrepancies = []
        else:
            k = rng.choice([1, 1, 2])  # bias toward a single discrepancy
            discrepancies = rng.sample(all_discrepancies, k)
        cases.append(build_case(case_seed, discrepancies))
    return cases


def evaluate_engine(n: int = 60, seed: int = 2024) -> EvalReport:
    """Run the deterministic engine over a labelled set and return metrics."""
    cases = build_eval_cases(n=n, seed=seed)
    golds = [set(c.injected_discrepancies) for c in cases]
    preds = [check_case(c).codes for c in cases]
    return evaluate_predictions(golds, preds, ALL_CODES)
