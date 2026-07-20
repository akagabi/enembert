from transformers import AutoTokenizer
from enembert.schema import Span, LABEL2ID
from enembert.training.dataset import encode_paragraph

def test_alignment_and_512():
    tok = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
    para = "o governo deve criar programas"
    enc = encode_paragraph(tok, para, [Span(0, 9, "AGENTE"), Span(15, 30, "ACAO")], max_length=512)
    ids = enc["labels"]
    assert ids[0] == -100 and ids[-1] == -100
    assert LABEL2ID["B-AGENTE"] in ids and LABEL2ID["B-ACAO"] in ids
    assert len(ids) == len(enc["input_ids"])
    assert enc["dropped_spans"] == 0

def test_tail_truncation_keeps_end():
    tok = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
    # long paragraph; the AGENTE span is at the very end
    prefix = "palavra " * 300
    para = prefix + "o governo deve agir"
    start = para.index("o governo")
    head = encode_paragraph(tok, para, [Span(start, start+9, "AGENTE")], max_length=64, tail=False)
    tail = encode_paragraph(tok, para, [Span(start, start+9, "AGENTE")], max_length=64, tail=True)
    # head-truncation loses the end span; tail-truncation keeps it
    assert head["dropped_spans"] == 1
    assert tail["dropped_spans"] == 0
    assert LABEL2ID["B-AGENTE"] in tail["labels"]
