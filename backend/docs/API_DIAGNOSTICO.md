# API do Módulo Diagnóstico

## Documentação interativa

Com a aplicação local em execução:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Endpoints encontrados

- `GET /api/v1/diagnosticos/complementar/saude`: `saude_camadas_complementares`
- `GET /api/v1/diagnosticos/checklist`: `consultar_checklist`
- `POST /api/v1/diagnosticos`: `criar_diagnostico`
- `GET /api/v1/diagnosticos/{diagnostico_id}`: `consultar_diagnostico`
- `PUT /api/v1/diagnosticos/{diagnostico_id}/mercados`: `atualizar_mercados`
- `PUT /api/v1/diagnosticos/{diagnostico_id}/respostas`: `registrar_respostas`
- `POST /api/v1/diagnosticos/{diagnostico_id}/calcular`: `calcular_diagnostico`
- `GET /api/v1/diagnosticos/{diagnostico_id}/resultado`: `consultar_resultado`
- `POST /api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida`: `executar_pesquisa_assistida`
- `POST /api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida/automatica`: `executar_pesquisa_assistida_automatica`
- `GET /api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida`: `consultar_pesquisa_assistida`

## Sequência principal

1. Criar uma sessão de diagnóstico.
2. Registrar produto e mercados.
3. Enviar respostas do checklist.
4. Calcular o diagnóstico determinístico.
5. Opcionalmente executar pesquisa assistida manual ou automática.
6. Consultar a pesquisa complementar persistida.

## Regra de independência

O resultado complementar pode acrescentar requisitos confirmados ou ressalvas, mas não pode alterar o score ou o nível calculado pelo motor determinístico.
