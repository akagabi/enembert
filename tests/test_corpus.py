from enembert.data.corpus import normalize_for_hash, dedup

def _row(cfg, text, i="x"):
    return {"config": cfg, "essay_id": i, "essay_text": text,
            "id_prompt": "p", "grades": [0, 0, 0, 0, 120, 120]}

def test_normalize_collapses_ws_and_case():
    assert normalize_for_hash("A  b\nC") == normalize_for_hash("a b c")

def test_dedup_priority_a_over_b():
    rows = [_row("sourceB", "mesmo texto"), _row("sourceAOnly", "Mesmo  texto")]
    out = dedup(rows)
    assert len(out) == 1 and out[0]["config"] == "sourceAOnly"

def test_dedup_keeps_distinct():
    assert len(dedup([_row("sourceB", "um"), _row("sourceB", "dois")])) == 2

def test_dedup_priority_holds_when_higher_priority_seen_first():
    # Reverse input order: higher-priority config seen first
    rows = [_row("sourceAOnly", "Mesmo  texto"), _row("sourceB", "mesmo texto")]
    out = dedup(rows)
    assert len(out) == 1 and out[0]["config"] == "sourceAOnly"

def test_dedup_same_priority_keeps_first():
    # Two rows with same priority (sourceB) and normalizing-equal text
    rows = [_row("sourceB", "mesmo texto"), _row("sourceB", "Mesmo  texto")]
    out = dedup(rows)
    assert len(out) == 1 and out[0]["essay_text"] == "mesmo texto"
