import re
from enembert.schema import Span

_PATTERNS = [
    ("MEIO", re.compile(r"(?:por meio d[eao]s?|através d[eao]s?|mediante|com o uso d[eao]s?)"
                        r"[^,.;]*", re.I)),
    ("EFEITO", re.compile(r"(?:a fim de|para que|com o (?:objetivo|intuito) de)[^,.;]*", re.I)),
    ("AGENTE", re.compile(r"(?:o governo|o estado|o poder p[úu]blico|o minist[ée]rio da? [\wà-ú]+"
                          r"|o mec|as? escolas?|a m[íi]dia|a fam[íi]lia|a sociedade"
                          r"|as redes sociais|ongs?)", re.I)),
    ("ACAO", re.compile(r"(?:deve[m]?|precisa[m]?(?: de)?|cabe(?: [àa]s?| aos?)?)\s+"
                        r"([\wà-ú]+(?:ir|ar|er)\b[^,.;]*)", re.I)),
]


def baseline_spans(paragraph: str) -> list[Span]:
    spans = []
    for label, pat in _PATTERNS:
        for m in pat.finditer(paragraph):
            start, end = (m.span(1) if label == "ACAO" and m.lastindex else m.span())
            spans.append(Span(start, end, label))
    return sorted(spans, key=lambda s: s.start)
