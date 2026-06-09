"""NLI-based groundedness scorer.

The idea: treat the context as a premise and each answer sentence as a
hypothesis, then ask a Natural Language Inference model whether the premise
entails the hypothesis. If the answer is entailed, it is grounded. If it is
contradicted or merely neutral, it is not. This is cheaper and faster than an
LLM judge and gives a continuous entailment score you can threshold.

The catch, and the reason it belongs in a multilingual project: most strong NLI
models are English-first. Cross-lingual NLI checkpoints exist (XNLI-trained
mDeBERTa and similar), but their quality is uneven across languages, which is
itself a finding worth reporting. Persian coverage in particular is thin.

`transformers` and `torch` are imported lazily inside `_load`, so the core
package and the test suite do not need them installed.
"""

from __future__ import annotations

from typing import Optional

from ..types import EvalItem, Judgment, Label
from .base import GroundednessScorer

# A multilingual NLI checkpoint is a reasonable starting point. Swap it for
# whatever you validate best on your gold set; the contract below does not care
# which model sits behind it.
DEFAULT_MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"


class NLIGroundednessScorer(GroundednessScorer):
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        entail_threshold: float = 0.5,
        contradiction_margin: float = 0.5,
        name: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.entail_threshold = entail_threshold
        self.contradiction_margin = contradiction_margin
        self.name = name or f"nli:{model_name.split('/')[-1]}"
        self._pipe = None  # populated on first use

    def _load(self):
        """Build the NLI pipeline once, on first call.

        Reference implementation (uncomment once you add the `nli` extra):

            from transformers import pipeline
            self._pipe = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,          # return scores for all labels
            )

        The model emits three labels: entailment, neutral, contradiction. Map
        the highest-probability label to a groundedness verdict in `score_item`.
        """
        raise NotImplementedError(
            "Install the 'nli' extra (pip install multifaith[nli]) and "
            "uncomment the pipeline construction in NLIGroundednessScorer._load."
        )

    def _entailment_scores(self, premise: str, hypothesis: str) -> dict[str, float]:
        """Return {entailment, neutral, contradiction} probabilities.

        Once `_load` is wired, this is roughly:

            out = self._pipe({"text": premise, "text_pair": hypothesis})
            return {d["label"].lower(): d["score"] for d in out[0]}
        """
        if self._pipe is None:
            self._load()
        raise NotImplementedError("Implement once the NLI pipeline is wired.")

    def score_item(self, item: EvalItem) -> Judgment:
        # A real implementation would split `item.answer` into sentences, score
        # each against the context, and aggregate (the weakest sentence usually
        # decides the verdict). The structure below shows the intended mapping.
        scores = self._entailment_scores(item.context, item.answer)
        entail = scores.get("entailment", 0.0)
        contra = scores.get("contradiction", 0.0)

        if entail >= self.entail_threshold:
            label = Label.GROUNDED
        elif contra >= self.contradiction_margin:
            label = Label.UNGROUNDED
        else:
            label = Label.PARTIAL

        return Judgment(
            item_id=item.id,
            scorer=self.name,
            label=label,
            score=entail,
            language=item.language,
            raw=scores,
        )
