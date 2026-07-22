# The score estimate does not work

*2026-07-22 — why enemBERT ships a highlighter and not a grade*

This is the report I'd have most wanted to read before building the thing. It
documents a feature that worked on every internal metric, survived a first
external check, and then collapsed the moment the external check got big enough
to mean anything.

## What was built

The demo used to show an estimated Competência 5 score (the 0–200 ENEM band for
the intervention proposal), plus the historical range of *total* essay scores
for essays that landed in that band. The estimator was a small multinomial
logistic regression over the tagger's own output — which of the five elements
were found, how many distinct elements, how many spans — running entirely in
the browser.

On the held-out, prompt-disjoint test set drawn from the training corpus it
reached **QWK 0.524** against real human C5 grades. Moderate agreement. Good
enough, I thought, to show as a range with a disclaimer.

## Why I didn't trust that number

Because the test set came from the same corpus as the training data. Same
scrape, same prompts, same era, same distribution of essay conventions. A model
can look competent on that and still be memorizing the corpus's habits rather
than reading the essay.

So I collected essays from **outside** it: published ENEM essays carrying real
per-competency grades from human graders, from INEP's *Cartilha do Participante*
and UOL's *Banco de Redações*. Every candidate was checked for contamination
against the training corpus and discarded if it appeared there.

That check mattered more than expected: **106 of 401 scraped essays (26%) were
contaminated** and thrown out. Any benchmark built without that filter would
have been measuring recall of the training set.

Two of the UOL parsers also needed fixing — their correction markup interleaves
the *grader's* words into the student's text, so a naive scrape was feeding the
model sentences the student never wrote.

## The first result was a lie

The first batch was 10 essays. Result:

| metric | value |
|---|---|
| Spearman(estimated C5, real C5) | **0.831** |
| MAE | 36 points |

That's a strong correlation. I nearly stopped here — and this is the part worth
dwelling on, because everything about the process up to this point was sound.
Contamination-checked, out-of-distribution, real human grades. It just wasn't
*enough essays*.

The bootstrap CI should have been the warning: **[0.45, 0.98]**. Enormously
wide. n=10 can't distinguish "strong" from "lucky."

## The real result

I expanded to 30 — 20 fresh essays, one per 50-point step from 200 to 1000, all
with full c1–c5 grades:

| metric | n=30 (all) | batch 1 (first 10) | batch 2 (fresh 20) |
|---|---|---|---|
| Spearman(estimated C5, real C5) | **0.347** | 0.831 | **0.064** |
| MAE | 62 pts | 36 pts | 76 pts |
| real total inside the shown range | 37% | 50% | — |

**95% CI on 0.347 = [−0.02, 0.65] — it includes zero.**

On 20 essays it had never been tuned against, the estimator is statistically
indistinguishable from no correlation at all. The 0.831 was small-sample luck:
batch 1 happened to contain two INEP *nota 1000* exemplars that the model aces.

## The failure is biased in the worst possible direction

It isn't noise scattered evenly. It systematically **under-credits good essays**:

| real C5 | n | our mean prediction | real mean | MAE |
|---|---|---|---|---|
| ≥ 150 | 13 | **105** | **181** | 78 |
| ≤ 100 | 17 | 75 | 76 | 51 |

It only looks accurate on weak essays, and for the wrong reason — "found few
elements" happens to be the right answer there, so the errors cancel. On strong
essays it is confidently, consistently wrong in the direction that would tell a
student who wrote a 180 that they wrote a 105.

That is precisely the harm the project set out to avoid. A number that reads as
precise, is not, and discourages the people who least deserve discouraging.

## The highlighter is also weaker than the in-corpus numbers suggested

The same benchmark re-tested the feature that *did* ship. Correlation between
the number of distinct elements found and the real C5 grade:

- **in-corpus** (held-out test set): ρ = 0.58
- **external** (n=30): ρ = **0.336**

And it is **non-monotonic** — essays where the model finds 3 elements average a
real C5 of 150, but essays where it finds 4 average 100. Only the extremes
behave sensibly: all 5 found → mean C5 200 (n=2); 0–1 found → 75–100.

So the element count is *not* a quality ranking, and the demo does not present
it as one. What survives external validation is the narrow, literal claim: the
model points at spans of text that look like each of the five elements, and it
is right often enough to be a useful second pair of eyes. Not a score. Not a
ranking. A highlighter.

## What I'd tell someone starting this

1. **An out-of-distribution benchmark is worth more than any in-corpus metric.**
   QWK 0.524 in-corpus and ρ≈0 out-of-corpus described the same model.
2. **n=10 is a pilot, not a result.** Compute the CI. If it spans half the
   possible range, you have learned nothing yet.
3. **Check contamination before you believe anything.** 26% of my scraped
   candidates were already in the training corpus.
4. **Look at the shape of the error, not just its size.** MAE 62 sounds
   survivable. "Systematically tells strong writers they are weak" does not.
5. **A negative result you can defend is a shippable artifact.** Deleting the
   feature made the project more useful, not less.

## Reproducing this

The estimator's coefficients are preserved at
[`score_model_v1.json`](score_model_v1.json) solely so this measurement stays
reproducible:

```
python scripts/eval_external.py runs/model/final
```

The benchmark essays themselves (`data/external_benchmark/`) are **not**
committed — they're copyrighted third-party text. Only aggregate numbers from
that set appear in this repo.
