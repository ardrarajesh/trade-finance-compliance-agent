"""
Evaluation metrics for discrepancy detection.

We treat each case as a MULTI-LABEL classification problem: the "labels" are the
discrepancy codes, and both the ground truth and the prediction are *sets* of
codes. For each code we count:

    TP  code was injected AND detected
    FP  code was detected but NOT injected   (a false alarm)
    FN  code was injected but NOT detected    (a miss)

From those we derive precision, recall and F1 -- per code and aggregated. We
also report exact-match accuracy: the fraction of cases whose predicted set of
codes equals the injected set exactly.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


def _safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


@dataclass
class CodeMetrics:
    code: str
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return _safe_div(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float:
        return _safe_div(self.tp, self.tp + self.fn)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return _safe_div(2 * p * r, p + r) if (p + r) else 0.0


@dataclass
class EvalReport:
    per_code: dict[str, CodeMetrics]
    n_cases: int
    exact_matches: int

    @property
    def exact_match_accuracy(self) -> float:
        return _safe_div(self.exact_matches, self.n_cases)

    # ---- micro (pool all codes together) ----
    @property
    def micro_precision(self) -> float:
        tp = sum(m.tp for m in self.per_code.values())
        fp = sum(m.fp for m in self.per_code.values())
        return _safe_div(tp, tp + fp)

    @property
    def micro_recall(self) -> float:
        tp = sum(m.tp for m in self.per_code.values())
        fn = sum(m.fn for m in self.per_code.values())
        return _safe_div(tp, tp + fn)

    @property
    def micro_f1(self) -> float:
        p, r = self.micro_precision, self.micro_recall
        return _safe_div(2 * p * r, p + r) if (p + r) else 0.0

    # ---- macro (average the per-code metrics) ----
    @property
    def macro_f1(self) -> float:
        if not self.per_code:
            return 0.0
        return sum(m.f1 for m in self.per_code.values()) / len(self.per_code)


def evaluate_predictions(
    golds: list[set[str]],
    preds: list[set[str]],
    labels: Iterable[str],
) -> EvalReport:
    """Compare aligned lists of gold/predicted code sets and score them."""
    if len(golds) != len(preds):
        raise ValueError("golds and preds must be the same length")

    per_code = {label: CodeMetrics(code=label) for label in labels}

    exact = 0
    for gold, pred in zip(golds, preds):
        if gold == pred:
            exact += 1
        for label, m in per_code.items():
            in_gold = label in gold
            in_pred = label in pred
            if in_gold and in_pred:
                m.tp += 1
            elif in_pred and not in_gold:
                m.fp += 1
            elif in_gold and not in_pred:
                m.fn += 1

    return EvalReport(per_code=per_code, n_cases=len(golds), exact_matches=exact)
