"""The harness: run a set of scorers over a set of items and report.

This ties the pieces together. Given items and one or more scorers, it produces
all the judgments, then hands them to the analysis layer to build the per
language and per phenomenon tables. It does not know or care which scorers it is
running; that is the design that lets you drop in a new detection method and get
comparable numbers for free.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .analysis import breakdown
from .scorers.base import GroundednessScorer
from .types import EvalItem, Judgment, Label


@dataclass
class HarnessReport:
    """Everything one run produced, ready to serialise or print."""

    judgments: list[Judgment] = field(default_factory=list)
    # scorer name -> language -> metric dict
    judge_vs_human: dict[str, dict[str, dict[str, float]]] = field(default_factory=dict)
    # scorer name -> phenomenon -> {caught, missed}
    phenomenon_errors: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)


class Harness:
    def __init__(self, scorers: list[GroundednessScorer]) -> None:
        if not scorers:
            raise ValueError("Harness needs at least one scorer.")
        self.scorers = scorers

    def run(
        self, items: list[EvalItem], positive: Label = Label.UNGROUNDED
    ) -> HarnessReport:
        report = HarnessReport()

        for scorer in self.scorers:
            judgments = scorer.score_batch(items)
            report.judgments.extend(judgments)

            # Only items with a gold label contribute to these tables; the
            # breakdown functions already skip the rest.
            report.judge_vs_human[scorer.name] = breakdown.judge_vs_human_by_language(
                items, judgments, positive=positive
            )
            report.phenomenon_errors[scorer.name] = breakdown.error_counts_by_phenomenon(
                items, judgments, scorer=scorer.name
            )

        return report


def format_report(report: HarnessReport) -> str:
    """A plain-text summary suitable for stdout or a results/*.txt artifact."""
    lines: list[str] = []
    for scorer, by_lang in report.judge_vs_human.items():
        lines.append(f"\n=== {scorer} : judge vs human, per language ===")
        if not by_lang:
            lines.append("  (no gold-labelled items)")
            continue
        header = f"{'lang':<6}{'n':>5}{'agree':>8}{'kappa':>8}{'recall_ung':>12}{'macroF1':>9}"
        lines.append(header)
        for lang, m in by_lang.items():
            lines.append(
                f"{lang:<6}{int(m['n']):>5}{m['agreement']:>8.2f}"
                f"{m['cohen_kappa']:>8.2f}{m['recall_ungrounded']:>12.2f}"
                f"{m['macro_f1']:>9.2f}"
            )

    for scorer, by_phen in report.phenomenon_errors.items():
        if not by_phen:
            continue
        lines.append(f"\n=== {scorer} : missed errors by phenomenon ===")
        for phen, c in sorted(by_phen.items()):
            total = c["caught"] + c["missed"]
            rate = c["missed"] / total if total else 0.0
            lines.append(f"  {phen:<20} missed {c['missed']}/{total}  ({rate:.0%})")

    return "\n".join(lines) if lines else "(empty report)"
