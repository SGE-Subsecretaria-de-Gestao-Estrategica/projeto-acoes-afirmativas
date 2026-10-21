---
version: 1
slug: "src-dashboard-app-py"
primary_target: "src/dashboard/app.py"
related_targets: ["src/dashboard"]
---

# Painel de conformidade LPG

Scope: Dash app em `src/dashboard/` (rotas: visão geral, ente, edital, revisão, outras cotas). Mode: Operate.

Audience/job: equipe técnica do MinC responde, segregado por tipo de ente (Estados/DF vs. Capitais), se cada ente cumpriu a IN 5, e desce até o edital e sua evidência.
Content: somente `data/final/lpg_editais.xlsx` (abas editais, categorias, outras_cotas, evidencias). Nada de IBGE, mapas externos ou motivos inventados; motivos e remissões saem de `motivo_in5`/`motivo_negras`/`motivo_indigenas`.
Constraints: não punitivo (sem ranking de piores, sem vermelho gritante); incerteza visível (indeterminado, sem leitura, entes ausentes da base); evitar cara de dashboard genérico.
Unresolved: hospedagem e acesso; direção escolhida pelo sorteio sem confirmação explícita do usuário.

## Direction contract

THESIS: Cada ente é um ato publicado: o veredito da IN 5 em linguagem de ementa, com o parágrafo que o fundamenta. Recusa a linha de KPIs + mapa coroplético + tabela do painel gov padrão.

OWN-WORLD: Gazeta oficial em tela: papel branco, tinta quase preta, verde institucional no trilho de navegação, âmbar para indeterminado, tijolo discreto para não conforme, azul-aço para específico. Grotesco de trabalho (Public Sans) na interface, serifa de texto (Source Serif 4) só nas ementas e trechos citados. Fios de 1px, cabeçalho de seção com fio de 2px, sem cartões, sem sombras.

STORY: O analista abre e vê, lado a lado, Estados/DF e Capitais; percebe quantos entes não têm nenhum edital não conforme, quais têm e por qual parágrafo; abre um ente, depois um edital, e lê o trecho e a página que sustentam cada número.

FIRST VIEWPORT: Trilho verde à esquerda (Visão geral, Estados e DF, Capitais, Editais; Revisão: Não conformes, Indeterminados, Específicos; Outras cotas). Topo: título, linha de totais e legenda. Barra de filtros (grupo Todos/Negros/Indígenas, modalidade, ordem, busca). Duas colunas iguais, Estados/DF e Capitais, cada uma com resumo do tipo (entes sem não conforme, editais por status, % vagas reservadas) e uma linha por ente: nome, nº de editais, barra empilhada por status, ementa com remissão §, situação. Entes ausentes da base aparecem como linha "sem editais na base".

FORM: Diário Oficial da União, seções de atos; candidato 4 da lista ordenada; seed afbba2e6. Signature move: a remissão § (art. 5º, §3º, §4º) como etiqueta na ementa que, em foco/hover, mostra o texto resumido do parágrafo. Raises: colunas fixas, o status reestiliza a linha (quadro de partidas); refluxo por células inteiras (Crouwel); valor do edital numa rampa fixa de tamanho (atlas); ficha de edital com anterior/próximo da fila e teclas j/k (feed); todo número a um clique do trecho e página (monocromático).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
