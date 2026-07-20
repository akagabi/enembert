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


def test_out_of_range_para_idx_counts_its_elements_as_dropped():
    # para_idx 5 is out of range for a 2-paragraph input (valid indices: 0, 1).
    # The skipped item carries 2 elements that must count toward `dropped`.
    # The normal item (para_idx 0) has one valid, resolvable element and must
    # still produce a span, unaffected by the skipped item.
    raw = json.dumps({"paragraphs": [
        {"para_idx": 5, "elements": [
            {"label": "AGENTE", "quote": "o governo"},
            {"label": "EFEITO", "quote": "reduzir o problema"}]},
        {"para_idx": 0, "elements": [
            {"label": "ACAO", "quote": "sem proposta"}]}]})
    result = parse_response(raw, PARAS)
    assert len(result.spans) == 2
    assert len(result.spans[0]) == 1
    assert result.spans[1] == []
    assert result.dropped == 2


def test_out_of_range_para_idx_with_non_list_elements_is_safe():
    # A non-list `elements` on a skipped item (malformed LLM JSON) must not
    # raise, and must not be counted (we can't know how many elements it held).
    raw = json.dumps({"paragraphs": [{"para_idx": 5, "elements": "oops"}]})
    result = parse_response(raw, PARAS)
    assert result.spans == [[], []]
    assert result.dropped == 0


def test_non_dict_item_in_paragraphs_raises_labelerror_not_attributeerror():
    # A cheap model can return syntactically valid JSON where an entry of
    # "paragraphs" is not an object at all (e.g. a bare string). The old code
    # called item.get(...) unguarded and raised AttributeError straight out
    # of parse_response, which label_rows did not catch, crashing the whole
    # paid batch. parse_response must be total: this becomes a LabelError.
    raw = json.dumps({"paragraphs": ["oops", {"para_idx": 0, "elements": []}]})
    with pytest.raises(LabelError):
        parse_response(raw, PARAS)


def test_non_dict_element_in_elements_raises_labelerror_not_attributeerror():
    # Same failure mode one level deeper: a well-formed item whose "elements"
    # list contains a non-dict entry. el.get(...) would otherwise raise.
    raw = json.dumps({"paragraphs": [{"para_idx": 0, "elements": ["oops"]}]})
    with pytest.raises(LabelError):
        parse_response(raw, PARAS)
