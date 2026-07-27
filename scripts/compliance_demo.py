"""
Show a human-readable compliance audit report for a generated case.

This runs the deterministic engine directly on ground-truth objects (no LLM, no
RAM), so it always works. Example:

  python scripts\\compliance_demo.py --seed 5 --discrepancies AMOUNT_OVER_LC PORT_MISMATCH
"""

from __future__ import annotations

import argparse

from tradefin.compliance import check_case
from tradefin.generation import Discrepancy, build_case


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=5)
    parser.add_argument(
        "--discrepancies",
        nargs="*",
        default=["AMOUNT_OVER_LC", "PORT_MISMATCH"],
        help="discrepancy codes to inject (empty for a clean case)",
    )
    args = parser.parse_args()

    discs = [Discrepancy(code) for code in args.discrepancies]
    case = build_case(seed=args.seed, discrepancies=discs)
    report = check_case(case)

    print("=" * 70)
    print(f"COMPLIANCE AUDIT REPORT  --  {case.case_id}")
    print("=" * 70)
    print(f"LC {case.letter_of_credit.lc_number} | "
          f"beneficiary: {case.letter_of_credit.beneficiary.name}")
    print(f"Result: {'COMPLIANT' if report.is_compliant else 'DISCREPANCIES FOUND'}")
    print(f"Findings: {len(report.findings)}\n")

    for i, f in enumerate(report.findings, 1):
        print(f"[{i}] {f.title}  ({f.code})")
        print(f"    {f.detail}")
        print(f"    Cited: {f.ucp_article} - {f.ucp_summary[:80]}...")
        print()


if __name__ == "__main__":
    main()
