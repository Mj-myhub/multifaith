"""Command-line interface.

Two commands:

    multifaith run    --config experiments/configs/default.yaml
    multifaith report --results results/judgments.jsonl --data data/gold/sample.jsonl

`run` is the full pipeline (load data, build scorers, score, write judgments and
a summary). `report` recomputes the summary tables from saved judgments, so you
can re-slice results without paying for model calls again.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .data import load_items, save_judgments, load_judgments
from .harness import Harness, HarnessReport, format_report
from .scorers import build_scorer
from .analysis import breakdown


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    items = load_items(cfg["data"])
    if args.languages:
        keep = set(args.languages)
        items = [it for it in items if it.language in keep]
    print(f"loaded {len(items)} items "
          f"({sum(1 for i in items if i.gold_label) } with gold labels)")

    scorers = [build_scorer(s) for s in cfg["scorers"]]
    print(f"scorers: {', '.join(s.name for s in scorers)}")

    report = Harness(scorers).run(items)

    out_dir = Path(cfg.get("output_dir", "results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    save_judgments(report.judgments, out_dir / "judgments.jsonl")
    (out_dir / "summary.txt").write_text(format_report(report), encoding="utf-8")

    print(format_report(report))
    print(f"\nwrote {out_dir/'judgments.jsonl'} and {out_dir/'summary.txt'}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    items = load_items(args.data)
    judgments = load_judgments(args.results)

    report = HarnessReport(judgments=judgments)
    for scorer in sorted({j.scorer for j in judgments}):
        js = [j for j in judgments if j.scorer == scorer]
        report.judge_vs_human[scorer] = breakdown.judge_vs_human_by_language(items, js)
        report.phenomenon_errors[scorer] = breakdown.error_counts_by_phenomenon(
            items, js, scorer=scorer
        )
    print(format_report(report))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="multifaith")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run scorers over a dataset")
    p_run.add_argument("--config", required=True)
    p_run.add_argument(
        "--languages", nargs="*", default=None,
        help="restrict to these language codes, e.g. --languages en it fa",
    )
    p_run.set_defaults(func=_cmd_run)

    p_rep = sub.add_parser("report", help="recompute tables from saved judgments")
    p_rep.add_argument("--results", required=True)
    p_rep.add_argument("--data", required=True)
    p_rep.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
