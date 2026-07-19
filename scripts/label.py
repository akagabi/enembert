import argparse, json, random
from pathlib import Path
from enembert.labeling.run import assert_within_budget, label_rows, estimate_cost_usd

p = argparse.ArgumentParser()
p.add_argument("--set", choices=["g1", "pool", "gold"], required=True)
p.add_argument("--limit", type=int, default=0)
a = p.parse_args()

corpus = {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}
freeze = json.load(open("data/gold_freeze.json"))
ids = {"gold": freeze["gold_essay_ids"], "pool": freeze["pool_essay_ids"],
       "g1": freeze["pool_essay_ids"]}[a.set]
if a.set == "g1":
    ids = random.Random(42).sample(ids, 150)
if a.limit:
    ids = ids[: a.limit]
rows = [corpus[i] for i in ids]
assert_within_budget(rows)
print(f"labeling {len(rows)} essays, est ${estimate_cost_usd(rows):.2f}")
out = label_rows(rows)
Path("data/labels").mkdir(exist_ok=True)
with open(f"data/labels/{a.set}.jsonl", "w") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
failed = sum(1 for r in out if r["spans"] is None)
print(f"done, {failed} failed")
