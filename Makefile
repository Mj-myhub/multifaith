.PHONY: install install-all test lint run report clean

install:        ## core + dev (no model stack); enough to run tests
	pip install -e ".[dev]"

install-all:    ## everything, including model backends
	pip install -e ".[all]"

test:
	pytest

lint:
	ruff check src tests

run:            ## run the zero-setup demo (heuristic baseline, no API key)
	python experiments/run_eval.py --config experiments/configs/demo.yaml

report:         ## recompute tables from saved judgments
	python -m multifaith.cli report --results results/judgments.jsonl --data data/gold/sample.jsonl

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__ src/*.egg-info build dist
