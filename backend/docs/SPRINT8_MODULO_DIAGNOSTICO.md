# Sprint 8: Módulo Diagnóstico

## Objetivo

Entregar um diagnóstico de prontidão exportadora baseado em regras determinísticas e uma camada complementar opcional para pesquisa de requisitos por mercado.

## Princípio de arquitetura

O diagnóstico principal não depende de busca externa nem de modelo de linguagem.

- O motor determinístico calcula score, nível, bloqueadores e plano de ação.
- A pesquisa assistida apenas organiza evidências adicionais por país.
- A IA não calcula, não decide e não altera o score.
- Ausência de evidência não significa ausência de obrigação.
- Ausência de evidência não reduz a pontuação.
- Falhas externas não impedem a entrega do diagnóstico principal.

## Componentes entregues

- Sessões persistidas em SQLite.
- Checklist e motor determinístico.
- Contrato estruturado de inteligência.
- Catálogo controlado de fontes.
- Adaptador experimental do Ollama.
- Busca controlada com allowlist de domínios.
- Extração de HTML, texto e PDF.
- Pesquisa manual e automática por país.
- Endpoint de saúde da camada complementar.
- Testes automatizados e teste real opt-in.

## Endpoints encontrados no código

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

## Operação padrão segura

Os provedores de busca e inteligência permanecem `DESATIVADO` no `.env.example`.
