# Produção e handoff seguro

O Módulo Básico cria a jornada e solicita um código descartável para a origem autorizada do Módulo Diagnóstico. O código expira rapidamente e só pode ser consumido uma vez.

Variáveis obrigatórias em produção:

```env
EXPORTAI_AMBIENTE=PRODUCAO
EXPORTAI_DATABASE_URL=postgresql+psycopg://...
EXPORTAI_CORS_ORIGINS=https://exportai-brazil.netlify.app,https://export-recommend-wiz.lovable.app
EXPORTAI_HANDOFF_DESTINOS=https://DOMINIO-DO-DIAGNOSTICO.lovable.app
EXPORTAI_HANDOFF_SECRET=segredo-aleatorio-com-pelo-menos-32-caracteres
EXPORTAI_HANDOFF_TTL_SEGUNDOS=120
```

O segredo e as chaves de IA devem ficar apenas no provedor da API.
