import argparse, json, random
from pathlib import Path
from enembert.labeling.run import (assert_within_budget, check_env, label_rows,
                                   estimate_cost_usd)

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
# Validate the API key BEFORE touching the output file. Opening it for writing
# truncates any existing labels, so a missing/bad key used to destroy a previous
# run's results before a single essay was labeled. Fail fast, touch nothing.
check_env()
print(f"labeling {len(rows)} essays, est ${estimate_cost_usd(rows):.2f}")

out_path = Path(f"data/labels/{a.set}.jsonl")
if out_path.exists():  # keep the previous run recoverable
    out_path.replace(out_path.with_suffix(".jsonl.bak"))
Path("data/labels").mkdir(exist_ok=True)
# Open for writing and persist each row as it completes, BEFORE label_rows
# starts, so a crash (or Ctrl-C, or OOM) mid-batch never loses already-paid
# API results: everything labeled so far is already flushed to disk.
with open(f"data/labels/{a.set}.jsonl", "w") as f:
    def on_row(r: dict) -> None:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()

    out = label_rows(rows, on_row=on_row)

failed = sum(1 for r in out if r["spans"] is None)
print(f"done, {failed} failed")
