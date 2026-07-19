import json, os, time
from pathlib import Path
import requests
from enembert.data.paragraphs import split_paragraphs
from enembert.labeling.labeler import build_prompt, parse_response, LabelError

BUDGET_USD = 5.0
USD_PER_MTOKEN = 2.0  # deliberately pessimistic blended rate


class CostGuardError(Exception):
    pass


def estimate_cost_usd(rows: list[dict]) -> float:
    chars = sum(len(r["essay_text"]) for r in rows)
    prompt_overhead = 6000 * len(rows)  # guideline+examples per call, chars
    return (chars + prompt_overhead) / 3 / 1e6 * USD_PER_MTOKEN


def assert_within_budget(rows: list[dict]) -> None:
    est = estimate_cost_usd(rows)
    if est > BUDGET_USD:
        raise CostGuardError(f"estimated ${est:.2f} > budget ${BUDGET_USD}")


def check_env() -> str:
    key = os.environ.get("ENEMBERT_LABELER_KEY")
    if not key:
        raise RuntimeError("Set ENEMBERT_LABELER_KEY (PERSONAL key — never an org key).")
    for var, val in os.environ.items():
        if "example-org" in val.lower() and var.startswith(("HF_", "ENEMBERT_")):
            raise RuntimeError(f"{var} points at the org ({val}); personal billing only.")
    return key


def call_api(messages: list[dict]) -> str:
    url = os.environ.get("ENEMBERT_LABELER_URL", "https://api.deepseek.com")
    model = os.environ.get("ENEMBERT_LABELER_MODEL", "deepseek-chat")
    r = requests.post(url.rstrip("/") + "/chat/completions",
                      headers={"Authorization": f"Bearer {check_env()}"},
                      json={"model": model, "messages": messages, "temperature": 0},
                      timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def label_rows(rows: list[dict], client_call=call_api) -> list[dict]:
    out = []
    total_dropped = 0
    for n, r in enumerate(rows):
        paras = split_paragraphs(r["essay_text"])
        result = None
        for attempt in range(3):
            try:
                result = parse_response(client_call(build_prompt(paras)), paras)
                break
            except (LabelError, requests.RequestException):
                time.sleep(2 ** attempt)
        if result is None:
            out.append({"essay_id": r["essay_id"], "spans": None, "dropped": 0})
        else:
            total_dropped += result.dropped
            out.append({"essay_id": r["essay_id"],
                        "spans": [[s.__dict__ for s in ps] for ps in result.spans],
                        "dropped": result.dropped})
        if (n + 1) % 25 == 0:
            print(f"{n + 1}/{len(rows)}, dropped so far: {total_dropped}")
    print(f"total dropped elements: {total_dropped}")
    return out
