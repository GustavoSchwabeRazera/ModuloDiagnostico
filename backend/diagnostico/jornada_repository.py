from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from diagnostico.database import criar_fabrica_sessoes
from diagnostico.jornada_models import JornadaModel


class RepositorioJornadas:
    def __init__(self, fabrica_sessoes: sessionmaker | None = None):
        self.fabrica = fabrica_sessoes or criar_fabrica_sessoes()

    def criar(self, dados: dict) -> dict:
        row = JornadaModel(
            id=dados["journey_id"],
            resume_token_hash=dados["resume_token_hash"],
            status=dados["status"],
            produto_json=json.dumps(dados["produto"], ensure_ascii=False),
            mercados_basico_json=json.dumps(dados["mercados_basico"], ensure_ascii=False),
            mercados_escolhidos_json=json.dumps(dados.get("mercados_escolhidos", [])),
            diagnostico_id=dados.get("diagnostico_id"),
            criado_em=dados["criado_em"],
            atualizado_em=dados["atualizado_em"],
            ultimo_acesso_em=dados.get("ultimo_acesso_em"),
            expira_em=dados["expira_em"],
        )
        with self.fabrica() as session:
            session.add(row)
            session.commit()
        return dados

    def obter(self, journey_id: str) -> dict | None:
        with self.fabrica() as session:
            row = session.get(JornadaModel, journey_id)
            return self._to_dict(row) if row else None

    def salvar(self, dados: dict) -> dict:
        with self.fabrica() as session:
            row = session.get(JornadaModel, dados["journey_id"])
            if not row:
                raise KeyError("Jornada não encontrada.")
            row.status = dados["status"]
            row.mercados_escolhidos_json = json.dumps(dados.get("mercados_escolhidos", []))
            row.diagnostico_id = dados.get("diagnostico_id")
            row.atualizado_em = dados["atualizado_em"]
            row.ultimo_acesso_em = dados.get("ultimo_acesso_em")
            row.expira_em = dados["expira_em"]
            session.commit()
        return dados

    def limpar_expiradas(self, agora: datetime | None = None) -> int:
        agora = agora or datetime.now(timezone.utc)
        with self.fabrica() as session:
            result = session.execute(delete(JornadaModel).where(JornadaModel.expira_em < agora))
            session.commit()
            return int(result.rowcount or 0)

    @staticmethod
    def _to_dict(row: JornadaModel) -> dict:
        return {
            "journey_id": row.id,
            "resume_token_hash": row.resume_token_hash,
            "status": row.status,
            "produto": json.loads(row.produto_json),
            "mercados_basico": json.loads(row.mercados_basico_json),
            "mercados_escolhidos": json.loads(row.mercados_escolhidos_json or "[]"),
            "diagnostico_id": row.diagnostico_id,
            "criado_em": row.criado_em,
            "atualizado_em": row.atualizado_em,
            "ultimo_acesso_em": row.ultimo_acesso_em,
            "expira_em": row.expira_em,
        }


repositorio_jornadas = RepositorioJornadas()
