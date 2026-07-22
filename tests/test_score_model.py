"""The demo's score model must stay a coarse band, never a point estimate.

A 6-band point estimate of Competência 5 shipped once and failed external
validation badly (rho=0.347, 95% CI [-0.02, 0.65], systematically under-crediting
good essays — docs/reports/score-estimate-negative-result.md). These tests encode
the properties that made the replacement defensible, so a future regeneration
cannot quietly walk back to something the evidence doesn't support.
"""
import json
from pathlib import Path

import pytest

MODEL = Path("demo/public/score_model.json")

pytestmark = pytest.mark.skipif(not MODEL.exists(), reason="run scripts/calibrate_score.py first")


@pytest.fixture(scope="module")
def model():
    return json.loads(MODEL.read_text())


def test_is_a_coarse_band_not_a_point_estimate(model):
    assert model["kind"] == "coarse_element_bands"
    # A logistic head would reintroduce the failed per-essay point prediction.
    assert "coef" not in model and "intercept" not in model
    assert len(model["buckets"]) == 2, "two coarse buckets; finer splits inverted externally"


def test_buckets_partition_the_element_counts(model):
    lo, hi = model["buckets"]
    assert lo["min_elements"] == 0
    assert hi["max_elements"] == 5
    assert lo["max_elements"] + 1 == hi["min_elements"] == model["cut"]


def test_every_bucket_shows_a_range_never_a_single_number(model):
    for b in model["buckets"]:
        assert b["hi"] > b["lo"], f"bucket {b['min_elements']}-{b['max_elements']} collapsed to a point"
        assert 0 <= b["lo"] < b["hi"] <= 200
        assert b["lo"] <= b["median"] <= b["hi"]


def test_the_ranges_actually_overlap(model):
    """The overlap is the honest part — the UI draws it, so it must exist."""
    lo, hi = model["buckets"]
    assert hi["lo"] < lo["hi"], (
        "buckets no longer overlap, which would overstate how cleanly the model separates essays"
    )


def test_higher_element_count_maps_to_the_higher_band(model):
    lo, hi = model["buckets"]
    assert hi["median"] > lo["median"]


def test_caveats_travel_with_the_numbers(model):
    """The UI reads these; dropping them would strip the disclosure from the panel."""
    meta = model["meta"]
    assert meta["n_external"] >= 30
    assert meta["replicates_in_corpus"] is True
    # We do NOT require significance — we require that it be stated honestly.
    assert isinstance(meta["survives_correction"], bool)
    assert meta["mannwhitney_p"] > 0
    assert "not a grade" in meta["warning"].lower()


def test_sample_sizes_are_recorded(model):
    total = sum(b["n"] for b in model["buckets"])
    assert total == model["meta"]["n_external"]
    for b in model["buckets"]:
        assert b["n"] >= 5, "a bucket this thin cannot support a displayed range"
