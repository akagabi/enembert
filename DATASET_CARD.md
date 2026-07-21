---
language:
- pt
license: apache-2.0
task_categories:
- token-classification
tags:
- enem
- portuguese
- education
- weak-supervision
---

# enembert-annotations

**Projeto independente, não afiliado ao INEP/MEC.** / **Independent project, not affiliated with INEP/MEC.**

Stand-off span annotations of the five rhetorical elements of the ENEM *proposta de intervenção* (Competência 5) — AGENTE, AÇÃO, MEIO, EFEITO, DETALHAMENTO — over essays from [`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset).

---

## Português

### Por que "stand-off" (sem texto)

Este dataset **não contém texto de redação nenhum**. Cada linha traz apenas `essay_id`, a config de origem, e uma lista de trechos: índice de parágrafo, offsets de caractere (início/fim) e rótulo. Para reconstruir o texto anotado, use o loader (`load_enembert.py`) para baixar `kamel-usp/aes_enem_dataset` e reunir as anotações ao texto localmente.

O motivo é direito autoral upstream: as redações de `kamel-usp/aes_enem_dataset` têm proveniência UOL, e o próprio dataset de origem carrega essa ressalva. Redistribuir apenas offsets, sem o texto, evita duplicar esse problema — cada usuário baixa o texto diretamente da fonte, sob a licença dela.

### Como carregar

```bash
pip install datasets
python load_enembert.py   # smoke check: imprime um exemplo já unido a texto
```

```python
from load_enembert import load_split

for row in load_split("train.jsonl"):
    for span in row["para_spans"]:
        texto = row["paragraphs"][span["para_idx"]][span["start"]:span["end"]]
        print(span["label"], texto)
```

`load_split` baixa `kamel-usp/aes_enem_dataset` (todas as configs, todos os splits), separa cada redação em parágrafos com a mesma regra usada para gravar os offsets (`text.split("\n")`, cada parágrafo com espaços nas pontas removidos, parágrafos vazios descartados), e junta cada trecho anotado ao texto correspondente.

### Arquivos

- `train.jsonl` — 788 redações rotuladas (pool de treino).
- `gold.jsonl` — 255 redações rotuladas (conjunto de teste retido, disjunto por prompt do treino).
- `load_enembert.py` — loader autocontido (só depende de `datasets`).

### Esquema de rótulos

`AGENTE`, `ACAO`, `MEIO`, `EFEITO`, `DETALHAMENTO` — os cinco elementos retóricos da proposta de intervenção do ENEM, conforme a Cartilha do Participante (INEP). Anotação BIO plana; DETALHAMENTO é sempre seu próprio trecho, separado no limite da oração (a definição da Cartilha o descreve como elaboração de outro elemento, o que produziria trechos aninhados — impossíveis em BIO plano — então essa foi a convenção escolhida).

### O processo de rotulagem e os problemas encontrados

**Os rótulos foram gerados por um LLM (DeepSeek), não por humanos.** O modelo recebia o roteiro de anotação (baseado na Cartilha do Participante) e retornava, para cada parágrafo, uma lista de citações verbatim com seus rótulos. As citações eram resolvidas para offsets de caractere por busca exata de string (`str.find`); uma citação que não aparecesse exatamente no parágrafo era descartada, não corrigida ou aproximada.

Isso funcionou bem na maior parte do corpus, mas dois problemas concretos apareceram durante a construção deste dataset e vale documentar, porque afetam a qualidade e a cobertura dos rótulos:

**1. Texto corrompido por OCR.** Uma das três fontes do corpus (`sourceB`) chegou com erros de digitalização — por exemplo "Ministério da ducação" (falta o "E") ou "omunicação" (falta o "C"). O LLM tendia a "corrigir" esses erros ao citar o trecho ("ducação" virava "Educação" na citação), o que quebrava o casamento exato de string e descartava o elemento inteiro. Em uma amostra de 150 redações, isso produzia 97 elementos descartados. Instruir o modelo explicitamente a copiar os caracteres exatos, erros de digitação incluídos, reduziu os descartes para 60 nessa mesma amostra (−38%) e recuperou 78 trechos que antes se perdiam.

**2. Redações sem quebra de parágrafo.** Cerca de 73% do corpus (a config `sourceB`, ~85% das redações totais) perdeu as quebras de linha originais num crawl upstream — 86% dessas redações chegam como um único bloco de texto. Como a proposta de intervenção fica na conclusão (perto do fim do texto), qualquer truncamento agressivo do parágrafo cortaria a conclusão fora antes que o modelo a visse, ensinando (silenciosamente) que redações não têm proposta de intervenção. Não é um problema de rotulagem em si, mas afeta tanto a qualidade dos rótulos quanto do modelo treinado sobre eles — documentado com mais detalhe, incluindo a correção aplicada no treino, em `docs/writeup.md` do repositório de código.

Nenhum desses dois problemas foi completamente eliminado — redações vindas de `sourceB` continuam tendo taxa de descarte mais alta que as demais (0.43 elemento descartado por redação, contra 0.15 nas fontes limpas, medido na mesma amostra de 150).

### Divulgação importante: não é gold verificado por humanos

Os rótulos em `train.jsonl` e `gold.jsonl` **não foram revisados nem corrigidos por humanos.** Trate-os como rótulos "silver", adequados para treinar um modelo por supervisão fraca, não como padrão-ouro de avaliação. `gold.jsonl` é chamado de "gold" porque é o conjunto de teste retido (disjunto por prompt do treino), não porque tenha sido verificado por um humano — a nomenclatura é uma convenção de split, não uma alegação de qualidade.

### Créditos

Construído inteiramente sobre [`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset) (apache-2.0). Todo o texto das redações e as notas têm origem lá; este dataset apenas adiciona offsets e rótulos. Cite/credite o dataset de origem ao utilizar este.

### Licença

Apache-2.0.

---

## English

### Why stand-off (no text)

This dataset ships **no essay text at all**. Each row carries only `essay_id`, the source config, and a list of spans: paragraph index, character offsets (start/end), and label. To reconstruct annotated text, use the loader (`load_enembert.py`) to download `kamel-usp/aes_enem_dataset` and join the annotations to text locally.

The reason is upstream copyright: the essays in `kamel-usp/aes_enem_dataset` have UOL provenance, and the source dataset itself carries that caveat. Redistributing offsets only, without text, avoids compounding that problem — each user downloads the text directly from the source, under its license.

### How to load

```bash
pip install datasets
python load_enembert.py   # smoke check: prints one example already joined to text
```

```python
from load_enembert import load_split

for row in load_split("train.jsonl"):
    for span in row["para_spans"]:
        text = row["paragraphs"][span["para_idx"]][span["start"]:span["end"]]
        print(span["label"], text)
```

`load_split` downloads `kamel-usp/aes_enem_dataset` (all configs, all splits), splits each essay into paragraphs using the same rule the offsets were recorded against (`text.split("\n")`, each paragraph stripped, empty paragraphs dropped), and joins each annotated span back to the matching text.

### Files

- `train.jsonl` — 788 labeled essays (training pool).
- `gold.jsonl` — 255 labeled essays (held-out test set, prompt-disjoint from training).
- `load_enembert.py` — self-contained loader (only depends on `datasets`).

### Label schema

`AGENTE`, `ACAO`, `MEIO`, `EFEITO`, `DETALHAMENTO` — the five rhetorical elements of the ENEM proposta de intervenção, per the Cartilha do Participante (INEP). Flat BIO annotation; DETALHAMENTO is always its own span, split at the clause boundary (the Cartilha describes it as an elaboration of another element, which would produce nested spans — impossible under flat BIO — so this was the chosen convention).

### The labeling process and its hiccups

**Labels were generated by an LLM (DeepSeek), not by humans.** The model received the annotation guideline (based on the Cartilha do Participante) and returned, for each paragraph, a list of verbatim quotes with their labels. Quotes were resolved to character offsets by exact string search (`str.find`); a quote that did not appear exactly in the paragraph was dropped, not corrected or approximated.

That worked well over most of the corpus, but two concrete problems came up while building this dataset and are worth documenting, because they affect label quality and coverage:

**1. OCR-corrupted text.** One of the corpus's three source configs (`sourceB`) arrived with scanning errors — for example "Ministério da ducação" (missing the "E") or "omunicação" (missing the "C"). The LLM tended to "correct" these when quoting ("ducação" became "Educação" in the quote), which broke the exact string match and dropped the whole element. On a 150-essay sample, this produced 97 dropped elements. Explicitly instructing the model to copy exact characters, typos included, cut the drop count to 60 on that same sample (-38%) and recovered 78 spans that were previously lost.

**2. Essays with no paragraph breaks.** About 73% of the corpus (config `sourceB`, ~85% of all essays) lost its original line breaks in an upstream crawl — 86% of those essays arrive as a single block of text. Since the proposta de intervenção sits in the conclusion (near the end of the text), any aggressive paragraph truncation would cut the conclusion off before the model ever saw it, silently teaching it that essays have no proposta de intervenção. This is not strictly a labeling problem, but it affects both the labels' quality and the model trained on them — documented in more detail, including the training-time fix, in `docs/writeup.md` in the code repository.

Neither problem was fully eliminated — essays from `sourceB` still have a higher drop rate than the rest (0.43 dropped elements per essay versus 0.15 for the clean sources, measured on the same 150-essay sample).

### Important disclosure: not human-verified gold

Labels in `train.jsonl` and `gold.jsonl` were **not reviewed or corrected by a human.** Treat them as noisy silver labels, suitable for training a model under weak supervision, not as an evaluation gold standard. `gold.jsonl` is named "gold" because it is the held-out test split (prompt-disjoint from training), not because it was human-verified — the name is a split convention, not a quality claim.

### Credits

Built entirely on top of [`kamel-usp/aes_enem_dataset`](https://huggingface.co/datasets/kamel-usp/aes_enem_dataset) (apache-2.0). All essay text and grades originate there; this dataset only adds offsets and labels. Please cite/credit the source dataset when using this one.

### License

Apache-2.0.
