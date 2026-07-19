from enembert.labeling.examples import EXAMPLES
from enembert.schema import ELEMENTS

def test_quotes_verbatim_and_unique():
    for ex in EXAMPLES:
        for el in ex["elements"]:
            assert el["label"] in ELEMENTS
            assert ex["paragraph"].count(el["quote"]) == 1

def test_covers_all_five_labels_somewhere():
    seen = {el["label"] for ex in EXAMPLES for el in ex["elements"]}
    assert seen == set(ELEMENTS)
