# ExportAI Backend

Backend FastAPI do ExportAI, incluindo recomendações de mercados e o módulo de
Diagnóstico da Sprint 8. O diagnóstico é determinístico; IA e pesquisa web são
camadas complementares e não alteram pontuação, pesos ou criticidades.

## Executar localmente

No PowerShell, a partir de `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe start.py
```

- API: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`

## Produção

1. Configure PostgreSQL e HTTPS no provedor escolhido.
2. Copie `.env.production.example` para a configuração de variáveis do
   provedor e substitua todos os placeholders por valores reais.
3. Configure somente origens HTTPS publicadas em `EXPORTAI_CORS_ORIGINS` e o
   domínio do Diagnóstico em `EXPORTAI_HANDOFF_DESTINOS`.
4. Publique com o `Dockerfile` ou com `docker compose`, fornecendo um `.env`
   local que nunca deve ser versionado.

O processo de inicialização aplica `alembic upgrade head` antes de servir a
API. Consulte [docs/DEPLOY_NUVEM.md](docs/DEPLOY_NUVEM.md) para o checklist
completo.
