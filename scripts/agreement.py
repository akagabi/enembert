import argparse, json
from enembert.schema import Span
from enembert.labeling.agreement import corpus_f1

p = argparse.ArgumentParser()
p.add_argument("--gold", required=True)
p.add_argument("--pred", required=True)
a = p.parse_args()


def load(path: str) -> dict:
    """Load a labels jsonl into {essay_id: [[Span, ...] per paragraph, ...]}.

    Rows with spans == None (a labeling call that failed after retries, see
    label_rows in enembert.labeling.run) are skipped rather than turned into
    Span(**None)-shaped crashes.
    """
    rows = {}
    for line in open(path):
        row = json.loads(line)
        if row.get("spans") is None:
            continue
        rows[row["essay_id"]] = [[Span(**s) for s in para] for para in row["spans"]]
    return rows


gold_rows = load(a.gold)
pred_rows = load(a.pred)

for mode in ("exact", "overlap"):
    report = corpus_f1(gold_rows, pred_rows, mode)
    print(f"--- {mode} ---")
    print(f"micro_f1: {report['micro_f1']}")
    for el in sorted(report["per_element"]):
        print(f"  {el}: {report['per_element'][el]}")
