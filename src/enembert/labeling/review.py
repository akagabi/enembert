import re
from enembert.schema import ELEMENTS, Span

COLORS = {"AGENTE": "\033[42m", "ACAO": "\033[44m", "MEIO": "\033[45m",
          "EFEITO": "\033[43m", "DETALHAMENTO": "\033[46m"}
RESET = "\033[0m"


def render(paragraph: str, spans: list[Span]) -> str:
    out, last = [], 0
    for i, s in enumerate(sorted(spans, key=lambda x: x.start)):
        out += [paragraph[last:s.start], COLORS[s.label],
                paragraph[s.start:s.end], RESET, f"[{i+1}:{s.label}]"]
        last = s.end
    out.append(paragraph[last:])
    return "".join(out)


def apply_commands(spans: list[Span], paragraph: str, commands: list[str]) -> list[Span]:
    spans = sorted(spans, key=lambda x: x.start)
    for cmd in commands:
        cmd = cmd.strip()
        if m := re.fullmatch(r"r(\d+)", cmd):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(spans):
                spans = spans[:idx] + spans[idx + 1:]
        elif m := re.fullmatch(r'm (\w+) "(.+)"', cmd):
            label, quote = m.group(1), m.group(2)
            pos = paragraph.find(quote)
            # pos >= 0 guards against str.find's -1 (quote not found): a
            # rejected add must leave the span list unchanged, never insert
            # a corrupt Span(-1, ...) offset.
            if label in ELEMENTS and pos >= 0:
                spans.append(Span(pos, pos + len(quote), label))
                spans.sort(key=lambda x: x.start)
    return spans
