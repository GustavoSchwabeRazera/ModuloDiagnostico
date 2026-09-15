from copy import deepcopy
from datetime import date, datetime, timezone

import pytest

from diagnostico.inteligencia.orquestrador import ErroOrquestracao, OrquestradorPesquisaAssistida
from diagnostico.inteligencia.schemas import SaidaInteligenciaMercado


class RepoFake:
    def __init__(self, sessao):
        self.sessao = deepcopy(sessao)

    def obter(self, identificador):
        if identificador != self.sessao["diagnostico_id"]:
            return None
        return deepcopy(self.sessao)

    def salvar(self, identificador, sessao):
        self.sessao = deepcopy(sessao)
        return deepcopy(sessao)


class ProvedorFake:
    nome = "FAKE"

    def __init__(self, falhar_em=None):
        self.falhar_em = falhar_em
        self.chamadas = []

    def analisar(self, entrada):
        self.chamadas.append(entrada.pais.iso3)
        if entrada.pais.iso3 == self.falhar_em:
            raise RuntimeError("falha simulada")
        return SaidaInteligenciaMercado(
            pais_iso3=entrada.pais.iso3,
            status="CONCLUIDA_COM_RESSALVAS",
            resumo="Análise controlada concluída com ressalvas.",
            requisitos=[],
            nao_confirmados=["Aplicabilidade ainda não confirmada."],
            alertas=[],
            evidencias_disponiveis=[e.evidencia_id for e in entrada.evidencias],
        )


def sessao():
    agora = datetime.now(timezone.utc)
    return {
        "diagnostico_id": "diag-1",
        "status": "CALCULADO",
        "catalogo_versao": "1.0.0",
        "produto": {"ncm": "09011110", "hs6": "090111", "descricao": "Café não torrado"},
        "mercados_basico": [
            {"iso3": "DEU", "nome": "Alemanha"},
            {"iso3": "CHN", "nome": "China"},
            {"iso3": "ITA", "nome": "Itália"},
        ],
        "mercados_escolhidos": ["DEU", "CHN", "ITA"],
        "respostas": [],
        "resultado": {
            "score_geral": 72.5,
            "nivel": "QUASE_PRONTA",
            "pesquisas_mercado": [],
        },
        "criado_em": agora,
        "atualizado_em": agora,
    }


def doc_ue():
    return {
        "fonte_codigo": "EU_ACCESS2MARKETS",
        "url": "https://trade.ec.europa.eu/access-to-markets/en/content/product-requirements-0",
        "titulo": "Product requirements",
        "texto": "Conteúdo oficial suficientemente longo para ser aceito como evidência controlada.",
        "consultado_em": date(2026, 8, 31),
        "idioma": "en",
    }


def test_processa_tres_paises_separadamente():
    repo = RepoFake(sessao())
    provedor = ProvedorFake()
    resultado = OrquestradorPesquisaAssistida(repo, provedor).executar("diag-1", {
        "documentos_por_pais": [{"pais_iso3": "DEU", "documentos": [doc_ue()]}]
    })
    assert provedor.chamadas == ["DEU", "CHN", "ITA"]
    assert resultado.paises_solicitados == 3
    assert len(resultado.resultados) == 3


def test_falha_em_um_pais_nao_interrompe_outros():
    repo = RepoFake(sessao())
    provedor = ProvedorFake(falhar_em="CHN")
    resultado = OrquestradorPesquisaAssistida(repo, provedor).executar("diag-1", {})
    status = {r.pais_iso3: r.status for r in resultado.resultados}
    assert status["CHN"] == "ERRO"
    assert status["DEU"] == "CONCLUIDA_COM_RESSALVAS"
    assert status["ITA"] == "CONCLUIDA_COM_RESSALVAS"
    assert resultado.paises_com_erro == 1


def test_pontuacao_e_preservada():
    repo = RepoFake(sessao())
    resultado = OrquestradorPesquisaAssistida(repo, ProvedorFake()).executar("diag-1", {})
    assert resultado.score_geral_antes == 72.5
    assert resultado.score_geral_depois == 72.5
    assert resultado.pontuacao_preservada is True
    assert repo.sessao["resultado"]["score_geral"] == 72.5
    assert repo.sessao["resultado"]["nivel"] == "QUASE_PRONTA"


def test_pesquisa_completa_e_persistida():
    repo = RepoFake(sessao())
    OrquestradorPesquisaAssistida(repo, ProvedorFake()).executar("diag-1", {})
    assert repo.sessao["pesquisa_assistida"]["provedor"] == "FAKE"
    assert len(repo.sessao["pesquisa_assistida"]["resultados"]) == 3
    assert len(repo.sessao["resultado"]["pesquisas_mercado"]) == 3


def test_documento_de_pais_nao_selecionado_e_rejeitado():
    repo = RepoFake(sessao())
    with pytest.raises(ErroOrquestracao, match="não selecionados"):
        OrquestradorPesquisaAssistida(repo, ProvedorFake()).executar("diag-1", {
            "documentos_por_pais": [{"pais_iso3": "USA", "documentos": []}]
        })


def test_sessao_inexistente_e_rejeitada():
    repo = RepoFake(sessao())
    with pytest.raises(ErroOrquestracao, match="não encontrada"):
        OrquestradorPesquisaAssistida(repo, ProvedorFake()).executar("outra", {})


def test_sem_resultado_deterministico_tambem_funciona():
    dados = sessao()
    dados["resultado"] = None
    repo = RepoFake(dados)
    resultado = OrquestradorPesquisaAssistida(repo, ProvedorFake()).executar("diag-1", {})
    assert resultado.score_geral_antes is None
    assert resultado.score_geral_depois is None
    assert repo.sessao["resultado"] is None
