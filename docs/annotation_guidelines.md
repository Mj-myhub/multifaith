# Annotation Guidelines

These are the rules an annotator follows to label an item as grounded, partial, or ungrounded, and to tag *why* an ungrounded answer failed. The point of writing them down is repeatability: two people following this document should agree most of the time, and where they do not, the disagreement should be about a genuinely hard case, not about what the labels mean.

Read this before annotating. Re-read the examples when a case feels ambiguous.

## The one rule that governs everything

Judge the answer **against the retrieved context only**. Do not use what you personally know about the world.

This is the rule annotators break most often, because it feels wrong to mark a true statement as ungrounded. But in a RAG system the context is the only thing the model was supposed to rely on. An answer that happens to be correct while ignoring the context is still a reliability failure: next time the lucky guess will be a wrong guess. So:

- If the answer is supported by the context, it is grounded, even if it is incomplete.
- If the answer is true in reality but not supported by the context, it is **ungrounded**.
- If the answer contradicts the context, it is ungrounded, regardless of who is actually right.

## The three labels

**grounded** — every claim the answer makes is supported by the context. Paraphrase is fine. Reordering is fine. Leaving out details that were in the context is fine; an incomplete-but-supported answer is still grounded.

**partial** — the answer makes more than one claim, at least one is supported and at least one is not. The classic case is a correct core answer with an invented extra detail tacked on.

**ungrounded** — the main claim is not supported by the context, or it contradicts the context.

When you are torn between partial and ungrounded, ask which claim is load-bearing. If the unsupported part is the actual answer to the question, it is ungrounded. If the unsupported part is a side detail, it is partial.

## Phenomenon tags

For anything that is not grounded, add one or more tags describing the failure. These tags are what let the analysis say *how* a scorer fails, not just *that* it fails. Use as many as apply.

| tag | meaning |
|-----|---------|
| `entity_error` | wrong named entity (person, organisation, place, product) |
| `number_error` | wrong figure, date, count, or quantity |
| `unit_error` | the figure is right but the unit or currency is wrong |
| `unsupported_claim` | a plausible statement that simply is not in the context |
| `negation_flip` | asserts the opposite of what the context says |
| `overgeneralization` | context says "some" or "a", the answer says "all" or "every" |
| `agreement_error` | morphosyntactic agreement is wrong (gender, number) |
| `morphology_error` | wrong inflection or derivation; watch for this in Persian and Italian |
| `code_switching` | the answer drifts into another language |
| `refusal` | the model declined to answer; this is not a hallucination, but track it separately so refusals do not get scored as errors |

## Worked examples

English, grounded:
- Context: "the company reported net income of EUR 12 million for fiscal year 2023"
- Answer: "Net income for 2023 was 12 million euros." → **grounded**, no tags.

English, partial:
- Answer: "Net income for 2023 was 12 million euros, driven mainly by the cloud division." → **partial**, `unsupported_claim`. The figure is supported; the cause is invented.

English, ungrounded (negation flip):
- Context: "either party may terminate the agreement with 30 days' written notice"
- Answer: "No, the contract did not allow early termination." → **ungrounded**, `negation_flip`.

Italian, ungrounded (unit error):
- Context: "un utile netto di 12 milioni di euro"
- Answer: "l'utile netto è stato di 12 milioni di dollari" → **ungrounded**, `unit_error`. The number matches, the currency does not. This is the case cheap lexical scorers miss, because "12" is present in both.

Persian, ungrounded (number error):
- Context: "سود خالص ... برابر با ۱۲ میلیون یورو بود"
- Answer: "سود خالص ... معادل ۲۰ میلیون یورو بود" → **ungrounded**, `number_error`.

## Language-specific notes

These are the places where general guidelines are not enough and a linguist's attention pays off.

### Italian
- Currency and large-number formatting: Italian uses the comma as the decimal separator and the dot as the thousands separator. "1.200" is one thousand two hundred, not one point two. Do not mistake formatting for a number error.
- Gender agreement: an answer may copy a figure correctly but get the gender of an adjective or past participle wrong relative to the subject. Tag `agreement_error` only when the agreement error changes or muddies the meaning, not for stylistic infelicity.
- Formal versus informal register does not affect groundedness. Do not penalise register.

### Persian (Farsi)
- Digits: Persian text routinely uses Persian digits (۰۱۲۳۴۵۶۷۸۹). The harness normalises these to ASCII for number checks, but as a human annotator, read them as numbers and compare values, not glyphs.
- Right-to-left rendering can make a misplaced number or unit hard to spot in a left-to-right editor. Read carefully, ideally in a viewer that renders RTL correctly.
- Ezāfe and compounding: Persian links words with the ezāfe construction, which is often unwritten. An answer can fragment or misattach a compound in a way that changes the referent. When that happens and it shifts the meaning, tag `morphology_error` (or `entity_error` if it produces the wrong entity).
- Loanwords and code-switching: technical and financial Persian borrows heavily. A borrowed term is not code-switching. Reserve `code_switching` for the answer actually leaving Persian (for example, drifting into an English sentence).

## Process

1. Annotate independently. Do not look at the model's predicted label while assigning the human label; that biases you toward agreement with the model, which is exactly what the project is trying to measure honestly.
2. For a subset (aim for at least 50 items per language), have a second annotator label the same items, and report inter-annotator agreement (Cohen's kappa). If two competent humans cannot agree, an automated judge has no chance, and that is worth knowing.
3. Record annotator identity in the item's `meta` field. Single-annotator data is usable but its limits must be stated.
4. When you change a guideline, re-check earlier items that the change affects. The git history of `sample.jsonl` and your real gold file is part of the methodology.
