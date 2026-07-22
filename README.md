# enemBERT

**Projeto independente, não afiliado ao INEP/MEC.** / **Independent project, not affiliated with INEP/MEC.**

---

## Português

Modelo aberto (BERTimbau) que encontra os cinco elementos da proposta de intervenção — Competência 5 do ENEM — em redações: agente, ação, meio, efeito e detalhamento, marcados como trechos do próprio texto.

- **Não dá nota.** Aponta quais elementos estão presentes e quais faltam, apontando as palavras exatas. Mostra também uma faixa grosseira de Competência 5 (dois grupos, faixas sobrepostas, sinal fraco e declarado como tal) — nunca uma pontuação individual.
- **Roda no navegador** (transformers.js): a redação nunca sai do computador de quem usa.
- **Rótulos gerados por LLM**, não verificados por humanos — uma supervisão fraca, dita abertamente em todo lugar, não um gold padrão.

### Resultado, em cinco linhas

- O modelo supera um baseline de regex nos cinco elementos (F1 overlap micro 0.58 vs 0.27).
- DETALHAMENTO é o elemento mais fraco (F1 overlap 0.48), mesmo depois de corrigir um colapso de classe no treino.
- **A estimativa de nota exata de Competência 5 foi construída e descartada.** Ia bem dentro do corpus (QWK 0.524) e num primeiro teste externo de 10 redações (ρ = 0.831), mas em 30 redações externas caiu para ρ = 0.347, IC 95% [−0.02, 0.65] — inclui zero. Pior: errava para baixo justamente nas boas redações (C5 real ≥ 150: prevíamos 105, real 181).
- **O que sobrou é uma faixa grosseira, de dois grupos.** Redações em que o modelo acha 3+ elementos tiveram mediana de C5 real 150, contra 100 para 0–2 elementos (p = 0.035), e a direção se repete de forma independente no conjunto interno (medianas 80 → 200). O demo mostra isso como faixa larga, com a sobreposição entre os grupos desenhada na tela — nunca como nota. Ler [o relatório completo](./docs/reports/score-estimate-negative-result.md), a parte mais útil deste projeto.
- Os rótulos vêm de um LLM lendo a Cartilha do Participante (INEP), não de revisão humana — leia o [model card](./MODEL_CARD.md) e o [writeup](./docs/writeup.md) antes de tirar qualquer conclusão dos números.

### Links

- [Model card](./MODEL_CARD.md) — o que o modelo faz, métricas, como usar.
- [Dataset card](./DATASET_CARD.md) — o dataset stand-off e o processo de rotulagem.
- [Writeup](./docs/writeup.md) — a história completa: por que supervisão fraca, onde quebrou, o que a avaliação honesta diz.
- [Resultado negativo: a estimativa de nota](./docs/reports/score-estimate-negative-result.md) — o recurso que construímos, validamos e apagamos, com os números.
- Demo: *em breve* (GitHub Pages).
- Hugging Face: modelo `akagabi/enemBERT` e dataset `akagabi/enembert-annotations` *(em breve)*.

### Licença

Código: MIT (`LICENSE`). Pesos do modelo: Apache-2.0. Detalhes no [model card](./MODEL_CARD.md).

---

## English

Open model (BERTimbau) that finds the five elements of the ENEM *proposta de intervenção* — Competência 5 — in essays: agente (agent), ação (action), meio (means), efeito (effect) and detalhamento (elaboration), marked as spans in the text itself.

- **Never predicts a grade.** It points at which elements are present and which are missing, by pointing at the literal words. It also shows a coarse Competência 5 band (two buckets, overlapping ranges, weak signal, labeled as such) — never an individual score.
- **Runs in the browser** (transformers.js): the essay never leaves the user's machine.
- **Labels are LLM-generated**, not human-verified — weak supervision, stated plainly everywhere, not a gold standard.

### Results, in five lines

- The model beats a regex baseline on all five elements (micro overlap-F1 0.58 vs 0.27).
- DETALHAMENTO is the weakest element (0.48 overlap-F1), even after fixing a training-time class collapse.
- **The exact-score estimate was built and thrown away.** It looked fine in-corpus (QWK 0.524) and survived a first external check on 10 essays (ρ = 0.831), but on 30 external essays it fell to ρ = 0.347, 95% CI [−0.02, 0.65] — which includes zero. Worse, it erred downward specifically on good essays (real C5 ≥ 150: we predicted 105, real 181).
- **What survived is a coarse, two-bucket band.** Essays where the model finds 3+ elements had a median real C5 of 150 against 100 for 0–2 elements (p = 0.035), and the direction replicates independently in-corpus (medians 80 → 200). The demo shows that as a wide range with the overlap between buckets drawn on screen — never as a grade. Read [the full report](./docs/reports/score-estimate-negative-result.md), the most useful thing in this project.
- Labels come from an LLM reading the INEP Cartilha do Participante, not human review — read the [model card](./MODEL_CARD.md) and the [writeup](./docs/writeup.md) before drawing conclusions from the numbers above.

### Links

- [Model card](./MODEL_CARD.md) — what the model does, metrics, usage.
- [Dataset card](./DATASET_CARD.md) — the stand-off dataset and the labeling process.
- [Writeup](./docs/writeup.md) — the full story: why weak supervision, where it broke, what the honest evaluation says.
- [Negative result: the score estimate](./docs/reports/score-estimate-negative-result.md) — the feature we built, validated, and deleted, with the numbers.
- Demo: *coming soon* (GitHub Pages).
- Hugging Face: model `akagabi/enemBERT` and dataset `akagabi/enembert-annotations` *(coming soon)*.

### License

Code: MIT (`LICENSE`). Model weights: Apache-2.0. Details in the [model card](./MODEL_CARD.md).
