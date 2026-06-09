"""A naive, dependency-free baseline scorer.

This exists so the repo produces real output the moment it is cloned, with no
API key and no model download. It is also an honest floor: any method worth
shipping has to beat lexical overlap plus a number check. If your LLM judge
cannot clear this bar in some language, that is a finding, not an embarrassment.

How it works, and where it is deliberately dumb:

- Numbers: every number that appears in the answer must also appear in the
  context, after normalising Persian and Arabic-Indic digits to ASCII. This
  catches `number_error` cheaply and is the one part that works across scripts.
- Overlap: the fraction of answer content tokens that appear in the context.
  Above an upper threshold it calls the answer grounded, below a lower threshold
  ungrounded, in between partial.

It will be fooled by negation flips, paraphrase, and unsupported claims that
reuse context vocabulary. That is the point of having better scorers to compare
against.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from ..types import EvalItem, Judgment, Label
from .base import GroundednessScorer

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Very small stop-token sets to stop trivial words inflating overlap. Kept short
# on purpose; this is a baseline, not a linguistics project on its own.
_STOP = {
    "en": {"the", "a", "an", "of", "for", "in", "on", "to", "was", "is", "and"},
    "it": {"il", "la", "lo", "le", "di", "del", "della", "per", "in", "e", "un", "una"},
    "fa": {"و", "در", "از", "به", "که", "را", "با", "این", "است", "بود"},
}


def _to_ascii_digits(text: str) -> str:
    """Normalise Persian (۰-۹) and Arabic-Indic (٠-٩) digits to 0-9."""
    out = []
    for ch in text:
        if ch.isdigit():
            try:
                out.append(str(unicodedata.decimal(ch)))
                continue
            except (TypeError, ValueError):
                pass
        out.append(ch)
    return "".join(out)


def _numbers(text: str) -> set[str]:
    norm = _to_ascii_digits(text)
    return {n.replace(",", ".") for n in _NUM_RE.findall(norm)}


def _content_tokens(text: str, lang: str) -> set[str]:
    stop = _STOP.get(lang, set())
    return {t.lower() for t in _WORD_RE.findall(text) if t.lower() not in stop}


class HeuristicScorer(GroundednessScorer):
    name = "heuristic_baseline"

    def __init__(
        self,
        grounded_at: float = 0.6,
        ungrounded_below: float = 0.3,
        name: Optional[str] = None,
    ) -> None:
        self.grounded_at = grounded_at
        self.ungrounded_below = ungrounded_below
        if name:
            self.name = name

    def score_item(self, item: EvalItem) -> Judgment:
        ctx_numbers = _numbers(item.context)
        ans_numbers = _numbers(item.answer)
        number_mismatch = bool(ans_numbers) and not ans_numbers.issubset(ctx_numbers)

        ctx_tokens = _content_tokens(item.context, item.language)
        ans_tokens = _content_tokens(item.answer, item.language)
        overlap = (
            len(ans_tokens & ctx_tokens) / len(ans_tokens) if ans_tokens else 0.0
        )

        if number_mismatch:
            label = Label.UNGROUNDED
        elif overlap >= self.grounded_at:
            label = Label.GROUNDED
        elif overlap < self.ungrounded_below:
            label = Label.UNGROUNDED
        else:
            label = Label.PARTIAL

        return Judgment(
            item_id=item.id,
            scorer=self.name,
            label=label,
            score=overlap,
            language=item.language,
            rationale=(
                "number not found in context"
                if number_mismatch
                else f"token overlap {overlap:.2f}"
            ),
            raw={"overlap": overlap, "number_mismatch": number_mismatch},
        )
