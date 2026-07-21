EXAMPLES = [
    {"paragraph": ("Portanto, o Ministério da Educação, órgão responsável pela política "
                   "educacional do país, deve criar campanhas de conscientização nas escolas, "
                   "por meio de verbas destinadas à publicidade, a fim de reduzir a evasão "
                   "escolar entre os jovens."),
     "elements": [
        {"label": "AGENTE", "quote": "o Ministério da Educação"},
        {"label": "DETALHAMENTO", "quote": "órgão responsável pela política educacional do país"},
        {"label": "ACAO", "quote": "criar campanhas de conscientização nas escolas"},
        {"label": "MEIO", "quote": "por meio de verbas destinadas à publicidade"},
        {"label": "EFEITO", "quote": "a fim de reduzir a evasão escolar entre os jovens"}]},
    {"paragraph": ("Diante disso, cabe às redes sociais promover a checagem de notícias, "
                   "mediante parcerias com agências de verificação, para que a desinformação "
                   "perca alcance."),
     "elements": [
        {"label": "AGENTE", "quote": "às redes sociais"},
        {"label": "ACAO", "quote": "promover a checagem de notícias"},
        {"label": "MEIO", "quote": "mediante parcerias com agências de verificação"},
        {"label": "EFEITO", "quote": "para que a desinformação perca alcance"}]},
    {"paragraph": ("Conclui-se que o problema é grave e que a sociedade precisa refletir "
                   "sobre seus hábitos."),
     "elements": [
        {"label": "AGENTE", "quote": "a sociedade"},
        {"label": "ACAO", "quote": "refletir sobre seus hábitos"}]},
    # Proposta INDIRETA: sem "deve/cabe a", MEIO e EFEITO sem os marcadores clássicos.
    # Redações medianas escrevem assim — o rotulador precisa enxergar estes casos.
    {"paragraph": ("É urgente que o poder público invista em programas de reinserção social "
                   "conduzidos por psicólogos e assistentes sociais, garantindo que os "
                   "dependentes recebam acompanhamento contínuo."),
     "elements": [
        {"label": "AGENTE", "quote": "o poder público"},
        {"label": "ACAO", "quote": "invista em programas de reinserção social"},
        {"label": "MEIO", "quote": "conduzidos por psicólogos e assistentes sociais"},
        {"label": "EFEITO", "quote": "garantindo que os dependentes recebam acompanhamento contínuo"}]},
    # Proposta NOMINALIZADA e SEM agente explícito: marcar o que existe, não inventar AGENTE.
    {"paragraph": ("Campanhas educativas nas escolas, realizadas em parceria com universidades "
                   "públicas, seriam eficazes para diminuir o preconceito contra essas famílias."),
     "elements": [
        {"label": "ACAO", "quote": "Campanhas educativas nas escolas"},
        {"label": "MEIO", "quote": "realizadas em parceria com universidades públicas"},
        {"label": "EFEITO", "quote": "para diminuir o preconceito contra essas famílias"}]},
]
