"""Groundedness scorers and a small registry to build them from config."""

from __future__ import annotations

from typing import Any

from .base import GroundednessScorer
from .heuristic import HeuristicScorer
from .llm_judge import LLMJudgeScorer
from .nli_scorer import NLIGroundednessScorer
from .classifier import FineTunedClassifierScorer

__all__ = [
    "GroundednessScorer",
    "HeuristicScorer",
    "LLMJudgeScorer",
    "NLIGroundednessScorer",
    "FineTunedClassifierScorer",
    "build_scorer",
]

_REGISTRY = {
    "heuristic": HeuristicScorer,
    "llm_judge": LLMJudgeScorer,
    "nli": NLIGroundednessScorer,
    "classifier": FineTunedClassifierScorer,
}


def build_scorer(spec: dict[str, Any]) -> GroundednessScorer:
    """Instantiate a scorer from a config dict.

    Expected shape:
        {"type": "llm_judge", "model": "llama-3.3-70b-versatile", ...}
    Any keys other than "type" are passed straight to the constructor.
    """
    spec = dict(spec)
    kind = spec.pop("type", None)
    if kind not in _REGISTRY:
        raise ValueError(
            f"unknown scorer type {kind!r}; options: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[kind](**spec)
