"""Read and write the gold set and scorer outputs as JSONL.

JSONL (one JSON object per line) is chosen over a single big JSON array because
it is diff-friendly. When you add ten new annotated items, the git diff shows
ten new lines, not a reformatted blob. That matters when the dataset is the part
reviewers trust least and scrutinise most.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Union

from ..types import EvalItem, Judgment

PathLike = Union[str, Path]


def load_items(path: PathLike) -> list[EvalItem]:
    """Load a JSONL file of evaluation items."""
    items: list[EvalItem] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                items.append(EvalItem.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError) as exc:
                raise ValueError(f"{path}:{line_no}: cannot parse item ({exc})")
    return items


def save_items(items: Iterable[EvalItem], path: PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")


def load_judgments(path: PathLike) -> list[Judgment]:
    out: list[Judgment] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(Judgment.from_dict(json.loads(line)))
    return out


def save_judgments(judgments: Iterable[Judgment], path: PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for j in judgments:
            f.write(json.dumps(j.to_dict(), ensure_ascii=False) + "\n")
