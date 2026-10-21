---
name: Cotas LPG
description: Painel de conformidade das cotas da IN MinC nº 5/2023 nos editais da Lei Paulo Gustavo, para a equipe técnica do MinC.
colors:
  papel: "#ffffff"
  lavado: "#f3f5f4"
  lavado-2: "#e9eeeb"
  tinta: "#16191d"
  tinta-2: "#444a52"
  tinta-3: "#5d636b"
  fio: "#dcdfe3"
  fio-2: "#edeff1"
  fio-forte: "#c9ced3"
  verde: "#1f5f45"
  verde-2: "#174a36"
  verde-3: "#e4efe9"
  verde-txt: "#dfece5"
  ok: "#1f5f45"
  nc: "#9e3a2b"
  nc-lav: "#f6ebe8"
  esp: "#3e6e8e"
  esp-lav: "#e8f0f5"
  ind: "#8c5a0e"
  ind-cor: "#c48a2a"
  ind-lav: "#f8f0e1"
  sl: "#8a9097"
typography:
  titulo-pagina:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  cabecalho-secao:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    letterSpacing: "0.09em"
  numero-total:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    letterSpacing: "-0.01em"
    fontFeature: "tnum, lnum"
  body:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "tnum, lnum"
  label:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "11.5px"
    fontWeight: 600
    letterSpacing: "0.07em"
  ementa:
    fontFamily: "Source Serif 4, Georgia, Times New Roman, serif"
    fontSize: "13px"
    fontWeight: 400
  objeto:
    fontFamily: "Source Serif 4, Georgia, Times New Roman, serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  trecho:
    fontFamily: "Source Serif 4, Georgia, Times New Roman, serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  raio: "3px"
  etiqueta: "2px"
spacing:
  medianiz: "28px"
  medianiz-movel: "16px"
  trilho: "22px"
  coluna: "14px"
components:
  segmento:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta-2}"
    rounded: "{rounded.raio}"
    padding: "5px 11px"
  segmento-hover:
    backgroundColor: "{colors.lavado}"
    textColor: "{colors.tinta}"
  segmento-marcado:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
  busca:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.raio}"
    padding: "6px 10px"
    width: "280px"
  botao:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.raio}"
    padding: "5px 11px"
  botao-hover:
    backgroundColor: "{colors.lavado}"
  botao-desligado:
    backgroundColor: "{colors.lavado}"
    textColor: "{colors.tinta-3}"
  selo-conforme:
    backgroundColor: "{colors.verde-3}"
    textColor: "{colors.ok}"
    rounded: "{rounded.raio}"
    padding: "2px 8px"
  selo-nao-conforme:
    backgroundColor: "{colors.nc-lav}"
    textColor: "{colors.nc}"
    rounded: "{rounded.raio}"
    padding: "2px 8px"
  selo-especifico:
    backgroundColor: "{colors.esp-lav}"
    textColor: "{colors.esp}"
    rounded: "{rounded.raio}"
    padding: "2px 8px"
  selo-indeterminado:
    backgroundColor: "{colors.ind-lav}"
    textColor: "{colors.ind}"
    rounded: "{rounded.raio}"
    padding: "2px 8px"
  selo-sem-leitura:
    backgroundColor: "{colors.lavado}"
    textColor: "{colors.tinta-2}"
    rounded: "{rounded.raio}"
    padding: "2px 8px"
  remissao:
    backgroundColor: "{colors.verde-3}"
    textColor: "{colors.verde}"
    typography: "{typography.label}"
    rounded: "{rounded.etiqueta}"
    padding: "0 5px"
  remissao-texto:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    rounded: "{rounded.raio}"
    padding: "9px 11px"
    width: "280px"
  trilho-item:
    backgroundColor: "{colors.verde}"
    textColor: "{colors.verde-txt}"
    padding: "9px 22px"
  trilho-item-ativo:
    backgroundColor: "{colors.verde-2}"
    textColor: "{colors.papel}"
  aba:
    textColor: "{colors.tinta-2}"
    padding: "8px 14px 9px"
  aba-ativa:
    textColor: "{colors.tinta}"
---

# Design System: Cotas LPG

## Overview

**Creative North Star: "A Gazeta Oficial em Tela"**

O painel se comporta como uma seção de atos do Diário Oficial: papel branco, tinta quase preta, fios finos separando cada ato e um único trilho de navegação em verde institucional. Cada ente e cada edital é tratado como um ato publicado: um veredito curto em linguagem de ementa, a remissão ao parágrafo da IN 5 que o fundamenta e, a um clique, o trecho literal e a página do edital.

A densidade é de ferramenta de trabalho. Linhas em colunas fixas, números tabulares, rótulos pequenos e nenhuma moldura decorativa: não há cartões nem sombras de superfície, e a hierarquia vem de fios (1px para separar, 2px de tinta para abrir uma seção), peso tipográfico e da troca entre o grotesco de interface e a serifa de texto. A cor carrega estado, não decoração; o vermelho é tijolo discreto, nunca alarme, porque abaixo do mínimo não é automaticamente descumprimento.

A incerteza é desenhada, não escondida: "sem leitura" tem hachura própria, entes ausentes da base aparecem como linha tracejada "sem editais na base", e indeterminado tem cor própria (âmbar), distinta de não conforme.

**Key Characteristics:**
- Papel branco plano, tinta quase preta, verde institucional restrito ao trilho, à remissão e a ações de prova.
- Cinco estados com cor fixa: conforme, não conforme, específico, indeterminado, sem leitura.
- Grotesco (Public Sans) na interface; serifa (Source Serif 4) só em ementas, objeto e trechos citados.
- Fios de 1px; cabeçalho de seção com fio de 2px em tinta; sem cartões, sem sombras de superfície.
- Colunas fixas em que o status reestiliza a linha inteira; refluxo por células inteiras.
- Remissão § como etiqueta que revela o texto do parágrafo em hover/foco.

## Colors

Paleta de papel e tinta com um verde institucional e quatro cores de estado dessaturadas, cada uma com seu lavado.

### Primary
- **Verde Institucional** (verde): fundo do trilho de navegação, cor da remissão §, do link de volta, de links de prova e páginas citadas, do anel de foco, do marcador de mínimo nos medidores e do número "entes sem não conforme". Também é a cor de estado conforme (ok, mesmo valor).
- **Verde Fundo de Trilho** (verde-2): item ativo do trilho.
- **Verde Lavado** (verde-3): fundo da remissão §, do selo conforme e do trecho de evidência alvo (`:target`).
- **Verde Texto de Trilho** (verde-txt): texto em repouso sobre o trilho.

### Secondary (estados)
- **Tijolo Discreto** (nc) sobre **Lavado Tijolo** (nc-lav): não conforme. Usado em segmento de barra, marcador de linha, situação e selo; nunca como fundo de área grande.
- **Azul-Aço** (esp) sobre **Lavado Aço** (esp-lav): edital específico (dirigido integralmente a um grupo).
- **Âmbar** (ind-cor para preenchimentos, ind para texto) sobre **Lavado Âmbar** (ind-lav): indeterminado e pendente.
- **Cinza de Leitura** (sl): sem leitura, sempre como hachura diagonal de 2px, nunca como cor sólida.

### Neutral
- **Papel** (papel): fundo de página e de controles.
- **Lavado** (lavado) e **Lavado 2** (lavado-2): barra de filtros, hover de linhas e botões, selo sem leitura.
- **Tinta** (tinta): texto principal, segmento marcado, fio de 2px dos cabeçalhos de seção e fundo do texto da remissão.
- **Tinta 2** (tinta-2): texto secundário, ementas, preenchimento neutro de medidores e barras horizontais.
- **Tinta 3** (tinta-3): metadados, rótulos de coluna, placeholders.
- **Fio** (fio), **Fio 2** (fio-2), **Fio Forte** (fio-forte): divisores entre blocos, divisores entre linhas e trilhos de barra, contorno de controles.

### Named Rules
**A Regra da Cor de Estado.** As cinco cores de estado significam apenas estado. Nenhum elemento decorativo, gráfico neutro ou destaque usa ok, nc, esp ou ind; magnitudes neutras usam tinta-2.

**A Regra do Tijolo Discreto.** Não conforme aparece em marcas pequenas (quadrado de 8px, segmento de barra, texto de situação, selo com lavado). Nunca pinta uma linha, cartão ou cabeçalho inteiro.

## Typography

**Display Font:** Public Sans (com system-ui, Segoe UI)
**Body Font:** Public Sans (com system-ui, Segoe UI)
**Label/Mono Font:** Source Serif 4 (com Georgia) para texto citado e ementas

**Character:** Um grotesco de trabalho, governamental e sem afetação, para toda a interface; a serifa de texto entra só quando o conteúdo é a voz do edital ou a ementa do veredito, marcando a diferença entre o painel que fala e o documento citado.

### Hierarchy
- **Título de página** (700, 22px, 1.2, -0.01em, `text-wrap: balance`): um por rota, no cabeçalho.
- **Cabeçalho de seção** (700, 13px, caixa alta, 0.09em; 12.5px nos blocos da ficha): abre cada seção sobre fio de 2px em tinta.
- **Subtítulo de grupo** (700, 15px): Pessoas negras / Pessoas indígenas na ficha.
- **Número total** (600, 17px, -0.01em): linha de totais dos resumos; valores da ficha a 15px.
- **Body** (400, 14px, 1.45): base da interface; todos os números com algarismos tabulares e alinhados.
- **Label** (600, 11.5px, caixa alta, 0.07em): cabeçalhos de coluna das tabelas e linhas.
- **Ementa** (serifa 400, 13 a 13.5px): veredito resumido do ente e objeto na lista de editais.
- **Objeto** (serifa 400, 16px, 1.55, máx. 70ch) e **Trecho** (serifa 400, 14px, 1.55): texto do edital na ficha e nas evidências.

### Named Rules
**A Regra da Voz Citada.** A serifa é reservada à ementa e ao texto do edital. Rótulos, números, controles e navegação são sempre Public Sans.

**A Regra do Algarismo Tabular.** Todo número usa `tabular-nums lining-nums` e se alinha à direita em colunas.

## Layout

Casca em duas colunas: trilho fixo de 232px à esquerda (sticky, altura da janela) e área principal fluida. A barra de filtros é sticky no topo da área principal, sobre lavado com fio inferior. Medianiz horizontal de 28px em cabeçalhos, seções e colunas da ficha (16px no móvel); o trilho usa 22px.

A visão geral compara Estados/DF e Capitais em duas colunas iguais separadas por fio vertical. Linhas de ente usam colunas fixas (nome, nº de editais em 48px, barra empilhada, situação em 152px) com a ementa numa segunda faixa sob barra e situação; o status da linha reestiliza marcador, texto de situação e barra, sem mudar a grade. A lista de editais usa seis colunas fixas com cabeçalho sticky. A ficha do edital divide conteúdo (1.45fr) e evidências (mín. 320px, fundo quase branco).

Refluxo por células inteiras, nunca por encolhimento: a 1240px as duas colunas e a ficha empilham; a 980px a linha de edital vira nome + selo com metadados abaixo e o cabeçalho de colunas some; a 760px o trilho vira faixa horizontal no topo, filtros deixam de ser sticky, segmentos se separam em botões individuais, tabelas viram fichas rotuladas por `data-rot`, e a rampa de magnitude ganha legenda visível.

Hover de linha estende o lavado para além da medianiz (28px, 12px na coluna única, 16px no móvel) por sombra sem desfoque, para a linha ler como faixa inteira sem alterar a grade.

## Elevation & Depth

O sistema é plano. A profundidade vem de fios, do lavado sob a barra de filtros e da coluna de evidências em #fbfcfb; não há cartões nem sombras de superfície. A única camada flutuante é o texto da remissão §, que usa uma sombra ambiente suave por ser um tooltip sobre o conteúdo.

### Shadow Vocabulary
- **Tooltip da remissão** (`box-shadow: 0 6px 18px rgba(16, 24, 32, .22)`): somente no texto revelado da remissão §.
- **Marcador de ativo do trilho** (`box-shadow: inset 3px 0 0 #fff`; no móvel `inset 0 -3px 0 #fff`): é um fio, não elevação.

### Named Rules
**A Regra do Papel Plano.** Superfícies não flutuam. Separação se faz com fio de 1px (fio ou fio-2) ou fio de 2px em tinta; sombra só existe na camada flutuante da remissão.

## Shapes

Cantos quase retos: 3px (raio) em controles, selos, botões e tooltip; 2px na etiqueta §. Marcadores de status são quadrados de 8px (linha) e 10px (legenda), sem arredondamento. Barras empilhadas e medidores são retângulos chapados de 6 a 10px de altura, sem raio. A única forma circular é a rampa de magnitude do valor do edital: cinco passos fixos (contorno tracejado de 7px para valor ausente, depois 5, 8, 12 e 17px). Chevrons de navegação são desenhados com duas bordas de 1.6px giradas, não glifos.

## Components

### Buttons
Discretos e documentais.
- **Shape:** quase reto (3px), contorno fio-forte, fundo papel, 13px peso 500, padding 5px 11px.
- **Hover / Focus:** fundo lavado e contorno tinta-3 em 150ms; foco com contorno verde de 2px.
- **Desligado:** fundo lavado, texto tinta-3, contorno tracejado, `not-allowed`.
- **Teclas:** Anterior/Próximo da ficha respondem a k/j, mostradas como `kbd` com borda inferior de 2px.

### Chips (seletor segmentado)
- **Style:** grupo de rótulos unidos por fio-forte, fundo papel, 13px peso 500 em tinta-2.
- **State:** marcado inverte para tinta com texto branco; hover em lavado. No móvel, cada segmento vira um botão separado com 4px de intervalo.

### Selos de situação
- **Style:** 12px peso 600 (13px no selo grande da ficha), cor do estado sobre seu lavado, contorno no tom intermediário do estado, raio 3px.
- **Variantes:** conforme, não conforme, específico, indeterminado, sem leitura.

### Inputs / Fields
- **Style:** busca com contorno fio-forte, fundo papel, raio 3px, 13px, 280px (largura total no móvel).
- **Focus:** contorno e borda em verde.

### Navigation
- **Trilho:** fundo verde, marca em branco 16px, seções em rótulo de caixa alta (11.5px, 0.09em), itens 14px peso 500 com contagem alinhada à direita. Hover em branco translúcido; ativo em verde-2 com fio branco interno de 3px à esquerda. Rodapé com fonte e regras.
- **Abas:** texto tinta-2 com fio inferior de 2px; ativa em tinta peso 600 com fio verde.
- **Volta:** link verde de 13px com chevron desenhado, sublinhado no hover.

### Linha de ente (assinatura)
Grade fixa: marcador quadrado de status, nome em 600, contagem tabular, barra empilhada por status (9px, abre da esquerda em 700ms quando o movimento é permitido), situação em texto de estado alinhada à direita e ementa em serifa com remissão §. Entes sem editais na base ficam em tinta-3 com barra tracejada.

### Remissão § (assinatura)
Etiqueta 11.5px peso 600 em verde sobre verde lavado, raio 2px, focável. Em hover ou foco revela, abaixo, o texto resumido do parágrafo da IN 5 sobre tinta (280px, 12.5px), com entrada de 160ms em opacidade e 3px de deslocamento.

### Evidência
Trecho em serifa 14px com fio esquerdo de 1px em tinta-3, campo e página (verde) acima. O trecho alvo de um link de prova ganha fundo verde lavado.

## Do's and Don'ts

### Do:
- **Do** separar blocos com fio de 1px (fio) e linhas com fio-2; abra seções com cabeçalho em caixa alta sobre fio de 2px em tinta.
- **Do** usar as cinco cores de estado somente para estado, sempre com seu lavado em selos e com hachura diagonal para sem leitura.
- **Do** manter números em algarismos tabulares e alinhados à direita.
- **Do** levar todo número de conformidade a um link de prova (verde, sublinhado fino) que abre o trecho e a página.
- **Do** refluir por células inteiras nos pontos 1240px, 980px e 760px, em vez de comprimir colunas.
- **Do** usar a serifa apenas para ementas, objeto e trechos do edital.

### Don't:
- **Don't** usar cartões, sombras de superfície ou fundos coloridos de área; a única sombra é a do tooltip da remissão.
- **Don't** pintar linhas ou blocos inteiros de tijolo, nem ordenar entes como ranking de piores.
- **Don't** fundir indeterminado ou sem leitura com não conforme; cada um tem marca própria.
- **Don't** usar o verde institucional como decoração; ele marca navegação, remissão, prova, foco e conforme.
- **Don't** arredondar além de 3px nem usar glifos de ícone; chevrons e marcadores são desenhados em CSS.
