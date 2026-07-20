from enembert.schema import Span
from enembert.labeling.review import apply_commands, render

PAR = "Portanto, o governo deve criar programas."


def test_reject():
    spans = [Span(10, 19, "AGENTE"), Span(25, 40, "ACAO")]
    out = apply_commands(spans, PAR, ["r1"])
    assert out == [Span(25, 40, "ACAO")]


def test_add_missed():
    out = apply_commands([], PAR, ['m AGENTE "o governo"'])
    assert out == [Span(10, 19, "AGENTE")]


def test_render_marks_span():
    s = render(PAR, [Span(10, 19, "AGENTE")])
    assert "governo" in s and "AGENTE" in s


def test_add_missed_quote_not_found_is_noop():
    # str.find returns -1 for a quote absent from the paragraph; that must
    # never produce Span(-1, ...) -- a corrupt offset. Span list is unchanged.
    out = apply_commands([], PAR, ['m AGENTE "not in paragraph"'])
    assert out == []


def test_add_missed_unknown_label_is_noop():
    out = apply_commands([], PAR, ['m NOTALABEL "o governo"'])
    assert out == []


def test_apply_commands_keeps_result_sorted_by_start():
    out = apply_commands([], PAR, ['m ACAO "criar programas"', 'm AGENTE "o governo"'])
    assert [s.start for s in out] == sorted(s.start for s in out)
    assert out == [Span(10, 19, "AGENTE"), Span(25, 40, "ACAO")]


def test_render_orders_markers_by_start_regardless_of_input_order():
    s = render(PAR, [Span(25, 40, "ACAO"), Span(10, 19, "AGENTE")])
    assert s.index("[1:AGENTE]") < s.index("[2:ACAO]")
