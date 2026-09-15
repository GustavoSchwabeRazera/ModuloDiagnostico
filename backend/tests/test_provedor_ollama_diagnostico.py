import json
from datetime import date

import pytest

from diagnostico.inteligencia.fabrica import criar_provedor
from diagnostico.inteligencia.provedor_ollama import (
    ErroProvedorOllama,
    ProvedorInteligenciaOllama,
)
from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado


class RespostaFake:
    def __init__(self, conteudo):
        self.message = {"content": conteudo}


class ClienteFake:
    def __init__(self, conteudo=None, erro=None):
        self.conteudo = conteudo
        self.erro = erro
        self.chamadas = []

    def chat(self, **kwargs):
        self.chamadas.append(kwargs)
        if self.erro:
            raise self.erro
        return RespostaFake(self.conteudo)


def entrada(com_evidencia=True):
    evidencias = []
    if com_evidencia:
        evidencias = [{
            "evidencia_id": "fonte-001",
            "fonte_titulo": "Portal oficial",
            "fonte_url": "https://example.gov/requisitos",
            "tipo_fonte": "OFICIAL",
            "consultado_em": date(2026, 9, 8),
            "trecho": "Trecho oficial suficientemente longo para sustentar a análise.",
            "idioma": "pt-BR",
        }]
    return EntradaInteligenciaMercado(
        produto={"ncm": "09011110", "hs6": "090111", "descricao": "Café não torrado"},
        pais={"iso3": "DEU", "nome": "Alemanha"},
        evidencias=evidencias,
    )


def saida_valida():
    return json.dumps({
        "pais_iso3": "DEU",
        "status": "CONCLUIDA_COM_RESSALVAS",
        "resumo": "Uma exigência potencial foi organizada a partir da fonte.",
        "requisitos": [{
            "categoria": "ROTULAGEM",
            "titulo": "Verificar requisitos de rotulagem",
            "descricao": "A evidência indica regras que precisam de confirmação de aplicabilidade.",
            "obrigatoriedade": "POSSIVELMENTE_OBRIGATORIO",
            "status_evidencia": "CONFIRMADO_EM_FONTE_OFICIAL",
            "aplicabilidade": "POSSIVELMENTE_APLICAVEL",
            "autoridade": None,
            "fontes_ids": ["fonte-001"],
        }],
        "nao_confirmados": [],
        "alertas": ["Confirmar a aplicabilidade com a autoridade competente."],
        "evidencias_disponiveis": ["fonte-001"],
    }, ensure_ascii=False)


def test_modelo_obrigatorio():
    with pytest.raises(ErroProvedorOllama, match="EXPORTAI_DIAGNOSTICO_IA_MODELO"):
        ProvedorInteligenciaOllama(cliente=ClienteFake(), modelo="")


def test_sem_evidencias_nao_chama_ollama():
    cliente = ClienteFake()
    provedor = ProvedorInteligenciaOllama(cliente=cliente, modelo="modelo-teste")
    saida = provedor.analisar(entrada(False))
    assert saida.status == "CONCLUIDA_COM_RESSALVAS"
    assert saida.requisitos == []
    assert cliente.chamadas == []


def test_chamada_usa_schema_temperatura_zero_e_sem_stream():
    cliente = ClienteFake(saida_valida())
    provedor = ProvedorInteligenciaOllama(cliente=cliente, modelo="modelo-teste")
    saida = provedor.analisar(entrada())
    chamada = cliente.chamadas[0]
    assert chamada["format"]["type"] == "object"
    assert chamada["options"]["temperature"] == 0
    assert chamada["stream"] is False
    assert saida.pais_iso3 == "DEU"


def test_prompt_contem_somente_evidencias_fornecidas():
    cliente = ClienteFake(saida_valida())
    ProvedorInteligenciaOllama(cliente=cliente, modelo="modelo-teste").analisar(entrada())
    prompt = cliente.chamadas[0]["messages"][1]["content"]
    assert "fonte-001" in prompt
    assert "Trecho oficial" in prompt
    assert "090111" in prompt
    assert "DEU" in prompt


def test_json_invalido_e_rejeitado():
    provedor = ProvedorInteligenciaOllama(cliente=ClienteFake("não é json"), modelo="modelo-teste")
    with pytest.raises(ErroProvedorOllama, match="contrato estruturado"):
        provedor.analisar(entrada())


def test_fonte_inventada_e_rejeitada():
    dados = json.loads(saida_valida())
    dados["evidencias_disponiveis"] = ["fonte-001", "inventada"]
    provedor = ProvedorInteligenciaOllama(
        cliente=ClienteFake(json.dumps(dados)), modelo="modelo-teste"
    )
    with pytest.raises(ErroProvedorOllama, match="lista de evidências"):
        provedor.analisar(entrada())


def test_pais_diferente_e_rejeitado():
    dados = json.loads(saida_valida())
    dados["pais_iso3"] = "CHN"
    provedor = ProvedorInteligenciaOllama(
        cliente=ClienteFake(json.dumps(dados)), modelo="modelo-teste"
    )
    with pytest.raises(ErroProvedorOllama, match="país diferente"):
        provedor.analisar(entrada())


def test_falha_de_conexao_e_encapsulada():
    provedor = ProvedorInteligenciaOllama(
        cliente=ClienteFake(erro=ConnectionError("offline")), modelo="modelo-teste"
    )
    with pytest.raises(ErroProvedorOllama, match="Falha ao consultar"):
        provedor.analisar(entrada())


def test_fabrica_seleciona_ollama(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", "modelo-teste")
    provedor = criar_provedor("OLLAMA")
    assert provedor.nome == "OLLAMA"
