"""
Evaluate the compliance engine on a labelled synthetic set and print metrics.

  python scripts\\evaluate.py --n 100
"""

from __future__ import annotations

import argparse

from tradefin.evaluation import evaluate_engine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="number of eval cases")
    parser.add_argument("--seed", type=int, default=2024)
    args = parser.parse_args()

    report = evaluate_engine(n=args.n, seed=args.seed)

    print("=" * 68)
    print(f"COMPLIANCE ENGINE EVALUATION  ({report.n_cases} cases)")
    print("=" * 68)
    print(f"{'discrepancy code':<28}{'TP':>4}{'FP':>4}{'FN':>4}"
          f"{'prec':>7}{'rec':>7}{'F1':>7}")
    print("-" * 68)
    for code, m in report.per_code.items():
        print(f"{code:<28}{m.tp:>4}{m.fp:>4}{m.fn:>4}"
              f"{m.precision:>7.2f}{m.recall:>7.2f}{m.f1:>7.2f}")
    print("-" * 68)
    print(f"Micro precision: {report.micro_precision:.3f}   "
          f"Micro recall: {report.micro_recall:.3f}   "
          f"Micro F1: {report.micro_f1:.3f}")
    print(f"Macro F1: {report.macro_f1:.3f}   "
          f"Exact-match accuracy: {report.exact_match_accuracy:.3f}")


if __name__ == "__main__":
    main()
