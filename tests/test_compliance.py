"""Tests for the compliance engine (Module 5).

The strong test: the engine's findings must exactly match the discrepancies we
injected when generating each case. That is precision AND recall in one line.
"""

from tradefin.compliance import check_case
from tradefin.generation import Discrepancy, build_case

ALL_DISCREPANCIES = list(Discrepancy)


def test_compliant_cases_have_no_findings():
    for seed in range(1, 15):
        report = check_case(build_case(seed=seed))
        assert report.is_compliant, f"seed {seed} wrongly flagged: {report.codes}"


def test_each_injected_discrepancy_is_detected_exactly():
    # For every discrepancy type, the engine should report that code and no
    # others (no false positives, no misses).
    for discrepancy in ALL_DISCREPANCIES:
        case = build_case(seed=5, discrepancies=[discrepancy])
        report = check_case(case)
        assert report.codes == {discrepancy.value}, (
            f"{discrepancy.value}: engine reported {report.codes}"
        )


def test_multiple_discrepancies_detected_together():
    case = build_case(
        seed=9,
        discrepancies=[Discrepancy.AMOUNT_OVER_LC, Discrepancy.PORT_MISMATCH],
    )
    report = check_case(case)
    assert report.codes == {"AMOUNT_OVER_LC", "PORT_MISMATCH"}
    assert not report.is_compliant


def test_findings_carry_a_ucp_citation():
    case = build_case(seed=3, discrepancies=[Discrepancy.GOODS_DESCRIPTION_MISMATCH])
    finding = check_case(case).findings[0]
    assert finding.ucp_article.startswith("UCP 600 Article")
    assert len(finding.ucp_summary) > 0
    assert finding.detail  # a specific, human-readable explanation


def test_report_codes_across_all_generated_labels():
    # A broader sweep: many seeds, one random discrepancy each.
    for seed in range(20, 40):
        discrepancy = ALL_DISCREPANCIES[seed % len(ALL_DISCREPANCIES)]
        case = build_case(seed=seed, discrepancies=[discrepancy])
        assert discrepancy.value in check_case(case).codes
