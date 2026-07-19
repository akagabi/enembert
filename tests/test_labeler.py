import json

import pytest

from enembert.labeling.labeler import build_prompt, parse_response, LabelError
from enembert.schema import Span

PARAS = ["Introdução sem proposta.",
         "Portanto, o governo deve criar programas, a fim de reduzir o problema."]


def test_prompt_contains_guideline_examples_and_paragraphs():
    msgs = build_prompt(PARAS)
    joined = json.dumps(msgs, ensure_ascii=False)
    assert "DETALHAMENTO" in joined and "P2:" in joined


def test_parse_maps_quotes_to_offsets():
    raw = json.dumps({"paragraphs": [
        {"para_idx": 0, "elements": []},
        {"para_idx": 1, "elements": [
            {"label": "AGENTE", "quote": "o governo"},
            {"label": "EFEITO", "quote": "a fim de reduzir o problema"}]}]})
    result = parse_response(raw, PARAS)
    assert result.spans[0] == []
    s = result.spans[1][0]
    assert PARAS[1][s.start:s.end] == "o governo" and s.label == "AGENTE"


def test_missing_quote_dropped_not_fatal():
    raw = json.dumps({"paragraphs": [{"para_idx": 0, "elements": [
        {"label": "ACAO", "quote": "não está no texto"}]}, {"para_idx": 1, "elements": []}]})
    result = parse_response(raw, PARAS)
    assert result.spans[0] == []
    assert result.dropped == 1


def test_bad_json_raises():
    with pytest.raises(LabelError):
        parse_response("not json {", PARAS)
