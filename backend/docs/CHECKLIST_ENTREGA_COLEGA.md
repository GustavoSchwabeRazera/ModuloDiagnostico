# Checklist de entrega ao colega

## Entregar

- pasta `backend`;
- `Dockerfile`, `start.sh`, `requirements.txt` e `alembic.ini`;
- migrações;
- `.env.example`;
- documentação em `docs`;
- `openapi-exportai.json`;
- manifesto final;
- evidência da suíte de testes aprovada.

## Não entregar

- `.env`;
- chaves Gemini ou Groq;
- senha do PostgreSQL;
- `EXPORTAI_HANDOFF_SECRET` real;
- bancos SQLite com sessões;
- `.venv`, caches, logs e backups `*.bak`.

## Antes de publicar

- substituir o domínio provisório do Diagnóstico;
- gerar segredos novos no provedor;
- configurar somente origens HTTPS reais em produção;
- confirmar PostgreSQL e migrações;
- testar o fluxo entre os dois projetos Lovable.
