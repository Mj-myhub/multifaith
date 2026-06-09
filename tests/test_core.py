"""Tests that must stay green.

These cover the parts that do not need a model: the metrics math, the JSONL
round-trip, and the harness wiring (using a trivial fake scorer). A green CI
badge on a repo about evaluation is not decoration; it is the first thing a
reviewer checks to see whether you eat your own dog food.

Run with: pytest -q
"""

from __future__ import annotations

from pathlib import Path

from multifaith import EvalItem, Harness, Label
from multifaith.analysis import metrics
from multifaith.data import load_items, save_items, save_judgments, load_judgments
from multifaith.scorers.base import GroundednessScorer
from multifaith.types import Judgment

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = REPO_ROOT / "data" / "gold" / "sample.jsonl"


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def test_accuracy_perfect_and_empty():
    g = [Label.GROUNDED, Label.UNGROUNDED]
    assert metrics.accuracy(g, g) == 1.0
    assert metrics.accuracy([], []) == 0.0


def test_precision_recall_f1():
    gold = [Label.UNGROUNDED, Label.UNGROUNDED, Label.GROUNDED, Label.GROUNDED]
    pred = [Label.UNGROUNDED, Label.GROUNDED, Label.GROUNDED, Label.UNGROUNDED]
    m = metrics.precision_recall_f1(gold, pred, Label.UNGROUNDED)
    # tp=1, fp=1, fn=1 -> precision = recall = 0.5, f1 = 0.5
    assert abs(m["precision"] - 0.5) < 1e-9
    assert abs(m["recall"] - 0.5) < 1e-9
    assert abs(m["f1"] - 0.5) < 1e-9
    assert m["support"] == 2


def test_cohen_kappa_bounds():
    a = [Label.GROUNDED, Label.UNGROUNDED, Label.GROUNDED, Label.UNGROUNDED]
    assert abs(metrics.cohen_kappa(a, a) - 1.0) < 1e-9  # perfect agreement
    b = [Label.UNGROUNDED, Label.GROUNDED, Label.UNGROUNDED, Label.GROUNDED]
    assert metrics.cohen_kappa(a, b) < 0.0  # systematic disagreement -> negative


def test_kappa_corrects_for_chance():
    # Both raters say GROUNDED almost always; raw agreement is high but kappa low.
    a = [Label.GROUNDED] * 9 + [Label.UNGROUNDED]
    b = [Label.GROUNDED] * 8 + [Label.UNGROUNDED, Label.GROUNDED]
    assert metrics.agreement_rate(a, b) >= 0.8
    assert metrics.cohen_kappa(a, b) < metrics.agreement_rate(a, b)


# --------------------------------------------------------------------------- #
# data round-trip
# --------------------------------------------------------------------------- #
def test_sample_loads():
    items = load_items(SAMPLE)
    assert len(items) >= 9
    langs = {it.language for it in items}
    assert {"en", "it", "fa"} <= langs
    assert all(it.gold_label is not None for it in items)


def test_jsonl_round_trip(tmp_path):
    items = load_items(SAMPLE)
    out = tmp_path / "rt.jsonl"
    save_items(items, out)
    reloaded = load_items(out)
    assert [i.to_dict() for i in items] == [i.to_dict() for i in reloaded]


# --------------------------------------------------------------------------- #
# harness wiring with a deterministic fake scorer
# --------------------------------------------------------------------------- #
class AlwaysGrounded(GroundednessScorer):
    name = "always_grounded"

    def score_item(self, item: EvalItem) -> Judgment:
        return Judgment(
            item_id=item.id, scorer=self.name, label=Label.GROUNDED,
            language=item.language,
        )


def test_harness_runs_and_reports():
    items = load_items(SAMPLE)
    report = Harness([AlwaysGrounded()]).run(items)
    assert len(report.judgments) == len(items)
    table = report.judge_vs_human["always_grounded"]
    # Every language the gold set covers should appear.
    assert {"en", "it", "fa"} <= set(table)
    # A scorer that calls everything grounded misses every real error, so its
    # recall on UNGROUNDED must be 0 wherever there are ungrounded gold items.
    assert table["fa"]["recall_ungrounded"] == 0.0


def test_phenomenon_breakdown_counts_misses():
    items = load_items(SAMPLE)
    report = Harness([AlwaysGrounded()]).run(items)
    by_phen = report.phenomenon_errors["always_grounded"]
    # number_error appears in the gold set and must be recorded as missed here.
    assert by_phen["number_error"]["missed"] >= 1
    assert by_phen["number_error"]["caught"] == 0


def test_judgment_round_trip(tmp_path):
    items = load_items(SAMPLE)
    judgments = AlwaysGrounded().score_batch(items)
    out = tmp_path / "j.jsonl"
    save_judgments(judgments, out)
    assert len(load_judgments(out)) == len(judgments)
