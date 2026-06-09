"""Reproducible entry point for a full evaluation run.

This is the script you cite in the README and point reviewers at. It is a thin
wrapper over the CLI's run command so that `python experiments/run_eval.py` and
`multifaith run` do the same thing. Keep all run parameters in the YAML config,
not in code, so a result is fully described by (config file + model versions +
gold set commit).
"""

from __future__ import annotations

import argparse

from multifaith.cli import main as cli_main


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a MultiFaith evaluation.")
    ap.add_argument(
        "--config",
        default="experiments/configs/default.yaml",
        help="path to the run config",
    )
    ap.add_argument("--languages", nargs="*", default=None)
    args = ap.parse_args()

    argv = ["run", "--config", args.config]
    if args.languages:
        argv += ["--languages", *args.languages]
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
