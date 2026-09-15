from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from threading import RLock

from sqlalchemy import delete, inspect, select, text
from sqlalchemy.engine import Engine

from diagnostico.database import Base, criar_engine, criar_fabrica_sessoes
from diagnostico.models import DiagnosticoModel


class RepositorioDiagnosticosSQLite:
    """Repositório persistente compatível com a interface usada pelos endpoints."""

    def __init__(self, engine: Engine | None = None, criar_tabelas: bool = True) -> None:
        self.engine = engine or criar_engine()
        self.SessionLocal = criar_fabrica_sessoes(self.engine)
        self._lock = RLock()
        if criar_tabelas:
            Base.metadata.create_all(self.engine)
            self._migrar_pesquisa_assistida()

    def _migrar_pesquisa_assistida(self) -> None:
        colunas = {c["name"] for c in inspect(self.engine).get_columns("diagnosticos")}
        if "pesquisa_assistida_json" not in colunas:
            with self.engine.begin() as conexao:
                conexao.execute(
                    text("ALTER TABLE diagnosticos ADD COLUMN pesquisa_assistida_json TEXT")
                )

    @staticmethod
    def _json(valor) -> str:
        return json.dumps(valor, ensure_ascii=False, separators=(",", ":"), default=str)

    @staticmethod
    def _carregar(valor: str | None):
        return None if valor is None else json.loads(valor)

    @classmethod
    def _para_modelo(cls, sessao: dict) -> DiagnosticoModel:
        return DiagnosticoModel(
            diagnostico_id=sessao["diagnostico_id"],
            status=sessao["status"],
            catalogo_versao=sessao["catalogo_versao"],
            produto_json=cls._json(sessao["produto"]),
            mercados_basico_json=cls._json(sessao["mercados_basico"]),
            mercados_escolhidos_json=cls._json(sessao["mercados_escolhidos"]),
            respostas_json=cls._json(sessao["respostas"]),
            resultado_json=cls._json(sessao["resultado"]) if sessao.get("resultado") is not None else None,
            pesquisa_assistida_json=cls._json(sessao["pesquisa_assistida"]) if sessao.get("pesquisa_assistida") is not None else None,
            criado_em=sessao["criado_em"],
            atualizado_em=sessao["atualizado_em"],
        )

    @classmethod
    def _para_dict(cls, modelo: DiagnosticoModel) -> dict:
        return {
            "diagnostico_id": modelo.diagnostico_id,
            "status": modelo.status,
            "catalogo_versao": modelo.catalogo_versao,
            "produto": cls._carregar(modelo.produto_json),
            "mercados_basico": cls._carregar(modelo.mercados_basico_json),
            "mercados_escolhidos": cls._carregar(modelo.mercados_escolhidos_json),
            "respostas": cls._carregar(modelo.respostas_json),
            "resultado": cls._carregar(modelo.resultado_json),
            "pesquisa_assistida": cls._carregar(modelo.pesquisa_assistida_json),
            "criado_em": modelo.criado_em,
            "atualizado_em": modelo.atualizado_em,
        }

    def criar(self, sessao: dict) -> dict:
        with self._lock, self.SessionLocal() as db:
            if db.get(DiagnosticoModel, sessao["diagnostico_id"]) is not None:
                raise ValueError(f"Diagnóstico já existe: {sessao['diagnostico_id']}")
            db.add(self._para_modelo(sessao))
            db.commit()
        return deepcopy(sessao)

    def obter(self, identificador: str) -> dict | None:
        with self.SessionLocal() as db:
            modelo = db.get(DiagnosticoModel, identificador)
            return None if modelo is None else self._para_dict(modelo)

    def salvar(self, identificador: str, sessao: dict) -> dict:
        with self._lock, self.SessionLocal() as db:
            modelo = db.get(DiagnosticoModel, identificador)
            if modelo is None:
                raise KeyError(identificador)
            atualizado = self._para_modelo(sessao)
            modelo.status = atualizado.status
            modelo.catalogo_versao = atualizado.catalogo_versao
            modelo.produto_json = atualizado.produto_json
            modelo.mercados_basico_json = atualizado.mercados_basico_json
            modelo.mercados_escolhidos_json = atualizado.mercados_escolhidos_json
            modelo.respostas_json = atualizado.respostas_json
            modelo.resultado_json = atualizado.resultado_json
            modelo.pesquisa_assistida_json = atualizado.pesquisa_assistida_json
            modelo.criado_em = atualizado.criado_em
            modelo.atualizado_em = atualizado.atualizado_em
            db.commit()
        return deepcopy(sessao)

    def limpar(self) -> None:
        with self._lock, self.SessionLocal() as db:
            db.execute(delete(DiagnosticoModel))
            db.commit()

    def contar(self) -> int:
        with self.SessionLocal() as db:
            return len(db.scalars(select(DiagnosticoModel.diagnostico_id)).all())


repositorio_diagnosticos = RepositorioDiagnosticosSQLite()
