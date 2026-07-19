import random
from enembert.data.splits import freeze_gold, _bucket

def _mk(n_prompts=40, per=12):
    """All essays multi-paragraph -> every prompt is structure-eligible;
    this fixture exists to test disjointness/size/determinism, not
    eligibility filtering."""
    rows, c5s = [], [0, 40, 80, 120, 160, 200]
    for p in range(n_prompts):
        for i in range(per):
            rows.append({"essay_id": f"e{p}_{i}", "id_prompt": f"p{p}",
                         "c5": c5s[(p + i) % 6], "n_paragraphs": 3})
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

    The two rare-bucket prompts are deliberately the LARGEST (20 essays vs
    10), so smallest-first ordering puts them dead last. The loop therefore
    reaches `target` using only low/mid prompts, and the missing-bucket
    check is the sole reason it keeps going far enough to admit "p0" and
    "p11". Delete `covered >= {...}` and this fixture stops at low/mid only
    -- which is exactly what makes the test discriminating. Sizes here are
    load-bearing: equalising them silently disarms the test.
    """
    rows = []
    ordinary = [f"p{i}" for i in range(20) if i not in (0, 11)]
    for name in ordinary:
        for i in range(10):
            # alternates low (c5=40) / mid (c5=120); never zero or top.
            rows.append({"essay_id": f"{name}_{i}", "id_prompt": name,
                         "c5": 40 if i % 2 == 0 else 120, "n_paragraphs": 3})
    for i in range(20):
        rows.append({"essay_id": f"p0_{i}", "id_prompt": "p0", "c5": 0,
                     "n_paragraphs": 3})
    for i in range(20):
        rows.append({"essay_id": f"p11_{i}", "id_prompt": "p11", "c5": 200,
                     "n_paragraphs": 3})
    return rows

def test_stratification_buckets_present():
    rows = _mk_late_rare_buckets()
    out = freeze_gold(rows, target=100, seed=42)
    ids = set(out["gold_essay_ids"])
    got = {r["c5"] for r in rows if r["essay_id"] in ids}
    assert {_bucket(c) for c in got} == {"zero", "low", "mid", "top"}, \
        f"missing bucket(s); c5 values present in gold: {sorted(got)}"

def test_eligibility_excludes_single_paragraph_prompts():
    """A prompt whose essays are predominantly single-paragraph must never
    enter gold, even when it alone would satisfy the size target."""
    rows = []
    # One huge, structurally-ineligible prompt: 300 essays, all blobs
    # (n_paragraphs=1), spanning every c5 bucket -- on size and coverage
    # alone this prompt would satisfy the old stop condition by itself.
    c5s = [0, 40, 80, 120, 160, 200]
    for i in range(300):
        rows.append({"essay_id": f"blob_{i}", "id_prompt": "blob_prompt",
                     "c5": c5s[i % 6], "n_paragraphs": 1})
    # A handful of small, eligible, multi-paragraph prompts covering all
    # buckets, so a valid gold set is still reachable without "blob_prompt".
    for p in range(10):
        for i in range(5):
            rows.append({"essay_id": f"ok{p}_{i}", "id_prompt": f"ok{p}",
                         "c5": c5s[(p + i) % 6], "n_paragraphs": 2})

    out = freeze_gold(rows, target=20, seed=42)
    assert "blob_prompt" not in set(out["gold_prompts"])
    # every gold essay_id must belong to one of the eligible "ok*" prompts
    assert set(out["gold_essay_ids"]) <= {r["essay_id"] for r in rows
                                           if r["id_prompt"] != "blob_prompt"}

def test_prompt_count_favors_many_small_prompts():
    """Pins the defect this amendment fixes: with many small eligible
    prompts and a few giant ones, gold must span many distinct prompts
    rather than being dominated by one or two giants.

    Against the OLD shuffle-whole-list-then-admit-until-target strategy,
    seed=42 draws a giant prompt early (see test_deterministic's `_mk`-style
    corpus for precedent that shuffle order is seed-sensitive), which alone
    clears both the essay-count target and full bucket coverage -- so the
    old code stops after 1-2 prompts. Smallest-first ordering can't do
    that: it must exhaust the small prompts before a giant is even
    reachable, so gold ends up spanning most/all of the small prompts.
    """
    rows = []
    c5s = [0, 40, 80, 120, 160, 200]
    # Two giant prompts, each alone bigger than target and individually
    # bucket-complete -- exactly the failure mode from the real corpus.
    for g in range(2):
        for i in range(200):
            rows.append({"essay_id": f"giant{g}_{i}", "id_prompt": f"giant{g}",
                         "c5": c5s[i % 6], "n_paragraphs": 3})
    # 30 small eligible prompts (5 essays each -> 150 essays total), each
    # individually bucket-incomplete, together covering all four buckets.
    for p in range(30):
        for i in range(5):
            rows.append({"essay_id": f"small{p}_{i}", "id_prompt": f"small{p}",
                         "c5": c5s[(p + i) % 6], "n_paragraphs": 2})

    out = freeze_gold(rows, target=100, seed=42)
    gold_prompts = set(out["gold_prompts"])
    small_prompts_in_gold = {p for p in gold_prompts if p.startswith("small")}
    giant_prompts_in_gold = {p for p in gold_prompts if p.startswith("giant")}
    # smallest-first must exhaust (or nearly exhaust) the 30 small prompts
    # before it can reach either 200-essay giant.
    assert len(small_prompts_in_gold) >= 20
    assert len(gold_prompts) >= 20
    assert not giant_prompts_in_gold or len(small_prompts_in_gold) == 30
