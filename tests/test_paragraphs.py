from enembert.data.paragraphs import split_paragraphs

def test_split_strips_and_drops_empties():
    assert split_paragraphs("a  \n\n b\n") == ["a", "b"]

def test_preserves_internal_spacing():
    assert split_paragraphs("uma  frase") == ["uma  frase"]
