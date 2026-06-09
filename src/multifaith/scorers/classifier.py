"""Fine-tuned classifier baseline.

A small encoder (the kind you can fine-tune on a single GPU, or even CPU for a
toy run) trained directly on your gold labels. The input is the context and the
answer concatenated; the output is one of the three labels. It will not beat a
strong LLM judge on raw accuracy, and that is the point. A classifier you
trained yourself, on a few hundred examples, is the honest baseline that makes
the LLM-judge numbers mean something. It is also the low-latency option a
production team would reach for, so it earns its place.

This is the most "research engineering" component in the kit: data prep,
training loop, checkpointing, inference. I left the heavy parts as clearly
marked stubs because they depend on choices (model size, epochs, GPU vs CPU)
that are yours to make and to defend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..types import EvalItem, Judgment, Label
from .base import GroundednessScorer

DEFAULT_BASE_MODEL = "microsoft/mdeberta-v3-base"  # multilingual encoder


class FineTunedClassifierScorer(GroundednessScorer):
    def __init__(
        self,
        checkpoint_dir: str,
        base_model: str = DEFAULT_BASE_MODEL,
        name: Optional[str] = None,
    ) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.base_model = base_model
        self.name = name or "finetuned_classifier"
        self._model = None
        self._tokenizer = None

    # ------------------------------------------------------------------ #
    # Training (run once, offline)
    # ------------------------------------------------------------------ #
    @staticmethod
    def train(
        train_items: list[EvalItem],
        out_dir: str,
        base_model: str = DEFAULT_BASE_MODEL,
        epochs: int = 3,
    ) -> None:
        """Fine-tune the baseline on labelled items and save to `out_dir`.

        Sketch of a real implementation (needs the 'nli' extra plus
        `accelerate` and `datasets`):

            1. Build examples as text = context + [SEP] + answer, label = gold.
            2. Tokenize with AutoTokenizer.from_pretrained(base_model).
            3. AutoModelForSequenceClassification with num_labels=3.
            4. Trainer / a plain torch loop, epochs as given, eval each epoch.
            5. model.save_pretrained(out_dir); tokenizer.save_pretrained(out_dir).

        With a gold set of a few hundred items you will want stratified k-fold
        rather than a single split, and you should report variance across folds.
        A single accuracy number from one split on 300 examples is not evidence;
        a reviewer who knows this will ask, so get ahead of it.
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        raise NotImplementedError(
            "Implement training. See the docstring for the intended pipeline."
        )

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #
    def _load(self):
        """Load a saved checkpoint on first use.

            from transformers import (
                AutoModelForSequenceClassification, AutoTokenizer,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(self.checkpoint_dir)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.checkpoint_dir
            ).eval()
        """
        raise NotImplementedError(
            "Train a checkpoint first (FineTunedClassifierScorer.train), then "
            "wire _load to read it back."
        )

    _ID2LABEL = {0: Label.GROUNDED, 1: Label.PARTIAL, 2: Label.UNGROUNDED}

    def score_item(self, item: EvalItem) -> Judgment:
        if self._model is None:
            self._load()
        # Intended shape once wired:
        #   text = item.context + " [SEP] " + item.answer
        #   logits = self._model(**self._tokenizer(text, ...)).logits
        #   idx = int(logits.argmax()); label = self._ID2LABEL[idx]
        raise NotImplementedError("Implement classifier inference.")
