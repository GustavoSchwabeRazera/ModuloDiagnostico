# Teste ponta a ponta

## Backend

- `/health` responde com sucesso.
- migração atual é `20260911_03`;
- CORS aceita os três domínios publicados e rejeita origem não autorizada;
- nenhum segredo aparece em respostas ou logs.

## Jornada

- criar jornada com 1 e com 20 mercados;
- rejeitar NCM e HS6 inconsistentes;
- recuperar jornada com token válido;
- rejeitar token inválido e jornada expirada;
- selecionar 1 e 3 mercados;
- rejeitar 4 mercados e ISO3 fora do Básico.

## Handoff

- criar para destino autorizado;
- rejeitar destino diferente;
- trocar uma vez;
- rejeitar reutilização;
- rejeitar código expirado.

## Diagnóstico

- salvar respostas parciais;
- retomar a sessão;
- calcular resultado com e sem impeditivos;
- preservar score quando IA ou busca estiver indisponível;
- permitir acesso ao Módulo Vendas com aviso não bloqueante.

## IA

- testar Gemini isoladamente;
- testar Groq isoladamente;
- testar fallback;
- validar JSON contra Pydantic;
- confirmar que a IA não altera score, pesos ou criticidades.
