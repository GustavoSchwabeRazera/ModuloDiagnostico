from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import sessionmaker

from diagnostico.database import Base, criar_engine
from diagnostico.jornada_repository import RepositorioJornadas
from diagnostico.jornada_service import JornadaExpirada, ServicoJornadas


def criar_servico():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = RepositorioJornadas(sessionmaker(bind=engine, expire_on_commit=False))
    return ServicoJornadas(repo), repo


def dados_basicos():
    produto = {
        "ncm": "09011110",
        "hs6": "090111",
        "descricao": "Café não torrado",
    }
    mercados = [
        {
            "iso3": "DEU",
            "nome": "Alemanha",
            "ranking_personalizado": 1,
            "score_exportai": 56.3,
            "faixa_confianca": "ALTA",
            "tipo_oportunidade": "MERCADO_ATUAL_COM_WITS",
        }
    ]
    return produto, mercados


def test_salvar_persiste_expira_em():
    service, repo = criar_servico()
    produto, mercados = dados_basicos()
    data, _ = service.criar(produto, mercados)
    nova_expiracao = datetime.now(timezone.utc) - timedelta(minutes=1)
    data["expira_em"] = nova_expiracao
    repo.salvar(data)
    recuperada = repo.obter(data["journey_id"])
    expira_em = recuperada["expira_em"]
    if expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=timezone.utc)
    assert expira_em <= datetime.now(timezone.utc)


def test_servico_rejeita_expiracao_persistida():
    service, repo = criar_servico()
    produto, mercados = dados_basicos()
    data, token = service.criar(produto, mercados)
    data["expira_em"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    repo.salvar(data)
    try:
        service.autenticar(data["journey_id"], token)
        assert False, "Era esperado JornadaExpirada"
    except JornadaExpirada:
        pass
