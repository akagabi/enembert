import pytest

from enembert.labeling.run import estimate_cost_usd, check_env, CostGuardError


def test_cost_estimate_scales():
    rows = [{"essay_text": "x" * 3000}] * 100
    assert 0 < estimate_cost_usd(rows) < 5


def test_cost_guard_trips():
    rows = [{"essay_text": "x" * 3000}] * 100000
    with pytest.raises(CostGuardError):
        from enembert.labeling.run import assert_within_budget
        assert_within_budget(rows)


def test_env_refuses_org_vars(monkeypatch):
    monkeypatch.setenv("ENEMBERT_LABELER_KEY", "k")
    monkeypatch.setenv("HF_ORG", "example-org")
    with pytest.raises(RuntimeError):
        check_env()
