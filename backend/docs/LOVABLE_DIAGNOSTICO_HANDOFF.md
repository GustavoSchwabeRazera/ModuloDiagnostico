# Handoff para o Lovable do Módulo Diagnóstico

## Materiais

- Contrato completo: `docs/openapi-exportai.json`
- Backend publicado: substituir `API_BASE_URL` pela URL HTTPS real.
- Autorização de jornada: `Authorization: Bearer <resume_token>`.

## Fluxo do Módulo Básico

1. Após gerar recomendações, enviar produto e até 20 mercados para `POST /api/v1/jornadas`.
2. Guardar temporariamente `journey_id` e `resume_token` no contexto do Módulo Básico.
3. Solicitar `POST /api/v1/jornadas/{journey_id}/handoff`, usando o Bearer token.
4. Navegar ao Módulo Diagnóstico levando somente `handoff_code`.
5. Não enviar Gemini, Groq, PostgreSQL ou outros segredos ao frontend.

## Fluxo do Módulo Diagnóstico

1. Ler `handoff_code` na chegada.
2. Trocar o código uma única vez em `POST /api/v1/jornadas/handoff/trocar`.
3. Remover o código da barra de endereço com `history.replaceState`.
4. Manter `journey_id` e `resume_token` apenas pelo período necessário à jornada.
5. Recuperar a jornada e apresentar os mercados trazidos pelo Básico.
6. Permitir a seleção de 1 a 3 mercados.
7. Criar o diagnóstico usando o payload preparado pela API.
8. Associar o `diagnostico_id` à jornada.

## Telas

1. Boas-vindas e resumo do produto.
2. Seleção de até três mercados.
3. Checklist em seis dimensões com salvamento parcial.
4. Revisão.
5. Resultado com score, nível, dimensões, impeditivos e plano de ação.
6. Pesquisa complementar, quando disponível.
7. Acesso não bloqueante ao Módulo Vendas.

## Estados obrigatórios

- carregando;
- sem jornada;
- handoff inválido, expirado ou consumido;
- jornada expirada;
- erro de validação;
- erro temporário da pesquisa complementar;
- diagnóstico salvo;
- retomada de diagnóstico existente.

## Prompt inicial sugerido ao Lovable

Use o arquivo `openapi-exportai.json` como contrato da API. Crie um frontend responsivo para o Módulo Diagnóstico do ExportAI. Não replique regras de score no frontend. Consuma todos os cálculos do backend. Implemente o fluxo de handoff descartável, seleção de até três mercados, checklist com salvamento parcial, resultado, impeditivos e plano de ação. Nunca exponha segredos ou chaves de IA.
