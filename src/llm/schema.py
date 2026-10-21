"""Schema da extração de editais da LPG.

Todos os campos são obrigatórios e aceitam null: o modelo precisa responder
cada um, e usa null quando a informação não está no documento.
"""
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")  # gera additionalProperties: false


class Categoria(_Base):
    nome: str = Field(description="Nome da categoria/módulo/linha/faixa, como no edital")
    vagas: Optional[int] = Field(description="Número de vagas/projetos/prêmios da categoria")
    valor_por_vaga: Optional[float] = Field(description="Valor unitário por projeto/prêmio, em reais")
    valor_categoria: Optional[float] = Field(description="Valor total da categoria, em reais")
    vagas_negras: Optional[int] = Field(description="Vagas reservadas a pessoas negras NESTA categoria, se o edital informar")
    vagas_indigenas: Optional[int] = Field(description="Vagas reservadas a pessoas indígenas NESTA categoria, se o edital informar")
    vagas_pcd: Optional[int] = Field(description="Vagas reservadas a pessoas com deficiência NESTA categoria, se o edital informar")
    vagas_lgbtqia: Optional[int] = Field(description="Vagas reservadas a pessoas LGBTQIA+ NESTA categoria, se o edital informar")
    vagas_quilombolas: Optional[int] = Field(description="Vagas reservadas a quilombolas NESTA categoria, se o edital informar")


GrupoPadrao = Literal[
    "pcd", "lgbtqia", "quilombolas", "mulheres", "povos_tradicionais",
    "pessoas_idosas", "territorio", "outro",
]


class OutraCota(_Base):
    grupo_padrao: GrupoPadrao = Field(
        description="Classificação do grupo: pcd (pessoas com deficiência), lgbtqia (LGBTQIA+, pessoas trans, "
                    "travestis), quilombolas, mulheres, povos_tradicionais (ciganos, ribeirinhos, terreiros etc.), "
                    "pessoas_idosas, territorio (regiões, periferias, interior) ou outro"
    )
    grupo: str = Field(description="Grupo beneficiado como escrito no edital")
    percentual: Optional[float] = Field(description="Percentual reservado, como fração (0.05 = 5%)")
    vagas: Optional[int] = Field(description="Número de vagas reservadas, se informado")


class Evidencia(_Base):
    campo: str = Field(description="Campo que o trecho sustenta (ex.: percentual_negras, vagas_totais, objeto)")
    trecho: str = Field(description="Trecho literal do edital, até ~300 caracteres")
    pagina: Optional[int] = Field(description="Página do trecho (marcador <!-- página N -->)")


class Edital(_Base):
    tipo_documento: Literal["edital", "retificacao", "resultado", "anexo", "outro"]
    objeto: Optional[str] = Field(description="Objeto do edital, resumido em até 2 frases")
    modalidade: Literal["fomento_execucao", "premio", "bolsa", "subsidio", "outro"]
    area_cultural: Optional[str] = Field(description="Ex.: audiovisual, demais áreas, multilinguagem")
    valor_total: Optional[float] = Field(description="Valor total do edital, em reais")
    vagas_totais: Optional[int] = Field(description="Total de projetos/propostas/prêmios a serem selecionados")
    possui_categorias: bool
    categorias: list[Categoria]
    percentual_negras: Optional[float] = Field(description="Cota para pessoas negras, como fração (0.20 = 20%)")
    percentual_indigenas: Optional[float] = Field(description="Cota para pessoas indígenas, como fração (0.10 = 10%)")
    vagas_negras_total: Optional[int] = Field(description="Total de vagas reservadas a pessoas negras no edital, se informado")
    vagas_indigenas_total: Optional[int] = Field(description="Total de vagas reservadas a pessoas indígenas no edital, se informado")
    cotas_por_categoria: Literal["sim", "nao", "nao_informado", "sem_categorias"] = Field(
        description="O edital diz que as cotas valem em cada categoria?"
    )
    edital_especifico_grupo: Optional[str] = Field(
        description="Se o edital inteiro é destinado a um grupo (ex.: 'indígenas', 'pessoas negras'), o grupo; senão null"
    )
    outras_cotas: list[OutraCota]
    pontuacao_bonus: list[str] = Field(
        description="Grupos que recebem pontuação extra/bônus/indutores na avaliação (não é cota)"
    )
    outros_editais_no_documento: list[str] = Field(
        description="Outros editais contidos no mesmo PDF e não extraídos (ex.: 'Seleção Pública nº 025/2023 - demais áreas')"
    )
    observacoes: Optional[str] = Field(description="Ambiguidades relevantes para a análise de cotas, em 1-2 frases")
    evidencias: list[Evidencia]
