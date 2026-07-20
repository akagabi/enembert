import torch
from enembert.schema import ID2LABEL, Span, bio_to_spans


def decode(tokens: list[tuple[int, int]], ids: list[int]) -> list[Span]:
    keep = [(t, ID2LABEL[i]) for t, i in zip(tokens, ids) if t[0] != t[1]]
    return bio_to_spans([t for t, _ in keep], [tag for _, tag in keep])


def predict_spans(model, tokenizer, paragraph: str, max_length: int = 384, tail: bool = False) -> list[Span]:
    tokenizer.truncation_side = "left" if tail else "right"
    enc = tokenizer(paragraph, truncation=True, max_length=max_length,
                    return_offsets_mapping=True, return_tensors="pt")
    offsets = enc.pop("offset_mapping")[0].tolist()
    with torch.no_grad():
        logits = model(**{k: v.to(model.device) for k, v in enc.items()}).logits[0]
    return decode([tuple(o) for o in offsets], logits.argmax(-1).tolist())
