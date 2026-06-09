"""MultiFaith: a multilingual faithfulness and judge-reliability harness for RAG.

Public API:

    from multifaith import Harness, EvalItem, Label
    from multifaith.scorers import LLMJudgeScorer, build_scorer
    from multifaith.data import load_items

See the README for the project framing and the docs/ folder for the annotation
guidelines, data card, and EU AI Act mapping.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .types import EvalItem, Judgment, Label, PHENOMENA
from .harness import Harness, HarnessReport, format_report

__all__ = [
    "__version__",
    "EvalItem",
    "Judgment",
    "Label",
    "PHENOMENA",
    "Harness",
    "HarnessReport",
    "format_report",
]
