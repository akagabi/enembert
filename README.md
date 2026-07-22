# enemBERT

**Um modelo aberto que encontra os cinco elementos da proposta de intervenção do ENEM — e que não te dá nota.**

*An open model that finds the five elements of the ENEM intervention proposal — and refuses to grade you.*

`BERTimbau` · `token classification` · `pt-BR` · roda no navegador · MIT / Apache-2.0

**▶ [Testar agora / Try it now](https://akagabi.github.io/enembert/)** · [🤗 Modelo](https://huggingface.co/akagabi/enemBERT)

[Português](#português) · [English](#english)

---

## Português

A Competência 5 do ENEM pede uma **proposta de intervenção** na conclusão, feita de cinco
partes: quem age (**agente**), o que faz (**ação**), como (**meio**), para quê (**efeito**)
e um detalhe que desenvolva uma delas (**detalhamento**). Diferente das outras quatro
competências, essa pergunta é quase mecânica: os cinco elementos estão lá ou não estão.

O enemBERT marca esses cinco elementos no seu próprio texto:

```
Portanto, é imprescindível que [o Ministério da Educação]AGENTE, [órgão responsável
pela política educacional do país]DETALHAMENTO, [amplie o programa de bolsa-permanência]AÇÃO,
[por meio de parcerias com as secretarias estaduais]MEIO, [a fim de reduzir a evasão
escolar no ensino médio]EFEITO.
```

### O que ele faz — e o que ele não faz

|  | |
|---|---|
| ✅ | Aponta **quais dos cinco elementos aparecem** e quais faltam, mostrando as palavras exatas |
| ✅ | Roda **inteiramente no seu navegador** — sua redação nunca é enviada a nenhum servidor |
| ✅ | Mostra uma **faixa grosseira** de Competência 5, com a incerteza desenhada na tela |
| ❌ | **Não dá nota.** Nunca produz uma pontuação individual |
| ❌ | Não avalia gramática, argumentação, coesão nem as outras quatro competências |
| ❌ | Não é oficial, não tem vínculo com o INEP/MEC e não substitui um corretor |

### Resultados

| métrica | valor |
|---|---|
| F1 (overlap, micro) vs. baseline de regex | **0.58** vs. 0.27 |
| Elemento mais forte / mais fraco | AGENTE 0.66 · **DETALHAMENTO 0.48** |
| Correlação nº de elementos × nota real de C5 (dentro do corpus) | ρ = 0.58 |
| A mesma correlação, **fora** do corpus (n=30) | ρ = **0.336**, não monotônica |

Os rótulos de treino vieram de um **LLM lendo a Cartilha do Participante**, não de
corretores do ENEM, e nunca passaram por revisão de especialista. Isso é supervisão
fraca, e está dito em todo lugar — não é um padrão-ouro. Leia o
[model card](./MODEL_CARD.md) antes de citar qualquer número daqui.

### A parte mais útil deste repositório é um resultado negativo

Este projeto construiu uma estimativa de nota de Competência 5, validou, e **jogou fora**.

Dentro do corpus ela ia bem (QWK 0.524). Num primeiro teste externo com 10 redações
já corrigidas, ρ = 0.831 — melhor ainda. Aí o teste cresceu para 30 redações e a
correlação caiu para **ρ = 0.347, IC 95% [−0.02, 0.65]** — o intervalo inclui zero.
Nas 20 redações novas, ρ = 0.064.

Pior que ser fraca, ela errava **para baixo justamente nas boas redações**: entre as
que tiraram C5 ≥ 150 de verdade, prevíamos em média 105 contra 181 reais. Um número
confiante que diria a quem escreveu bem que escreveu mal.

Sobrou apenas um corte grosseiro, de dois grupos, que sobrevive ao mesmo teste — e
que o demo mostra com a sobreposição entre os grupos desenhada, não escondida.

📄 **[Leia o relatório completo](./docs/reports/score-estimate-negative-result.md)** —
com a taxa de contaminação de 26% nas redações coletadas, por que n=10 enganou, e o
que sobrou.

### Rodando o demo localmente

```bash
git clone https://github.com/akagabi/enembert.git
cd enembert/demo
npm install
npm run dev          # http://localhost:5173
```

O build de produção busca os pesos no Hugging Face; o modo `dev` usa os pesos locais
em `demo/public/models/`. Detalhes em [`demo/README.md`](./demo/README.md).

### Reproduzindo a avaliação

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                     # 74 testes
python scripts/eval_model.py               # F1 vs. o conjunto retido
python scripts/eval_external.py            # o benchmark externo (precisa dos dados locais)
```

### Estrutura

| caminho | o que é |
|---|---|
| `src/enembert/` | pacote: corpus, rotulagem, treino, exportação ONNX |
| `scripts/` | pipeline executável, um passo por arquivo |
| `demo/` | app de página única (TypeScript + transformers.js) |
| `annotation/guideline.md` | o roteiro de anotação dado ao rotulador |
| `docs/writeup.md` | a história completa, incluindo os erros |
| `docs/decisions.md` | decisões vinculantes, com a evidência medida |
| `docs/reports/` | avaliações, baseline e o resultado negativo |

**Os dados não estão aqui.** O corpus de origem é de terceiros e tem restrição de
direitos autorais, então este repositório nunca contém texto de redação — só
anotações *stand-off* (ids e posições de caracteres). Veja o
[dataset card](./DATASET_CARD.md).

### Links

- [Model card](./MODEL_CARD.md) — o que o modelo faz, métricas, como usar
- [Dataset card](./DATASET_CARD.md) — o dataset stand-off e a rotulagem
- [Writeup](./docs/writeup.md) — por que supervisão fraca, onde quebrou, o que a avaliação honesta diz
- [Resultado negativo](./docs/reports/score-estimate-negative-result.md) — o recurso construído, medido e apagado
- **[Testar o demo online](https://akagabi.github.io/enembert/)** — roda no seu navegador, nada é enviado
- **[Modelo no Hugging Face](https://huggingface.co/akagabi/enemBERT)** — `akagabi/enemBERT`

### Licença e créditos

Código MIT (`LICENSE`); pesos Apache-2.0. Modelo-base
[BERTimbau](https://huggingface.co/neuralmind/bert-base-portuguese-cased). Dados de
treino: [`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset)
(apache-2.0). Definições adaptadas da Cartilha do Participante (INEP).

Feito por [akagabi](https://github.com/akagabi). Projeto independente, sem qualquer
vínculo com o INEP ou o MEC.

---

## English

ENEM — Brazil's national university-entrance exam, taken by roughly 4 million people a
year — asks for an **intervention proposal** in the essay's conclusion, built from five
parts: who acts (**agente**), what they do (**ação**), how (**meio**), to what end
(**efeito**), and an elaboration of one of them (**detalhamento**). Unlike the other four
competencies, that question is close to mechanical: the five parts are there or they
aren't.

enemBERT marks those five elements in the text itself:

```
Portanto, é imprescindível que [o Ministério da Educação]AGENTE, [órgão responsável
pela política educacional do país]DETALHAMENTO, [amplie o programa de bolsa-permanência]AÇÃO,
[por meio de parcerias com as secretarias estaduais]MEIO, [a fim de reduzir a evasão
escolar no ensino médio]EFEITO.
```

### What it does — and doesn't

|  | |
|---|---|
| ✅ | Points at **which of the five elements appear** and which are missing, by the literal words |
| ✅ | Runs **entirely in the browser** — the essay is never uploaded anywhere |
| ✅ | Shows a **coarse band** for Competência 5, with its uncertainty drawn on screen |
| ❌ | **Never predicts a grade.** No individual score, ever |
| ❌ | Does not judge grammar, argument, cohesion, or the other four competencies |
| ❌ | Is not official, has no link to INEP/MEC, and does not replace a human grader |

### Results

| metric | value |
|---|---|
| Overlap-F1 (micro) vs. regex baseline | **0.58** vs. 0.27 |
| Strongest / weakest element | AGENTE 0.66 · **DETALHAMENTO 0.48** |
| Correlation of element count with real C5 grade (in-corpus) | ρ = 0.58 |
| Same correlation **out-of-corpus** (n=30) | ρ = **0.336**, non-monotonic |

Training labels came from an **LLM reading the official rubric**, not from ENEM graders,
and were never expert-reviewed. That's weak supervision, said plainly everywhere — not a
gold standard. Read the [model card](./MODEL_CARD.md) before citing any number here.

### The most useful thing in this repo is a negative result

This project built a Competência 5 score estimate, validated it, and **threw it away**.

In-corpus it looked fine (QWK 0.524). A first external check on 10 human-graded essays
gave ρ = 0.831 — better still. Then the benchmark grew to 30 essays and the correlation
fell to **ρ = 0.347, 95% CI [−0.02, 0.65]** — the interval includes zero. On the 20 new
essays alone, ρ = 0.064.

Worse than weak, it erred **downward specifically on good essays**: among those that
really scored C5 ≥ 150, it predicted a mean of 105 against a real mean of 181. A
confident number that would tell strong writers they were weak.

What survived is a single coarse two-bucket split that holds up on the same benchmark —
and the demo draws the overlap between buckets rather than hiding it.

📄 **[Read the full report](./docs/reports/score-estimate-negative-result.md)** — the 26%
contamination rate among scraped essays, why n=10 misled, and what was left standing.

### Running the demo locally

```bash
git clone https://github.com/akagabi/enembert.git
cd enembert/demo
npm install
npm run dev          # http://localhost:5173
```

The production build streams weights from Hugging Face; `dev` mode uses the local weights
in `demo/public/models/`. See [`demo/README.md`](./demo/README.md).

### Reproducing the evaluation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                     # 74 tests
python scripts/eval_model.py               # F1 against the held-out set
python scripts/eval_external.py            # the external benchmark (needs local data)
```

### Layout

| path | what it is |
|---|---|
| `src/enembert/` | package: corpus, labeling, training, ONNX export |
| `scripts/` | runnable pipeline, one step per file |
| `demo/` | single-page app (TypeScript + transformers.js) |
| `annotation/guideline.md` | the annotation rubric handed to the labeler |
| `docs/writeup.md` | the full story, mistakes included |
| `docs/decisions.md` | binding decisions with the measured evidence |
| `docs/reports/` | evaluations, baseline, and the negative result |

**The data is not here.** The source corpus is third-party and copyright-restricted, so
this repository never contains essay text — only *stand-off* annotations (ids and
character offsets). See the [dataset card](./DATASET_CARD.md).

### Links

- [Model card](./MODEL_CARD.md) — what the model does, metrics, usage
- [Dataset card](./DATASET_CARD.md) — the stand-off dataset and the labeling process
- [Writeup](./docs/writeup.md) — why weak supervision, where it broke, what honest evaluation says
- [Negative result](./docs/reports/score-estimate-negative-result.md) — the feature built, measured, and deleted
- **[Try the live demo](https://akagabi.github.io/enembert/)** — runs in your browser, nothing is uploaded
- **[Model on Hugging Face](https://huggingface.co/akagabi/enemBERT)** — `akagabi/enemBERT`

### License and credits

Code MIT (`LICENSE`); weights Apache-2.0. Base model
[BERTimbau](https://huggingface.co/neuralmind/bert-base-portuguese-cased). Training data:
[`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset)
(apache-2.0). Element definitions adapted from the INEP Cartilha do Participante.

Built by [akagabi](https://github.com/akagabi). Independent project, unaffiliated with
INEP or MEC.
