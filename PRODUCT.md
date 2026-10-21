# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

App Python em Dash, próximo ao pipeline existente (src/dashboard/, `python main.py painel`).

## Users

Equipe técnica do Ministério da Cultura (MinC): gestores e analistas que acompanham se os editais de fomento da Lei Paulo Gustavo (LC 195/2022) publicados pelos Estados, DF e Capitais cumprem as cotas da IN MinC nº 5/2023. O trabalho deles é identificar quais entes e editais estão conformes, quais não estão e por quê, e sustentar essa leitura com evidência do próprio edital.

## Product Purpose

Transformar um acervo disperso de editais em PDF numa base estruturada e verificável sobre ações afirmativas na LPG. O pipeline extrai de cada edital as cotas, categorias, vagas e valores, aplica as regras do art. 5º da IN 5 em código e classifica cada edital. A primeira superfície planejada é um painel interativo para a equipe técnica explorar esse resultado.

Sucesso significa que um analista consegue, para qualquer ente ou edital, ver a classificação de conformidade, o motivo e o trecho/página do edital que a fundamenta, sem abrir o PDF nem a planilha.

## Positioning

A classificação não é opinião do modelo: o LLM só extrai (com trecho literal e página como evidência) e as regras da IN 5 (percentuais mínimos de 20% negros e 10% indígenas, arredondamento do §2º, cotas em todas as categorias pelo §3º, exceção de vaga única do §4º) são aplicadas em código auditável e testado. Cada conclusão é rastreável até a página do edital.

## Operating Context

- Entrada: PDFs dos editais em `data/EDITAIS/{Capitais,Estados}/<ente>/`.
- Etapas (via `src/main.py`): conversão PDF→Markdown, contagem de tokens/custo, extração com Claude (Message Batches, saída estruturada Pydantic), regras de conformidade, consolidação.
- Saída atual: `data/final/lpg_editais.xlsx`; gastos em `data/interim/LPG/gastos.csv`.
- Avaliação: piloto de 10 editais e gabarito manual de cerca de 20% da base, estratificado por ente (F1 por campo, acurácia da classificação).
- Histórico: adaptação do pipeline da pesquisa da PNAB (ciclo 1), que já produzia mapas por UF em matplotlib/geopandas.

## Capabilities and Constraints

- Classificações de edital: `conforme`, `nao_conforme`, `indeterminado`, `especifico` (dirigido integralmente a um grupo), `nao_aplicavel` (retificação, resultado etc.), sempre com motivo.
- Além das cotas da IN 5, a base levanta outras cotas (PcD, mulheres, LGBTQIA+, quilombolas etc.), pontuação bônus, objeto, modalidade, valor total, número de vagas e tabela de categorias.
- Agregação por ente: percentuais de vagas e de valores reservados por grupo, conforme a metodologia do README.
- Orçamento de API com teto (`ORCAMENTO_USD`) e checagem de pior caso antes de qualquer envio.
- Terminologia: "ente" (Estado, DF ou Capital), "edital específico", "ampla concorrência", "IN 5", "LPG", "PNAB".
- O painel usa somente data/final/lpg_editais.xlsx; nenhuma base externa (IBGE, mapas).
- Em aberto: hospedagem e controle de acesso do painel.

## Evidence on Hand

- Base real de editais (PDFs) e planilha consolidada `data/final/lpg_editais.xlsx`.
- Evidência por campo extraído: trecho literal e página do edital.
- Testes das regras em `tests/test_conformidade.py`.
- Metodologia de cálculo e interpretação documentada no README.
- Não há resultados de avaliação (F1, acurácia) registrados aqui; não inventar números, totais de editais ou achados que não venham da base.

## Product Principles

1. **Toda conclusão mostra sua prova.** Classificação, motivo e trecho/página do edital andam juntos.
2. **Abaixo do mínimo não é automaticamente descumprimento.** Editais específicos e o arredondamento do §2º podem explicar percentuais agregados menores; a interface deve deixar isso legível, não alarmista.
3. **Regra em código, não em julgamento.** O painel reflete as regras da IN 5 como implementadas; incerteza aparece como `indeterminado`, nunca é escondida.
4. **Feito para o trabalho do analista.** Filtrar por ente, tipo de ente e situação, e chegar ao edital individual, vem antes de qualquer apresentação.
