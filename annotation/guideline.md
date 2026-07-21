# Guia de anotação — elementos da proposta de intervenção (v1)

Base: definições da Competência 5 na *Cartilha do Participante* (INEP). Anotamos **presença
textual** dos elementos, como spans. Não julgamos qualidade nem nota.

## Os 5 elementos

- **AGENTE** — quem executa a ação. Sintagma nominal explícito: "o Ministério da Educação",
  "as escolas", "a mídia", "a família", "o poder público". Pronomes anafóricos ("ele", "esta")
  NÃO são marcados. Sujeito oculto não é marcado (não há span sem palavras).
- **ACAO** — o que deve ser feito. Começa no verbo de conteúdo: em "deve criar campanhas
  educativas", o span é "criar campanhas educativas" (o modal "deve" fica fora). Inclui o
  objeto direto.
- **MEIO** — como/por qual instrumento. INCLUI o marcador: "por meio de verbas publicitárias",
  "mediante parcerias com ONGs", "com o uso das redes sociais".
- **EFEITO** — finalidade/resultado. INCLUI o marcador: "a fim de conscientizar os jovens",
  "para que a população compreenda o problema".
- **DETALHAMENTO** — especificação extra de OUTRO elemento (aposto, oração relativa,
  exemplificação com "como ..."). É SEMPRE um span próprio, separado na fronteira da oração:
  em "o MEC, órgão responsável pela educação nacional, deve...", o span DETALHAMENTO é
  "órgão responsável pela educação nacional" (sem as vírgulas).

## Regras de fronteira

1. Pontuação nas bordas fica FORA do span; modificadores internos ficam DENTRO.
2. Um span não cruza fronteira de sentença (exceção: DETALHAMENTO em oração relativa).
3. Elementos vagos ainda são marcados ("o governo" = AGENTE; "agir" = ACAO). Vagueza afeta
   nota, não presença — e nota não é nosso problema.
4. Se houver mais de uma proposta no texto, marcar TODAS as instâncias de todos os elementos.
5. Parágrafos sem elementos (introdução, desenvolvimento): nenhum span — são negativos válidos.
6. Em caso de dúvida entre dois rótulos, escolher pelo marcador (preposição/conjunção); sem
   marcador, escolher pela função sintática predominante.
7. **Propostas INDIRETAS contam — este é o erro mais comum.** Nem toda proposta usa o molde
   "deve/cabe a … por meio de … a fim de". Redações mais fracas quase nunca usam. Marque
   também:
   - **ação nominalizada**, sem verbo modal: "campanhas educativas nas escolas",
     "controle do tráfico", "programas de reinserção social";
   - **proposta avaliativa ou condicional**: "seriam eficazes", "é importante que",
     "é necessário investir em…";
   - **MEIO sem marcador**: "conduzidos por psicólogos", "com apoio das universidades",
     "feitas em parceria com ONGs";
   - **EFEITO sem marcador**: "garantindo que os dependentes recebam acompanhamento",
     "assim, o problema diminui";
   - **proposta sem AGENTE explícito**: marque os outros elementos normalmente e deixe
     AGENTE ausente — não invente um agente que não está escrito.
   A ausência do marcador não impede a marcação; ela só torna o elemento mais difícil de
   ver. Só NÃO marque quando não houver proposta alguma — um fecho puramente retórico
   ("os problemas são muitos, assim como suas soluções") não contém elemento nenhum.

## Exemplos trabalhados

Ver `src/enembert/labeling/examples.py` — 3 conclusões anotadas usadas como few-shot do
rotulador e como referência humana. Em revisão manual, o guia vence o rotulador.
