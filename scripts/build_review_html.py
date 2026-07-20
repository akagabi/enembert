"""Generate a self-contained, LOCAL HTML review tool for the G1 labels.

The output (data/g1_review.html) embeds essay text and is therefore gitignored
and NEVER published — it opens with file:// in the annotator's own browser, so
the essays never leave their machine (stand-off constraint). This generator
carries no essay text and is safe to commit.

Usage: python scripts/build_review_html.py [--limit N] [--in FILE] [--out FILE]
Then open the printed path in a browser. Review, click "Baixar correções",
and hand the downloaded JSON back.
"""
import argparse
import json
from pathlib import Path

from enembert.data.paragraphs import split_paragraphs

COLORS = {  # element -> (light bg, dark bg)
    "AGENTE": ("#bfe6c3", "#2f5d38"),
    "ACAO": ("#bcd3ef", "#2b4a6f"),
    "MEIO": ("#e6c3e0", "#5d3557"),
    "EFEITO": ("#ecdcae", "#5f4d24"),
    "DETALHAMENTO": ("#bde3e6", "#28565b"),
}
ELEMENTS = list(COLORS)

CHEAT = {
    "AGENTE": "quem executa a ação (ex.: o governo, as escolas, a mídia). Pronomes e sujeito oculto NÃO contam.",
    "ACAO": "o que deve ser feito — começa no verbo (ex.: criar campanhas). O modal “deve” fica de fora.",
    "MEIO": "como / por qual instrumento — inclui o marcador (ex.: por meio de, mediante, com o uso de).",
    "EFEITO": "finalidade / resultado — inclui o marcador (ex.: a fim de, para que).",
    "DETALHAMENTO": "especificação extra de outro elemento (aposto, oração relativa, exemplo com “como…”).",
}


def build_data(corpus, rows, limit):
    out = []
    for r in rows:
        if r["spans"] is None:
            continue
        eid = r["essay_id"]
        paras = split_paragraphs(corpus[eid]["essay_text"])
        # only carry paragraphs + AI spans; NO grade (avoid biasing the reviewer)
        out.append({
            "id": eid,
            "short": eid.split(":", 1)[0] + " … " + eid.rsplit(":", 1)[-1],
            "paras": paras,
            "ai": [[{"s": s["start"], "e": s["end"], "l": s["label"]} for s in ps]
                   for ps in r["spans"]],
        })
        if limit and len(out) >= limit:
            break
    return out


HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>enemBERT — revisão G1</title>
<style>
:root{--bg:#faf9f7;--card:#fff;--ink:#1c1a17;--muted:#6b655d;--line:#e6e1d8;--accent:#7a5cff}
@media(prefers-color-scheme:dark){:root{--bg:#161513;--card:#211f1c;--ink:#ece8e1;--muted:#9c958a;--line:#332f2a;--accent:#a892ff}}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:12px 20px;display:flex;flex-wrap:wrap;gap:12px 18px;align-items:center}
header h1{font-size:17px;margin:0;font-weight:650}
.sp{flex:1}
.prog{font-size:14px;color:var(--muted)}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:7px 13px}
button.primary{background:var(--accent);color:#fff;border-color:transparent;font-weight:600}
button:disabled{opacity:.4;cursor:default}
main{max-width:820px;margin:0 auto;padding:20px}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.chip{font-size:12.5px;padding:3px 10px;border-radius:20px;font-weight:600;color:#111}
details.help{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin-bottom:18px}
details.help summary{cursor:pointer;font-weight:600}
details.help li{margin:6px 0;font-size:14.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.eid{font-size:12px;color:var(--muted);font-family:ui-monospace,monospace;margin-bottom:14px}
.para{white-space:pre-wrap;margin:0 0 14px;padding:2px 0}
.para:last-of-type{margin-bottom:0}
mark{border-radius:4px;padding:1px 2px;color:#111;position:relative;cursor:default}
mark .tag{font-size:9.5px;font-weight:700;letter-spacing:.03em;vertical-align:super;margin:0 3px;opacity:.75}
mark .x{cursor:pointer;font-weight:700;margin-left:2px;padding:0 3px;border-radius:3px;background:rgba(0,0,0,.12)}
mark .x:hover{background:rgba(200,0,0,.55);color:#fff}
.hint{font-size:13px;color:var(--muted);margin:14px 0 0;border-top:1px dashed var(--line);padding-top:12px}
.popup{position:absolute;z-index:20;background:var(--card);border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:8px;display:none;gap:6px;flex-wrap:wrap;max-width:260px}
.popup button{padding:5px 9px;font-size:13px;font-weight:600;color:#111}
.nav{display:flex;gap:10px;align-items:center;margin-top:18px}
.done-badge{color:#2e9e5b;font-weight:600;font-size:14px}
.empty{color:var(--muted);font-style:italic}
</style></head><body>
<header>
  <h1>enemBERT · revisão G1</h1>
  <span class="prog" id="prog"></span>
  <span class="sp"></span>
  <button id="prev">← anterior</button>
  <button id="next">próxima →</button>
  <button class="primary" id="dl">Baixar correções</button>
</header>
<main>
  <div class="legend" id="legend"></div>
  <details class="help"><summary>O que é cada elemento? (clique)</summary><ul id="cheat"></ul>
    <p style="font-size:13.5px;color:var(--muted);margin:10px 0 0">
    Aceite os trechos corretos, clique no <b>×</b> para remover um errado, e para
    <b>adicionar</b> um que faltou: selecione o texto com o mouse e escolha o elemento.
    Julgue só a <b>presença</b> do elemento — não a qualidade nem a nota.</p>
  </details>
  <div id="view"></div>
</main>
<div class="popup" id="popup"></div>
<script>
const DATA = __DATA__;
const COLORS = __COLORS__;
const CHEAT = __CHEAT__;
const ELEMENTS = Object.keys(COLORS);
const KEY = "enembert_g1_review_v1";
const dark = matchMedia("(prefers-color-scheme: dark)").matches;
function bg(l){return COLORS[l][dark?1:0]}

// state: {id: {spans: [[{s,e,l}]...], done: bool}}
let state = JSON.parse(localStorage.getItem(KEY) || "{}");
let idx = 0;
for(const d of DATA){ if(!state[d.id]) state[d.id] = {spans: d.ai.map(p=>p.map(x=>({...x}))), done:false}; }

const view = document.getElementById("view");
const popup = document.getElementById("popup");

function save(){ localStorage.setItem(KEY, JSON.stringify(state)); renderProg(); }
function renderProg(){
  const done = DATA.filter(d=>state[d.id].done).length;
  document.getElementById("prog").textContent = `redação ${idx+1}/${DATA.length} · ${done} revisada(s)`;
}
// build legend + cheat
document.getElementById("legend").innerHTML = ELEMENTS.map(l=>
  `<span class="chip" style="background:${bg(l)}">${l}</span>`).join("");
document.getElementById("cheat").innerHTML = ELEMENTS.map(l=>
  `<li><b>${l}</b> — ${CHEAT[l]}</li>`).join("");

// absolute char offset of (node,off) within the paragraph's ORIGINAL text.
// The .tag (label) and .x (reject button) nodes injected into each <mark> are
// NOT part of the source paragraph, so they must be skipped or offsets of any
// selection after a highlight would be inflated by their length.
function absOff(container, node, off){
  let n=0;
  const w=document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(t){ return t.parentElement.closest(".tag,.x") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; }
  });
  let cur;
  while((cur=w.nextNode())){ if(cur===node) return n+off; n+=cur.length; }
  return n;
}

function renderEssay(){
  const d = DATA[idx]; const st = state[d.id];
  const wrap = document.createElement("div"); wrap.className="card";
  wrap.innerHTML = `<div class="eid">${d.short} &nbsp;(${idx+1}/${DATA.length})</div>`;
  d.paras.forEach((text, pi)=>{
    const spans = (st.spans[pi]||[]).slice().sort((a,b)=>a.s-b.s);
    const p = document.createElement("div"); p.className="para"; p.dataset.pi=pi;
    let last=0;
    spans.forEach((sp)=>{
      if(sp.s>last) p.appendChild(document.createTextNode(text.slice(last,sp.s)));
      const m=document.createElement("mark"); m.style.background=bg(sp.l);
      m.appendChild(document.createTextNode(text.slice(sp.s,sp.e)));
      const tag=document.createElement("span"); tag.className="tag"; tag.textContent=sp.l;
      const x=document.createElement("span"); x.className="x"; x.textContent="×"; x.title="remover";
      x.onclick=(ev)=>{ev.stopPropagation(); st.spans[pi]=st.spans[pi].filter(z=>!(z.s===sp.s&&z.e===sp.e&&z.l===sp.l)); save(); renderEssay();};
      m.appendChild(tag); m.appendChild(x); p.appendChild(m);
      last=sp.e;
    });
    if(last<text.length) p.appendChild(document.createTextNode(text.slice(last)));
    if(spans.length===0 && text.trim()==="") return;
    wrap.appendChild(p);
  });
  const anyAi = d.ai.flat().length;
  const nav=document.createElement("div"); nav.className="nav";
  nav.innerHTML = st.done ? `<span class="done-badge">✓ revisada</span>` : "";
  const doneBtn=document.createElement("button"); doneBtn.className="primary";
  doneBtn.textContent = st.done ? "marcar como não revisada" : "✓ revisar e avançar";
  doneBtn.onclick=()=>{ st.done=!st.done; save(); if(st.done && idx<DATA.length-1){idx++;} renderEssay(); };
  const resetBtn=document.createElement("button"); resetBtn.textContent="restaurar sugestões da IA";
  resetBtn.onclick=()=>{ st.spans=d.ai.map(p=>p.map(x=>({...x}))); save(); renderEssay(); };
  nav.appendChild(doneBtn); nav.appendChild(resetBtn);
  wrap.appendChild(nav);
  const hint=document.createElement("p"); hint.className="hint";
  hint.textContent = anyAi ? "Selecione um trecho com o mouse para adicionar um elemento que faltou."
    : "A IA não marcou nada aqui. Se houver proposta de intervenção, selecione os trechos; se não houver, apenas marque como revisada.";
  wrap.appendChild(hint);
  view.innerHTML=""; view.appendChild(wrap);
  renderProg();
}

// selection -> add span popup
document.addEventListener("mouseup",(ev)=>{
  if(popup.contains(ev.target)) return;
  const sel=window.getSelection();
  if(!sel.rangeCount || sel.isCollapsed){ popup.style.display="none"; return; }
  const range=sel.getRangeAt(0);
  const p = ev.target.closest ? ev.target.closest(".para") : null;
  const startP = range.startContainer.parentElement?.closest?.(".para");
  const endP = range.endContainer.parentElement?.closest?.(".para");
  if(!startP || startP!==endP){ popup.style.display="none"; return; }
  const pi=+startP.dataset.pi;
  const s=absOff(startP, range.startContainer, range.startOffset);
  const e=absOff(startP, range.endContainer, range.endOffset);
  if(e<=s){ popup.style.display="none"; return; }
  popup.innerHTML="";
  ELEMENTS.forEach(l=>{
    const b=document.createElement("button"); b.textContent=l; b.style.background=bg(l);
    b.onclick=()=>{ const st=state[DATA[idx].id]; (st.spans[pi]=st.spans[pi]||[]).push({s,e,l});
      popup.style.display="none"; window.getSelection().removeAllRanges(); save(); renderEssay(); };
    popup.appendChild(b);
  });
  const r=range.getBoundingClientRect();
  popup.style.display="flex";
  popup.style.left=(window.scrollX+r.left)+"px";
  popup.style.top=(window.scrollY+r.bottom+6)+"px";
});

document.getElementById("prev").onclick=()=>{ if(idx>0){idx--;renderEssay();} };
document.getElementById("next").onclick=()=>{ if(idx<DATA.length-1){idx++;renderEssay();} };
document.getElementById("dl").onclick=()=>{
  const out = DATA.filter(d=>state[d.id].done).map(d=>({
    essay_id:d.id, verified:true,
    spans: state[d.id].spans.map(p=>p.map(x=>({start:x.s,end:x.e,label:x.l})))
  }));
  if(out.length===0){ alert("Nenhuma redação marcada como revisada ainda."); return; }
  const blob=new Blob([out.map(o=>JSON.stringify(o)).join("\\n")],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob);
  a.download="g1_human.jsonl"; a.click();
};
renderEssay();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/labels/g1.jsonl")
    ap.add_argument("--out", default="data/g1_review.html")
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()
    corpus = {r["essay_id"]: r for r in map(json.loads, open("data/corpus.jsonl"))}
    rows = [json.loads(l) for l in open(a.inp)]
    data = build_data(corpus, rows, a.limit)
    html = (HTML
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__COLORS__", json.dumps(COLORS))
            .replace("__CHEAT__", json.dumps(CHEAT, ensure_ascii=False)))
    Path(a.out).write_text(html, encoding="utf-8")
    print(f"wrote {a.out} with {len(data)} essays")


if __name__ == "__main__":
    main()
