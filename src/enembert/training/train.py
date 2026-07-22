import numpy as np
import torch
from collections import Counter
from torch import nn
from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                          DataCollatorForTokenClassification, EarlyStoppingCallback,
                          Trainer, TrainingArguments)
from enembert.schema import ID2LABEL, LABEL2ID
from enembert.training.dataset import build_hf_dataset

BACKBONE = "neuralmind/bert-base-portuguese-cased"


def class_weights(ds) -> torch.Tensor:
    """sqrt-balanced class weights to counter the rare-element collapse.

    MEIO (353) and DETALHAMENTO (129) training spans are dwarfed by AGENTE/ACAO
    (~1000 each) and by the dominant "O" token, so plain cross-entropy learns to
    never predict the rare classes. Weight each class by sqrt(total/(n*count)) —
    upweights rare classes without the instability of raw inverse-frequency —
    clamped to [0.5, 20]. Computed from the actual train split, not hardcoded.
    """
    counts = Counter()
    for ex in ds["train"]:
        for l in ex["labels"]:
            if l != -100:
                counts[l] += 1
    total = sum(counts.values())
    n = len(LABEL2ID)
    w = torch.ones(n)
    for i in range(n):
        w[i] = (total / (n * counts.get(i, 1))) ** 0.5
    return w.clamp(0.5, 20.0)


class WeightedTrainer(Trainer):
    def __init__(self, *a, class_weights=None, **k):
        super().__init__(*a, **k)
        self._cw = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fn = nn.CrossEntropyLoss(weight=self._cw.to(logits.device), ignore_index=-100)
        loss = loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def latest_checkpoint(out_dir: str):
    """Newest checkpoint-N in out_dir, or None. Lets training survive being killed."""
    import re
    from pathlib import Path
    cks = [p for p in Path(out_dir).glob("checkpoint-*") if (p / "trainer_state.json").exists()]
    if not cks:
        return None
    return str(max(cks, key=lambda p: int(re.search(r"checkpoint-(\d+)", p.name).group(1))))


def train(out_dir="runs/model", epochs=6, lr=2e-5, batch=8, save_steps=250, resume=True):
    tok = AutoTokenizer.from_pretrained(BACKBONE)
    ds = build_hf_dataset(tok)
    model = AutoModelForTokenClassification.from_pretrained(
        BACKBONE, num_labels=len(LABEL2ID), id2label=ID2LABEL, label2id=LABEL2ID)
    cw = class_weights(ds)
    print("class weights:", {ID2LABEL[i]: round(float(cw[i]), 2) for i in range(len(cw))})

    def metrics(p):
        from seqeval.metrics import f1_score
        preds = np.argmax(p.predictions, -1)
        y_true, y_pred = [], []
        for pr, lb in zip(preds, p.label_ids):
            y_true.append([ID2LABEL[l] for l in lb if l != -100])
            y_pred.append([ID2LABEL[q] for q, l in zip(pr, lb) if l != -100])
        return {"f1": f1_score(y_true, y_pred)}

    # Checkpoint every `save_steps` rather than per-epoch: long runs on this machine
    # get killed, and step-level checkpoints mean each partial run banks progress that
    # the next invocation resumes from instead of starting over.
    args = TrainingArguments(out_dir, learning_rate=lr, num_train_epochs=epochs,
                             warmup_ratio=0.1, per_device_train_batch_size=batch,
                             eval_strategy="steps", save_strategy="steps",
                             eval_steps=save_steps, save_steps=save_steps,
                             save_total_limit=3,
                             load_best_model_at_end=True, metric_for_best_model="f1",
                             seed=42, logging_steps=50)
    ck = latest_checkpoint(out_dir) if resume else None
    if ck:
        print(f"resuming from {ck}")
    WeightedTrainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["dev"],
                    data_collator=DataCollatorForTokenClassification(tok),
                    compute_metrics=metrics, class_weights=cw,
                    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
                    ).train(resume_from_checkpoint=ck)
    model.save_pretrained(out_dir + "/final"); tok.save_pretrained(out_dir + "/final")
