"""Paragraph splitting utilities.

WARNING: split_paragraphs() defines the offsets contract for the entire project.
Every span recorded in the dataset is a pair of character offsets into the
output of split_paragraphs(essay_text)[para_idx]. If this function's behavior
ever changes, every previously recorded annotation silently points at the
wrong characters. Treat this function as a frozen contract.
"""


def split_paragraphs(essay_text: str) -> list[str]:
    return [p.strip() for p in essay_text.split("\n") if p.strip()]
