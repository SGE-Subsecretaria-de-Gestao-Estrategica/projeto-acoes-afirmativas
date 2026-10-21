import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from transform.conformidade import arredonda_in5, avalia_edital  # noqa: E402


def edital(**kw):
    base = {
        "tipo_documento": "edital", "vagas_totais": None, "possui_categorias": False, "categorias": [],
        "percentual_negras": None, "percentual_indigenas": None, "vagas_negras_total": None,
        "vagas_indigenas_total": None, "cotas_por_categoria": "sem_categorias", "edital_especifico_grupo": None,
    }
    return base | kw


def cat(nome, vagas, negras=None, indigenas=None):
    return {"nome": nome, "vagas": vagas, "vagas_negras": negras, "vagas_indigenas": indigenas}


def test_arredondamento_paragrafo_2():
    assert arredonda_in5(2.5) == 3
    assert arredonda_in5(2.4) == 2
    assert arredonda_in5(0.5) == 1
    assert arredonda_in5(0.2 * 12) == 2   # 2,4
    assert arredonda_in5(0.1 * 15) == 2   # 1,5
    assert arredonda_in5(0.2 * 7) == 1    # 1,4


def test_percentuais_minimos_sem_categorias():
    r = avalia_edital(edital(vagas_totais=10, percentual_negras=0.2, percentual_indigenas=0.1))
    assert r["status_in5"] == "conforme"
    assert r["vagas_cotas_negras"] == 2 and r["vagas_cotas_indigenas"] == 1


def test_percentual_abaixo():
    r = avalia_edital(edital(vagas_totais=10, percentual_negras=0.15, percentual_indigenas=0.1))
    assert r["status_negras"] == "nao_conforme"
    assert r["status_in5"] == "nao_conforme"


def test_percentual_informado_como_inteiro():
    r = avalia_edital(edital(vagas_totais=10, percentual_negras=20, percentual_indigenas=10))
    assert r["status_in5"] == "conforme"


def test_sem_cota():
    r = avalia_edital(edital(vagas_totais=10))
    assert r["status_in5"] == "nao_conforme"


def test_categorias_com_reservas_ok():
    cats = [cat("A", 10, 2, 1), cat("B", 5, 1, 1)]  # 5*0,2=1 ; 5*0,1=0,5->1
    r = avalia_edital(edital(possui_categorias=True, categorias=cats, cotas_por_categoria="sim"))
    assert r["status_in5"] == "conforme"


def test_categoria_abaixo_do_minimo_paragrafo_3():
    cats = [cat("A", 10, 2, 1), cat("B", 5, 1, 0)]  # B precisa de 1 indígena
    r = avalia_edital(edital(possui_categorias=True, categorias=cats, cotas_por_categoria="sim"))
    assert r["status_indigenas"] == "nao_conforme"
    assert "B" in r["motivo_indigenas"]


def test_categoria_com_uma_vaga_paragrafo_4():
    # categorias de 1 vaga na ampla concorrência, mas o total do edital atinge 20%/10%
    cats = [cat("A", 1, 0, 0), cat("B", 1, 0, 0), cat("C", 8, 2, 1)]  # total 10 -> 2 e 1
    r = avalia_edital(edital(possui_categorias=True, categorias=cats, cotas_por_categoria="sim"))
    assert r["status_in5"] == "conforme"


def test_paragrafo_4_sem_compensar_no_total():
    cats = [cat("A", 1, 0, 0), cat("B", 1, 0, 0), cat("C", 1, 0, 0), cat("D", 2, 0, 0)]
    r = avalia_edital(edital(possui_categorias=True, categorias=cats, cotas_por_categoria="sim"))
    # D: 2*0,2=0,4 -> 0 e 2*0,1 -> 0, mas o total (5) exige 1 vaga para pessoas negras
    assert r["status_negras"] == "nao_conforme"


def test_cotas_so_no_total_com_categorias():
    cats = [cat("A", 10), cat("B", 10)]
    r = avalia_edital(edital(possui_categorias=True, categorias=cats, percentual_negras=0.2,
                             percentual_indigenas=0.1, cotas_por_categoria="nao"))
    assert r["status_in5"] == "nao_conforme"


def test_edital_especifico():
    r = avalia_edital(edital(vagas_totais=10, edital_especifico_grupo="povos indígenas"))
    assert r["status_in5"] == "especifico"
    assert r["vagas_cotas_indigenas"] == 10 and r["vagas_cotas_negras"] == 0


def test_documento_nao_edital():
    assert avalia_edital(edital(tipo_documento="retificacao"))["status_in5"] == "nao_aplicavel"
