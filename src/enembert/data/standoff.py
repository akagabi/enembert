"""Stand-off conversion: labels rows (which carry only offsets, never essay
text) -> the flat stand-off record shape shipped in the published dataset.

WARNING: this module must never touch essay text. The whole point of
"stand-off" annotations is that the published files contain essay_id +
char offsets + labels only; consumers re-download the source corpus
(kamel-usp/aes_enem_dataset) and re-join by essay_id + split_paragraphs()
offsets (see data/standoff/load_enembert.py). Do not add an essay_text
field here, ever.
"""


def to_standoff(labels_row: dict) -> dict:
    flat = []
    for i, para in enumerate(labels_row["spans"] or []):
        for s in para:
            flat.append({"para_idx": i, "start": s["start"], "end": s["end"],
                         "label": s["label"]})
    cfg = labels_row["essay_id"].split(":", 1)[0]
    return {"essay_id": labels_row["essay_id"], "config": cfg,
            "kamel_usp_config": cfg, "para_spans": flat}
