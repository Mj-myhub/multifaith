"""LLM-as-judge groundedness scorer.

A second model reads the context and the answer and decides whether the answer
is supported. This is the most common method in production and also the one with
the sharpest failure mode for this project: a judge that is fluent in English
and shaky in Persian will hand you confident, wrong verdicts in Persian. The
"can the judge judge?" experiment is built on exactly this scorer.

What is real here: the prompt, the parsing of the model reply, and the language
handling. What you must wire up: `_complete`, the single method that sends text
to a model and returns text. I left it as a stub on purpose so the choice of
provider (Groq, OpenAI, Anthropic, a local server) stays yours and stays out of
the core package. There is a worked example in the docstring of `_complete`.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from ..types import EvalItem, Judgment, Label
from .base import GroundednessScorer

# The judge is asked to reply with strict JSON. Asking for a rationale *before*
# the label nudges the model to reason first and commit second, which tends to
# reduce label flips. The instruction to judge only against the context is
# repeated because judges love to "correct" answers using world knowledge.
JUDGE_PROMPT = """You are evaluating whether an ANSWER is faithful to a CONTEXT.

Judge ONLY against the CONTEXT. Do not use outside knowledge. An answer can be
true in the real world and still UNGROUNDED if the CONTEXT does not support it.

Reply with a single JSON object and nothing else:
{{"rationale": "<one sentence>", "label": "grounded|partial|ungrounded"}}

- grounded:   every claim in the answer is supported by the context
- partial:    the answer's main claim IS supported, but it adds at least one extra detail the context does not support
- ungrounded: the answer's main claim contradicts the context, or is not supported by it

QUERY:
{query}

CONTEXT:
{context}

ANSWER:
{answer}
"""

# When the judge itself runs in the target language rather than English, prepend
# a short instruction in that language. Whether this helps is an empirical
# question the project is meant to answer, so it is a toggle, not a default.
LANG_PREAMBLE = {
    "it": "Rispondi solo con l'oggetto JSON richiesto.",
    "fa": "فقط با همان شیء JSON خواسته‌شده پاسخ بده.",
}

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class LLMJudgeScorer(GroundednessScorer):
    def __init__(
        self,
        model: str,
        name: Optional[str] = None,
        judge_in_target_language: bool = False,
    ) -> None:
        self.model = model
        self.name = name or f"llm_judge:{model}"
        self.judge_in_target_language = judge_in_target_language

    # ------------------------------------------------------------------ #
    # The one method you implement.
    # ------------------------------------------------------------------ #
    def _complete(self, prompt: str) -> str:
        """Send `prompt` to the model and return the raw text reply.

        Wire this to your provider. A Groq example (you already use Groq):

            from groq import Groq
            client = Groq()  # reads GROQ_API_KEY from the environment

            def _complete(self, prompt: str) -> str:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return resp.choices[0].message.content

        Keep temperature at 0 so the judge is reproducible. Record the model
        string in results so a reader knows exactly which judge produced which
        numbers; judges drift between versions.
        """
        from groq import Groq

        client = Groq()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content

    def _build_prompt(self, item: EvalItem) -> str:
        prompt = JUDGE_PROMPT.format(
            query=item.query, context=item.context, answer=item.answer
        )
        if self.judge_in_target_language:
            pre = LANG_PREAMBLE.get(item.language)
            if pre:
                prompt = pre + "\n\n" + prompt
        return prompt

    def _parse(self, reply: str, item: EvalItem) -> Judgment:
        """Pull a label out of the model reply, defending against chatter."""
        rationale: Optional[str] = None
        label = Label.UNGROUNDED  # conservative default if parsing fails
        raw: dict = {"reply": reply}

        match = _JSON_RE.search(reply or "")
        if match:
            try:
                obj = json.loads(match.group(0))
                label = Label.from_str(obj.get("label", "ungrounded"))
                rationale = obj.get("rationale")
            except (json.JSONDecodeError, ValueError):
                raw["parse_error"] = True
        else:
            raw["parse_error"] = True

        return Judgment(
            item_id=item.id,
            scorer=self.name,
            label=label,
            rationale=rationale,
            language=item.language,
            raw=raw,
        )

    def score_item(self, item: EvalItem) -> Judgment:
        reply = self._complete(self._build_prompt(item))
        return self._parse(reply, item)
