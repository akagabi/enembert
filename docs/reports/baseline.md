# enemBERT — regex baseline evaluation

Baseline (marker-driven regex tagger) vs LLM labels on the held-out, prompt-disjoint gold set. For comparison against docs/reports/eval.md (the trained model). No essay text below, aggregates only.

## Per-element F1 (baseline vs LLM labels, gold set)

### Overlap (Jaccard >= 0.5)
```json
{
  "micro_f1": 0.27,
  "per_element": {
    "MEIO": 0.479,
    "AGENTE": 0.239,
    "ACAO": 0.181,
    "DETALHAMENTO": 0.0,
    "EFEITO": 0.376
  }
}
```

### Exact
```json
{
  "micro_f1": 0.216,
  "per_element": {
    "MEIO": 0.424,
    "AGENTE": 0.174,
    "ACAO": 0.131,
    "DETALHAMENTO": 0.0,
    "EFEITO": 0.345
  }
}
```

## Grade correlation (external validity, for parity with the model report)
```json
{
  "spearman": 0.488,
  "mean_c5_full": null,
  "mean_c5_low": 78.2,
  "n": 255,
  "n_full": 0,
  "n_low": 67
}
```

## Qualitative examples (essay_id + elements found only, no essay text)

- `gradesThousand:test:A Persistência da Violência contra a Mulher na Sociedade Brasileira:175`: ACAO, AGENTE, MEIO
- `gradesThousand:test:A Persistência da Violência contra a Mulher na Sociedade Brasileira:176`: AGENTE, MEIO
- `gradesThousand:test:A Persistência da Violência contra a Mulher na Sociedade Brasileira:179`: AGENTE, MEIO
- `gradesThousand:test:Caminhos para combater a intolerância religiosa no Brasil:189`: AGENTE, MEIO
- `gradesThousand:test:Desafios para o enfrentamento da invisibilidade do trabalho de cuidado realizado pela mulher no Brasil:252`: ACAO, AGENTE, EFEITO, MEIO
