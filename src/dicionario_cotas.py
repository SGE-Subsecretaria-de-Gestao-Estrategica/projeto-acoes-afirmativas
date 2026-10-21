"""Dicionário das formas como cada grupo de cota aparece nos editais.

Usado em dois lugares:
- no prompt (llm/prompt.py), para orientar a classificação do grupo_padrao;
- na conferência (transform/consolida_lpg.py): se o texto menciona o grupo perto de
  uma palavra de reserva e o LLM não achou cota, o edital é marcado para revisão.

Os termos são regex (sem acento obrigatório, case-insensitive).
"""
import re

TERMOS_GRUPO: dict[str, list[str]] = {
    "negras": [
        r"pessoas?\s+negr[ao]s?", r"negr[ao]s?", r"pret[ao]s?\s+(?:e|ou)\s+pard[ao]s?",
        r"popula[cç][aã]o\s+negra", r"afrodescendentes?", r"afro-?brasileir[ao]s?",
    ],
    "indigenas": [
        r"ind[ií]genas?", r"povos?\s+origin[aá]rios?", r"aldead[ao]s?", r"etnias?\s+ind[ií]genas?",
    ],
    "pcd": [
        r"pessoas?\s+com\s+defici[eê]ncias?", r"\bpcds?\b", r"deficientes?",
        r"pessoas?\s+(?:surdas?|cegas?|autistas?)", r"transtorno\s+do\s+espectro\s+autista", r"\bTEA\b",
        r"neurodivergentes?",
    ],
    "lgbtqia": [
        r"lgbt\w*\+?", r"pessoas?\s+trans\b", r"transexua(?:l|is)", r"transg[eê]neros?", r"travestis?",
        r"n[aã]o[\s-]?bin[aá]ri[aoe]s?", r"diversidade\s+sexual", r"l[eé]sbicas?", r"bissexua(?:l|is)",
        r"intersexo", r"homossexua(?:l|is)",
    ],
    "quilombolas": [
        r"quilombolas?", r"remanescentes?\s+de\s+quilombos?", r"comunidades?\s+quilombolas?", r"quilombos?",
    ],
}

# Palavras que indicam reserva de vagas (e não só menção ao grupo)
TERMOS_RESERVA = [
    r"cotas?", r"reserv(?:a|am|ad[ao]s?)", r"destinad[ao]s?", r"percentual\s+m[ií]nimo",
    r"vagas?\s+exclusivas?", r"ampla\s+concorr[eê]ncia",
]

JANELA = 200  # caracteres antes/depois do termo do grupo

_RE_GRUPO = {g: re.compile("|".join(t), re.IGNORECASE) for g, t in TERMOS_GRUPO.items()}
_RE_RESERVA = re.compile("|".join(TERMOS_RESERVA), re.IGNORECASE)


def menciona(texto: str, grupo: str) -> bool:
    return bool(_RE_GRUPO[grupo].search(texto))


def mencoes_reserva(texto: str, grupo: str) -> list[str]:
    """Trechos em que o grupo aparece a até JANELA caracteres de uma palavra de reserva."""
    trechos = []
    for m in _RE_GRUPO[grupo].finditer(texto):
        ini, fim = max(0, m.start() - JANELA), m.end() + JANELA
        if _RE_RESERVA.search(texto, ini, fim):
            trechos.append(" ".join(texto[ini:fim].split()))
    return trechos


def formas_para_prompt() -> str:
    """Lista legível das formas de cada grupo, para o prompt."""
    exemplos = {
        "pcd": "pessoas com deficiência, PcD, deficientes, pessoas surdas/cegas, autistas (TEA), neurodivergentes",
        "lgbtqia": "LGBT, LGBTQIA+, LGBTQIAPN+, pessoas trans, transexuais, transgêneros, travestis, "
                   "pessoas não binárias, diversidade sexual e de gênero, lésbicas, gays, bissexuais, intersexo",
        "quilombolas": "quilombolas, comunidades quilombolas, remanescentes de quilombo",
    }
    return "\n".join(f'  - "{g}": {t}' for g, t in exemplos.items())
