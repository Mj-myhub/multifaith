# EU AI Act: an engineer's mapping to evaluation procedures

This document connects a few EU AI Act obligations to concrete things MultiFaith can help measure. It is an engineer's reading of public material, not legal advice, and the Act's implementation is still moving (the "Digital Omnibus" simplification package has been adjusting timelines). Treat this as a way to frame why language-stratified faithfulness evaluation matters commercially, and check current dates and obligations with a qualified source before relying on them.

## Why this is relevant at all

The Act applies in phases. Prohibited practices and AI-literacy duties came first. Obligations for general-purpose AI models followed. The set of obligations that carries the most operational weight for most organisations concerns high-risk systems: risk management, data governance, logging, human oversight, and a conformity assessment before the system goes to market. There are real penalties attached, on the order of tens of millions of euros or a percentage of global turnover, which is what turns "evaluation" from a nice-to-have into a line item.

For a system deployed across the EU, evaluation that only covers English is hard to defend, because the people affected are not answering in English. An English benchmark score does not predict behaviour in Italian or any other official language. That single gap is the commercial hook for this project.

A note on roles, because it changes who carries which duty: a team building a RAG pipeline on top of a foundation model is generally a *deployer*. Substantially fine-tuning a model can push you toward being treated as a *provider*, with heavier obligations. Where you sit affects what you must document. The boundary is a grey area worth tracking.

## Obligation to evaluation, mapped

The mapping below is intentionally modest. MultiFaith addresses a slice of these duties (the measurement and evidence parts), not the whole compliance programme.

| Obligation area | What it asks for, in plain terms | How MultiFaith contributes |
|---|---|---|
| Risk management | Identify and reduce foreseeable risks across the lifecycle | Quantifies one concrete risk (ungrounded answers) and shows where it concentrates by language and by failure type, so mitigation can be targeted rather than generic |
| Data and evaluation quality | Use representative, appropriately tested data and procedures | The gold set and annotation guidelines are an auditable, versioned evaluation procedure with stated coverage and limits |
| Per-language adequacy | Performance claims should hold for the populations actually served | Language-stratified metrics make "it works in English" an inadequate claim explicit, with numbers per language |
| Logging and record-keeping | Keep records that let you reconstruct how the system behaved | JSONL judgments plus pinned model versions and dated runs give a reproducible evidence trail |
| Human oversight | A person must be able to understand and check the system's outputs | Per-item rationales and a phenomenon taxonomy give a reviewer a readable basis for spot-checking, rather than an opaque score |
| Transparency about evaluation limits | Be honest about what was and was not tested | The data card and the limitations section state coverage, sample size, and known biases up front |

## What MultiFaith does not do

It is not a conformity-assessment tool, it does not produce regulator-ready documentation, and it does not cover most of what a high-risk obligation requires (governance, post-market monitoring, incident reporting, and so on). It measures one risk well and produces evidence about it. In an interview, that distinction is worth making yourself, before anyone makes it for you: overclaiming regulatory coverage is a faster way to lose credibility than admitting a clear scope.

## How to talk about this without overreaching

Good framing: "Under the AI Act, organisations deploying across languages need evidence that their systems behave acceptably in each language, not just in English. This project measures faithfulness per language and shows where automated evaluation itself becomes unreliable, which is the kind of evidence that feeds a risk-management file."

Framing to avoid: "This makes you AI Act compliant." It does not, and a knowledgeable interviewer will press on it.
