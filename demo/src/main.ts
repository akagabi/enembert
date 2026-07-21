import './styles.css';
import {
  ELEMENTS,
  loadModel,
  isModelLoaded,
  splitParagraphs,
  tagParagraph,
  LOW_CONFIDENCE_THRESHOLD,
  type TagSpan,
  type Element,
} from './tagger';
import { ELEMENT_INFO, RUBRIC_ATTRIBUTION } from './rubric';
import { loadScoreModel, estimateC5, type C5Estimate } from './scorer';

const ICON_LOCK = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>`;
const ICON_INFO = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;

/** The 6 C5 bands the score model was trained on, low to high. */
const C5_BANDS = [0, 40, 80, 120, 160, 200] as const;

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function varName(e: Element): string {
  return e.toLowerCase();
}

// ---------- static shell ----------

const app = document.querySelector<HTMLDivElement>('#app')!;

app.innerHTML = `
  <div class="wrap">
    <header>
      <p class="eyebrow"><span class="mark-dot" aria-hidden="true"></span>enemBERT · ferramenta de estudo (não oficial)</p>
      <span class="privacy-badge">${ICON_LOCK}sua redação não sai do seu navegador</span>
      <h1>Confira se sua proposta de intervenção tem os <span class="swipe">5 elementos</span></h1>
      <p class="lede">Cole a conclusão da sua redação e veja, marcado no próprio texto, quais dos 5 elementos da proposta de intervenção — agente, ação, meio, efeito e detalhamento — o modelo encontrou.</p>
      <div class="disclaimer">
        ${ICON_INFO}
        <p><strong>Isto não é uma nota nem uma correção.</strong> É um apoio de estudo — confirme sempre com seu professor.</p>
      </div>
      <ul class="legend">
        ${ELEMENTS.map(
          (e) =>
            `<li><span class="swatch" style="background:var(--el-${varName(e)})" aria-hidden="true"></span>${escapeHtml(ELEMENT_INFO[e].displayName)}</li>`,
        ).join('')}
      </ul>
    </header>

    <form id="analyze-form" novalidate>
      <label class="field-label" for="essay">Cole o texto da sua proposta de intervenção</label>
      <textarea
        id="essay"
        rows="10"
        placeholder="Cole aqui a conclusão (ou a redação inteira) — por exemplo: &quot;Portanto, cabe ao Ministério da Educação, órgão responsável pela política educacional do país, criar campanhas de conscientização nas escolas, por meio de parcerias com ONGs, a fim de reduzir a evasão escolar entre os jovens.&quot;"
      ></textarea>
      <div class="form-row">
        <button id="go" type="submit" disabled>Encontrar elementos</button>
        <div id="status" class="status-line">
          <span class="dot" aria-hidden="true"></span>
          <span id="status-text">carregando o modelo…</span>
        </div>
        <button id="retry-btn" type="button" class="btn-retry" hidden>Tentar novamente</button>
      </div>
      <div id="progress-wrap" class="progress-track">
        <div id="progress-fill" class="progress-fill" style="width:0%"></div>
      </div>
      <p id="field-warning" class="field-warning" hidden>Cole o texto da sua redação antes de continuar.</p>
    </form>

    <section class="results">
      <h2>Sua redação, marcada</h2>
      <div id="output"></div>
      <p id="hedge-note" class="hedge-note" hidden>
        Trechos com <span class="sample">sublinhado tracejado</span> são casos em que o modelo teve baixa confiança —
        vale conferir esses com mais atenção.
      </p>
    </section>

    <section id="verdict" class="verdict" hidden>
      <h2>Checklist dos 5 elementos</h2>
      <ul class="checklist" id="checklist"></ul>
      <p class="limits-note">
        <strong>Sobre a confiabilidade:</strong> a detecção é a estimativa de um modelo de linguagem treinado para
        isso — não uma verificação garantida. Ela erra às vezes, principalmente em detalhamento e meio, que são os
        elementos mais difíceis de reconhecer no texto. Use como um segundo par de olhos, não como palavra final.
      </p>
    </section>

    <section id="score-panel" class="score-panel" hidden aria-labelledby="score-heading">
      <span class="score-washi" aria-hidden="true"></span>
      <h2 id="score-heading">Estimativa <em>(aproximada)</em></h2>
      <div id="score-body"></div>
    </section>

    <footer>
      <p>enemBERT é um projeto independente, não afiliado ao INEP/MEC.</p>
      <p>Definições dos elementos adaptadas de ${RUBRIC_ATTRIBUTION}. Código aberto; o modelo roda localmente via transformers.js — nenhum texto é enviado a servidores.</p>
    </footer>
  </div>
`;

// ---------- element refs ----------

const statusLine = document.querySelector<HTMLDivElement>('#status')!;
const statusText = document.querySelector<HTMLSpanElement>('#status-text')!;
const progressWrap = document.querySelector<HTMLDivElement>('#progress-wrap')!;
const progressFill = document.querySelector<HTMLDivElement>('#progress-fill')!;
const goBtn = document.querySelector<HTMLButtonElement>('#go')!;
const retryBtn = document.querySelector<HTMLButtonElement>('#retry-btn')!;
const form = document.querySelector<HTMLFormElement>('#analyze-form')!;
const textarea = document.querySelector<HTMLTextAreaElement>('#essay')!;
const output = document.querySelector<HTMLDivElement>('#output')!;
const hedgeNote = document.querySelector<HTMLParagraphElement>('#hedge-note')!;
const warning = document.querySelector<HTMLParagraphElement>('#field-warning')!;
const verdictSection = document.querySelector<HTMLElement>('#verdict')!;
const checklistEl = document.querySelector<HTMLUListElement>('#checklist')!;
const scorePanel = document.querySelector<HTMLElement>('#score-panel')!;
const scoreBody = document.querySelector<HTMLDivElement>('#score-body')!;

// ---------- rendering helpers ----------

function emptyStateHtml(): string {
  return `<div class="empty-state">Cole o texto acima e clique em "Encontrar elementos" para ver sua redação marcada aqui, elemento por elemento.</div>`;
}

function errorStateHtml(message: string): string {
  return `<div class="empty-state status-line error"><span class="dot" aria-hidden="true"></span>${escapeHtml(message)}</div>`;
}

function renderParagraphHtml(paragraph: string, spans: TagSpan[]): { html: string; hedged: boolean } {
  let html = '';
  let last = 0;
  let hedged = false;
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  for (const s of sorted) {
    if (s.start < last) continue; // guard against overlapping spans
    html += escapeHtml(paragraph.slice(last, s.start));
    const hedge = s.score < LOW_CONFIDENCE_THRESHOLD;
    if (hedge) hedged = true;
    const pct = Math.round(s.score * 100);
    const info = ELEMENT_INFO[s.label];
    html += `<mark class="el-${s.label}${hedge ? ' hedge' : ''}" title="${escapeHtml(info.displayName)} · confiança ${pct}%">${escapeHtml(paragraph.slice(s.start, s.end))}</mark>`;
    last = s.end;
  }
  html += escapeHtml(paragraph.slice(last));
  return { html: `<p>${html}</p>`, hedged };
}

interface FoundQuote {
  text: string;
  score: number;
}

function computeElementResults(
  paragraphs: string[],
  spansPerPara: TagSpan[][],
): Record<Element, FoundQuote[]> {
  const result = Object.fromEntries(ELEMENTS.map((e) => [e, [] as FoundQuote[]])) as Record<
    Element,
    FoundQuote[]
  >;
  paragraphs.forEach((p, i) => {
    for (const s of spansPerPara[i]) {
      result[s.label].push({ text: p.slice(s.start, s.end), score: s.score });
    }
  });
  return result;
}

function uniqueTexts(items: FoundQuote[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    const t = item.text.trim();
    if (!seen.has(t)) {
      seen.add(t);
      out.push(t);
    }
  }
  return out.slice(0, 4);
}

function renderChecklist(results: Record<Element, FoundQuote[]>): string {
  return ELEMENTS.map((e) => {
    const items = results[e];
    const found = items.length > 0;
    const maxScore = found ? Math.max(...items.map((i) => i.score)) : 0;
    const weak = found && maxScore < LOW_CONFIDENCE_THRESHOLD;
    const info = ELEMENT_INFO[e];
    const stateClass = found ? (weak ? 'found weak' : 'found') : '';
    const chip = found ? '✓' : '–';
    const tag = !found ? 'não encontrado' : weak ? 'encontrado · sinal fraco' : 'encontrado';
    const quotesHtml = items.length
      ? `<ul class="found-quotes">${uniqueTexts(items)
          .map((t) => `<li>"${escapeHtml(t)}"</li>`)
          .join('')}</ul>`
      : '';
    return `
      <li>
        <details class="${stateClass}">
          <summary>
            <span class="chip" aria-hidden="true">${chip}</span>
            <span class="swatch-inline" style="background:var(--el-${varName(e)})" aria-hidden="true"></span>
            <span class="name">${escapeHtml(info.displayName)}</span>
            <span class="tag">${tag}</span>
            <span class="caret" aria-hidden="true">›</span>
          </summary>
          <div class="details-body">
            <p class="definition">${escapeHtml(info.definition)}</p>
            <p class="example">${escapeHtml(info.example)}</p>
            ${quotesHtml}
            <p class="attribution">Definição adaptada de ${RUBRIC_ATTRIBUTION}.</p>
          </div>
        </details>
      </li>`;
  }).join('');
}

function c5RangePhrase(est: C5Estimate): string {
  if (est.rangeLo === est.rangeHi) {
    return `em torno de ${est.c5} de 200`;
  }
  return `em torno de ${est.c5} de 200 (provavelmente entre ${est.rangeLo} e ${est.rangeHi})`;
}

function renderScorePanelHtml(est: C5Estimate): string {
  const lastIdx = C5_BANDS.length - 1;
  const loIdx = C5_BANDS.indexOf(est.rangeLo as (typeof C5_BANDS)[number]);
  const hiIdx = C5_BANDS.indexOf(est.rangeHi as (typeof C5_BANDS)[number]);
  const pointIdx = C5_BANDS.indexOf(est.c5 as (typeof C5_BANDS)[number]);
  const leftPct = (loIdx / lastIdx) * 100;
  const widthPct = ((hiIdx - loIdx) / lastIdx) * 100;
  const pointPct = (pointIdx / lastIdx) * 100;

  return `
    <div
      class="score-meter"
      role="img"
      aria-label="Competência 5 estimada ${c5RangePhrase(est)}"
    >
      <div class="score-meter-track">
        <div class="score-meter-range" style="left:${leftPct}%;width:${widthPct}%"></div>
        <div class="score-meter-point" style="left:${pointPct}%">
          <span class="score-meter-point-label">${est.c5}</span>
        </div>
      </div>
      <div class="score-meter-ticks">
        ${C5_BANDS.map((c) => `<span>${c}</span>`).join('')}
      </div>
    </div>
    <p class="score-line">Competência 5: <strong>${c5RangePhrase(est)}</strong>.</p>
    <p class="score-total">
      Redações com uma proposta assim costumam ter nota total entre
      <strong>${est.totalLo}</strong> e <strong>${est.totalHi}</strong> (de 1000).
    </p>
    <div class="score-disclaimer">
      ${ICON_INFO}
      <p>
        <strong>Estimativa aproximada — não é a nota oficial.</strong>
        O resultado final depende de fatores que este modelo não avalia (gramática, argumentação, coesão).
      </p>
    </div>
  `;
}

// ---------- model lifecycle ----------

async function initModel(): Promise<void> {
  statusLine.classList.remove('ready', 'error');
  statusText.textContent = 'carregando o modelo…';
  progressWrap.hidden = false;
  progressFill.style.width = '0%';
  retryBtn.hidden = true;
  goBtn.disabled = true;

  try {
    await loadModel((p) => {
      const pct = Math.round(p);
      progressFill.style.width = `${pct}%`;
      statusText.textContent = `carregando o modelo… ${pct}%`;
    });
    statusLine.classList.add('ready');
    statusText.textContent = 'modelo pronto — pode colar sua redação';
    progressWrap.hidden = true;
    goBtn.disabled = false;
  } catch (err) {
    console.error('falha ao carregar o modelo enemBERT:', err);
    statusLine.classList.add('error');
    statusText.textContent = 'não foi possível carregar o modelo';
    progressWrap.hidden = true;
    retryBtn.hidden = false;
    output.innerHTML = errorStateHtml(
      'O modelo não carregou. Verifique sua conexão e tente novamente — sua redação continua segura, nada foi enviado.',
    );
  }
}

retryBtn.addEventListener('click', () => {
  void initModel();
});

// ---------- analysis ----------

output.innerHTML = emptyStateHtml();

form.addEventListener('submit', (ev) => {
  ev.preventDefault();
  void runAnalysis();
});

async function runAnalysis(): Promise<void> {
  if (!isModelLoaded()) return;

  const raw = textarea.value;
  const paragraphs = splitParagraphs(raw);
  if (paragraphs.length === 0) {
    warning.hidden = false;
    return;
  }
  warning.hidden = true;

  goBtn.disabled = true;
  const originalLabel = goBtn.textContent ?? 'Encontrar elementos';
  goBtn.textContent = 'Analisando…';

  try {
    const spansPerPara: TagSpan[][] = [];
    for (const p of paragraphs) {
      spansPerPara.push(await tagParagraph(p));
    }
    const rendered = paragraphs.map((p, i) => renderParagraphHtml(p, spansPerPara[i]));
    output.innerHTML = `<div class="essay-output">${rendered.map((r) => r.html).join('')}</div>`;
    hedgeNote.hidden = !rendered.some((r) => r.hedged);

    const results = computeElementResults(paragraphs, spansPerPara);
    checklistEl.innerHTML = renderChecklist(results);
    verdictSection.hidden = false;

    // The score estimate is a bonus, not core to the tagging feature: a
    // failure here (e.g. score_model.json didn't load) must not blow away
    // the essay highlighting or checklist the user already sees.
    try {
      await loadScoreModel();
      const estimate = estimateC5(spansPerPara, raw, paragraphs.length);
      scoreBody.innerHTML = renderScorePanelHtml(estimate);
      scorePanel.hidden = false;
    } catch (scoreErr) {
      console.error('falha ao estimar a Competência 5:', scoreErr);
      scorePanel.hidden = true;
    }
  } catch (err) {
    console.error('falha ao analisar o texto:', err);
    output.innerHTML = errorStateHtml(
      'Não foi possível analisar o texto agora. Tente novamente em instantes.',
    );
    hedgeNote.hidden = true;
    verdictSection.hidden = true;
    scorePanel.hidden = true;
  } finally {
    goBtn.disabled = false;
    goBtn.textContent = originalLabel;
  }
}

// Warm the (tiny) score model cache in the background; independent of the
// tagger model's own loading lifecycle above.
void loadScoreModel().catch((err) => {
  console.error('falha ao pré-carregar o modelo de estimativa:', err);
});

void initModel();
