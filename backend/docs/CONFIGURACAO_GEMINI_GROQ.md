# Configuração Gemini e Groq

## Dependências

- `google-genai`
- `groq`

## Variáveis

```env
EXPORTAI_DIAGNOSTICO_IA_PROVEDOR=DESATIVADO
EXPORTAI_DIAGNOSTICO_IA_FALLBACK=
GEMINI_API_KEY=
EXPORTAI_GEMINI_MODELO=
GROQ_API_KEY=
EXPORTAI_GROQ_MODELO=
EXPORTAI_GROQ_STRUCTURED_STRICT=false
```

As chaves devem existir apenas nos segredos do backend hospedado. Nunca devem ser enviadas ao Lovable, gravadas no repositório ou retornadas pela API.

## Ativação sugerida após testes reais

```env
EXPORTAI_DIAGNOSTICO_IA_PROVEDOR=GEMINI
EXPORTAI_DIAGNOSTICO_IA_FALLBACK=GROQ
```

## Regras

- Ambos recebem somente evidências já aprovadas pela busca controlada.
- Ambos devolvem saída validada pelo schema Pydantic existente.
- O fallback só é chamado quando o provedor primário falha.
- Ollama foi mantido apenas no histórico e é redirecionado para o modo desativado.
- Nenhum provedor recebe ou altera score, pesos ou nível de prontidão.
