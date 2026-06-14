#!/usr/bin/env python3
"""Interactive annotation helper for the MultiFaith gold set.

Run it, answer the prompts, and it appends a schema-valid item to the gold file.
It reuses the package's own types, so anything it writes is guaranteed to load
back in. You never edit JSON by hand.

    python tools/annotate.py
    python tools/annotate.py --out data/gold/sample.jsonl

The workflow it is built for: have your FinDocRAG outputs (or any document-QA
pairs) open in another window. For each one, paste the question, the retrieved
context, and the model's answer, then judge whether the answer is grounded in
that context per docs/annotation_guidelines.md.

Items are written the moment you finish each one, so quitting never loses work.
Type q at the language prompt to stop.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Make the package importable whether or not it has been pip-installed.
SRC = Path(__file__).resolve().parents[1] / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from multifaith.types import EvalItem, Label, PHENOMENA  # noqa: E402

LANG_NAMES = {"en": "English", "it": "Italian", "fa": "Persian"}
LABEL_SHORTCUTS = {"g": Label.GROUNDED, "p": Label.PARTIAL, "u": Label.UNGROUNDED}


def _existing(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            rows.append(json.loads(line))
    return rows


def _next_id(rows: list[dict], lang: str) -> str:
    """Continue the en-001 / it-004 numbering per language."""
    nums = []
    for r in rows:
        if r.get("language") == lang:
            m = re.search(r"(\d+)$", str(r.get("id", "")))
            if m:
                nums.append(int(m.group(1)))
    return f"{lang}-{(max(nums) + 1) if nums else 1:03d}"


def _ask(prompt: str) -> str:
    return input(prompt).strip()


def _ask_block(prompt: str) -> str:
    """Read text that may span several lines (a pasted context, say).

    Paste the text, then type END on its own line to finish. This handles
    multi-paragraph retrieved chunks without breaking the prompt flow.
    """
    print(prompt)
    print("  (paste the text, then type END on its own line)")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _ask_label() -> Label:
    while True:
        raw = _ask("label  [g]rounded / [p]artial / [u]ngrounded: ").lower()
        if raw in LABEL_SHORTCUTS:
            return LABEL_SHORTCUTS[raw]
        try:
            return Label.from_str(raw)
        except ValueError:
            print("  please answer g, p, or u")


def _ask_phenomena() -> list[str]:
    print("phenomena (why it failed) — enter numbers separated by commas, or blank for none:")
    for i, ph in enumerate(PHENOMENA, start=1):
        print(f"  {i:>2}. {ph}")
    raw = _ask("> ")
    if not raw:
        return []
    chosen: list[str] = []
    for token in raw.replace(" ", "").split(","):
        if token.isdigit() and 1 <= int(token) <= len(PHENOMENA):
            chosen.append(PHENOMENA[int(token) - 1])
        elif token in PHENOMENA:
            chosen.append(token)
        else:
            print(f"  ignoring unknown phenomenon: {token}")
    return chosen


def _append(item: EvalItem, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")


def _counts(path: Path) -> str:
    rows = _existing(path)
    by_lang = Counter(r.get("language") for r in rows)
    parts = [f"{LANG_NAMES.get(k, k)}: {v}" for k, v in sorted(by_lang.items())]
    return f"{len(rows)} items total  ({', '.join(parts) or 'none yet'})"


def main() -> int:
    ap = argparse.ArgumentParser(description="Add gold-set items interactively.")
    ap.add_argument("--out", default="data/gold/sample.jsonl", help="gold file to append to")
    ap.add_argument("--domain", default="finance", help="default domain tag for new items")
    args = ap.parse_args()

    path = Path(args.out)
    print(f"Annotating into {path}")
    print(_counts(path))
    print("Type q at the language prompt to stop.\n")

    added = 0
    while True:
        lang = _ask("language  [en/it/fa]  (q to quit): ").lower()
        if lang in {"q", "quit", "exit"}:
            break
        if lang not in LANG_NAMES:
            print("  please enter en, it, or fa\n")
            continue

        rows = _existing(path)
        item_id = _next_id(rows, lang)
        print(f"  new id: {item_id}")

        query = _ask("query / question: ")
        context = _ask_block("retrieved context (what the answer must be grounded in):")
        answer = _ask_block("model answer (the text under test):")
        if not (query and context and answer):
            print("  query, context, and answer are all required; skipping this one\n")
            continue

        label = _ask_label()
        phenomena = _ask_phenomena() if label != Label.GROUNDED else []
        domain = _ask(f"domain [{args.domain}]: ") or args.domain

        item = EvalItem(
            id=item_id,
            language=lang,
            query=query,
            context=context,
            answer=answer,
            gold_label=label,
            phenomena=phenomena,
            domain=domain,
        )
        _append(item, path)
        added += 1
        print(f"  saved {item_id} ({label.value})  —  {_counts(path)}\n")

    print(f"\nDone. Added {added} item(s) this session.")
    print(_counts(path))
    if added:
        print("\nNext: re-run your evaluation to see the numbers move:")
        print("  python experiments/run_eval.py --config experiments/configs/demo.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
