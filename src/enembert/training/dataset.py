import json
import random
from enembert.schema import LABEL2ID, Span, spans_to_bio
from enembert.data.paragraphs import split_paragraphs


def encode_paragraph(tokenizer, paragraph, spans, max_length=512, tail=False):
    tokenizer.truncation_side = "left" if tail else "right"
    enc = tokenizer(paragraph, truncation=True, max_length=max_length,
                    return_offsets_mapping=True)
    offsets = enc.pop("offset_mapping")
    tokens = [(a, b) for a, b in offsets]
    tags = spans_to_bio(paragraph, spans, tokens)
    labels = [-100 if a == b else LABEL2ID[t] for (a, b), t in zip(tokens, tags)]
    # a span is "dropped" if no surviving content token overlaps it
    content = [(a, b) for a, b in tokens if a != b]
    def survives(sp):
        return any(a < sp.end and sp.start < b for a, b in content)
    dropped = sum(0 if survives(sp) else 1 for sp in spans)
    out = dict(enc)
    out["labels"] = labels
    out["dropped_spans"] = dropped
    return out


def _split_rows():
    corpus = {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}
    rows = [json.loads(l) for l in open("data/labels/pool.jsonl")]
    rows = [r for r in rows if r["spans"] is not None]
    prompts = sorted({corpus[r["essay_id"]]["id_prompt"] for r in rows})
    random.Random(42).shuffle(prompts)
    dev_prompts = set(prompts[: max(1, len(prompts) // 10)])
    return corpus, rows, dev_prompts


def _encode_row(tokenizer, corpus, r, out_list, drop_acc):
    text = corpus[r["essay_id"]]["essay_text"]
    paras = split_paragraphs(text)
    tail = len(paras) == 1
    for para, raw in zip(paras, r["spans"]):
        enc = encode_paragraph(tokenizer, para, [Span(**s) for s in raw],
                               max_length=384, tail=tail)
        drop_acc[0] += enc.pop("dropped_spans")
        out_list.append(enc)


def build_hf_dataset(tokenizer):
    from datasets import Dataset, DatasetDict
    corpus, rows, dev_prompts = _split_rows()
    feats = {"train": [], "dev": []}
    drop = [0]
    for r in rows:
        split = "dev" if corpus[r["essay_id"]]["id_prompt"] in dev_prompts else "train"
        _encode_row(tokenizer, corpus, r, feats[split], drop)
    print(f"spans dropped by truncation: {drop[0]}")
    return DatasetDict({k: Dataset.from_list(v) for k, v in feats.items()})


def count_truncation_drops(tokenizer):
    corpus, rows, _ = _split_rows()
    drop = [0]
    total_spans = 0
    for r in rows:
        total_spans += sum(len(p) for p in r["spans"])
        _encode_row(tokenizer, corpus, r, [], drop)
    return {"dropped": drop[0], "total_spans": total_spans,
            "pct": round(100 * drop[0] / max(total_spans, 1), 2)}
