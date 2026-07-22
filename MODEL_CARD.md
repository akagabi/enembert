---
language:
- pt
license: apache-2.0
library_name: transformers
pipeline_tag: token-classification
base_model: neuralmind/bert-base-portuguese-cased
tags:
- enem
- portuguese
- token-classification
- education
- weak-supervision
---

# enemBERT

**Projeto independente, não afiliado ao INEP/MEC.** / **Independent project, not affiliated with INEP/MEC** (the Brazilian bodies that administer the ENEM exam).

A BERTimbau (`neuralmind/bert-base-portuguese-cased`) fine-tune that finds the five rhetorical elements of the ENEM *proposta de intervenção* — Competência 5 — inside an essay conclusion: AGENTE, AÇÃO, MEIO, EFEITO, DETALHAMENTO.

---

## Português

### O que faz e o que não faz

**Faz:** recebe um parágrafo (tipicamente a conclusão de uma redação do ENEM) e marca, como trechos do próprio texto, quais dos cinco elementos da proposta de intervenção estão presentes: quem deve agir (agente), o que deve ser feito (ação), como (meio), para quê (efeito) e um detalhamento adicional de algum desses elementos.

**Não faz:** **não dá nota.** O modelo nunca produz uma pontuação, nota de Competência 5 ou qualquer estimativa de nota. Ele aponta presença/ausência de elementos apontando as palavras exatas — nada além disso. Também não corrige erros gramaticais, não reescreve texto e não avalia as outras quatro competências do ENEM.

### Rótulos gerados por LLM — não é gold verificado por humanos

**Isto é supervisão fraca (weak supervision).** Os rótulos de treino e de avaliação foram gerados por um LLM (DeepSeek) aplicando o roteiro da Cartilha do Participante (INEP), com os trechos resolvidos para offsets de caracteres por casamento exato de citação. Nenhum rótulo passou por revisão ou correção humana. Isso é dito aqui de forma direta porque importa: o modelo aprendeu a imitar o rotulador, não uma verdade validada por um especialista. Veja "Avaliação" abaixo para o que isso implica na hora de ler os números.

### Esquema de rótulos

Esquema BIO plano sobre 5 tipos de elemento (11 rótulos, ids 0–10):

`O, B-AGENTE, I-AGENTE, B-ACAO, I-ACAO, B-MEIO, I-MEIO, B-EFEITO, I-EFEITO, B-DETALHAMENTO, I-DETALHAMENTO`

| Elemento | Definição (parafraseada da Cartilha do Participante, INEP) |
|---|---|
| AGENTE | Quem deve executar a ação — instituição, órgão ou grupo social nomeado explicitamente. |
| AÇÃO | A medida concreta proposta para enfrentar o problema discutido na redação. |
| MEIO | Como a ação será colocada em prática — o instrumento ou modo utilizado. |
| EFEITO | Para quê a ação serve — a finalidade ou o resultado esperado. |
| DETALHAMENTO | Uma explicação a mais sobre outro elemento da proposta — detalha, exemplifica ou justifica. |

### Avaliação

Sem gold humano, não há como medir "acerto" no sentido usual. O que existe são duas verificações, e ambas são reportadas com essa ressalva:

**1. Concordância com o rotulador (não é "correção").** F1 por elemento do modelo contra os rótulos do LLM, no conjunto de teste retido e disjunto por prompt (255 redações, prompt-disjoint das 788 usadas em treino). "Overlap" conta um acerto quando a sobreposição entre trecho previsto e trecho rotulado passa de 50% (Jaccard ≥ 0.5); "exact" exige limites idênticos.

| Elemento | F1 overlap (modelo) | F1 overlap (baseline regex) | F1 exact (modelo) |
|---|---|---|---|
| AGENTE | 0.66 | 0.24 | 0.53 |
| AÇÃO | 0.50 | 0.18 | 0.34 |
| MEIO | 0.63 | 0.48 | 0.53 |
| EFEITO | 0.58 | 0.38 | 0.52 |
| DETALHAMENTO | 0.48 | 0.00 | 0.40 |
| **micro** | **0.58** | **0.27** | **0.45** |

O modelo supera o baseline (um marcador regex sobre conectivos como "por meio de", "a fim de") nos cinco elementos. Isso mostra que ele aprendeu algo além de casar palavras-gatilho, não que ele está "certo" num sentido absoluto — o baseline e o modelo estão sendo comparados contra o mesmo rótulo ruidoso.

**2. Correlação com a nota real (a validação externa).** Para cada redação do conjunto de teste, contamos quantos elementos distintos o modelo encontra e comparamos com a nota real de Competência 5 do ENEM daquela redação — uma nota atribuída por corretores humanos de verdade, nunca usada como sinal de treino. Correlação de Spearman ρ = **0.58** (n=255). Redações onde o modelo encontra os 5 elementos têm nota C5 média de 197.2 pontos (n=43); redações onde encontra ≤1 elemento têm média de 72.3 (n=57). Esse número é ancorado em avaliação humana real — mas **só vale dentro deste corpus**: num benchmark externo de 30 redações publicadas, a mesma correlação cai para ρ = 0.336 e deixa de ser monotônica (3 elementos → C5 médio 150; 4 elementos → C5 médio 100). Não use a contagem de elementos como nota. Ver [o relatório do resultado negativo](./docs/reports/score-estimate-negative-result.md).

### Como usar

**Python:**

```python
from transformers import pipeline

tagger = pipeline("token-classification", model="akagabi/enemBERT", aggregation_strategy="simple")
resultado = tagger(paragrafo_da_conclusao)
```

**JavaScript (navegador, via transformers.js) — a redação nunca sai da máquina do usuário:**

```js
import { pipeline } from '@huggingface/transformers';

const tagger = await pipeline('token-classification', 'akagabi/enemBERT', { dtype: 'q8' });
const resultado = await tagger(paragrafo, { aggregation_strategy: 'simple' });
```

### Dados de treino

Treinado sobre `kamel-usp/aes_enem_dataset` (apache-2.0), 3.792 redações únicas ao todo. 800 redações foram rotuladas pelo LLM para o pool de treino (788 utilizáveis, 12 falharam na rotulagem), gerando 3.035 trechos rotulados: AGENTE 963, AÇÃO 1043, MEIO 353, EFEITO 547, DETALHAMENTO 129. O conjunto de teste retido (255 redações, 44 prompts, disjunto por prompt do treino) foi rotulado à parte, apenas para comparação com o baseline — a nota C5 real de cada redação já vinha no corpus original.

### Limitações conhecidas

- **DETALHAMENTO é o elemento mais fraco** (F1 overlap 0.48) mesmo depois de corrigir o colapso de classe (ver o writeup para a história completa). É também o elemento com definição mais ambígua na própria Cartilha.
- **Treinado em rótulos de LLM, não verificados por humanos.** O modelo herda os pontos cegos e as idiossincrasias do rotulador — por exemplo, ocasionalmente marcar um verbo como "devemos" como AGENTE.
- Cerca de 86% de uma das três fontes do corpus (`sourceB`, ~85% do total de redações) chegou como um único bloco de texto sem quebras de parágrafo, por dano de OCR/crawl upstream. Essas redações são mais difíceis tanto para o rotulador quanto para o modelo.
- F1 exact é bem menor que F1 overlap (micro 0.45 vs 0.58) — o modelo costuma acertar a região certa, mas não sempre o limite exato do trecho.
- A distribuição de notas C5 do conjunto de teste não reflete a do corpus real (superrepresenta notas altas); os números acima são um diagnóstico por faixa de nota, não uma estimativa de acurácia populacional.

### Estimativa de Competência 5: reduzida a uma faixa grosseira

O demo chegou a mostrar uma estimativa de nota exata de Competência 5. **Ela foi removida** — não por cautela, mas porque a medimos direito e ela não funciona. No lugar dela ficou uma faixa grosseira de dois grupos, que é o que a evidência sustenta.

- **Como funcionava:** uma regressão logística multinomial pequena sobre quais dos 5 elementos o tagger encontrou, quantos elementos distintos e quantos trechos. Rodava só no navegador.
- **Dentro do corpus** (conjunto de teste retido, disjunto por prompt): QWK = 0.524, concordância moderada. Parecia utilizável.
- **Fora do corpus** (30 redações publicadas com nota humana real, verificadas como ausentes do corpus de treino): Spearman ρ = **0.347**, IC 95% = **[−0.02, 0.65]**. O intervalo inclui zero — estatisticamente indistinguível de nenhuma correlação.
- **O primeiro teste externo enganou.** Nas 10 primeiras redações, ρ = 0.831. Nas 20 seguintes, ρ = 0.064. As 10 primeiras continham duas redações nota 1000 do INEP que o modelo acerta com facilidade.
- **O erro tinha a pior forma possível:** subestimava sistematicamente as boas redações. Para C5 real ≥ 150 (n=13), prevíamos em média 105 contra 181 real. Só parecia acertar nas redações fracas, onde "achou pouco" calha de ser a resposta certa.
- **A nota total (0–1000) nunca foi mostrada.** Prevê-la diretamente chegou a QWK 0.60, mas com erro médio de ±223 pontos.
- **Um quase-erro anterior, que vale registrar:** uma versão incluía o comprimento da redação como variável e chegava a QWK 0.681, mas o comprimento dominava o modelo — uma redação curta e boa, com os 5 elementos, tirava C5=40 só por ser curta. O comprimento foi removido.

**O que o demo mostra hoje:** um único corte grosseiro em 3+ dos cinco elementos. Redações com 3+ elementos tiveram mediana de C5 real 150 (metade central 100–200, n=16); com 0–2 elementos, mediana 100 (metade central 50–140, n=14); Mann-Whitney p = 0.035. A direção se repete de forma independente no conjunto interno (medianas 80 → 200, n=255) — é por isso que ela é exibida. O painel declara na própria tela que as faixas se sobrepõem, que a amostra é de 30 redações e que a diferença não sobrevive à correção de Bonferroni para os 6 cortes testados. Cortes mais finos foram rejeitados por evidência: em 4+ elementos, p = 0.38, e as medianas por contagem exata não são monotônicas (3 elementos supera 4).

Relatório completo, com tabelas e método: [resultado negativo da estimativa de nota](./docs/reports/score-estimate-negative-result.md).

**Consequência para a contagem de elementos:** o mesmo benchmark externo mostrou que a correlação entre número de elementos encontrados e nota real de C5 cai de ρ = 0.58 (dentro do corpus) para ρ = **0.336** fora dele, e não é monotônica — redações com 3 elementos encontrados têm média de C5 150, mas as com 4 têm média 100. **Não use a contagem de elementos como medida de qualidade.**

### Créditos

- Dados: [`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset) (apache-2.0).
- Roteiro de anotação: INEP — Cartilha do Participante, Competência 5.
- Modelo-base: `neuralmind/bert-base-portuguese-cased` (BERTimbau).

### Licença

Pesos: **Apache-2.0**. Código do pipeline (treino, avaliação, demo): MIT, no repositório GitHub.

---

## English

### What it does and what it does not

**Does:** takes a paragraph (typically an ENEM essay's conclusion) and marks, as spans of the original text, which of the five *proposta de intervenção* elements are present: who should act (agente), what should be done (ação), how (meio), to what end (efeito), and an additional elaboration of one of those elements (detalhamento).

**Does not:** **never predicts a grade.** No output, score, or Competência 5 estimate. It points at presence/absence of elements by pointing at the literal words, nothing more. It does not correct grammar, does not rewrite text, and does not evaluate any of the other four ENEM competencies.

### LLM-generated labels — not human-verified gold

**This is weak supervision.** Training and test labels were produced by an LLM (DeepSeek) applying the INEP Cartilha do Participante rubric, resolved to character offsets by exact quote matching. No label was human-reviewed or human-corrected. Stated plainly because it matters: the model learned to imitate the labeler, not a truth validated by an expert. See "Evaluation" below for what that means when reading the numbers.

### Label schema

Flat BIO scheme over 5 element types (11 labels, ids 0-10):

`O, B-AGENTE, I-AGENTE, B-ACAO, I-ACAO, B-MEIO, I-MEIO, B-EFEITO, I-EFEITO, B-DETALHAMENTO, I-DETALHAMENTO`

| Element | Definition (paraphrased from the Cartilha do Participante, INEP) |
|---|---|
| AGENTE | Who should carry out the action — an institution, agency, or social group named explicitly. |
| ACAO | The concrete measure proposed to address the essay's problem. |
| MEIO | How the action will be carried out — the instrument or method used. |
| EFEITO | What the action is for — its purpose or expected result. |
| DETALHAMENTO | An additional elaboration of another element — detailing, exemplifying, or justifying it. |

### Evaluation

Without human gold, "correctness" in the usual sense is not measurable. What exists instead are two checks, both reported with that caveat attached:

**1. Agreement with the labeler (not "correctness").** Per-element F1 of the model against the LLM labels, on the held-out, prompt-disjoint gold set (255 essays, prompt-disjoint from the 788 used in training). "Overlap" counts a match when predicted and labeled spans overlap by at least 50% (Jaccard >= 0.5); "exact" requires identical boundaries.

| Element | F1 overlap (model) | F1 overlap (regex baseline) | F1 exact (model) |
|---|---|---|---|
| AGENTE | 0.66 | 0.24 | 0.53 |
| ACAO | 0.50 | 0.18 | 0.34 |
| MEIO | 0.63 | 0.48 | 0.53 |
| EFEITO | 0.58 | 0.38 | 0.52 |
| DETALHAMENTO | 0.48 | 0.00 | 0.40 |
| **micro** | **0.58** | **0.27** | **0.45** |

The model beats the baseline (a regex tagger over discourse markers like "por meio de", "a fim de") on all five elements. That shows it learned something beyond trigger-word matching, not that it is "right" in an absolute sense — both model and baseline are being scored against the same noisy label.

**2. Correlation with the real grade (the external check).** For each held-out essay, we count how many distinct elements the model finds and compare against that essay's real ENEM Competência 5 grade — assigned by actual human graders, never used as a training signal. Spearman ρ = **0.58** (n=255). Essays where the model finds all 5 elements average a C5 grade of 197.2 (n=43); essays where it finds <=1 element average 72.3 (n=57). This number is anchored to real human judgment — but it **only holds inside this corpus**: on an external benchmark of 30 published essays the same correlation drops to ρ = 0.336 and stops being monotonic (3 elements → mean C5 150; 4 elements → mean C5 100). Do not use the element count as a grade. See [the negative-result report](./docs/reports/score-estimate-negative-result.md).

### Usage

**Python:**

```python
from transformers import pipeline

tagger = pipeline("token-classification", model="akagabi/enemBERT", aggregation_strategy="simple")
result = tagger(conclusion_paragraph)
```

**JavaScript (browser, via transformers.js) — the essay never leaves the user's machine:**

```js
import { pipeline } from '@huggingface/transformers';

const tagger = await pipeline('token-classification', 'akagabi/enemBERT', { dtype: 'q8' });
const result = await tagger(paragraph, { aggregation_strategy: 'simple' });
```

### Training data

Trained on `kamel-usp/aes_enem_dataset` (apache-2.0), 3,792 unique essays overall. 800 essays were LLM-labeled for the training pool (788 usable, 12 failed labeling), yielding 3,035 labeled spans: AGENTE 963, ACAO 1043, MEIO 353, EFEITO 547, DETALHAMENTO 129. The held-out gold set (255 essays, 44 prompts, prompt-disjoint from training) was labeled separately for the baseline comparison — its real C5 grades came from the original corpus.

### Known limitations

- **DETALHAMENTO is the weakest element** (0.48 overlap F1) even after fixing a class-collapse problem (see the writeup for the full story). It is also the element with the most ambiguous definition in the rubric itself.
- **Trained on LLM labels, not human-verified.** The model inherits the labeler's blind spots and quirks — for instance, occasionally tagging a verb like "devemos" (we should) as AGENTE.
- About 86% of one of the corpus's three source configs (`sourceB`, roughly 85% of all essays) arrived as a single unbroken block of text with no paragraph breaks, due to upstream OCR/crawl damage. Those essays are harder for both the labeler and the model.
- Exact-span F1 is noticeably lower than overlap F1 (micro 0.45 vs 0.58) — the model usually finds the right region but not always the exact boundary.
- The gold set's C5 grade distribution does not match the real corpus (it over-represents high-scoring essays); the numbers above are a diagnostic across score bands, not a population-level accuracy estimate.

### Competência 5 score estimate: reduced to a coarse band

The demo used to show an estimated exact Competência 5 grade. **It has been removed** — not out of caution, but because we measured it properly and it does not work. What replaced it is a coarse two-bucket band, which is what the evidence supports.

- **How it worked:** a small multinomial logistic regression over which of the 5 elements the tagger found, how many distinct elements, and how many spans. Ran entirely in the browser.
- **In-corpus** (held-out, prompt-disjoint test set): QWK = 0.524, moderate agreement. It looked usable.
- **Out-of-corpus** (30 published essays with real human grades, each verified absent from the training corpus): Spearman ρ = **0.347**, 95% CI = **[−0.02, 0.65]**. The interval includes zero — statistically indistinguishable from no correlation.
- **The first external check was misleading.** On the first 10 essays, ρ = 0.831. On the next 20, ρ = 0.064. Those first 10 happened to include two INEP *nota 1000* exemplars the model aces.
- **The error had the worst possible shape:** it systematically under-credited good essays. For real C5 ≥ 150 (n=13) we predicted a mean of 105 against a real mean of 181. It only looked accurate on weak essays, where "found little" happens to be the right answer.
- **The total (0–1000) was never shown.** Predicting it directly reached QWK 0.60 but with an average error of ±223 points.
- **An earlier near-miss worth recording:** one version added essay length as a feature and reached QWK 0.681, but length dominated the model — a short, well-written essay with all 5 elements scored C5=40 just for being short. Length was dropped.

**What the demo shows today:** a single coarse cut at 3+ of the five elements. Essays with 3+ elements had a median real C5 of 150 (middle half 100–200, n=16); essays with 0–2 had a median of 100 (middle half 50–140, n=14); Mann-Whitney p = 0.035. The direction replicates independently on the in-corpus gold set (medians 80 → 200, n=255), which is why it is shown at all. The panel states on its own face that the ranges overlap, that the sample is 30 essays, and that the difference does not survive Bonferroni correction for the 6 cuts tried. Finer cuts were rejected on evidence: at 4+ elements p = 0.38, and per-exact-count medians are non-monotonic (3 elements outscores 4).

Full report with tables and method: [score-estimate negative result](./docs/reports/score-estimate-negative-result.md).

**Consequence for the element count:** the same external benchmark showed the correlation between number of elements found and real C5 grade drops from ρ = 0.58 (in-corpus) to ρ = **0.336** externally, and is not monotonic — essays where 3 elements are found average a real C5 of 150, while those with 4 average 100. **Do not use the element count as a quality score.**

### Credits

- Data: [`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset) (apache-2.0).
- Annotation rubric: INEP — Cartilha do Participante, Competência 5.
- Base model: `neuralmind/bert-base-portuguese-cased` (BERTimbau).

### License

Weights: **Apache-2.0**. Pipeline code (training, evaluation, demo): MIT, in the GitHub repository.
