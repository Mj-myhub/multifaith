# Data Card: MultiFaith Gold Set

This card documents the hand-annotated evaluation set. The bundled `sample.jsonl` is a 12-item seed that demonstrates the format and phenomenon coverage; the sections below are written for the full set you will build on top of it. Fill in the bracketed parts as the set grows.

## Motivation

The set exists to measure agreement between automated groundedness scorers and human judgement, separately for each language. It is an evaluation set, not a training set. Its value comes from careful labelling against a written standard, not from size.

## Composition

- **Unit**: one `EvalItem` = a query, the retrieved context, a model answer, a human label, and phenomenon tags.
- **Languages**: English (`en`), Italian (`it`), Persian (`fa`).
- **Domain(s)**: [finance and legal document QA in the seed; state your final domains].
- **Size**: [target ~300–500 items per language; report the actual count and the per-language, per-label breakdown here].
- **Label balance**: deliberately not natural. The set over-samples ungrounded answers and specific phenomena, because a set that mirrors a low natural error rate would tell you little about where scorers break. State the balance; do not present skewed support as if it were a base rate.

## Collection and construction

- **Contexts**: [describe sources. If derived from public filings or documents, note the source and licence. If synthetic, say so plainly.]
- **Answers**: [describe how candidate answers were produced. Real model outputs from your RAG system are strongest; hand-written contrast pairs are acceptable for covering rare phenomena, but label them as such in `meta`.]
- **Translation note**: where items were adapted across languages rather than independently sourced, record it. Machine translation is an accepted but inferior fallback that prior multilingual benchmarks have used; if you use it anywhere, flag those items so a reader can exclude them.

## Annotation

- **Guidelines**: see [`annotation_guidelines.md`](annotation_guidelines.md).
- **Annotators**: [who; language competence; native vs fluent]. Record per-item annotator identity in `meta`.
- **Inter-annotator agreement**: [report Cohen's kappa on the doubly-annotated subset, per language].
- **Known annotator bias**: [single-annotator portions, domain familiarity, anything that could skew labels].

## Intended use

- Comparing groundedness scorers across languages.
- Auditing LLM-as-judge reliability per language ("can the judge judge?").
- A teaching example of language-stratified evaluation.

## Out-of-scope use

- Training a production hallucination detector. The set is too small and too deliberately skewed.
- Claiming a model's general multilingual quality. This measures faithfulness to provided context on a specific item distribution, nothing broader.

## Limitations and ethical considerations

- Small size limits statistical power; report confidence, not just point estimates.
- The phenomenon taxonomy is a simplification of how language fails and will not fit every case; `untagged` is allowed and should itself be tracked.
- Contexts may contain entities or figures from real documents. [Confirm no personal data is included, or describe handling if it is.]
- Persian and Italian are under-served by existing tooling, which is part of the motivation, but it also means automated comparisons against them rest on shakier model support. Do not over-read small differences.

## Maintenance

- Versioned with the repository; the git history of the JSONL is the changelog.
- When guidelines change, affected items are re-reviewed (see the annotation process).
- File format: JSONL, UTF-8, one `EvalItem` per line, schema in `src/multifaith/types.py`.
