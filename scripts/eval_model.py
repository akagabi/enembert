"""Honest evaluation of the trained model: vs the LLM labels on the held-out
gold set (never vs a "grade"), plus the grade-correlation external-validity
check. Writes docs/reports/eval.md — aggregates only, no essay text.

RUN step (not exercised by tests): requires runs/model/final,
data/corpus.jsonl, data/gold_freeze.json, data/labels/gold.jsonl.
"""
import json
from pathlib import Path

from transformers import AutoModelForTokenClassification, AutoTokenizer

from enembert.data.paragraphs import split_paragraphs
from enembert.labeling.agreement import corpus_f1
from enembert.schema import Span
from enembert.training.dataset import count_truncation_drops
from enembert.training.evaluate import grade_correlation
from enembert.training.predict import predict_spans

MODEL_DIR = "runs/model/final"
N_EXAMPLES = 5


def load_corpus() -> dict:
    return {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}


def load_gold_labels() -> dict:
    rows = (json.loads(l) for l in open("data/labels/gold.jsonl"))
    return {r["essay_id"]: [[Span(**s) for s in para] for para in r["spans"]]
            for r in rows if r["spans"] is not None}


def build_predictor(model, tok, corpus: dict, cache: dict) -> callable:
    def predictor(essay_id):
        if essay_id not in cache:
            paras = split_paragraphs(corpus[essay_id]["essay_text"])
            tail = len(paras) == 1
            cache[essay_id] = [predict_spans(model, tok, para, tail=tail) for para in paras]
        return cache[essay_id]
    return predictor


def write_report(overlap: dict, exact: dict, correlation: dict, drops: dict,
                  examples: list[tuple[str, list[str]]]) -> None:
    lines = [
        "# enemBERT — model evaluation",
        "",
        "Model vs LLM labels on the held-out, prompt-disjoint gold set. Labels are "
        "LLM-generated (weak supervision) — this is model-vs-labeler agreement, not "
        "model-vs-expert-human agreement. No essay text below, aggregates only.",
        "",
        "## Per-element F1 (model vs LLM labels, gold set)",
        "",
        "### Overlap (Jaccard >= 0.5)",
        "```json",
        json.dumps(overlap, indent=2, ensure_ascii=False),
        "```",
        "",
        "### Exact",
        "```json",
        json.dumps(exact, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Grade correlation (external validity)",
        "",
        "Spearman correlation between #distinct elements the model tags and the "
        "essay's real Competencia 5 grade (never used as training signal).",
        "```json",
        json.dumps(correlation, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Truncation drops (512 max_length, tail-truncation for single-paragraph essays)",
        "```json",
        json.dumps(drops, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Qualitative examples (essay_id + elements found only, no essay text)",
        "",
    ]
    for eid, found in examples:
        lines.append(f"- `{eid}`: {', '.join(found) if found else '(none found)'}")
    lines.append("")
    Path("docs/reports").mkdir(parents=True, exist_ok=True)
    Path("docs/reports/eval.md").write_text("\n".join(lines))


def main() -> None:
    corpus = load_corpus()
    freeze = json.load(open("data/gold_freeze.json"))
    gold_essay_ids = freeze["gold_essay_ids"]
    gold_labels = load_gold_labels()

    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)
    model.eval()

    cache: dict = {}
    predictor = build_predictor(model, tok, corpus, cache)

    model_preds = {eid: predictor(eid) for eid in gold_labels}
    overlap = corpus_f1(gold_labels, model_preds, "overlap")
    exact = corpus_f1(gold_labels, model_preds, "exact")

    gold_rows = [{"essay_id": i} for i in gold_essay_ids]
    correlation = grade_correlation(predictor, gold_rows, corpus)

    drops = count_truncation_drops(tok)

    examples = []
    for eid in gold_essay_ids[:N_EXAMPLES]:
        found = sorted({s.label for para in predictor(eid) for s in para})
        examples.append((eid, found))

    write_report(overlap, exact, correlation, drops, examples)
    print("wrote docs/reports/eval.md")


if __name__ == "__main__":
    main()
