# What happened building enemBERT

## Why this exists

Every year, roughly 4 million people take the ENEM, Brazil's national college-entrance exam. The essay is worth 1,000 of the total 5,000 points, split across five competencies. Competência 5 asks for a *proposta de intervenção*: a concrete policy proposal in the conclusion, built from five specific parts — who should act (agente), what they should do (ação), how (meio), why (efeito), and an elaboration of one of those (detalhamento). Unlike the other four competencies, which reward things like argumentative coherence or command of formal register, Competência 5 is close to mechanical: did the conclusion include all five pieces or not. That makes it a rare case in essay grading where "did I do the thing" is a real, checkable question, not just a judgment call.

I wanted to build something that checks that, and I wanted to build it honestly. I'm not an ENEM corretor. I have no standing to say "this span is correct" the way a trained human grader can. So instead of pretending otherwise, this project leans into what it actually is: a small BERTimbau model trained on labels an LLM produced by reading the official rubric, evaluated as honestly as I could manage without expert ground truth, and shipped as an open model, an open (text-free) dataset, and a browser tool that never uploads anyone's essay. It doesn't grade anything. It finds the five parts and tells you which ones it found.

This is what weak supervision looks like when you're one person with a personal budget and no annotation team: you get a much bigger labeled corpus than you could hand-label yourself, and in exchange you give up the right to call any of it ground truth. I think that's a fair trade for a Portuguese NLP task with basically no existing tooling, as long as you say so everywhere, which is the point of this document.

## Where it broke

Four things went wrong in ways worth describing in some detail, because each one taught me something about working with real, messy, ENEM-scale data.

**The corpus had swallowed its own paragraph breaks.** The training data comes from `kamel-usp/aes_enem_dataset`, and about 73% of it (a source config called `sourceB`, roughly 3,200 of the 3,792 essays) had lost its newlines in an upstream crawl. Most of those essays — 86% of them — arrived as a single unbroken blob of text, median length around 431 tokens. The proposta de intervenção lives in the conclusion, which starts about 72% of the way through the essay. My original plan truncated paragraphs at 256 tokens, which is a completely reasonable number for a well-structured essay and a disaster for a blob: only 6.9% of these single-paragraph essays would have fit. For the rest, the truncation would have sliced the conclusion clean off, and because nothing counted what got dropped, the model would have quietly learned that most essays contain no proposta de intervenção at all. Nobody would have noticed until the model came out weirdly bad at exactly the thing it was supposed to do. The fix was to raise the token budget and, for single-paragraph essays, truncate from the front instead of the back, so the end of the text — where the conclusion is — always survives. I measured the actual trade-off on the labeled training pool (3,035 spans): 512 tokens dropped 7 spans, 384 dropped 22, 256 dropped 75. I ended up training at 384 rather than 512 for a mundane reason — on my machine's GPU, batch-16 training at 512 tokens thrashed memory badly enough that a run projected to take 33 hours. 384 tokens at batch 8 trains in about an hour and drops only 22 of 3,035 spans (0.72%), which felt like the right trade.

**My held-out test set turned out to measure almost nothing.** The first version of the gold-set selection algorithm admitted whole essay prompts until it hit a target count, with no cap on how many essays a single prompt could contribute. Prompt sizes in this corpus are wildly uneven, and the first big prompt alone happened to satisfy every stated coverage requirement, so the loop stopped after admitting essays from just 3 of the corpus's 102 prompts. Any score computed on that set would have mostly measured how well the model handles three specific essay topics, not whether it generalizes at all. I fixed this by requiring a prompt to have real paragraph structure before it's eligible for gold, and by adding prompts smallest-first so no single prompt can dominate. The result is 255 essays spread across 44 prompts — a real test of generalization, even though its grade distribution now skews toward higher-scoring essays than the corpus as a whole, which I've noted wherever those numbers get reported.

**The label quality problem I didn't expect: the LLM was too good a copyeditor.** The `sourceB` essays aren't just missing paragraph breaks, they're OCR-damaged — letters dropped mid-word, like "Ministério da ducação" instead of "Educação". The labeling prompt asks the model to quote elements verbatim so the quote can be matched back to exact character offsets. Left to its own judgment, the labeler kept quietly fixing the typos it was quoting, which meant the "fixed" quote no longer existed in the actual text and got silently discarded. On a 150-essay sample this dropped 97 elements. Telling the labeler explicitly, in the prompt, to copy characters exactly and never correct spelling — because the source might be OCR-damaged — cut that to 60 drops on the same sample, a 38% reduction, and recovered 78 spans that would otherwise have vanished.

**The model learned to ignore its two rarest labels.** MEIO and DETALHAMENTO are simply less common in these essays than AGENTE or AÇÃO, and the first trained model responded to that imbalance by nearly never predicting them: DETALHAMENTO overlap-F1 came out at 0.00 and MEIO at 0.03, essentially collapsed classes. The fix was sqrt-balanced class weighting in the loss function, upweighting the rare labels relative to their frequency. Re-training with that change brought DETALHAMENTO to 0.48 and MEIO to 0.63, both now above the regex baseline. No extra data, no architecture change, just weighting the loss to match reality.

## What the evaluation actually says

Without expert-labeled data, I can't report "accuracy" in the normal sense. What I can report is agreement with the LLM labeler on the held-out set (overlap-F1, since span boundaries are inherently a little fuzzy): micro-F1 0.58 against the labeler, against a regex baseline's 0.27, with the model ahead on all five elements individually. That's evidence the model learned real structure and not just marker-matching, but it's still model-vs-labeler agreement, not model-vs-truth.

The number I used to trust more was the correlation with real grades. Each essay in the corpus carries its actual ENEM Competência 5 score, assigned by human graders and never shown to the model during training. The number of distinct elements the model finds correlates with that real score at Spearman ρ = 0.58: essays where it finds all five elements average a C5 grade of 197 out of 200; essays where it finds one or none average 72. That correlation didn't come from anything I annotated, which is why I trusted it more than the F1 numbers above it.

Then I tested the same thing on essays from outside the corpus entirely, and ρ = 0.58 became ρ = 0.336 — and stopped being monotonic. That story is the next section, and it's the most useful thing I learned.

## The score I built, validated, and deleted

This is the part of the project I'd most want someone else to read.

I wanted the demo to show a score. Not the full 0–1000 total — I tried that first, and it reached QWK 0.60 with an average error of ±223 points, which means telling a student their essay is "around 700" when it's really 480, or really 920. That's the exact harm I set out to avoid, so the total was never on the table.

Competência 5 alone looked much more promising. C5 correlates with the total score at ρ = 0.90 in this corpus, and with the other four competencies at ρ = 0.79 — essay quality moves together, so a good C5 estimate would say something real about the whole essay without pretending to grade the whole essay. I built a small logistic regression over the tagger's own output (which elements it found, how many, how many spans) predicting the real C5 band. On the held-out, prompt-disjoint test set it hit **QWK 0.524** against real human grades: moderate agreement, exact band about 36% of the time, within one band about 66%.

An earlier version of it reached 0.681 by including essay length, but length turned out to be doing most of the work — a well-written short essay with all five elements scored C5=40 just for being short, while the same elements in a longer essay scored 200. I dropped length and took 0.524 in exchange for a model that gives the same answer whether the essay is 185 or 1,086 characters. I felt good about that trade. It was the right call and it was nowhere near enough.

**The problem is that the test set came from the same corpus as the training data.** Same scrape, same prompts, same era, same conventions. A model can look competent on that while having learned the corpus's habits rather than how to read an essay. So I collected essays from outside it: published ENEM essays with real per-competency human grades, from INEP's *Cartilha do Participante* and UOL's *Banco de Redações*, each one checked against the training corpus and discarded if it appeared there. That check alone disqualified **106 of 401 candidates — 26%**. A benchmark built without it would have been measuring memorization.

The first 10 essays gave Spearman ρ = **0.831**. Better than the in-corpus number. I nearly stopped there, and I want to be precise about why stopping would have been wrong, because the process up to that point was genuinely sound — contamination-checked, out-of-distribution, real human grades. It just wasn't enough essays. The bootstrap CI was **[0.45, 0.98]**, which is another way of writing "no idea."

So I expanded to 30, adding 20 fresh essays spanning one per 50-point step from 200 to 1000:

| | n=30 (all) | first 10 | fresh 20 |
|---|---|---|---|
| Spearman(estimated C5, real C5) | **0.347** | 0.831 | **0.064** |
| MAE | 62 pts | 36 pts | 76 pts |
| real total inside the shown range | 37% | 50% | — |

**The 95% CI on 0.347 is [−0.02, 0.65]. It includes zero.** On twenty essays it had never been tuned against, the estimator was statistically indistinguishable from no correlation whatsoever. The 0.831 was luck: those first ten happened to include two INEP *nota 1000* exemplars that the model handles easily.

And the errors weren't evenly scattered. They were biased in the worst available direction — **systematic under-crediting of good essays**:

| real C5 | n | predicted (mean) | real (mean) | MAE |
|---|---|---|---|---|
| ≥ 150 | 13 | **105** | **181** | 78 |
| ≤ 100 | 17 | 75 | 76 | 51 |

It only looked accurate on weak essays, and for a hollow reason: "found few elements" happens to be the right answer there. On strong essays it would have consistently told a student who wrote a 180 that they wrote a 105 — discouraging exactly the people who least deserved it.

So the score is gone. Not softened, not hedged behind a bigger disclaimer — deleted. A disclaimer doesn't fix a number that's wrong in a specific, harmful direction; people read the number and skip the caveat.

What I did keep is the one claim that survived the same benchmark, and only because it survived it: a coarse two-bucket split. Essays where the model finds three or more elements had a median real C5 of 150 against 100 for essays where it finds two or fewer (p = 0.035), and — the part that convinced me — the same direction shows up independently on the in-corpus gold set, medians 80 against 200. Two independent sets agreeing on direction is a much better reason to ship something than one set agreeing with itself.

It's still weak, so the demo says so where you can't miss it: the meter draws the *other* bucket's range underneath yours, so the enormous overlap is visible rather than described, and the caption states n=30 and that the difference doesn't survive correcting for the six splits I tried. Finer splits were rejected on evidence — cutting at four elements gives p = 0.38, and the per-count medians are non-monotonic, with three elements outscoring four. The displayed ranges come from the external set rather than the in-corpus one, because the gold set over-represents high-scoring essays and its ranges would flatter the reader.

The distance between "your essay scores 105" and "essays with 3+ elements usually landed between 100 and 200, and here's how much that overlaps with everyone else" is the whole lesson of this project.

The same benchmark also forced me to downgrade a claim about the feature that *did* ship. The element count correlates with real C5 at ρ = 0.58 in-corpus but only **0.336** externally, and non-monotonically: essays where the model finds 3 elements average a real C5 of 150, while essays where it finds 4 average 100. Only the extremes behave (all five found → mean 200, n=2; zero or one → 75–100). So the element count is not a quality ranking, and the demo doesn't present it as one.

What survives is the narrow claim I can actually defend: the model points at spans that look like each of the five elements, and it's right often enough to be a useful second pair of eyes. Not a grade. Not a ranking. A highlighter. That's a smaller product than I set out to build, and it's the one the evidence supports.

The full report, with method and reproduction instructions, is in [docs/reports/score-estimate-negative-result.md](./reports/score-estimate-negative-result.md).

## What I'd do next

The honest next step is to label the full 3,792-essay corpus rather than the 800 I used, specifically to give MEIO and DETALHAMENTO more real examples instead of leaning entirely on loss weighting to compensate for scarcity. After that, the thing this project actually needs and doesn't have is a small expert-checked test set, even fifty essays reviewed by someone who has graded ENEM essays for real, so the F1 numbers above stop being "agreement with an LLM" and start being something closer to accuracy. I looked into doing that review myself and concluded I'm not qualified to be that judge, which is the whole reason this project is framed as weak supervision instead of pretending otherwise. A bigger external benchmark would help too: 30 essays was enough to kill the score estimate, but it's thin for measuring the highlighter itself, and the essays are hard to collect because most published ones are already in the training corpus. If someone with real ENEM grading experience wants to build that test set, the model, the code, and 255 already-selected, prompt-diverse essays are sitting here waiting for them.
