"""Label every pool essay that isn't labeled yet, resumably and in budget-safe chunks.

`scripts/label.py` always labels from the start of the list and truncates its
output, which is fine for a fixed sample but not for finishing a large corpus.
This script:
  - reads the already-labeled essay_ids out of data/labels/pool.jsonl and skips them,
  - processes the remainder in chunks small enough that each chunk passes the
    per-run US$5 cost guard,
  - APPENDS each essay as it completes, so an interruption never loses paid work
    and re-running simply resumes.

Usage: python scripts/label_rest.py [--chunk 800] [--max-essays N]
"""
import argparse
import json
from pathlib import Path

from enembert.labeling.run import (assert_within_budget, check_env, estimate_cost_usd,
                                   label_rows)

OUT = Path("data/labels/pool.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=800, help="essays per budget-checked chunk")
    ap.add_argument("--max-essays", type=int, default=0, help="stop after N new essays (0 = all)")
    a = ap.parse_args()

    check_env()  # fail before touching anything if the key is missing

    corpus = {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}
    pool_ids = json.load(open("data/gold_freeze.json"))["pool_essay_ids"]

    done = set()
    if OUT.exists():
        for line in open(OUT):
            line = line.strip()
            if line:
                done.add(json.loads(line)["essay_id"])
    todo = [i for i in pool_ids if i not in done]
    if a.max_essays:
        todo = todo[: a.max_essays]

    print(f"already labeled: {len(done)}   remaining to label: {len(todo)}")
    if not todo:
        print("nothing to do")
        return

    total_est = estimate_cost_usd([corpus[i] for i in todo])
    print(f"pessimistic estimate for the remainder: ${total_est:.2f} "
          f"(real cost is far lower; the guideline prefix is prompt-cached)")

    labeled = 0
    for start in range(0, len(todo), a.chunk):
        batch_ids = todo[start:start + a.chunk]
        rows = [corpus[i] for i in batch_ids]
        assert_within_budget(rows)  # per-chunk guard
        n = start // a.chunk + 1
        total_chunks = (len(todo) + a.chunk - 1) // a.chunk
        print(f"\n--- chunk {n}/{total_chunks}: {len(rows)} essays, "
              f"est ${estimate_cost_usd(rows):.2f} ---", flush=True)
        with open(OUT, "a") as f:  # append: never clobber prior work
            def on_row(r: dict) -> None:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()

            out = label_rows(rows, on_row=on_row)
        labeled += len(out)
        failed = sum(1 for r in out if r["spans"] is None)
        print(f"chunk done: {len(out)} labeled, {failed} failed "
              f"(running total {len(done) + labeled})", flush=True)

    print(f"\nALL DONE — pool.jsonl now has {sum(1 for _ in open(OUT))} rows")


if __name__ == "__main__":
    main()
