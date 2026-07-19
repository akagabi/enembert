from dataclasses import dataclass

ELEMENTS = ["AGENTE", "ACAO", "MEIO", "EFEITO", "DETALHAMENTO"]
LABELS = ["O"] + [p + e for e in ELEMENTS for p in ("B-", "I-")]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


@dataclass(frozen=True)
class Span:
    start: int
    end: int  # exclusive
    label: str


def _overlaps(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 < b1 and b0 < a1


def spans_to_bio(text: str, spans: list[Span], tokens: list[tuple[int, int]]) -> list[str]:
    """Convert character-level spans to per-token BIO tags.

    Resolution policy for overlapping spans: spans are applied in ascending
    ``start`` order. Where two or more spans overlap the same token, the
    later-starting span wins that token (it overwrites any tag already
    assigned). BIO tagging cannot represent overlapping spans, so an earlier
    span may be silently truncated on a spans -> BIO -> spans round-trip if
    a later span claims some of its tokens. A span that overlaps no token at
    all contributes no tags and vanishes with no signal.
    """
    tags = ["O"] * len(tokens)
    for sp in sorted(spans, key=lambda s: s.start):
        first = True
        for i, (t0, t1) in enumerate(tokens):
            if _overlaps(sp.start, sp.end, t0, t1):
                tags[i] = ("B-" if first else "I-") + sp.label
                first = False
    return tags


def bio_to_spans(tokens: list[tuple[int, int]], tags: list[str]) -> list[Span]:
    """Convert per-token BIO tags back to character-level spans.

    Malformed tag sequences (as a trained model may emit) are recovered by
    dropping the offending tag, never by mis-attributing it to a different
    label. Concretely: an ``I-`` tag with no preceding open ``B-`` of the
    same label is treated as if it were ``O`` (silently dropped, no span
    produced for it). An ``I-`` tag whose label does not match the
    currently open span closes that open span as-is and the mismatched
    ``I-`` tag itself is dropped rather than starting a new span.
    """
    spans: list[Span] = []
    cur = None  # (label, start, end)
    for (t0, t1), tag in zip(tokens, tags):
        if tag.startswith("B-"):
            if cur: spans.append(Span(cur[1], cur[2], cur[0]))
            cur = (tag[2:], t0, t1)
        elif tag.startswith("I-") and cur and tag[2:] == cur[0]:
            cur = (cur[0], cur[1], t1)
        else:
            if cur: spans.append(Span(cur[1], cur[2], cur[0]))
            cur = None
    if cur: spans.append(Span(cur[1], cur[2], cur[0]))
    return spans
