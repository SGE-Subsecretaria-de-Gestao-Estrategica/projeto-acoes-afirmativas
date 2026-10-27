---
version: 1
slug: "relatorios-relatorio-cotas-lpg-html"
primary_target: "relatorios/relatorio_cotas_lpg.html"
related_targets: ["src/relatorio_cotas.py"]
---

# Relatório de cotas LPG

Scope: página HTML única gerada por `src/relatorio_cotas.py` em `relatorios/relatorio_cotas_lpg.html`. Mode: Read, com um controle de Operate (escopo). Herda o mundo de DESIGN.md.
Audience/job: equipe técnica do MinC responde seis perguntas diretas: quantos entes cumprem a IN 5 (por edital e pelo agregado do README), quanto de recurso e de vagas vai para as cotas, quanto e quais são as outras cotas, sempre com recorte Todos / Estados e DF / Capitais.
Content: somente data/final/lpg_editais.xlsx (e f1_lpg.xlsx para a qualidade); exclui os 8 editais fora do escopo definidos pelo usuário; todo número calculado pelo script.
Constraints: valores de cota são estimativas (vagas × valor médio da vaga); tom técnico, não punitivo; entes em ordem alfabética, nunca ranking de piores.

## Direction contract

THESIS: Quadro de respostas: cada pergunta do usuário vira uma resposta numerada com o número-resposta grande, a ementa em serifa e a prova ao lado. Recusa o painel de KPIs em cartões.

OWN-WORLD: Faixa verde institucional, papel branco, fios de 1px e fio de 2px de tinta nos cabeçalhos, Public Sans, Source Serif 4 nas ementas, cores de estado do painel, seletor segmentado tinta/papel.

STORY: O leitor escolhe o recorte, lê as seis respostas em ordem, confere na tabela por ente e termina em método e limites.

FIRST VIEWPORT: Faixa verde com título e o seletor segmentado Todos / Estados e DF / Capitais; abaixo, régua de seis respostas curtas (número + pergunta) que leva a cada seção; resposta 1 começa na dobra.

FORM: Nota de respostas com recorte; pedido precisamente especificado em mundo estabelecido, sem rolagem de conceito. Signature move: o seletor de recorte troca todos os números da página de uma vez, com a URL guardando o recorte.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
