import random
from enembert.data.splits import freeze_gold

def _mk(n_prompts=40, per=12):
    rows, c5s = [], [0, 40, 80, 120, 160, 200]
    for p in range(n_prompts):
        for i in range(per):
            rows.append({"essay_id": f"e{p}_{i}", "id_prompt": f"p{p}",
                         "c5": c5s[(p + i) % 6]})
    return rows

def test_prompt_disjoint_and_size():
    rows = _mk()
    out = freeze_gold(rows, target=100, seed=42)
    gold_prompts = set(out["gold_prompts"])
    for r in rows:
        in_gold = r["essay_id"] in set(out["gold_essay_ids"])
        assert in_gold == (r["id_prompt"] in gold_prompts)
    assert len(out["gold_essay_ids"]) >= 100

def test_deterministic():
    rows = _mk()
    assert freeze_gold(rows, 100, 42) == freeze_gold(rows, 100, 42)

def test_stratification_buckets_present():
    rows = _mk()
    ids = set(freeze_gold(rows, 100, 42)["gold_essay_ids"])
    got = {r["c5"] for r in rows if r["essay_id"] in ids}
    assert 0 in got and 200 in got
