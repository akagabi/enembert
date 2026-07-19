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


def freeze_gold(rows: list[dict], target: int = 250, seed: int = 42) -> dict:
    by_prompt: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_prompt[r["id_prompt"]].append(r)
    prompts = sorted(by_prompt)
    random.Random(seed).shuffle(prompts)
    gold_prompts: list[str] = []
    covered: set[str] = set()
    n = 0
    for p in prompts:
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
    Path("data/gold_freeze.json").write_text(json.dumps(out, indent=1))
    print({"gold": len(out["gold_essay_ids"]), "pool": len(out["pool_essay_ids"]),
           "gold_prompts": len(out["gold_prompts"])})
