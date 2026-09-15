import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "diagnostico"

def carregar(nome):
    return json.loads((BASE / "data" / nome).read_text(encoding="utf-8"))

def test_catalogo_diagnostico_v1_coerente():
    catalogo = carregar("catalogo_checklist_v1.json")
    regras = carregar("regras_pontuacao_v1.json")
    itens = catalogo["itens"]
    assert itens
    assert len({x["codigo"] for x in itens}) == len(itens)
    assert all(x["peso"] == regras["pesos_criticidade"][x["criticidade"]] for x in itens)

def test_diagnostico_nao_bloqueia_vendas():
    regras = carregar("regras_pontuacao_v1.json")
    assert regras["integracao_vendas"]["dependencia_do_diagnostico"] is False
    assert regras["integracao_vendas"]["bloqueia_acesso"] is False

def test_limites_de_mercados():
    regras = carregar("regras_pontuacao_v1.json")
    assert regras["mercados_basico_maximo"] == 20
    assert regras["mercados_diagnostico_maximo"] == 3
