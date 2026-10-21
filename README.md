# Ações Afirmativas na Lei Paulo Gustavo: verificação das cotas nos editais dos Estados, DF e Capitais

> Branch `lpg`: adaptação do pipeline usado na pesquisa da Política Nacional Aldir Blanc (PNAB, ciclo 1) para os editais da **Lei Complementar nº 195/2022 (Lei Paulo Gustavo - LPG)**.

## 📖 Visão Geral

O objetivo é verificar se os editais de fomento publicados com recursos da LPG cumprem as cotas da [Instrução Normativa MinC nº 5/2023](https://www.in.gov.br/en/web/dou/-/instrucao-normativa-minc-n-5-de-10-de-agosto-de-2023-502407937), art. 5º:

- no mínimo **20% das vagas para pessoas negras** (pretas ou pardas) e **10% para pessoas indígenas**;
- **§2º** frações iguais ou maiores que 0,5 arredondam para cima e menores que 0,5 para baixo;
- **§3º** editais divididos em categorias devem ter cotas em **todas** elas;
- **§4º** categoria com uma única vaga pode ir para a ampla concorrência, desde que o edital como um todo reserve 20% e 10%.

Além disso, o pipeline levanta outras cotas (PcD, mulheres, LGBTQIA+, quilombolas etc.), pontuações bônus, objeto, modalidade, valor total, número de vagas e a tabela de categorias (vagas e valores) de cada edital.

## 📂 Estrutura do Projeto
<br>    ├── data/EDITAIS/            # PDFs: {Capitais,Estados}/<ente>/*.pdf (só a raiz de cada ente é lida)
<br>    ├── data/interim/LPG/        # Markdown, manifesto, respostas brutas, gastos (gerados)
<br>    ├── data/final/lpg_editais.xlsx  # Resultado
<br>    ├── src/main.py              # Orquestrador das etapas
<br>    ├── src/extract/pdf_to_md.py # Conversão PDF -> Markdown (PyMuPDF)
<br>    ├── src/llm/                 # Prompt, schema, extração (Claude) e controle de orçamento
<br>    ├── src/transform/conformidade.py # Regras da IN 5 em código
<br>    ├── src/transform/consolida_lpg.py # Planilha final
<br>    └── tests/                   # Testes das regras de cota

## 📊 Fluxo de extração

### 1. Conversão de PDF para Markdown
Cada edital é convertido com **PyMuPDF (pymupdf4llm)**, que preserva as tabelas em Markdown, com um marcador `<!-- página N -->` no início de cada página. PDFs escaneados (sem camada de texto) são recomprimidos e enviados ao modelo como PDF, que lê as páginas como imagem.

### 2. Edital inteiro em uma única chamada
Diferente da PNAB, **não há divisão em blocos nem filtro por regex**: o edital completo é enviado ao modelo. Isso evita cortar as tabelas de categorias (necessárias para o §3º) e perder trechos, como o objeto, que não casam com os padrões de busca.

### 3. Extração estruturada com LLM
Modelo **Claude Sonnet 5.5** (`claude-sonnet-5-5`), via Message Batches API, com **saída estruturada** (JSON validado por um schema Pydantic, `src/llm/schema.py`). Para cada campo-chave o modelo devolve o trecho literal e a página como evidência. O modelo só extrai: não calcula vagas nem julga conformidade.

### 4. Regras da IN 5 em código
`src/transform/conformidade.py` aplica as regras (percentuais mínimos, arredondamento do §2º, categorias do §3º e exceção do §4º) e classifica cada edital como `conforme`, `nao_conforme`, `indeterminado`, `especifico` (edital dirigido integralmente a um grupo) ou `nao_aplicavel` (retificação, resultado etc.), com o motivo.

### 5. Controle de custo
Antes de qualquer envio o pipeline conta os tokens exatos de cada edital (endpoint gratuito) e calcula o **pior caso** da etapa. Se gasto acumulado + pior caso passar do teto (`ORCAMENTO_USD` em `settings.py`), nada é enviado. O gasto real fica em `data/interim/LPG/gastos.csv`.

### 6. Avaliação
Piloto com 10 editais e gabarito manual de cerca de 20% da base (estratificado por ente), com F1 por campo e acurácia da classificação de conformidade.

## 💻 Como usar

```
python -m venv .venv
.venv\Scriptsctivate          # Windows
pip install -r requirements.txt
```

Crie `src/.env` com `ANTHROPIC_API_KEY=...` e rode, a partir de `src/`:

```
python main.py converter      # PDF -> Markdown (local)
python main.py contar         # tokens e custo estimado (gratuito)
python main.py piloto 10      # 10 editais, síncrono
python main.py amostra 77     # sorteia a amostra do gabarito
python main.py batch amostra  # extrai a amostra do gabarito
python main.py coletar        # coleta batches terminados
python main.py batch          # extrai todos os pendentes
python main.py consolidar     # gera data/final/lpg_editais.xlsx
python main.py gasto          # gasto acumulado
```

Testes das regras: `pytest tests`.

## 🧮 Cálculo e agregação dos dados

A identificação do número de vagas e dos valores reservados por ente em cada categoria de cota seguiu critérios matemáticos padronizados, organizados em duas etapas complementares: cálculo por edital (nível individual) e agregação por ente federativo (nível consolidado). 

### 1. Cálculo de vagas 

#### 1.1 Cálculo do número de vagas reservadas por edital (nível individual)

Nesta etapa, calculou-se o número de vagas reservadas por categoria de cota em cada edital analisado, a partir dos seguintes procedimentos: 

**1.1.1** Para obter o número de vagas destinadas a cada categoria de cota (vagas_cota_edital), multiplicou-se o total de vagas do edital (vagas_total_edital) pelo percentual de reserva destinado a cada categoria (p_cota_edital).  

$$
\text{vagas-total-edital} \times \text{p-cota-edital} = \text{vagas-cota-edital}
$$

**1.1.2** Quando o resultado foi um número fracionário, aplicou-se a regra prevista no art. 5º, § 2º, da IN MinC nº 5/2023, adotando-se arredondamento para o número inteiro imediatamente superior em frações iguais ou superiores a 0,5 e para o inteiro imediatamente inferior em frações menores que 0,5. 

**1.1.3** Nos casos de editais específicos integralmente destinados a um dos três grupos prioritários (pessoas negras, pessoas indígenas e PCD), a totalidade das vagas foi contabilizada na respectiva categoria de cota. 

#### 1.2 Agregação das vagas reservadas por ente federativo (nível consolidado)  

Após o cálculo por edital, os dados foram consolidados por ente federativo, com o objetivo de estimar o percentual aproximado de vagas reservadas por categoria em cada ente. Para tanto, adotou-se o seguinte fluxo:  

**1.2.1.** Primeiro, apurou-se o total de vagas destinadas a cada categoria nos editais de cada ente (vagas_cota_ente), por meio do somatório (∑) das vagas reservadas em todos os editais publicados (∑ vagas_cota_edital).  

$$
\sum \text{vagas-cota-edital} = \text{vagas-cota-ente}
$$

**1.2.2.** Em seguida, obteve-se o total de vagas dos editais de cada ente (vagas_total_ente), mediante o somatório das vagas previstas em todos os editais publicados (∑ vagas_total_edital). 

\sum \text{vagas-total-ente} = \text{vagas-total-ente}

**1.2.3**. Por fim, o percentual de reserva de cada ente (p_agregado_vagas_ente) foi obtido pela razão entre o total de vagas reservadas e o total geral de vagas: 

$$
\frac{\text{vagas-cota-ente}}{\text{vagas-total-ente}} \times 100 = \text{p-agregado-vagas-cotas-ente}
$$

### 2. Cálculo dos valores 

#### 2.1 Cálculo de valores reservados por edital (nível individual) 

Além do número de vagas, calculou-se o valor destinado a cada categoria de cota por edital, a partir de um procedimento de estimativa, descrito nas etapas a seguir: 

**2.1.1** Inicialmente, estimou-se o valor unitário de cada vaga (valor_vaga_edital) por meio da divisão do valor total do edital (valor_total_edital) pelo total de vagas previstas (vagas_total_edital).  

$$
\frac{\text{valor-total-edital}}{\text{vagas-total-edital}} = \text{valor-vaga-edital}
$$

**2.1.2** Em seguida, calculou-se o valor destinado a cada categoria de cota no edital (valor_cota_edital), multiplicando o número de vagas reservadas (vagas_cota_edital) pelo valor unitário obtido no passo anterior. 

$$
\text{vagas-cota-edital} \times \text{valor-vaga-edital} = \text{valor-cota-edital}
$$

#### 2.2 Agregação dos valores reservadas por ente federativo (nível consolidado)

Após o cálculo individual por edital, os dados foram consolidados por ente federativo, a fim de estimar o percentual aproximado de valores reservados a cada categoria de cota em cada ente. Para isso, adotou-se o seguinte procedimento: 

**2.2.1.** Primeiro, apurou-se o valor total reservado por ente a cada categoria (valor_cota_ente), mediante o somatório dos valores correspondentes nos editais por ele publicados (∑valor_cota_edital). 

$$
\sum \text{valor-cota-edital} = \text{valor-cota-ente}
$$

**2.2.2.** Em seguida, obteve-se o total dos valores dos editais de cada ente (valor_total_ente), mediante o somatório dos valores previstaos em todos os editais publicados (∑ valores_total_ente). 

$$
\sum \text{valores-total-ente} = \text{valor-total-ente}
$$

**2.2.3** Por fim, o percentual do valor reservado para cada categoria de cota (p_ agregado_valor_cota_ente) foi calculado, em cada ente, pela razão entre o valor total destinado às cotas (valor_cota_ente) e o valor total destinado (valor_total_ente), multiplicada por 100. 

$$
\left( \frac{\text{valor-cota-ente}}{\text{valor-total-ente}} \right) \times 100 = \text{p-agregado-valor-cota-ente}
$$


## 🔎 Interpretação dos resultados

A análise considerou, de forma agregada, os percentuais de vagas e de recursos previstos nos editais de cada ente. A identificação de índices ligeiramente inferiores ao mínimo normativo não implica, por si só, descumprimento das regras de cotas. Essas variações podem decorrer de fatores técnicos, como: 

- **Uso de editais específicos**: a publicação de editais exclusivos para determinados grupos prioritários pode alterar a proporção de reservas quando se observa o conjunto dos editais. Nesses casos, a ação afirmativa se dá por meio de instrumentos focalizados, sem que haja descumprimento das diretrizes no resultado global.
- **Regras de arredondamento**: a conversão de frações em números inteiros pode produzir percentuais levemente inferiores ao parâmetro previsto. Trata-se, muitas vezes, de efeito da aplicação correta da regra de arredondamento estabelecida no art. 5º, § 2º, da IN MinC nº 5/2023, sem indicar necessariamente descumprimento da reserva.


## 📈 Análise e consolidação de dados 

A análise da implementação das cotas nos estados, capitais e DF baseou-se nos índices e cálculos de distribuição detalhados na seção anterior, necessários para mensurar a aplicação das cotas dentro de editais universais. Já o exame do uso de editais específicos não exigiu cálculos de partilha, visto que são destinados a um público exclusivo.  

Para este grupo, realizou-se uma triagem manual dos 496 editais levantados, fundamentada nos parâmetros dispostos no art. 14 da IN MinC nº 10/2023, para identificar: i. a configuração do certame (se específico para grupos e territórios vulnerabilizados); e ii. o público-alvo do instrumento. Dados como valores, número de vagas e ente responsável foram obtidos via extração automatizada, o que permitiu uma análise quantitativa padronizada com os critérios de reserva de vagas. 

Esse percurso metodológico consolidou um acervo disperso em uma base de dados estruturada, permitindo que o processamento quantitativo das duas modalidades de ação afirmativa seguisse quatro frentes principais: 

- **Adesão:** Implementação de cotas e editais específicos em estados, DF e capitais  

- **Alcance:** Quantidade de vagas destinadas a cada grupo e percentuais.  

- **Investimento:** Volume de recursos financeiros direcionados por grupo e percentuais.  

- **Comparação demográfica:** análise comparada dos percentuais de cotas com a composição demográfica dos estados e DF, apenas;

Essa estrutura permitiu analisar a dinâmica das ações afirmativas no Ciclo 1 da Política Nacional Aldir Blanc, revelando pistas sobre o grau de incorporação de cotas e editais específicos por estados, capitais e Distrito Federal. 


## 📜 Licença

Este projeto está sob a licença MIT.
