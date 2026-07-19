import dataclasses

import pytest

from enembert.schema import LABELS, ELEMENTS, LABEL2ID, ID2LABEL, Span, spans_to_bio, bio_to_spans

def test_labels_fixed_order():
    assert LABELS[0] == "O" and len(LABELS) == 11
    assert LABELS[1:3] == ["B-AGENTE", "I-AGENTE"]
    assert LABELS[9:] == ["B-DETALHAMENTO", "I-DETALHAMENTO"]

def test_bio_roundtrip():
    text = "o MEC deve criar campanhas"
    toks = [(0, 1), (2, 5), (6, 10), (11, 16), (17, 26)]
    spans = [Span(2, 5, "AGENTE"), Span(11, 26, "ACAO")]
    tags = spans_to_bio(text, spans, toks)
    assert tags == ["O", "B-AGENTE", "O", "B-ACAO", "I-ACAO"]
    assert bio_to_spans(toks, tags) == [Span(2, 5, "AGENTE"), Span(11, 26, "ACAO")]

def test_partial_token_overlap_counts():
    toks = [(0, 4), (4, 8)]
    spans = [Span(2, 6, "MEIO")]
    assert spans_to_bio("abcdabcd", spans, toks) == ["B-MEIO", "I-MEIO"]


# --- Finding 1: overlapping-span resolution (documented, pinned) ---

def test_overlapping_spans_later_start_wins_shared_token():
    """Two spans share token index 1. The later-starting span (ACAO)
    wins that token, truncating AGENTE on round-trip from (0,4) to (0,2)."""
    tokens = [(0, 2), (2, 4), (4, 6)]
    spans = [Span(0, 4, "AGENTE"), Span(2, 6, "ACAO")]
    tags = spans_to_bio("abcdef", spans, tokens)
    assert tags == ["B-AGENTE", "B-ACAO", "I-ACAO"]
    # AGENTE is silently truncated to (0, 2) on round-trip; ACAO survives intact.
    assert bio_to_spans(tokens, tags) == [
        Span(0, 2, "AGENTE"),
        Span(2, 6, "ACAO"),
    ]


def test_span_overlapping_no_token_vanishes():
    """A span that overlaps no token contributes no tags and disappears
    with no error or signal."""
    tokens = [(0, 3)]
    spans = [Span(5, 8, "MEIO")]
    assert spans_to_bio("abc", spans, tokens) == ["O"]


# --- Finding 2: bio_to_spans malformed-input handling (documented, pinned) ---

def test_stray_i_tag_with_no_open_span_is_dropped():
    """A stray I-AGENTE with no preceding B- is silently dropped, as if it
    were O; it does not start a span."""
    tokens = [(0, 2), (2, 4)]
    tags = ["I-AGENTE", "O"]
    assert bio_to_spans(tokens, tags) == []


def test_mismatched_i_tag_closes_open_span_and_is_dropped():
    """An I-ACAO following an open B-AGENTE closes the AGENTE span as-is
    and the mismatched I-ACAO tag itself is dropped, never mis-attributed
    to a new ACAO span."""
    tokens = [(0, 2), (2, 4)]
    tags = ["B-AGENTE", "I-ACAO"]
    assert bio_to_spans(tokens, tags) == [Span(0, 2, "AGENTE")]


# --- Minor: LABEL2ID / ID2LABEL coverage ---

def test_label_id_mappings():
    assert LABEL2ID["O"] == 0
    assert ID2LABEL[10] == "I-DETALHAMENTO"
    assert len(LABEL2ID) == len(ID2LABEL) == 11
    assert all(ID2LABEL[LABEL2ID[label]] == label for label in LABELS)
    assert all(LABEL2ID[ID2LABEL[i]] == i for i in ID2LABEL)


# --- Minor: Span immutability ---

def test_span_is_frozen():
    span = Span(0, 2, "AGENTE")
    with pytest.raises(dataclasses.FrozenInstanceError):
        span.start = 5
