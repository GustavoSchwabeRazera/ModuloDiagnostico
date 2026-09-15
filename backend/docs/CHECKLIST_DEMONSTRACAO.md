# Checklist de demonstração da Sprint 8

## Preparação

- [ ] Ativar a `.venv`.
- [ ] Instalar `requirements.txt`.
- [ ] Manter provedores externos desativados na demonstração principal.
- [ ] Executar `python -m pytest -q`.
- [ ] Iniciar `python -m uvicorn app.main:app --reload`.

## Demonstração principal

- [ ] Abrir `/docs`.
- [ ] Criar uma sessão.
- [ ] Informar produto e mercados.
- [ ] Enviar respostas.
- [ ] Calcular o diagnóstico.
- [ ] Mostrar score, nível, bloqueadores e plano de ação.

## Demonstração complementar

- [ ] Abrir o endpoint `/api/v1/diagnosticos/complementar/saude`.
- [ ] Mostrar busca e IA como desativadas sem erro geral.
- [ ] Executar pesquisa assistida sem evidências.
- [ ] Confirmar que o score antes e depois é idêntico.
- [ ] Explicar que ausência de evidência gera ressalva, não penalização.

## Critério de aprovação

A demonstração está aprovada quando o diagnóstico determinístico funciona isoladamente e qualquer indisponibilidade da camada complementar não altera sua pontuação.
