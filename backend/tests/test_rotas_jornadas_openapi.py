from app.main import app


def test_openapi_contem_rotas_de_jornada():
    paths = app.openapi()["paths"]
    assert "/api/v1/jornadas" in paths
    assert "/api/v1/jornadas/{journey_id}" in paths
    assert "/api/v1/jornadas/{journey_id}/mercados" in paths
    assert "/api/v1/jornadas/{journey_id}/diagnostico-payload" in paths
    assert "/api/v1/jornadas/{journey_id}/diagnostico" in paths
