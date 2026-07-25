"""
Generate a synthetic dataset of trade-finance cases.

Usage:
    python scripts/generate_data.py --n 12 --out data/synthetic

Produces, per case, a folder with three PDFs + ground_truth.json. Roughly half
the cases are fully compliant; the rest have 1-2 injected discrepancies, chosen
deterministically so the dataset is reproducible.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from tradefin.generation import Discrepancy, build_case
from tradefin.generation.render import render_case

ALL_DISCREPANCIES = list(Discrepancy)


def choose_discrepancies(rng: random.Random) -> list[Discrepancy]:
    """~50% compliant; otherwise 1-2 distinct random discrepancies."""
    if rng.random() < 0.5:
        return []
    k = rng.choice([1, 1, 2])  # bias toward a single discrepancy
    return rng.sample(ALL_DISCREPANCIES, k)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic trade-finance cases.")
    parser.add_argument("--n", type=int, default=12, help="number of cases")
    parser.add_argument("--out", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--seed", type=int, default=42, help="master seed for reproducibility")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    master = random.Random(args.seed)

    summary = []
    for i in range(args.n):
        case_seed = master.randrange(1, 99999)
        discrepancies = choose_discrepancies(master)
        case = build_case(case_seed, discrepancies)
        render_case(case, args.out)
        summary.append((case.case_id, [d.value for d in discrepancies]))

    print(f"Generated {args.n} cases in {args.out}\n")
    for case_id, discs in summary:
        label = "COMPLIANT" if not discs else ", ".join(discs)
        print(f"  {case_id}: {label}")


if __name__ == "__main__":
    main()
