# Deploy do ExportAI na nuvem

Para publicar no Render, use `../render.yaml` e siga `DEPLOY_RENDER.md`.

## Ordem obrigatória

1. Provisionar PostgreSQL.
2. Copiar `.env.production.example` para o cofre de variáveis do provedor e
   substituir todos os placeholders; nunca publicar esse arquivo com valores reais.
3. Configurar os segredos e variáveis do serviço.
4. Construir a imagem a partir de `backend/Dockerfile`.
5. Iniciar o serviço. O `start.sh` executa `alembic upgrade head` antes da API.
6. Confirmar `/health`, `/docs` e `/openapi.json` por HTTPS.
7. Executar a suíte de smoke tests.
8. Configurar a rotina agendada `python -m app.commands.limpar_sessoes_expiradas`.

## Variáveis obrigatórias

```env
EXPORTAI_AMBIENTE=PRODUCAO
EXPORTAI_DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@HOST:5432/BANCO
EXPORTAI_CORS_ORIGINS=https://exportai-brazil.netlify.app,https://export-recommend-wiz.lovable.app,https://DOMINIO-REAL-DO-DIAGNOSTICO.lovable.app
EXPORTAI_HANDOFF_DESTINOS=https://DOMINIO-REAL-DO-DIAGNOSTICO.lovable.app
EXPORTAI_HANDOFF_SECRET=SEGREDO-ALEATORIO-DE-PELO-MENOS-32-CARACTERES
EXPORTAI_HANDOFF_TTL_SEGUNDOS=120
EXPORTAI_SESSAO_RETENCAO_HORAS=24
```

## IA opcional

```env
EXPORTAI_DIAGNOSTICO_IA_PROVEDOR=GEMINI
EXPORTAI_DIAGNOSTICO_IA_FALLBACK=GROQ
GEMINI_API_KEY=SEGREDO
EXPORTAI_GEMINI_MODELO=MODELO-VALIDADO
GROQ_API_KEY=SEGREDO
EXPORTAI_GROQ_MODELO=MODELO-VALIDADO
EXPORTAI_GROQ_STRUCTURED_STRICT=false
```

As chaves pertencem exclusivamente ao backend. Não devem ser inseridas no Lovable, no navegador ou no repositório.

## Validação após deploy

```bash
python -m alembic current
python -m app.commands.limpar_sessoes_expiradas
```

O Alembic deve indicar `20260911_03 (head)`.
