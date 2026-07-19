import random
from enembert.data.splits import freeze_gold, _bucket

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

def _mk_late_rare_buckets():
    """Corpus where the rare c5 buckets ("zero" and "top") live in exactly
    one prompt each, and every other prompt carries only "low"/"mid"
    values. Unlike `_mk`, no single prompt here is independently
    bucket-complete, so `covered` can only reach all four buckets by
    admitting the two rare-bucket prompts specifically.

    The two rare-bucket prompts ("p0" and "p11") are placed dead last in
    `random.Random(42).shuffle(sorted(prompt_names))` order for the 20
    prompt names "p0".."p19" (verified empirically -- see the loop in this
    module's git history / task report). Every ordinary prompt is large
    enough (10 essays) that `n >= target` is satisfied after just the
    first 10 of the 18 ordinary prompts admitted in shuffle order --
    long before "p0"/"p11" are reached at shuffle positions 19 and 20.
    So the *only* thing that can keep the loop going past that point,
    and force it to admit "p0" and "p11", is the missing-bucket check.
    """
    rows = []
    ordinary = [f"p{i}" for i in range(20) if i not in (0, 11)]
    for name in ordinary:
        for i in range(10):
            # alternates low (c5=40) / mid (c5=120); never zero or top.
            rows.append({"essay_id": f"{name}_{i}", "id_prompt": name,
                         "c5": 40 if i % 2 == 0 else 120})
    for i in range(5):
        rows.append({"essay_id": f"p0_{i}", "id_prompt": "p0", "c5": 0})
    for i in range(5):
        rows.append({"essay_id": f"p11_{i}", "id_prompt": "p11", "c5": 200})
    return rows

def test_stratification_buckets_present():
    rows = _mk_late_rare_buckets()
    out = freeze_gold(rows, target=100, seed=42)
    ids = set(out["gold_essay_ids"])
    got = {r["c5"] for r in rows if r["essay_id"] in ids}
    assert {_bucket(c) for c in got} == {"zero", "low", "mid", "top"}, \
        f"missing bucket(s); c5 values present in gold: {sorted(got)}"
