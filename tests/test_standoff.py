import json

from enembert.data.standoff import to_standoff


def test_no_text_leaks():
    row = {"essay_id": "sourceB:1", "config": "sourceB",
           "spans": [[{"start": 0, "end": 5, "label": "AGENTE"}], []]}
    out = to_standoff(row)
    assert "essay_text" not in json.dumps(out)
    assert out["para_spans"][0] == {"para_idx": 0, "start": 0, "end": 5, "label": "AGENTE"}
