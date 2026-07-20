import numpy as np
from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                          DataCollatorForTokenClassification, EarlyStoppingCallback,
                          Trainer, TrainingArguments)
from enembert.schema import ID2LABEL, LABEL2ID
from enembert.training.dataset import build_hf_dataset

BACKBONE = "neuralmind/bert-base-portuguese-cased"


def train(out_dir="runs/model", epochs=6, lr=2e-5, batch=16):
    tok = AutoTokenizer.from_pretrained(BACKBONE)
    ds = build_hf_dataset(tok)
    model = AutoModelForTokenClassification.from_pretrained(
        BACKBONE, num_labels=len(LABEL2ID), id2label=ID2LABEL, label2id=LABEL2ID)

    def metrics(p):
        from seqeval.metrics import f1_score
        preds = np.argmax(p.predictions, -1)
        y_true, y_pred = [], []
        for pr, lb in zip(preds, p.label_ids):
            y_true.append([ID2LABEL[l] for l in lb if l != -100])
            y_pred.append([ID2LABEL[q] for q, l in zip(pr, lb) if l != -100])
        return {"f1": f1_score(y_true, y_pred)}

    args = TrainingArguments(out_dir, learning_rate=lr, num_train_epochs=epochs,
                             warmup_ratio=0.1, per_device_train_batch_size=batch,
                             eval_strategy="epoch", save_strategy="epoch",
                             load_best_model_at_end=True, metric_for_best_model="f1",
                             seed=42, logging_steps=50)
    Trainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["dev"],
            data_collator=DataCollatorForTokenClassification(tok),
            compute_metrics=metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]).train()
    model.save_pretrained(out_dir + "/final"); tok.save_pretrained(out_dir + "/final")
