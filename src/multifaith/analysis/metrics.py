"""Evaluation metrics, implemented in plain Python on purpose.

There is a temptation to import scikit-learn for precision, recall, and Cohen's
kappa. I wrote them by hand here for two reasons. First, it keeps the core
package installable with no scientific stack, so the test suite runs in a second
on any machine. Second, in an interview you will be asked how kappa is computed
and what it corrects for. Writing it yourself means you can answer.

All functions take lists of `Label` and return floats or small dicts. None of
them call a model or touch the network.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from ..types import Label


def _check_equal_length(a: list, b: list) -> None:
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} vs {len(b)}")


def accuracy(gold: list[Label], pred: list[Label]) -> float:
    _check_equal_length(gold, pred)
    if not gold:
        return 0.0
    correct = sum(1 for g, p in zip(gold, pred) if g == p)
    return correct / len(gold)


def confusion_counts(
    gold: list[Label], pred: list[Label], positive: Label
) -> tuple[int, int, int, int]:
    """Return (tp, fp, fn, tn) treating `positive` as the class of interest.

    For hallucination work the class of interest is usually UNGROUNDED: you care
    most about catching the bad answers, so recall on UNGROUNDED is the number a
    risk owner will look at first.
    """
    _check_equal_length(gold, pred)
    tp = fp = fn = tn = 0
    for g, p in zip(gold, pred):
        if p == positive and g == positive:
            tp += 1
        elif p == positive and g != positive:
            fp += 1
        elif p != positive and g == positive:
            fn += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def precision_recall_f1(
    gold: list[Label], pred: list[Label], positive: Label
) -> dict[str, float]:
    tp, fp, fn, _ = confusion_counts(gold, pred, positive)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}


def macro_f1(gold: list[Label], pred: list[Label]) -> float:
    labels = list(Label)
    scores = [precision_recall_f1(gold, pred, lab)["f1"] for lab in labels]
    return sum(scores) / len(scores) if scores else 0.0


def cohen_kappa(a: list[Label], b: list[Label]) -> float:
    """Cohen's kappa between two raters (or a rater and a model).

    Kappa corrects raw agreement for the agreement you would expect by chance.
    A value near 0 means the scorer is no better than guessing the base rate;
    1.0 is perfect agreement. This is the headline number for the "can the judge
    judge?" experiment: it tells you whether an automated judge actually tracks
    human judgement in a given language, or just happens to share its prior.
    """
    _check_equal_length(a, b)
    n = len(a)
    if n == 0:
        return 0.0

    observed = sum(1 for x, y in zip(a, b) if x == y) / n

    count_a = Counter(a)
    count_b = Counter(b)
    labels = set(count_a) | set(count_b)
    expected = sum((count_a[lab] / n) * (count_b[lab] / n) for lab in labels)

    if expected == 1.0:
        # Both raters used a single label for everything; agreement is trivial.
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def agreement_rate(a: list[Label], b: list[Label]) -> float:
    """Raw fraction of items where two raters gave the same label."""
    return accuracy(a, b)


def label_distribution(labels: Iterable[Label]) -> dict[str, float]:
    labels = list(labels)
    n = len(labels)
    if n == 0:
        return {}
    counts = Counter(labels)
    return {lab.value: counts.get(lab, 0) / n for lab in Label}
