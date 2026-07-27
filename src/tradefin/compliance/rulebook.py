"""
Load the paraphrased UCP 600 rulebook so findings can cite the rule they offend.

This is the deterministic, curated knowledge source. In a later step we can add
semantic retrieval (RAG) over a fuller rule corpus, but for coded checks a direct
article -> summary lookup is more precise than retrieval: each rule already knows
exactly which article it enforces.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# repo_root/data/rules/ucp600_summary.json  (this file is src/tradefin/compliance/)
_DEFAULT_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "rules" / "ucp600_summary.json"
)


@lru_cache(maxsize=1)
def load_rulebook(path: str | None = None) -> dict[str, dict]:
    """Load and cache the rulebook JSON."""
    p = Path(path) if path else _DEFAULT_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def get_rule(key: str) -> dict:
    """Return {'article', 'title', 'summary'} for a rule key like 'art_18'."""
    rulebook = load_rulebook()
    if key not in rulebook:
        raise KeyError(f"Unknown UCP rule key: {key!r}")
    return rulebook[key]
