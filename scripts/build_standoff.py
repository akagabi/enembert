"""Build the stand-off dataset: data/standoff/{train,gold}.jsonl (essay_id +
config + char offsets + labels -- NEVER essay text), plus a self-contained
loader (data/standoff/load_enembert.py) and a bilingual dataset card
(data/standoff/README.md).

Source-copyright constraint: kamel-usp/aes_enem_dataset carries an upstream
copyright caveat on the essay text, so this project never redistributes it.
Every row this script writes must be text-free -- verify with
`grep -c essay_text data/standoff/*.jsonl` (must be 0) after running.

RUN step (not exercised by tests): requires data/labels/pool.jsonl and
data/labels/gold.jsonl. No network access.
"""
import json
from pathlib import Path

from enembert.data.standoff import to_standoff

OUT_DIR = Path("data/standoff")

LOADER_SOURCE = '''"""Self-contained loader for the enemBERT stand-off dataset.

This project never redistributes kamel-usp/aes_enem_dataset essay text (see
its upstream copyright caveat). The files shipped alongside this loader
(train.jsonl / gold.jsonl) contain only essay_id + char offsets + labels.
This loader re-downloads the source corpus from the Hugging Face Hub and
re-joins each stand-off row to its paragraph text by essay_id + offsets.

No dependency on the enembert package itself -- copy/paste-safe. Only
dependency: `datasets` (`pip install datasets`).

Usage:
    python load_enembert.py                     # smoke check
    from load_enembert import load_split
    rows = list(load_split("train.jsonl"))       # or "gold.jsonl"
"""
import json
from pathlib import Path

CONFIGS = ["sourceAOnly", "gradesThousand", "sourceB"]
DATASET = "kamel-usp/aes_enem_dataset"

HERE = Path(__file__).parent


def split_paragraphs(essay_text: str) -> list[str]:
    """Mirrors enembert.data.paragraphs.split_paragraphs exactly: this is
    the frozen offsets contract every span in this dataset was recorded
    against. Do not change this function's behavior."""
    return [p.strip() for p in essay_text.split("\\n") if p.strip()]


def _download_essays() -> dict:
    """Re-download every config/split of the source dataset and index by
    essay_id, mirroring enembert.data.corpus.load_all's essay_id scheme:
    f"{config}:{split_name}:{id_prompt}:{id}"."""
    from datasets import load_dataset

    essays = {}
    for cfg in CONFIGS:
        ds = load_dataset(DATASET, cfg)
        for split_name, split in ds.items():
            for r in split:
                id_prompt = str(r["id_prompt"])
                essay_id = f"{cfg}:{split_name}:{id_prompt}:{r[\'id\']}"
                essays[essay_id] = r["essay_text"]
    return essays


def load_split(standoff_path: str = "train.jsonl"):
    """Yield {essay_id, config, paragraphs, para_spans} for every row in a
    stand-off file, joining offsets back onto freshly-downloaded essay text.

    paragraphs[i] is the text that para_spans entries with para_idx == i
    index into (via split_paragraphs(essay_text)[para_idx]).
    """
    essays = _download_essays()
    path = Path(standoff_path)
    if not path.is_absolute() and not path.exists():
        path = HERE / standoff_path
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            essay_text = essays.get(row["essay_id"])
            if essay_text is None:
                continue
            paragraphs = split_paragraphs(essay_text)
            yield {
                "essay_id": row["essay_id"],
                "config": row["config"],
                "paragraphs": paragraphs,
                "para_spans": row["para_spans"],
            }


if __name__ == "__main__":
    example = next(load_split("train.jsonl"))
    labels = [s["label"] for s in example["para_spans"]]
    print(f"essay_id: {example[\'essay_id\']}")
    print(f"config: {example[\'config\']}")
    print(f"n_paragraphs: {len(example[\'paragraphs\'])}")
    print(f"element labels: {labels}")
'''

README_SOURCE = """# enemBERT stand-off dataset (DRAFT)

## What this is / O que é isto

**EN.** Stand-off span annotations of ENEM "proposta de intervenção"
(Competência 5) rhetorical elements -- AGENTE, AÇÃO, MEIO, EFEITO,
DETALHAMENTO -- over essays from `kamel-usp/aes_enem_dataset`. "Stand-off"
means this dataset ships **no essay text**: only `essay_id`, `config`,
paragraph index, character offsets, and label per span. Because the source
dataset carries an upstream copyright caveat on essay text, we never
redistribute it. Use `load_enembert.py` to re-download the source corpus
and re-join annotations to text locally.

**PT.** Anotações "stand-off" (sem o texto) de elementos retóricos da
proposta de intervenção do ENEM (Competência 5) -- AGENTE, AÇÃO, MEIO,
EFEITO, DETALHAMENTO -- sobre redações de `kamel-usp/aes_enem_dataset`.
"Stand-off" significa que este dataset **não contém o texto das redações**:
apenas `essay_id`, `config`, índice de parágrafo, offsets de caracteres e
o rótulo de cada trecho. Como o dataset de origem tem uma ressalva de
direitos autorais sobre o texto das redações, nunca o redistribuímos. Use
`load_enembert.py` para baixar o corpus de origem e reconstruir localmente
a junção entre anotações e texto.

## Labels are LLM-generated, NOT human-verified gold / Rótulos gerados por LLM, NÃO são gold verificado por humanos

**EN. Important disclosure:** the spans in `train.jsonl` (and, unless noted
otherwise in a future release, `gold.jsonl`) were produced by an LLM under
weak supervision -- they are **not** human-annotated or human-verified
ground truth. Treat them as noisy silver labels suitable for pretraining /
prototyping, not as an evaluation gold standard, unless a specific split is
explicitly documented as human-reviewed.

**PT. Divulgação importante:** os trechos anotados em `train.jsonl` (e, a
menos que uma release futura documente o contrário, em `gold.jsonl`) foram
gerados por um LLM sob supervisão fraca (weak supervision) -- **não** são
anotações ou verificações feitas por humanos. Trate-os como rótulos "silver"
ruidosos, adequados para pré-treino/prototipagem, e não como padrão-ouro de
avaliação, a menos que um split específico seja explicitamente documentado
como revisado por humanos.

## Files

- `train.jsonl` -- stand-off rows built from the labeling pool.
- `gold.jsonl` -- stand-off rows built from the held-out gold set (see the
  disclosure above: this is LLM-labeled, not human-verified, unless stated
  otherwise).
- `load_enembert.py` -- self-contained loader (only depends on `datasets`).

Each row:

```json
{"essay_id": "sourceB:full:...:119.html",
 "config": "sourceB",
 "kamel_usp_config": "sourceB",
 "para_spans": [{"para_idx": 3, "start": 120, "end": 128, "label": "AGENTE"}, ...]}
```

## How to load / Como carregar

```bash
pip install datasets
python load_enembert.py            # smoke check: prints one joined example's labels
```

```python
from load_enembert import load_split

for row in load_split("train.jsonl"):
    print(row["essay_id"], row["config"])
    for span in row["para_spans"]:
        text = row["paragraphs"][span["para_idx"]][span["start"]:span["end"]]
        print(span["label"], text)
```

`load_split` re-downloads `kamel-usp/aes_enem_dataset` (all configs, all
splits) from the Hugging Face Hub, splits each essay into paragraphs with
the same rule the offsets were recorded against (split on `\\n`, strip,
drop empty paragraphs), and joins each stand-off row's `para_spans` back
onto `paragraphs[para_idx][start:end]`.

## Label set / Conjunto de rótulos

`AGENTE`, `ACAO`, `MEIO`, `EFEITO`, `DETALHAMENTO` -- the five rhetorical
elements of the ENEM "proposta de intervenção" (Competência 5).

## Credit / Crédito

Built entirely on top of **`kamel-usp/aes_enem_dataset`**
(https://huggingface.co/datasets/kamel-usp/aes_enem_dataset). All essay
text and grades originate there; this dataset only adds span annotations
and offsets. Please cite/credit the source dataset when using this one.

Construído inteiramente sobre **`kamel-usp/aes_enem_dataset`**
(https://huggingface.co/datasets/kamel-usp/aes_enem_dataset). Todo o texto
das redações e as notas têm origem lá; este dataset apenas adiciona
anotações de trechos e offsets. Cite/credite o dataset de origem ao
utilizar este.

## Non-affiliation

Projeto independente, não afiliado ao INEP/MEC. Independent project, not
affiliated with INEP/MEC (the Brazilian bodies that administer the ENEM
exam).

## Status

**DRAFT.** This card and the `data/standoff/` files are local-only build
artifacts (the `data/` directory is gitignored) pending deliberate
publication to the Hugging Face Hub.
"""


def _rows_from(path: Path) -> list[dict]:
    out = []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            if row.get("spans") is None:
                continue
            out.append(to_standoff(row))
    return out


def build() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    train_rows = _rows_from(Path("data/labels/pool.jsonl"))
    gold_rows = _rows_from(Path("data/labels/gold.jsonl"))

    with open(OUT_DIR / "train.jsonl", "w") as f:
        for r in train_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(OUT_DIR / "gold.jsonl", "w") as f:
        for r in gold_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    (OUT_DIR / "load_enembert.py").write_text(LOADER_SOURCE)
    (OUT_DIR / "README.md").write_text(README_SOURCE)

    return {"train": len(train_rows), "gold": len(gold_rows)}


if __name__ == "__main__":
    stats = build()
    print(f"wrote {stats['train']} train rows, {stats['gold']} gold rows to {OUT_DIR}/")
