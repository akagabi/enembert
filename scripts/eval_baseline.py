"""Honest evaluation of the regex baseline: vs the LLM labels on the held-out
gold set, for parity with scripts/eval_model.py. Writes docs/reports/baseline.md
— aggregates only, no essay text.

RUN step (not exercised by tests): requires data/corpus.jsonl,
data/gold_freeze.json, data/labels/gold.jsonl.
"""
import json
from pathlib import Path

from enembert.data.paragraphs import split_paragraphs
from enembert.labeling.agreement import corpus_f1
from enembert.schema import Span
from enembert.training.baseline import baseline_spans
from enembert.training.evaluate import grade_correlation

N_EXAMPLES = 5


def load_corpus() -> dict:
    return {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}


def load_gold_labels() -> dict:
    rows = (json.loads(l) for l in open("data/labels/gold.jsonl"))
    return {r["essay_id"]: [[Span(**s) for s in para] for para in r["spans"]]
            for r in rows if r["spans"] is not None}


def build_predictor(corpus: dict, cache: dict) -> callable:
    def predictor(essay_id):
        if essay_id not in cache:
            paras = split_paragraphs(corpus[essay_id]["essay_text"])
            cache[essay_id] = [baseline_spans(p) for p in paras]
        return cache[essay_id]
    return predictor


def write_report(overlap: dict, exact: dict, correlation: dict,
                  examples: list[tuple[str, list[str]]]) -> None:
    lines = [
        "# enemBERT — regex baseline evaluation",
        "",
        "Baseline (marker-driven regex tagger) vs LLM labels on the held-out, "
        "prompt-disjoint gold set. For comparison against docs/reports/eval.md "
        "(the trained model). No essay text below, aggregates only.",
        "",
        "## Per-element F1 (baseline vs LLM labels, gold set)",
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
        "## Grade correlation (external validity, for parity with the model report)",
        "```json",
        json.dumps(correlation, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Qualitative examples (essay_id + elements found only, no essay text)",
        "",
    ]
    for eid, found in examples:
        lines.append(f"- `{eid}`: {', '.join(found) if found else '(none found)'}")
    lines.append("")
    Path("docs/reports").mkdir(parents=True, exist_ok=True)
    Path("docs/reports/baseline.md").write_text("\n".join(lines))


def main() -> None:
    corpus = load_corpus()
    freeze = json.load(open("data/gold_freeze.json"))
    gold_essay_ids = freeze["gold_essay_ids"]
    gold_labels = load_gold_labels()

    cache: dict = {}
    predictor = build_predictor(corpus, cache)

    baseline_preds = {eid: predictor(eid) for eid in gold_labels}
    overlap = corpus_f1(gold_labels, baseline_preds, "overlap")
    exact = corpus_f1(gold_labels, baseline_preds, "exact")

    gold_rows = [{"essay_id": i} for i in gold_essay_ids]
    correlation = grade_correlation(predictor, gold_rows, corpus)

    examples = []
    for eid in gold_essay_ids[:N_EXAMPLES]:
        found = sorted({s.label for para in predictor(eid) for s in para})
        examples.append((eid, found))

    write_report(overlap, exact, correlation, examples)
    print("wrote docs/reports/baseline.md")


if __name__ == "__main__":
    main()
