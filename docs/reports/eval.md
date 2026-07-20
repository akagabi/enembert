# enemBERT — model evaluation

Model vs LLM labels on the held-out, prompt-disjoint gold set. Labels are LLM-generated (weak supervision) — this is model-vs-labeler agreement, not model-vs-expert-human agreement. No essay text below, aggregates only.

## Per-element F1 (model vs LLM labels, gold set)

### Overlap (Jaccard >= 0.5)
```json
{
  "micro_f1": 0.575,
  "per_element": {
    "EFEITO": 0.578,
    "DETALHAMENTO": 0.475,
    "AGENTE": 0.658,
    "ACAO": 0.499,
    "MEIO": 0.633
  }
}
```

### Exact
```json
{
  "micro_f1": 0.454,
  "per_element": {
    "EFEITO": 0.524,
    "DETALHAMENTO": 0.403,
    "AGENTE": 0.531,
    "ACAO": 0.341,
    "MEIO": 0.525
  }
}
```

## Grade correlation (external validity)

Spearman correlation between #distinct elements the model tags and the essay's real Competencia 5 grade (never used as training signal).
```json
{
  "spearman": 0.581,
  "mean_c5_full": 197.2,
  "mean_c5_low": 72.3,
  "n": 255,
  "n_full": 43,
  "n_low": 57
}
```

## Truncation drops (512 max_length, tail-truncation for single-paragraph essays)
```json
{
  "dropped": 22,
  "total_spans": 3035,
  "pct": 0.72
}
```

## Qualitative examples (essay_id + elements found only, no essay text)

- `gradesThousand:test:A Persistência da Violência contra a Mulher na Sociedade Brasileira:175`: ACAO, AGENTE, EFEITO
- `gradesThousand:test:A Persistência da Violência contra a Mulher na Sociedade Brasileira:176`: ACAO, AGENTE, MEIO
- `gradesThousand:test:A Persistência da Violência contra a Mulher na Sociedade Brasileira:179`: ACAO, AGENTE, EFEITO, MEIO
- `gradesThousand:test:Caminhos para combater a intolerância religiosa no Brasil:189`: ACAO, AGENTE, DETALHAMENTO, MEIO
- `gradesThousand:test:Desafios para o enfrentamento da invisibilidade do trabalho de cuidado realizado pela mulher no Brasil:252`: ACAO, AGENTE, DETALHAMENTO, EFEITO, MEIO
