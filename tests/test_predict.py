from enembert.training.predict import decode
from enembert.schema import LABEL2ID, Span


def test_decode_bio_ids_to_spans():
    tokens = [(0, 0), (0, 9), (10, 14), (0, 0)]          # CLS, "o governo", "deve", SEP
    ids = [0, LABEL2ID["B-AGENTE"], 0, 0]
    assert decode(tokens, ids) == [Span(0, 9, "AGENTE")]
