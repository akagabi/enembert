import json

import pytest

from enembert.labeling import run as run_module
from enembert.labeling.run import estimate_cost_usd, check_env, CostGuardError, label_rows


def test_cost_estimate_scales():
    rows = [{"essay_text": "x" * 3000}] * 100
    assert 0 < estimate_cost_usd(rows) < 5


def test_cost_guard_trips():
    rows = [{"essay_text": "x" * 3000}] * 100000
    with pytest.raises(CostGuardError):
        from enembert.labeling.run import assert_within_budget
        assert_within_budget(rows)


def test_env_refuses_blocked_org_vars(monkeypatch):
    monkeypatch.setenv("ENEMBERT_LABELER_KEY", "k")
    monkeypatch.setenv("ENEMBERT_BLOCKED_ORG", "some-org")
    monkeypatch.setenv("HF_ORG", "some-org-labs")
    with pytest.raises(RuntimeError):
        check_env()


def test_env_allows_personal_key_when_no_org_is_blocked(monkeypatch):
    """The tripwire is opt-in: without ENEMBERT_BLOCKED_ORG it must not fire."""
    monkeypatch.delenv("ENEMBERT_BLOCKED_ORG", raising=False)
    monkeypatch.setenv("ENEMBERT_LABELER_KEY", "k")
    monkeypatch.setenv("HF_ORG", "any-org-at-all")
    assert check_env() == "k"


def _good_response(quote: str) -> str:
    return json.dumps({"paragraphs": [{"para_idx": 0, "elements": [
        {"label": "AGENTE", "quote": quote}]}]})


def _fake_client(messages):
    """Deterministic mock client_call: never touches the network. Routes on
    the essay's own paragraph text (embedded in the user message) so it
    behaves the same regardless of retry count."""
    user = messages[1]["content"]
    if "quebra o parser" in user:
        # Valid JSON, but "paragraphs" contains a non-dict entry — a
        # plausible cheap-model hallucination that used to crash the batch.
        return json.dumps({"paragraphs": ["oops"]})
    if "O governo" in user:
        return _good_response("O governo")
    return _good_response("A sociedade")


def test_malformed_response_isolates_one_essay_others_unaffected(monkeypatch):
    sleeps = []
    monkeypatch.setattr(run_module.time, "sleep", lambda s: sleeps.append(s))

    rows = [
        {"essay_id": "e1", "essay_text": "O governo deve agir para reduzir o problema."},
        {"essay_id": "e2", "essay_text": "Texto que quebra o parser de propósito."},
        {"essay_id": "e3", "essay_text": "A sociedade deve cobrar mudanças urgentes."},
    ]

    out = label_rows(rows, client_call=_fake_client)

    assert [r["essay_id"] for r in out] == ["e1", "e2", "e3"]
    # the malformed essay degrades to spans=None instead of crashing the batch
    assert out[1]["spans"] is None
    assert out[1]["dropped"] == 0
    # essays before/after it are unaffected and still get their normal spans
    assert out[0]["spans"][0][0]["label"] == "AGENTE"
    assert out[2]["spans"][0][0]["label"] == "AGENTE"

    # deterministic parse failure retries 3x total, sleeping only *between*
    # attempts (2**0, 2**1) — never after the final (3rd) failed attempt.
    assert sleeps == [1, 2]


def test_on_row_called_once_per_essay_in_order_matches_return_value(monkeypatch):
    monkeypatch.setattr(run_module.time, "sleep", lambda s: None)

    rows = [
        {"essay_id": "a", "essay_text": "O governo deve agir."},
        {"essay_id": "b", "essay_text": "quebra o parser"},
        {"essay_id": "c", "essay_text": "A sociedade deve cobrar."},
    ]

    seen = []
    out = label_rows(rows, client_call=_fake_client, on_row=seen.append)

    assert [r["essay_id"] for r in seen] == ["a", "b", "c"]
    assert seen == out
