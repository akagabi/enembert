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
import { loadScoreModel, coarseBand, type CoarseBand } from './scorer';

const ICON_LOCK = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>`;
const ICON_INFO = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
const ICON_EDIT = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`;

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
      <h1>Sua proposta de intervenção tem os <span class="swipe">5 elementos</span>?</h1>
      <p class="lede">Cole o texto e veja, marcado, quais dos cinco elementos aparecem — agente, ação, meio, efeito e detalhamento — e quais estão faltando.</p>
      <div class="notice-row">
        <span class="notice-chip">${ICON_LOCK}sua redação não sai do seu navegador</span>
        <span class="notice-chip">${ICON_INFO}não é uma nota nem uma correção</span>
        <button id="theme-toggle" type="button" class="theme-toggle" aria-label="Alternar tema claro/escuro">
          <span aria-hidden="true">◐</span><span id="theme-label">escuro</span>
        </button>
      </div>
    </header>

    <section class="workspace-card">
      <form id="analyze-form" novalidate>
        <label class="field-label" for="essay">Cole o texto da sua proposta de intervenção</label>
        <textarea
          id="essay"
          rows="8"
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
        <p id="analyze-error" class="field-warning" hidden></p>
      </form>

      <div id="result-view" class="result-view" hidden>
        <div class="result-toolbar">
          <h2>Sua redação, marcada</h2>
          <button id="edit-btn" type="button" class="btn-edit">${ICON_EDIT}editar / colar outra</button>
        </div>

        <section id="score-panel" class="score-panel" hidden aria-labelledby="score-heading">
          <h2 id="score-heading">Competência 5 — faixa aproximada</h2>
          <div id="score-body"></div>
        </section>

        <div id="output"></div>
        <p id="hedge-note" class="hedge-note" hidden>
          Trechos com <span class="sample">sublinhado tracejado</span> são casos em que o modelo teve baixa confiança —
          vale conferir esses com mais atenção.
        </p>

        <section id="verdict" class="verdict" hidden>
          <h2>Checklist dos 5 elementos</h2>
          <ul class="checklist" id="checklist"></ul>
          <p class="limits-note">
            <strong>Sobre a confiabilidade:</strong> é a estimativa de um modelo, não uma verificação garantida — erra
            mais em detalhamento e meio. Use como um segundo par de olhos, não como palavra final.
          </p>
        </section>
      </div>
    </section>

    <footer>
      <p>enemBERT é um projeto independente, não afiliado ao INEP/MEC · definições adaptadas de ${RUBRIC_ATTRIBUTION} · roda localmente via transformers.js — nenhum texto é enviado a servidores.</p>
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
const analyzeError = document.querySelector<HTMLParagraphElement>('#analyze-error')!;
const resultView = document.querySelector<HTMLDivElement>('#result-view')!;
const editBtn = document.querySelector<HTMLButtonElement>('#edit-btn')!;
const verdictSection = document.querySelector<HTMLElement>('#verdict')!;
const checklistEl = document.querySelector<HTMLUListElement>('#checklist')!;
const scorePanel = document.querySelector<HTMLElement>('#score-panel')!;
const scoreBody = document.querySelector<HTMLDivElement>('#score-body')!;

// ---------- rendering helpers ----------

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

// A compact inline row of 5 chips (not 5 stacked cards): each chip is a
// pill showing found/not-found + the element's color + name, and expands
// in place (native <details>) to reveal the definition/example/quotes.
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
          </summary>
          <div class="details-body">
            <p class="state-tag">${tag}</p>
            <p class="definition">${escapeHtml(info.definition)}</p>
            <p class="example">${escapeHtml(info.example)}</p>
            ${quotesHtml}
          </div>
        </details>
      </li>`;
  }).join('');
}


// The band as a WIDE range on a 0-200 track, never a single number. The earlier
// point-estimate version of this panel was measured against real grades and
// failed (rho 0.347, CI including zero), so what ships is the coarse 3+-elements
// split that survived — with its overlap and sample size stated on the face of
// the panel rather than buried in a tooltip.
function renderScorePanelHtml(b: CoarseBand): string {
  const pct = (v: number) => (v / 200) * 100;
  const groupLabel = b.isHigh
    ? `${b.cut} ou mais dos cinco elementos`
    : `menos de ${b.cut} dos cinco elementos`;
  const otherLabel = b.isHigh
    ? `quem tinha menos de ${b.cut}`
    : `quem tinha ${b.cut} ou mais`;

  return `
    <p class="score-lead">
      O modelo encontrou <strong>${b.nElements} de 5</strong> elementos. Num teste com 30 redações
      já corrigidas por humanos, as que tinham ${groupLabel} tiraram, na metade central dos casos,
      entre <strong>${b.lo}</strong> e <strong>${b.hi}</strong> pontos na Competência 5
      (mediana ${b.median}, de um máximo de 200).
    </p>
    <div class="score-meter" role="img"
         aria-label="Faixa aproximada de Competência 5: entre ${b.lo} e ${b.hi} de 200, mediana ${b.median}">
      <div class="score-meter-track">
        <div class="score-meter-other" style="left:${pct(b.otherLo)}%;width:${pct(b.otherHi - b.otherLo)}%"></div>
        <div class="score-meter-range" style="left:${pct(b.lo)}%;width:${pct(b.hi - b.lo)}%"></div>
        <div class="score-meter-point" style="left:${pct(b.median)}%"></div>
      </div>
      <div class="score-meter-ticks">
        <span>0</span><span>50</span><span>100</span><span>150</span><span>200</span>
      </div>
      <p class="score-meter-key">
        <span class="key-mine"></span> seu grupo
        <span class="key-other"></span> o outro grupo (${otherLabel}: ${b.otherLo}–${b.otherHi})
      </p>
    </div>
    <div class="score-disclaimer">
      ${ICON_INFO}
      <div>
        <p><strong>Isto não é uma nota, e o sinal é fraco.</strong></p>
        <p>
          A faixa olha só <em>quantos</em> dos cinco elementos aparecem — não o quanto foram bem
          desenvolvidos, nem gramática, argumentação ou coesão. As faixas dos dois grupos se
          sobrepõem bastante, a amostra tem apenas 30 redações e a diferença entre os grupos não é
          estatisticamente robusta. Uma versão anterior desta caixa tentava estimar a nota exata e
          errava em média 62 pontos, subestimando justamente as redações boas — por isso ela foi
          substituída por esta faixa larga.
        </p>
      </div>
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
    statusText.textContent = 'não foi possível carregar o modelo — verifique sua conexão';
    progressWrap.hidden = true;
    retryBtn.hidden = false;
  }
}

retryBtn.addEventListener('click', () => {
  void loadScoreModel().catch((err) => {
  console.error('falha ao pré-carregar as faixas de Competência 5:', err);
});

void initModel();
});

// ---------- view switching ----------
// Simplest, most robust way to avoid showing the essay twice: the marked-up
// essay replaces the textarea view in place (same card) rather than living
// in a separate section further down the page. "editar" just swaps back —
// the textarea still holds the original text, nothing is lost.

editBtn.addEventListener('click', () => {
  resultView.hidden = true;
  form.hidden = false;
  textarea.focus();
});

// ---------- analysis ----------

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
  analyzeError.hidden = true;

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

    // The band is a bonus on top of the tagging: if score_model.json failed to
    // load, the user still gets the highlighting and checklist they came for.
    try {
      await loadScoreModel();
      const nElements = ELEMENTS.filter((e) => results[e].length > 0).length;
      scoreBody.innerHTML = renderScorePanelHtml(coarseBand(nElements));
      scorePanel.hidden = false;
    } catch (scoreErr) {
      console.error('falha ao calcular a faixa de Competência 5:', scoreErr);
      scorePanel.hidden = true;
    }

    form.hidden = true;
    resultView.hidden = false;
  } catch (err) {
    console.error('falha ao analisar o texto:', err);
    analyzeError.textContent = 'Não foi possível analisar o texto agora. Tente novamente em instantes.';
    analyzeError.hidden = false;
    hedgeNote.hidden = true;
    verdictSection.hidden = true;
    scorePanel.hidden = true;
    resultView.hidden = true;
  } finally {
    goBtn.disabled = false;
    goBtn.textContent = originalLabel;
  }
}

void initModel();

// ---------- theme toggle (page defaults to light; dark is opt-in) ----------

const themeToggle = document.querySelector<HTMLButtonElement>('#theme-toggle')!;
const themeLabel = document.querySelector<HTMLSpanElement>('#theme-label')!;

function applyTheme(theme: 'light' | 'dark'): void {
  document.documentElement.setAttribute('data-theme', theme);
  themeLabel.textContent = theme === 'dark' ? 'claro' : 'escuro';
  try {
    localStorage.setItem('enembert-theme', theme);
  } catch {
    /* storage unavailable (private mode) — the toggle still works for this visit */
  }
}

let storedTheme: string | null = null;
try {
  storedTheme = localStorage.getItem('enembert-theme');
} catch {
  /* ignore */
}
applyTheme(storedTheme === 'dark' ? 'dark' : 'light');

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  applyTheme(current === 'dark' ? 'light' : 'dark');
});
