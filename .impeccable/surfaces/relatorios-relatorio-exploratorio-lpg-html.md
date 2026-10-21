---
version: 1
slug: "relatorios-relatorio-exploratorio-lpg-html"
primary_target: "relatorios/relatorio_exploratorio_lpg.html"
related_targets: ["src/relatorio_exploratorio.py"]
---

# Relatório exploratório LPG

Scope: página HTML única gerada por `src/relatorio_exploratorio.py` em `relatorios/relatorio_exploratorio_lpg.html`. Mode: Read. Herda o mundo de DESIGN.md (papel branco, verde institucional, Public Sans, Source Serif 4 na voz citada).
Audience/job: equipe técnica do MinC lê os principais achados da base e o que ela não permite afirmar.
Content: somente data/final/lpg_editais.xlsx; todo número calculado pelo script.
Constraints: tom técnico, não punitivo; toda afirmação acompanhada do limite.

## Direction contract

THESIS: Nota técnica de achados: dez achados numerados por importância, cada um com evidência e limite. Recusa o "relatório de EDA" genérico de histogramas por coluna.

OWN-WORLD: Faixa verde institucional no cabeçalho, papel branco, fios de 1px e fio de 2px nos cabeçalhos de seção, Public Sans na interface e no corpo, Source Serif 4 na ementa de cada achado, estados nas cores do painel.

STORY: O leitor lê o sumário executivo, vê os números-chave, percorre os achados pelo sumário lateral e termina na caixa de limites da base.

FIRST VIEWPORT: Faixa verde com título e linha de base; sumário executivo de cinco itens à esquerda e quadro de números-chave à direita; sumário de achados fixo à esquerda no desktop; achado 1 começa logo abaixo.

FORM: Relatório de auditoria com achados numerados; estrutura 1 da lista; seed 563e4252. Signature move: numeração do achado na margem com a ementa em serifa e a caixa "Limite" ao pé de cada achado.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
