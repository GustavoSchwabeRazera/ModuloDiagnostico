# Migração do Módulo Diagnóstico para PostgreSQL

## Estratégia

- Produção: PostgreSQL via `EXPORTAI_DATABASE_URL`.
- Desenvolvimento e testes: SQLite continua permitido.
- Migrações: Alembic.
- Driver: Psycopg 3.

## Instalação

```powershell
python -m pip install -r requirements.txt
```

## Configuração local com PostgreSQL

Crie um arquivo `.env` não versionado:

```env
EXPORTAI_DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/exportai
```

## Aplicar migrações

```powershell
python -m alembic upgrade head
python -m alembic current
```

## Produção

Configure a URL do banco como segredo no provedor de nuvem. Não salve credenciais no GitHub, no Lovable ou em arquivos versionados.

## Observação sobre o SQLite anterior

O código 41 não copia automaticamente sessões locais existentes para o PostgreSQL. Para a Demo, recomenda-se começar com o banco PostgreSQL vazio. Se houver dados locais que precisem ser preservados, faça uma migração de dados específica e auditada.
