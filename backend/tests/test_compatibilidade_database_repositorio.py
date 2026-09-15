from sqlalchemy import text

from diagnostico.database import criar_engine, criar_fabrica_sessoes


def test_criar_fabrica_sessoes_com_engine_temporaria():
    engine = criar_engine("sqlite:///:memory:")
    fabrica = criar_fabrica_sessoes(engine)
    with fabrica() as sessao:
        assert sessao.execute(text("select 1")).scalar_one() == 1


def test_repositorio_sqlite_pode_ser_importado():
    from diagnostico.repositorio_sqlite import RepositorioDiagnosticosSQLite
    assert RepositorioDiagnosticosSQLite is not None
