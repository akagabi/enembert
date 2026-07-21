import { ELEMENTS, type Element } from './tagger';

export interface ElementInfo {
  /** Accented pt-BR display name. */
  displayName: string;
  /** One-line definition, paraphrased from the Cartilha do Participante (INEP), Competência 5. */
  definition: string;
  /** A short textbook-style example the student can recognize. */
  example: string;
}

export const ELEMENT_INFO: Record<Element, ElementInfo> = {
  AGENTE: {
    displayName: 'Agente',
    definition:
      'Quem deve executar a ação proposta — uma instituição, órgão ou grupo social nomeado explicitamente no texto.',
    example: 'ex.: "o Ministério da Educação", "as escolas", "a mídia"',
  },
  ACAO: {
    displayName: 'Ação',
    definition: 'A medida concreta proposta para enfrentar o problema discutido na redação.',
    example: 'ex.: "criar campanhas de conscientização nas escolas"',
  },
  MEIO: {
    displayName: 'Meio',
    definition: 'Como a ação será colocada em prática — o instrumento ou modo utilizado.',
    example: 'ex.: "por meio de verbas destinadas à publicidade"',
  },
  EFEITO: {
    displayName: 'Efeito',
    definition: 'Para quê a ação serve — a finalidade ou o resultado esperado dela.',
    example: 'ex.: "a fim de reduzir a evasão escolar entre os jovens"',
  },
  DETALHAMENTO: {
    displayName: 'Detalhamento',
    definition:
      'Uma explicação a mais sobre outro elemento da proposta — detalha, exemplifica ou justifica.',
    example: 'ex.: "órgão responsável pela política educacional do país"',
  },
};

export const RUBRIC_ATTRIBUTION = 'INEP — Cartilha do Participante, Competência 5';

export const ELEMENT_ORDER: readonly Element[] = ELEMENTS;
