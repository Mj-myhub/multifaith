"""Slice results by language and by linguistic phenomenon.

The whole argument of this project is that a single aggregate number hides the
thing that matters: models and automated judges behave differently across
languages, and they fail in linguistically specific ways. This module turns a
flat list of judgments into the grouped tables that make that visible.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from ..types import EvalItem, Judgment, Label
from . import metrics


def _index_gold(items: list[EvalItem]) -> dict[str, EvalItem]:
    return {it.id: it for it in items}


def judge_vs_human_by_language(
    items: list[EvalItem],
    judgments: list[Judgment],
    positive: Label = Label.UNGROUNDED,
) -> dict[str, dict[str, float]]:
    """For one scorer, compare its labels to the human gold labels, per language.

    Returns a dict keyed by language, each value holding agreement, kappa, and
    precision/recall/F1 on the `positive` class. Items without a gold label are
    skipped, so this only reports on the hand-annotated set.
    """
    gold_index = _index_gold(items)
    by_lang_gold: dict[str, list[Label]] = defaultdict(list)
    by_lang_pred: dict[str, list[Label]] = defaultdict(list)

    for j in judgments:
        item = gold_index.get(j.item_id)
        if item is None or item.gold_label is None:
            continue
        lang = item.language
        by_lang_gold[lang].append(item.gold_label)
        by_lang_pred[lang].append(j.label)

    out: dict[str, dict[str, float]] = {}
    for lang in sorted(by_lang_gold):
        g, p = by_lang_gold[lang], by_lang_pred[lang]
        prf = metrics.precision_recall_f1(g, p, positive)
        out[lang] = {
            "n": float(len(g)),
            "agreement": metrics.agreement_rate(g, p),
            "cohen_kappa": metrics.cohen_kappa(g, p),
            "precision_ungrounded": prf["precision"],
            "recall_ungrounded": prf["recall"],
            "f1_ungrounded": prf["f1"],
            "macro_f1": metrics.macro_f1(g, p),
        }
    return out


def error_counts_by_phenomenon(
    items: list[EvalItem],
    judgments: list[Judgment],
    scorer: Optional[str] = None,
) -> dict[str, dict[str, int]]:
    """How often each scorer misses each phenomenon.

    For every item the human marked as not grounded and tagged with a phenomenon,
    count whether the scorer caught it (predicted not grounded) or missed it.
    This is the table that tells a linguist's story: maybe the judge catches
    number errors fine but is blind to negation flips in Persian.
    """
    gold_index = _index_gold(items)
    result: dict[str, dict[str, int]] = defaultdict(
        lambda: {"caught": 0, "missed": 0}
    )

    for j in judgments:
        if scorer is not None and j.scorer != scorer:
            continue
        item = gold_index.get(j.item_id)
        if item is None or item.gold_label is None:
            continue
        if item.gold_label == Label.GROUNDED:
            continue  # only interested in answers that should be flagged
        caught = j.label != Label.GROUNDED
        for ph in item.phenomena or ["untagged"]:
            result[ph]["caught" if caught else "missed"] += 1

    return dict(result)


def language_label_distribution(
    items: list[EvalItem], judgments: list[Judgment]
) -> dict[str, dict[str, float]]:
    """Distribution of predicted labels per language for one scorer's output."""
    gold_index = _index_gold(items)
    by_lang: dict[str, list[Label]] = defaultdict(list)
    for j in judgments:
        item = gold_index.get(j.item_id)
        lang = j.language or (item.language if item else "unknown")
        by_lang[lang].append(j.label)
    return {lang: metrics.label_distribution(labs) for lang, labs in by_lang.items()}
