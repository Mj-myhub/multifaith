"""Core data types shared across the harness.

Everything in MultiFaith moves around three objects:

- `EvalItem`   : one (query, retrieved context, model answer) triple, optionally
                 with a human gold label and linguistic phenomenon tags.
- `Judgment`   : the verdict a single scorer produced for one item.
- `Label`      : the verdict vocabulary (grounded / partial / ungrounded).

Keeping these small and explicit is deliberate. The whole point of the project
is that the *evaluation* is auditable, so the data structures that carry the
evidence should be readable by a human, not buried inside a framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class Label(str, Enum):
    """The verdict for whether an answer is supported by its context.

    PARTIAL exists because real answers are rarely all-or-nothing. A response
    can state three facts where two are grounded and one is invented. Forcing
    that into a binary throws away the most interesting cases, which are exactly
    the ones a hiring manager will ask you about.
    """

    GROUNDED = "grounded"
    PARTIAL = "partial"
    UNGROUNDED = "ungrounded"

    @classmethod
    def from_str(cls, value: str) -> "Label":
        return cls(value.strip().lower())


# Linguistic / failure-mode taxonomy used to tag *why* an answer is ungrounded.
# This is where computational-linguistics judgement does work that a generic
# "hallucinated: yes/no" label cannot. See docs/annotation_guidelines.md for
# definitions and language-specific notes for Italian and Persian.
PHENOMENA = (
    "entity_error",        # wrong named entity (person, org, place)
    "number_error",        # wrong figure, date, or quantity
    "unit_error",          # right figure, wrong unit or currency
    "unsupported_claim",   # plausible statement absent from the context
    "negation_flip",       # asserts the opposite of the context
    "overgeneralization",  # context says "some", answer says "all"
    "agreement_error",     # morphosyntactic agreement wrong (gender/number)
    "morphology_error",    # inflection/derivation wrong; common in fa, it
    "code_switching",      # answer drifts into another language
    "refusal",             # model declines; not a hallucination, tracked apart
)


@dataclass
class EvalItem:
    """One unit of evaluation.

    `context` is the text the answer is supposed to be grounded in (in a RAG
    system, the retrieved chunks). `answer` is the model output under test.
    Faithfulness is judged *against the context*, not against the world. An
    answer can be factually true in the world and still ungrounded if the
    context does not support it.
    """

    id: str
    language: str                                   # ISO 639-1: en, it, fa, ...
    query: str
    context: str
    answer: str
    gold_label: Optional[Label] = None              # human annotation, if any
    phenomena: list[str] = field(default_factory=list)
    domain: Optional[str] = None                    # e.g. "finance", "legal"
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.gold_label is not None:
            d["gold_label"] = self.gold_label.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvalItem":
        gold = d.get("gold_label")
        return cls(
            id=str(d["id"]),
            language=d["language"],
            query=d["query"],
            context=d["context"],
            answer=d["answer"],
            gold_label=Label.from_str(gold) if gold else None,
            phenomena=list(d.get("phenomena", [])),
            domain=d.get("domain"),
            meta=dict(d.get("meta", {})),
        )


@dataclass
class Judgment:
    """A single scorer's verdict for a single item."""

    item_id: str
    scorer: str
    label: Label
    score: Optional[float] = None        # continuous groundedness in [0, 1]
    rationale: Optional[str] = None      # short explanation, if the scorer gives one
    language: Optional[str] = None       # copied from the item for easy grouping
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["label"] = self.label.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Judgment":
        return cls(
            item_id=str(d["item_id"]),
            scorer=d["scorer"],
            label=Label.from_str(d["label"]),
            score=d.get("score"),
            rationale=d.get("rationale"),
            language=d.get("language"),
            raw=dict(d.get("raw", {})),
        )
