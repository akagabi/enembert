# enemBERT

**Projeto independente, não afiliado ao INEP/MEC.** / **Independent project, not affiliated with INEP/MEC.**

---

## Português

Modelo aberto (BERTimbau) que encontra os cinco elementos da proposta de intervenção — Competência 5 do ENEM — em redações: agente, ação, meio, efeito e detalhamento, marcados como trechos do próprio texto.

- **Não dá nota.** Aponta quais elementos estão presentes e quais faltam, apontando as palavras exatas — nunca uma pontuação.
- **Roda no navegador** (transformers.js): a redação nunca sai do computador de quem usa.
- **Rótulos gerados por LLM**, não verificados por humanos — uma supervisão fraca, dita abertamente em todo lugar, não um gold padrão.

### Resultado, em cinco linhas

- O modelo supera um baseline de regex nos cinco elementos (F1 overlap micro 0.58 vs 0.27).
- A contagem de elementos que o modelo encontra correlaciona com a nota real de Competência 5 do ENEM (Spearman ρ = 0.58) — o único número aqui ancorado em avaliação humana de verdade.
- DETALHAMENTO é o elemento mais fraco (F1 overlap 0.48), mesmo depois de corrigir um colapso de classe no treino.
- O demo inclui uma estimativa opcional de nota de Competência 5 (não a nota total, que ficou imprecisa demais para mostrar) — QWK 0.524 contra notas reais, sempre exibida como faixa, nunca como número isolado.
- Os rótulos vêm de um LLM lendo a Cartilha do Participante (INEP), não de revisão humana — leia o [model card](./MODEL_CARD.md) e o [writeup](./docs/writeup.md) antes de tirar qualquer conclusão dos números.

### Links

- [Model card](./MODEL_CARD.md) — o que o modelo faz, métricas, como usar.
- [Dataset card](./DATASET_CARD.md) — o dataset stand-off e o processo de rotulagem.
- [Writeup](./docs/writeup.md) — a história completa: por que supervisão fraca, onde quebrou, o que a avaliação honesta diz.
- Demo: *em breve* (GitHub Pages).
- Hugging Face: modelo `akagabi/enemBERT` e dataset `akagabi/enembert-annotations` *(em breve)*.

### Licença

Código: MIT (`LICENSE`). Pesos do modelo: Apache-2.0. Detalhes no [model card](./MODEL_CARD.md).

---

## English

Open model (BERTimbau) that finds the five elements of the ENEM *proposta de intervenção* — Competência 5 — in essays: agente (agent), ação (action), meio (means), efeito (effect) and detalhamento (elaboration), marked as spans in the text itself.

- **Never predicts a grade.** It points at which elements are present and which are missing, by pointing at the literal words — never a score.
- **Runs in the browser** (transformers.js): the essay never leaves the user's machine.
- **Labels are LLM-generated**, not human-verified — weak supervision, stated plainly everywhere, not a gold standard.

### Results, in five lines

- The model beats a regex baseline on all five elements (micro overlap-F1 0.58 vs 0.27).
- The number of elements the model finds correlates with the essay's real ENEM Competência 5 grade (Spearman ρ = 0.58) — the one number here anchored to genuine human judgment.
- DETALHAMENTO is the weakest element (0.48 overlap-F1), even after fixing a training-time class collapse.
- The demo includes an optional Competência 5 score estimate (not the total grade, which turned out too noisy to show) — QWK 0.524 against real grades, always shown as a range, never a bare number.
- Labels come from an LLM reading the INEP Cartilha do Participante, not human review — read the [model card](./MODEL_CARD.md) and the [writeup](./docs/writeup.md) before drawing conclusions from the numbers above.

### Links

- [Model card](./MODEL_CARD.md) — what the model does, metrics, usage.
- [Dataset card](./DATASET_CARD.md) — the stand-off dataset and the labeling process.
- [Writeup](./docs/writeup.md) — the full story: why weak supervision, where it broke, what the honest evaluation says.
- Demo: *coming soon* (GitHub Pages).
- Hugging Face: model `akagabi/enemBERT` and dataset `akagabi/enembert-annotations` *(coming soon)*.

### License

Code: MIT (`LICENSE`). Model weights: Apache-2.0. Details in the [model card](./MODEL_CARD.md).
