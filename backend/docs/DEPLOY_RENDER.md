# Publicação do backend no Render

## O que este projeto entrega

O arquivo `../render.yaml` cria dois recursos no Render:

- `exportai-api`: serviço web Docker com health check em `/health`;
- `exportai-postgres`: banco PostgreSQL ligado à API pela rede privada do Render.

O Blueprint cria um segredo de handoff automaticamente e mantém IA e busca
complementar desativadas. Nenhuma chave de IA é necessária para a primeira
publicação.

## Publicar

1. Crie um repositório GitHub privado e envie a pasta raiz `backend-Diagnostico`,
   incluindo `render.yaml` e a pasta `backend`.
2. No Render, escolha **New > Blueprint** e conecte o repositório.
3. Na criação, informe os valores solicitados para:

   ```text
   EXPORTAI_CORS_ORIGINS=https://SEU-PROJETO.lovable.app
   EXPORTAI_HANDOFF_DESTINOS=https://SEU-PROJETO.lovable.app
   ```

   Se o Módulo Básico estiver em outro domínio, inclua-o em
   `EXPORTAI_CORS_ORIGINS`, separado por vírgula.
4. Crie o Blueprint e espere os recursos ficarem disponíveis.
5. Copie a URL HTTPS da API, no formato
   `https://exportai-api-....onrender.com`.
6. Valide os endereços abaixo:

   ```text
   https://SUA-API.onrender.com/health
   https://SUA-API.onrender.com/docs
   https://SUA-API.onrender.com/openapi.json
   ```

## Conectar ao Lovable

No projeto Lovable, configure a URL HTTPS pública do Render como base da API e
forneça `backend/docs/openapi-exportai.json` ao agente. O frontend deve enviar
requisições diretamente para essa API; não copie `EXPORTAI_DATABASE_URL`,
`EXPORTAI_HANDOFF_SECRET`, `GEMINI_API_KEY` nem `GROQ_API_KEY` para o Lovable.

Depois que o Lovable tiver sido publicado, volte ao Render e confirme que as
origens exatas do domínio publicado constam em `EXPORTAI_CORS_ORIGINS` e
`EXPORTAI_HANDOFF_DESTINOS`.

## IA complementar (opcional)

Para ativar IA após a publicação inicial, adicione no painel do Render os
segredos `GEMINI_API_KEY` e/ou `GROQ_API_KEY`, os respectivos modelos validados
e altere `EXPORTAI_DIAGNOSTICO_IA_PROVEDOR`. Não registre esses valores no Git.

## Operação

O `start.sh` executa `alembic upgrade head` antes de iniciar a API. Configure
no Render um Cron Job para executar periodicamente:

```text
python -m app.commands.limpar_sessoes_expiradas
```

Use as mesmas variáveis `EXPORTAI_DATABASE_URL` e `EXPORTAI_HANDOFF_SECRET` no
Cron Job.
