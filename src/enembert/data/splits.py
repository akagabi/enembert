"""Prompt-disjoint gold/pool freeze for evaluation.

The gold set is frozen before any LLM labeling: it is the project's only
honest measuring stick. The split is prompt-disjoint -- an id_prompt lives
entirely in gold or entirely in the training pool -- because essays
answering the same prompt share vocabulary and arguments, and letting a
prompt straddle the split would leak the test set into training.
"""

import json, random
from collections import defaultdict
from pathlib import Path


def _bucket(c5: int) -> str:
    if c5 == 0: return "zero"
    if c5 <= 80: return "low"
    if c5 <= 160: return "mid"
    return "top"


def _structure_eligible(prompt_rows: list[dict]) -> bool:
    """A prompt is gold-eligible only if paragraph structure survived for
    most of its essays.

    Spans are char offsets into split_paragraphs(essay_text)[para_idx]. A
    prompt built mostly of single-paragraph blobs can't exercise
    paragraph-boundary behavior at all, and hand-annotating a ~1,800-char
    blob is far more error-prone than annotating real paragraphs. Threshold
    is on structure (n_paragraphs), never on config name -- config is
    incidental, paragraph structure is the actual reason.
    """
    multi = sum(1 for r in prompt_rows if r["n_paragraphs"] >= 2)
    return multi / len(prompt_rows) >= 0.8


def freeze_gold(rows: list[dict], target: int = 250, seed: int = 42) -> dict:
    by_prompt: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_prompt[r["id_prompt"]].append(r)

    # Only structure-eligible prompts may enter gold; everything else falls
    # through to the pool untouched, same as any other non-gold prompt.
    eligible = [p for p in sorted(by_prompt) if _structure_eligible(by_prompt[p])]

    # seed breaks ties among equal-sized prompts, deterministically: shuffle
    # first, then a *stable* sort by size preserves the shuffled relative
    # order within each size tie. Neither step depends on PYTHONHASHSEED
    # (random.Random(seed) is seeded from a plain int; sorted()/list.sort()
    # order by string/int value, not hash), so the result is byte-identical
    # across runs and processes.
    random.Random(seed).shuffle(eligible)
    eligible.sort(key=lambda p: len(by_prompt[p]))  # smallest prompt first

    gold_prompts: list[str] = []
    covered: set[str] = set()
    n = 0
    for p in eligible:
        if n >= target and covered >= {"zero", "low", "mid", "top"}:
            break
        gold_prompts.append(p)
        n += len(by_prompt[p])
        covered |= {_bucket(r["c5"]) for r in by_prompt[p]}
    gp = set(gold_prompts)
    return {"gold_prompts": sorted(gp),
            "gold_essay_ids": sorted(r["essay_id"] for r in rows if r["id_prompt"] in gp),
            "pool_essay_ids": sorted(r["essay_id"] for r in rows if r["id_prompt"] not in gp)}


def main():
    rows = [json.loads(l) for l in open("data/corpus.jsonl")]
    out = freeze_gold(rows)
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("data/gold_freeze.json").write_text(json.dumps(out, indent=1))
    print({"gold": len(out["gold_essay_ids"]), "pool": len(out["pool_essay_ids"]),
           "gold_prompts": len(out["gold_prompts"])})
