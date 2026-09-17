from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import sessionmaker

from diagnostico.database import Base, criar_engine
from diagnostico.jornada_models import JornadaModel
from diagnostico.jornada_repository import RepositorioJornadas
from diagnostico.jornada_service import (
    JornadaExpirada,
    ServicoJornadas,
    TokenJornadaInvalido,
)


def service_and_repo():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = RepositorioJornadas(sessionmaker(bind=engine, expire_on_commit=False))
    return ServicoJornadas(repo), repo


def payload():
    return (
        {"ncm": "09011110", "hs6": "090111", "descricao": "Café não torrado"},
        [{"iso3": "DEU", "nome": "Alemanha", "ranking_personalizado": 1, "score_exportai": 56.3, "faixa_confianca": "ALTA", "tipo_oportunidade": "MERCADO_ATUAL_COM_WITS"}],
    )


def test_token_original_nao_e_armazenado():
    service, repo = service_and_repo()
    produto, mercados = payload()
    data, token = service.criar(produto, mercados)
    saved = repo.obter(data["journey_id"])
    assert token != saved["resume_token_hash"]
    assert len(saved["resume_token_hash"]) == 64


def test_token_valido_recupera_jornada():
    service, _ = service_and_repo()
    produto, mercados = payload()
    data, token = service.criar(produto, mercados)
    recovered = service.autenticar(data["journey_id"], token)
    assert recovered["produto"]["ncm"] == "09011110"


def test_token_invalido_e_rejeitado():
    service, _ = service_and_repo()
    produto, mercados = payload()
    data, _ = service.criar(produto, mercados)
    try:
        service.autenticar(data["journey_id"], "incorreto")
        assert False, "Era esperado TokenJornadaInvalido"
    except TokenJornadaInvalido:
        pass


def test_so_seleciona_mercado_do_basico():
    service, _ = service_and_repo()
    produto, mercados = payload()
    data, _ = service.criar(produto, mercados)
    updated = service.selecionar_mercados(data, ["DEU"])
    assert updated["mercados_escolhidos"] == ["DEU"]


def test_payload_do_diagnostico_preserva_contexto():
    service, _ = service_and_repo()
    produto, mercados = payload()
    data, _ = service.criar(produto, mercados)
    data = service.selecionar_mercados(data, ["DEU"])
    result = service.diagnostic_payload(data)
    assert result["produto"]["hs6"] == "090111"
    assert result["mercados_escolhidos"] == ["DEU"]


def test_jornada_por_hs6_sem_ncm_preserva_contexto():
    service, _ = service_and_repo()
    produto, mercados = payload()
    produto.pop("ncm")
    data, _ = service.criar({**produto, "ncm": None}, mercados)
    data = service.selecionar_mercados(data, ["DEU"])
    result = service.diagnostic_payload(data)
    assert result["produto"]["ncm"] is None
    assert result["produto"]["hs6"] == "090111"


def test_jornada_expirada_e_rejeitada():
    service, repo = service_and_repo()
    produto, mercados = payload()
    data, token = service.criar(produto, mercados)
    data["expira_em"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    repo.salvar(data)
    try:
        service.autenticar(data["journey_id"], token)
        assert False, "Era esperado JornadaExpirada"
    except JornadaExpirada:
        pass
