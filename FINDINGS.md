# Findings

This is my first real look at how well a Groq-hosted LLM judge agrees with human
faithfulness labels in English, Italian, and Persian. The set is small, so read
everything here as a direction, not a settled result. The limitations section is
honest about where the edges are.

## Setup

- Data: 36 items I annotated by hand, 11 English, 12 Italian, 13 Persian. The
  domain is corporate financial filing QA with a few legal clause items. Each item
  is a (query, retrieved context, model answer) triple, labelled grounded, partial,
  or ungrounded against the context, with a phenomenon tag on every error.
- Annotator: just me, native or fluent in all three languages. The rubric is in
  `docs/annotation_guidelines.md`.
- Judge: `llama-3.3-70b-versatile` on Groq, temperature 0, in two modes: `judge_en`
  (instructions in English) and `judge_native` (instructions in the item's own
  language).
- Judge prompt: version 3. How I got there is below.

## What I found

Across all three languages the judge agrees with my labels at Cohen's kappa between
0.86 and 1.00, including on cases I built specifically to trip up a judge that works
in English first. Comprehension of Italian and Persian was never the problem. Every
disagreement that survived sits on a real labelling boundary, not on the judge
failing to understand the language.

## Per language agreement (judge prompt v3)

`judge_en` (instructions in English):

| lang | n  | agreement | kappa | recall (ungrounded) | macro-F1 |
|------|----|-----------|-------|---------------------|----------|
| en   | 11 | 1.00      | 1.00  | 1.00                | 1.00     |
| it   | 12 | 0.92      | 0.86  | 0.86                | 0.91     |
| fa   | 13 | 0.92      | 0.87  | 0.88                | 0.91     |

`judge_native` (instructions in the item's language):

| lang | n  | agreement | kappa | recall (ungrounded) | macro-F1 |
|------|----|-----------|-------|---------------------|----------|
| en   | 11 | 1.00      | 1.00  | 1.00                | 1.00     |
| it   | 12 | 1.00      | 1.00  | 1.00                | 1.00     |
| fa   | 13 | 0.92      | 0.86  | 1.00                | 0.87     |

## The hard cases held up

I seeded the set with items meant to break a judge working in English first: Persian
ezafe attribution (parent versus subsidiary net income), Persian aspect and modality
(intending to build a factory versus having built one), the Italian restrictive
"non ... se non" (dividends paid only to preferred shareholders), entity attribution
swaps, scope overreach, and an English litotes ("not without risk"). The judge got
all of them, in both modes. On the "se non" case it even spelled out in its own
rationale that dividends had gone to preferred shareholders, so it clearly parsed
the construction. The only thing left to argue about was the label, not the
comprehension.

## Prompt iteration

The version that taught me the most was the one that failed. It took three tries to
land the judge prompt.

- v1 had loose label definitions. Agreement was already high, with a single
  borderline Italian disagreement on the "se non" case (judge said partial, I said
  ungrounded).
- v2 sharpened the ungrounded definition to "a single contradicted claim is
  ungrounded even if a minor detail aligns." That fixed the one case I was chasing
  and broke a whole class: the judge started calling genuine partial answers (a
  correct core plus one invented detail) ungrounded in every language, and English
  agreement dropped from 1.00 to 0.73. One overfit tweak, six new errors.
- v3 pulled apart the two situations v2 had blurred together. A contradicted core is
  ungrounded. A correct core with an unsupported addition is partial. Agreement came
  back, the original case resolved, and the partial class survived.

The lesson stuck: label definitions in a judge prompt have global effects, so you
have to score a change on the whole set, not on the example that made you write it.

## Residual disagreements

Two things still disagree under v3, and both are judgment calls, not bugs.

The first is currency: right number, wrong unit. For an answer like "340 dollars"
where the context says euros, judging in English calls it partial (the number is
right) while judging in the answer's own language calls it ungrounded and matches me.
That split held across runs. It is also a fair rubric question on its own: is the
currency part of the core claim? My rubric says a wrong currency makes the claim
false, so ungrounded.

The second is omission. When an answer leaves out a detail from the context but says
nothing false, my rubric counts it as grounded, incomplete but supported. The judge
sometimes marks it partial, docking it for the missing detail. This one flipped
between runs, so I read it as run to run noise on a borderline case, not a real
effect.

## Native versus English judging

The one difference between the two modes that reproduced was on the currency cases:
judging in the answer's own language agreed with me where judging in English did not,
which lifted Italian from 0.92 to 1.00. It is a small effect, one or two items over
two runs, so I treat it as a question for a bigger set rather than a finding. Still,
it pokes a hole in the easy assumption that a judge instructed in English behaves the
same whatever language the answer is in.

## Stability

Over two runs at temperature 0, the currency disagreements and native judging's
agreement on those same items stayed put. The omission disagreement did not. So even
at temperature 0 the judge wobbles, and it wobbles exactly on the most borderline
item, which is about what I would expect. Running each configuration many more times
and reporting the variance is the obvious next thing.

## Limitations

- 36 items, one annotator. Each language cell holds 11 to 13 items, so this is
  indicative, not conclusive.
- I tuned the judge prompt on the same 36 items I then scored it on, so the v3
  numbers are optimistic. The honest check is a held out set, which I have not built
  yet.
- Two runs is nowhere near enough to pin down judge variance.
- One model, one day. The numbers will move as the model changes.

## Next steps

- Build a held out set and re-measure v3 on data it never saw during tuning.
- Run each configuration five to ten times and report agreement with confidence
  intervals.
- Bring in a second annotator on a subset and report how often we agree, to give the
  judge a human ceiling to be measured against.
- Grow the borderline classes (currency, omission, scope), since that is where the
  interesting disagreements live.
