# Binding decisions

Decisions taken at spending gates that later work must honour, with the measured
evidence behind each one. Aggregates only, never essay text.

---

## D1 — Training truncation (binding on Task 17) — decided at G0, 2026-07-19

**Problem.** 73% of the corpus (`sourceB`, 3,218 essays) lost its paragraph
breaks in the upstream crawl: 86% of those essays are a single blob, median
~431 estimated tokens. The proposta de intervenção sits in the **conclusion**,
beginning ~72% of the way through the text. Only **6.9%** of blobs fit the
plan's `encode_paragraph(max_length=256)`.

Under the plan as written, head-truncation at 256 tokens cuts the conclusion
off for the large majority of `sourceB`. The intervention spans then fall past
the truncation point and produce no tags — so those examples would actively
train the model that essays contain **no** intervention elements. The failure
is silent: nothing counts a span lost this way.

**Decision.**

1. `max_length = 512` (BERTimbau supports it). 75.1% of blobs then fit entirely.
2. **Left/tail truncation for single-paragraph essays** — keep the end, not the
   start, because that is where the intervention is.
3. **Task 17 must count and report spans dropped by truncation.** Silently
   dropping them is what made this dangerous in the first place.

**Amendment (2026-07-20, at training time).** `max_length` reduced 512 → **384**.
Reason: on this machine (Apple MPS), batch-16 × 512-token training thrashed GPU
memory — per-step time climbed 15s → 91s → 145s with a 33-hour ETA. Measured the
truncation-drop trade-off on the real 800-essay labeled pool (3,035 spans):

| max_length | spans dropped |
|---|---|
| 512 | 7 (0.23%) |
| **384** | **22 (0.72%)** |
| 256 | 75 (2.47%) |

384 drops only 22 spans — negligibly more than 512's 7, and far better than the
256 the original plan would have used — while being light enough to train at
batch 8 in ~1 hour without thrashing. The tail-truncation rule (keep the
conclusion) is unchanged, so D1's intent — never truncate away the intervention
— still holds: 99.3% of spans survive. Training uses `max_length=384, batch=8`.

`sourceB` is retained for training rather than discarded; dropping it would cost
85% of the corpus.

---

## D2 — Gold set selection — decided at G0, 2026-07-19

**Problem.** The plan's `freeze_gold` shuffled prompts and admitted them whole
until an essay-count target and C5-bucket coverage were both satisfied. On the
real corpus it produced **349 essays from 3 of 102 prompts, 100% from one
config, 88% single-paragraph text**.

Root cause is structural, not seed luck: the algorithm has no size cap and no
term for prompt-count or config diversity, while prompt sizes are wildly unequal
(`sourceB` median 88 essays/prompt vs `sourceAOnly`'s 3). The first large prompt
alone satisfies full C5 coverage, after which only the essay count remains — met
by two more large prompts. A 20-seed sweep found seed 42 the worst of 20, but
every seed inherits the defect.

A 3-prompt gold set cannot do its job: it covers 2.9% of prompts, so any score
computed on it mostly measures performance on three specific essay topics rather
than generalization to unseen prompts. It also contained zero essays with real
paragraph structure, so no paragraph-boundary behaviour could be tested at all.

**Decision.** Replace the selection strategy in `freeze_gold`:

1. **Structure eligibility** — a prompt may enter gold only if ≥80% of its
   essays have `n_paragraphs >= 2`. Expressed on paragraph structure, never on
   config name: config is incidental, structure is the reason. Spans are offsets
   into `split_paragraphs(essay_text)[para_idx]`, and hand-annotating an
   ~1,800-char blob is far more error-prone than annotating real paragraphs.
2. **Smallest-prompt-first ordering** — bounds overshoot past `target` and
   maximises the number of distinct prompts in gold.
3. **`seed` breaks ties among equal-sized prompts** (shuffle, then a *stable*
   sort by size). Deterministic across runs and across `PYTHONHASHSEED` values.
4. Ineligible prompts fall through to the training pool; nothing is discarded.

**Result:** gold = **255 essays across 44 prompts**, pool = 3,537, 1%
single-paragraph, all four C5 buckets present
(`zero 45 / low 56 / mid 36 / top 118`).

**Caveat that must be honoured when reporting.** Gold's C5 proportions do **not**
match the corpus — gold over-represents `top` and under-represents `mid`
(corpus is 55% `mid`). Therefore **gold F1 is a diagnostic across strata, not a
population estimate.** Do not report it as "expected real-world accuracy". If a
population-level figure is ever wanted, reweight per-stratum scores by the
corpus distribution.

**Supersedes** the 3-prompt `data/gold_freeze.json`. No labeling had been run
against the old freeze — which is why the G0 gate exists.
