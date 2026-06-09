"""The scorer interface.

A scorer takes an `EvalItem` and returns a `Judgment`: its verdict on whether
the answer is grounded in the context. Every detection method in the project
implements this one interface, which is what lets the harness compare an
LLM-as-judge against an NLI model against a fine-tuned classifier without any
special-casing.

To add a method, subclass `GroundednessScorer`, set `name`, and implement
`score_item`. That is the whole contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import EvalItem, Judgment


class GroundednessScorer(ABC):
    #: short, stable identifier used in result files and tables
    name: str = "base"

    @abstractmethod
    def score_item(self, item: EvalItem) -> Judgment:
        """Return a judgment for a single item."""
        raise NotImplementedError

    def score_batch(self, items: list[EvalItem]) -> list[Judgment]:
        """Default sequential implementation.

        Override this if your backend supports real batching (a local model can
        process a batch far faster than a loop of single calls).
        """
        return [self.score_item(it) for it in items]
