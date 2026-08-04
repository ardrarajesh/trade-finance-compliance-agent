"""Tests for the evaluation harness (Module 8)."""

from tradefin.evaluation import evaluate_engine, evaluate_predictions


def test_metric_math_on_a_hand_computed_example():
    # Codes A, B, C. Three cases:
    #   case1: gold {A}   pred {A}     -> A: TP
    #   case2: gold {A,B} pred {B}     -> A: FN, B: TP
    #   case3: gold {}    pred {A}     -> A: FP
    golds = [{"A"}, {"A", "B"}, set()]
    preds = [{"A"}, {"B"}, {"A"}]
    report = evaluate_predictions(golds, preds, ["A", "B", "C"])

    a = report.per_code["A"]
    assert (a.tp, a.fp, a.fn) == (1, 1, 1)
    assert a.precision == 0.5
    assert a.recall == 0.5

    b = report.per_code["B"]
    assert (b.tp, b.fp, b.fn) == (1, 0, 0)
    assert b.precision == 1.0 and b.recall == 1.0

    c = report.per_code["C"]
    assert (c.tp, c.fp, c.fn) == (0, 0, 0)
    assert c.f1 == 0.0  # never seen -> zero, not a crash

    # Only case1 matched exactly.
    assert report.exact_matches == 1
    assert report.n_cases == 3


def test_engine_scores_perfectly_on_synthetic_labels():
    # The deterministic engine should perfectly recover the injected labels.
    report = evaluate_engine(n=80, seed=2024)
    assert report.micro_recall == 1.0
    assert report.micro_precision == 1.0
    assert report.exact_match_accuracy == 1.0
