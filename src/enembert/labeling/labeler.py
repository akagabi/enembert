import json
import re
from dataclasses import dataclass
from pathlib import Path

from enembert.schema import ELEMENTS, Span
from enembert.labeling.examples import EXAMPLES

GUIDELINE = Path(__file__).resolve().parents[3] / "annotation" / "guideline.md"


class LabelError(Exception):
    pass


@dataclass(frozen=True)
class ParseResult:
    spans: list[list[Span]]   # per-paragraph spans, as before
    dropped: int              # count dropped (bad label / empty quote / quote not found)


def build_prompt(paragraphs: list[str]) -> list[dict]:
    ex_txt = "\n\n".join(
        "PARÁGRAFO: " + e["paragraph"] + "\nRESPOSTA: " +
        json.dumps({"elements": e["elements"]}, ensure_ascii=False) for e in EXAMPLES)
    numbered = "\n".join(f"P{i + 1}: {p}" for i, p in enumerate(paragraphs))
    system = ("Você anota elementos da proposta de intervenção (Competência 5 do ENEM) em "
              "redações, seguindo este guia:\n\n" + GUIDELINE.read_text() +
              "\n\nResponda APENAS com JSON no formato "
              '{"paragraphs":[{"para_idx":0,"elements":[{"label":"AGENTE","quote":"..."}]}]} '
              "usando citações VERBATIM do parágrafo. Exemplos:\n\n" + ex_txt)
    return [{"role": "system", "content": system},
            {"role": "user", "content": numbered}]


def parse_response(raw: str, paragraphs: list[str]) -> ParseResult:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise LabelError("no JSON object in response")
    try:
        obj = json.loads(m.group(0))
        items = obj["paragraphs"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise LabelError(str(e))
    out: list[list[Span]] = [[] for _ in paragraphs]
    dropped = 0
    for item in items:
        i = item.get("para_idx")
        if not isinstance(i, int) or not (0 <= i < len(paragraphs)):
            continue
        for el in item.get("elements", []):
            label, quote = el.get("label"), el.get("quote", "")
            if label not in ELEMENTS or not quote:
                dropped += 1
                continue
            pos = paragraphs[i].find(quote)
            if pos < 0:
                dropped += 1
                continue
            out[i].append(Span(pos, pos + len(quote), label))
    return ParseResult(spans=out, dropped=dropped)
