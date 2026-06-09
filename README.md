# MultiFaith

**A multilingual faithfulness and judge-reliability evaluation harness for RAG, with first-class Italian and Persian support.**

[![ci](https://github.com/Mj-myhub/multifaith/actions/workflows/ci.yml/badge.svg)](https://github.com/Mj-myhub/multifaith/actions)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

> One-line version, for a recruiter: this is a tool that measures whether an AI system gives answers it can actually back up, and it checks that separately for each language, because the new EU AI Act treats that as a requirement and most evaluation tools only really work in English.

MultiFaith does two things. It scores whether the answers a RAG system produces are *grounded* in the documents it retrieved, and it audits whether the automated judges people use to do that scoring can be trusted once you leave English. The second part is the interesting one, and it is where this repo tries to say something most benchmarks do not.

---

## Why this exists

If you have built a RAG system, you have run into the obvious next question: how do you know the answers are any good? The standard move is to have a second model read the retrieved context and the answer and decide whether one supports the other. That works well enough in English. It quietly stops working in other languages, and almost nobody checks.

Three facts sit behind this project.

Hallucination is still the failure mode that keeps LLM applications out of production. A factual claim that is not supported by the source erodes trust and, in regulated settings, creates real legal exposure. Detection has become a small industry of its own, usually combining an LLM-as-judge for broad factuality, a groundedness scorer for RAG outputs, a fine-tuned classifier for low latency, and human review for the hard cases.

Performance does not transfer across languages. On parallel questions, models lose a large amount of accuracy moving from high-resource to low-resource languages, with reported gaps of around 24 points. An English benchmark score does not predict how a system behaves in Italian, let alone Persian.

The judges are part of the problem. LLM-as-judge reliability is itself language-dependent, and its quality on low-resource languages is largely unvalidated. So the tool you use to catch multilingual hallucinations may be least trustworthy in exactly the languages where you need it most. That is the gap MultiFaith is built around.

There is also a regulatory clock. Under the EU AI Act, general-purpose model obligations are already in force and the high-risk obligations (risk management, data governance, logging, human oversight) carry the heaviest weight. For a European organisation deploying AI across languages, "we tested it in English" is not going to be a defensible answer. See [`docs/eu_ai_act_mapping.md`](docs/eu_ai_act_mapping.md) for how specific obligations map onto concrete evaluation procedures, written as an engineer's reading rather than legal advice.

## What this is, and what it is not

It is a small, readable harness for comparing groundedness scorers across languages on a hand-annotated gold set, with the analysis sliced by language and by the linguistic reason an answer failed. It ships with a zero-setup baseline so it runs the moment you clone it.

It is not a giant new benchmark. The shelf is already full of multilingual benchmarks (MMLU-ProX, MultiLoKo, INCLUDE, Global-MMLU, BenchMAX, and others), and a solo "yet another multilingual hallucination benchmark" would add little. The contribution here is narrower and, I think, more useful: a method and a tool for asking whether your evaluation itself holds up in each language, demonstrated on English, Italian, and Persian.

## The core idea

Every detection method implements one interface (`GroundednessScorer`): given a query, the retrieved context, and the model's answer, return a verdict of grounded, partial, or ungrounded. Because every method speaks that one interface, the harness can line them up side by side and ask the question that matters: where, and in which language, do they disagree with a human?

```
                    ┌─────────────────────────────┐
   gold set ──────► │           Harness           │
 (EN / IT / FA,     │  runs each scorer over each │
  human-labelled)   │  item, collects judgments   │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  LLM-as-judge            NLI groundedness          fine-tuned classifier
 (judge_en vs                (entailment)              (your baseline)
  judge_native)
        └──────────────────────────┼──────────────────────────┘
                                   ▼
                     ┌─────────────────────────────┐
                     │     Analysis (per scorer)   │
                     │  • agreement + Cohen's κ     │
                     │    vs human, per language    │
                     │  • missed errors, per        │
                     │    linguistic phenomenon     │
                     └─────────────────────────────┘
```

The headline number is Cohen's kappa between each automated scorer and the human labels, computed separately for each language. A judge that tracks human judgement in English but collapses to near-chance kappa in Persian is the finding the whole project is designed to surface.

## Quickstart

```bash
git clone https://github.com/Mj-myhub/multifaith.git
cd multifaith
pip install -e ".[dev]"        # core + test tooling, no model stack needed
pytest                          # 9 tests, should be green
make run                        # zero-setup demo on the sample gold set
```

`make run` uses the heuristic baseline, so it needs no API key and downloads nothing. On the bundled sample it prints something like:

```
=== heuristic_baseline : judge vs human, per language ===
lang      n   agree   kappa  recall_ung  macroF1
en        4    1.00    1.00        1.00     1.00
fa        4    1.00    1.00        1.00     0.67
it        4    0.75    0.50        0.50     0.49

=== heuristic_baseline : missed errors by phenomenon ===
  unit_error           missed 1/1  (100%)
  ...
```

Even this dumb baseline already tells a story: it looks perfect in English, holds up in Persian, and breaks in Italian, because it misses a currency error ("dollari" where the context says "euro") that shares the same number. That is a miniature version of exactly the cross-language blind spot the real scorers are meant to expose.

To run a real LLM judge, wire one method (`LLMJudgeScorer._complete`) to your provider, then:

```bash
pip install -e ".[judge]"
python experiments/run_eval.py --config experiments/configs/default.yaml
```

## What counts as a hallucination here

Faithfulness is judged *against the retrieved context*, not against the world. An answer can be true in reality and still ungrounded if the context does not support it, because in a RAG system an unsupported-but-lucky answer is still a reliability problem. The three labels and the phenomenon taxonomy (number error, unit error, negation flip, unsupported claim, agreement and morphology errors, and so on) are defined in [`docs/annotation_guidelines.md`](docs/annotation_guidelines.md), with worked examples in Italian and Persian.

## Repository layout

```
multifaith/
├── src/multifaith/
│   ├── types.py              # EvalItem, Judgment, Label, phenomenon taxonomy
│   ├── harness.py            # orchestrates scorers, assembles the report
│   ├── cli.py                # `multifaith run` / `multifaith report`
│   ├── scorers/
│   │   ├── base.py           # the GroundednessScorer interface
│   │   ├── heuristic.py      # zero-setup baseline (no deps)
│   │   ├── llm_judge.py      # LLM-as-judge (wire _complete to your provider)
│   │   ├── nli_scorer.py     # entailment-based scorer (transformers)
│   │   └── classifier.py     # fine-tuned baseline (train then infer)
│   ├── data/loader.py        # JSONL read/write
│   └── analysis/
│       ├── metrics.py        # precision/recall/F1, Cohen's κ (hand-written)
│       └── breakdown.py      # per-language and per-phenomenon slicing
├── data/gold/sample.jsonl    # 12 labelled EN/IT/FA items to start from
├── experiments/
│   ├── configs/{demo,default}.yaml
│   └── run_eval.py
├── docs/
│   ├── annotation_guidelines.md
│   ├── data_card.md
│   └── eu_ai_act_mapping.md
├── results/                  # judgments + summary land here
└── tests/test_core.py        # metrics, round-trip, harness wiring
```

## Methodology

The gold set is the part reviewers will trust least, so it is the part to get right. The bundled `sample.jsonl` is a seed, not a dataset; it shows the format and the phenomenon coverage. The real work is annotating a few hundred items per language to a written standard, which is where native competence in the target languages earns its keep. Annotate against the guidelines, record who annotated what, and keep the file diff-friendly so every change is visible in git history.

Scorers are compared on the same items. The two LLM-judge entries in `default.yaml` are the same method judging in English versus in the target language; their per-language kappa is the experiment. The NLI scorer and the fine-tuned classifier are there as cheaper, lower-latency points of comparison, and as an honest floor: a method that cannot beat the heuristic baseline in a given language is not ready for that language.

Report variance, not point estimates. A single accuracy number from one split on a few hundred examples is not evidence. Use stratified k-fold for the classifier and report the spread. See the limitations below; a reviewer who knows this will ask.

## Results

Fill this in as you go. A template lives in [`results/FINDINGS_TEMPLATE.md`](results/FINDINGS_TEMPLATE.md). The shape you are aiming for:

| scorer | lang | n | agreement | Cohen's κ | recall (ungrounded) | macro F1 |
|--------|------|---|-----------|-----------|---------------------|----------|
| judge_en | en | … | … | … | … | … |
| judge_en | it | … | … | … | … | … |
| judge_en | fa | … | … | … | … | … |
| judge_native | fa | … | … | … | … | … |

The single most quotable result will probably read like: "the LLM judge agrees with human annotators at κ = 0.8 in English but only κ = 0.4 in Persian, and most of the gap is negation flips and morphology errors it does not register." If that holds up, it is a finding worth a short writeup and possibly a workshop submission.

## Limitations

I would rather state these than have an interviewer find them.

- The sample gold set is tiny and illustrative. Conclusions need a properly sized, annotated set.
- Single-annotator labels carry bias. Where possible, get a second annotator on a subset and report inter-annotator agreement.
- LLM-as-judge has a circularity problem: you are using a model to grade a model. The human gold set is the anchor that keeps this honest, which is why it cannot be skipped.
- Multilingual NLI and judge models have uneven, sometimes thin coverage of Persian. That unevenness is partly the object of study, but it also limits what the automated scorers can do.
- Results drift as models update. Pin model versions and date your runs; a number without a model string and a date is not reproducible.

## Roadmap

1. Freeze scope: three languages, one domain, a clear definition of "ungrounded". Write the annotation guidelines first.
2. Build and wire one real LLM-judge backend; confirm the pipeline end to end.
3. Annotate the gold set in EN, IT, FA. This is the credibility core; do not rush it.
4. Add the NLI scorer and train the classifier baseline; run the comparison.
5. Generate the per-language and per-phenomenon tables and figures; write the findings note and the limitations honestly.
6. Ship a short demo (a Hugging Face Space or a recorded walkthrough) and a writeup framing the business and regulatory problem.

## Related work

This project sits next to, not on top of, the multilingual evaluation literature: MMLU-ProX and MultiLoKo for parallel multilingual benchmarks, INCLUDE and Global-MMLU for regional knowledge, and RAGTruth, HaluBench, and HaluEval for hallucination and groundedness specifically. Those measure how well models do. MultiFaith asks a smaller, complementary question: how well does your *evaluation* do, language by language.

## Citation

```bibtex
@software{jafari_multifaith_2026,
  author  = {Majid Jafari},
  title   = {MultiFaith: a multilingual faithfulness and judge-reliability
             evaluation harness for RAG},
  year    = {2026},
  url     = {https://github.com/Mj-myhub/multifaith}
}
```

## License

MIT. See [`LICENSE`](LICENSE).
