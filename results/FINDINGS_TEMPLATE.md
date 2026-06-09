# Findings (template)

Fill this in once you have run real scorers over a properly annotated gold set. Keep it short and quotable. This is the document that becomes your LinkedIn post, your interview talking point, and possibly a workshop abstract.

## Setup (one paragraph)

- Languages: en, it, fa
- Domain: [your domain]
- Gold set: [N per language], annotated per `docs/annotation_guidelines.md`, [single/double] annotated, inter-annotator κ = [value]
- Scorers compared: [heuristic baseline, LLM judge (en), LLM judge (native), NLI, fine-tuned classifier]
- Models and versions: [exact model strings], run on [date]

## Headline result

> [One sentence. Example shape: "The LLM judge agrees with human annotators at κ = 0.8X in English but only κ = 0.4X in Persian, and the gap is concentrated in negation flips and morphology errors."]

## Per-language agreement with human labels

| scorer | en κ | it κ | fa κ | notes |
|--------|------|------|------|-------|
| heuristic_baseline | | | | |
| judge_en | | | | |
| judge_native | | | | |
| nli | | | | |
| classifier | | | | |

## Where scorers fail, by phenomenon

[A short table or figure: missed-error rate per phenomenon per language. Call out the phenomena where the gap between English and the other languages is largest. This is the linguistically interesting part and the part only you can interpret well.]

## Did judging in the target language help?

[Compare `judge_en` against `judge_native`. State whether instructing the judge to work in the target language closed the gap, made no difference, or made it worse. A negative or null result here is still a result; report it plainly.]

## Limitations specific to this run

[Sample size, annotator coverage, model support for Persian, anything that should stop a reader over-reading the numbers.]

## What I would do next

[Two or three concrete next steps. Shows you see the project as a starting point, not a finished claim.]
