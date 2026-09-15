# Configuração da camada complementar

## Modo padrão

```env
EXPORTAI_DIAGNOSTICO_IA_PROVEDOR=DESATIVADO
EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR=DESATIVADO
EXPORTAI_TESTE_INTEGRACAO_REAL=false
```

Nesse modo, o diagnóstico principal continua operacional.

## Ollama experimental

```env
EXPORTAI_DIAGNOSTICO_IA_PROVEDOR=OLLAMA
EXPORTAI_DIAGNOSTICO_IA_MODELO=nome-exato-do-modelo
EXPORTAI_DIAGNOSTICO_OLLAMA_HOST=http://127.0.0.1:11434
```

O nome do modelo deve corresponder a um modelo instalado localmente.

## SearXNG experimental

```env
EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR=SEARXNG
EXPORTAI_DIAGNOSTICO_SEARXNG_URL=https://endereco-da-instancia
```

A instância deve permitir resposta JSON no endpoint de pesquisa.

## Teste real

```env
EXPORTAI_TESTE_INTEGRACAO_REAL=true
```

Ative apenas em ambiente controlado, com os dois provedores configurados.

## Restrições da recuperação

- Somente HTTPS.
- Somente fontes e domínios cadastrados.
- Bloqueio de localhost e redes privadas.
- Limites de tempo e tamanho.
- Redirecionamentos não são aceitos.
- PDF sem camada de texto não passa por OCR no MVP.
