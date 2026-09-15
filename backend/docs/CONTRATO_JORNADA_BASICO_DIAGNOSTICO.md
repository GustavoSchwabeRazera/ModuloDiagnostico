# Contrato da jornada anônima

## Criação pelo Módulo Básico

`POST /api/v1/jornadas`

A resposta devolve `journey_id` e `resume_token`. O token é mostrado uma única vez e não é armazenado em texto puro.

## Transporte entre os módulos

- O `journey_id` pode ser transportado como parâmetro de navegação.
- O `resume_token` não deve ser colocado na URL.
- O frontend deve enviá-lo no cabeçalho `Authorization: Bearer <token>`.
- O frontend não deve registrar o token em analytics ou logs.

## Retomada

`GET /api/v1/jornadas/{journey_id}`

## Seleção de mercados

`PUT /api/v1/jornadas/{journey_id}/mercados`

Apenas 1 a 3 ISO3 presentes no resultado do Módulo Básico são aceitos.

## Preparação do Diagnóstico

`GET /api/v1/jornadas/{journey_id}/diagnostico-payload`

O frontend usa o payload devolvido para criar a sessão no endpoint já existente do Módulo Diagnóstico e, depois, associa o `diagnostico_id` à jornada.

## Retenção

Configurada por `EXPORTAI_SESSAO_RETENCAO_HORAS`, com padrão de 24 horas e limite máximo interno de 168 horas.
