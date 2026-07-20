import argparse, json
from pathlib import Path
from enembert.schema import Span
from enembert.labeling.review import render, apply_commands
from enembert.data.paragraphs import split_paragraphs

p = argparse.ArgumentParser()
p.add_argument("--in", dest="inp", required=True)
p.add_argument("--out", required=True)
p.add_argument("--blind", action="store_true")
a = p.parse_args()

corpus = {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}
done = set()
if Path(a.out).exists():
    done = {json.loads(l)["essay_id"] for l in open(a.out)}
# Append, never truncate: re-running this script after a prior session (or
# a crash mid-session) must resume, not clobber already-verified rows. The
# `done` set above is read BEFORE this open() so an essay already flushed to
# a.out is skipped below rather than re-annotated and duplicated.
out_f = open(a.out, "a")
for line in open(a.inp):
    row = json.loads(line)
    if row["essay_id"] in done or row["spans"] is None:
        continue
    paras = split_paragraphs(corpus[row["essay_id"]]["essay_text"])
    fixed = []
    for i, (para, raw) in enumerate(zip(paras, row["spans"])):
        spans = [] if a.blind else [Span(**s) for s in raw]
        while True:
            print(f"\n--- {row['essay_id']} p{i+1}/{len(paras)} ---")
            print(render(para, spans))
            cmd = input("[a]ccept | rN reject | m LABEL \"quote\" | q quit > ").strip()
            if cmd == "q":
                out_f.close(); raise SystemExit(0)
            if cmd in ("a", ""):
                break
            spans = apply_commands(spans, para, [cmd])
        fixed.append([s.__dict__ for s in spans])
    out_f.write(json.dumps({"essay_id": row["essay_id"], "spans": fixed,
                            "verified": True}, ensure_ascii=False) + "\n")
    out_f.flush()
