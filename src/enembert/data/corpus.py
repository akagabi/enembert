"""Corpus download, dedup, and audit report for the ENEM AES dataset.

WARNING: essay_id encodes provenance as
``{config}:{split}:{id_prompt}:{id}``. The ``id`` column returned by the
source dataset is NOT a per-essay identifier: it is a small sequential index
("0.html", "1.html", ...) assigned per *prompt*, so it repeats across
different prompts within the very same (config, split) pair -- verified live:
in sourceAOnly/train, id "0.html" alone identifies 13 different essays (13
different id_prompt/essay_title/essay_year/essay_text values). Keying only on
``{config}:{split}:{id}`` (the originally-proposed fix for the split-
concatenation collision) collapses 3792 rows to 367 "unique" ids -- verified
by the uniqueness assertion below actually firing on the live run. The
composite key that IS unique per row, verified live across every
(config, split): ``(id_prompt, id)``. Hence id_prompt is included too.

Note: ``id_prompt`` is a clean slug in sourceAOnly/sourceB but is the raw
natural-language prompt title (which can itself contain a colon, e.g.
"Invisibilidade e registro civil: garantia de acesso...") in gradesThousand.
This does not break Task 15's ``essay_id.split(":", 1)[0]`` -> config
recovery, since only the *first* colon is used and ``config`` values
(sourceAOnly/gradesThousand/sourceB) never contain one.
"""

import hashlib
import json
from pathlib import Path

from enembert.data.paragraphs import split_paragraphs

CONFIGS = ["sourceAOnly", "gradesThousand", "sourceB"]  # dedup priority order
_PRIORITY = {c: i for i, c in enumerate(CONFIGS)}
DATASET = "kamel-usp/aes_enem_dataset"


def normalize_for_hash(text: str) -> str:
    import re

    return re.sub(r"\s+", " ", text).strip().casefold()


def dedup(rows: list[dict]) -> list[dict]:
    """Collapse rows with identical normalized essay_text, keeping the
    highest-priority config (sourceAOnly > gradesThousand > sourceB)."""
    best: dict[str, dict] = {}
    for r in rows:
        h = hashlib.sha1(normalize_for_hash(r["essay_text"]).encode()).hexdigest()
        if h not in best or _PRIORITY[r["config"]] < _PRIORITY[best[h]["config"]]:
            best[h] = r
    return list(best.values())


def load_all() -> list[dict]:  # network
    """Download every config and every split of the source dataset.

    Each config in the source dataset has a different split layout
    (sourceAOnly/gradesThousand: train+validation+test; sourceB: a single
    unnamed/full split). Taking only one split per config (e.g. just
    "train") silently drops the majority of the corpus -- verified against
    the live HF API: sourceAOnly alone loses 137 of 395 rows (65 val + 71
    test never loaded) if only "train" is read. Iterate every split.
    """
    from datasets import load_dataset

    rows = []
    for cfg in CONFIGS:
        ds = load_dataset(DATASET, cfg)
        for split_name, split in ds.items():
            for r in split:
                id_prompt = str(r["id_prompt"])
                rows.append(
                    {
                        "config": cfg,
                        "essay_id": f"{cfg}:{split_name}:{id_prompt}:{r['id']}",
                        "id_prompt": id_prompt,
                        "essay_text": r["essay_text"],
                        "grades": list(r["grades"]),
                    }
                )
    return rows


def build(out_dir: Path) -> dict:
    all_rows = load_all()
    rows = dedup(all_rows)

    ids = [r["essay_id"] for r in rows]
    unique_ids = set(ids)
    id_unique = len(ids) == len(unique_ids)
    if not id_unique:
        raise ValueError(
            f"essay_id collision detected: {len(ids)} rows but only "
            f"{len(unique_ids)} unique essay_id values. Refusing to write a "
            f"corpus with duplicate ids."
        )

    consistent = 0
    for r in rows:
        g = r["grades"]
        if sum(g[:5]) == g[5]:
            consistent += 1
    consistency_rate = round(consistent / max(len(rows), 1), 4)

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "corpus.jsonl", "w") as f:
        for r in rows:
            r["c5"] = int(r["grades"][4])
            r["n_paragraphs"] = len(split_paragraphs(r["essay_text"]))
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_paras = [r["n_paragraphs"] for r in rows]
    stats = {
        "pre_dedup_total": len(all_rows),
        "total": len(rows),
        "duplicates_removed": len(all_rows) - len(rows),
        "by_config": {c: sum(1 for r in rows if r["config"] == c) for c in CONFIGS},
        "c5_hist": {
            g: sum(1 for r in rows if r["c5"] == g)
            for g in sorted({r["c5"] for r in rows})
        },
        "para_avg": round(sum(n_paras) / max(len(rows), 1), 2),
        "para_min": min(n_paras) if n_paras else None,
        "para_max": max(n_paras) if n_paras else None,
        "grades_consistency_rate": consistency_rate,
        "essay_id_unique": id_unique,
        "essay_id_count": len(ids),
        "essay_id_unique_count": len(unique_ids),
    }
    (out_dir / "audit.md").write_text(
        "# G0 audit\n\n```json\n"
        + json.dumps(stats, indent=2, ensure_ascii=False)
        + "\n```\n"
    )
    return stats
