from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from diagnostico.inteligencia.fontes_schemas import DocumentoRecuperado
from diagnostico.inteligencia.schemas import ISO3, SaidaInteligenciaMercado


class OrquestradorSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DocumentosPorPais(OrquestradorSchema):
    pais_iso3: ISO3
    documentos: list[DocumentoRecuperado] = Field(default_factory=list, max_length=100)


class ExecutarPesquisaAssistidaRequest(OrquestradorSchema):
    documentos_por_pais: list[DocumentosPorPais] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validar_paises_unicos(self):
        paises = [item.pais_iso3 for item in self.documentos_por_pais]
        if len(paises) != len(set(paises)):
            raise ValueError("Cada país deve aparecer apenas uma vez em documentos_por_pais.")
        return self


class PesquisaPaisResultado(OrquestradorSchema):
    pais_iso3: ISO3
    status: Literal[
        "CONCLUIDA",
        "CONCLUIDA_COM_RESSALVAS",
        "INDISPONIVEL",
        "ERRO",
    ]
    evidencias_encontradas: int = Field(ge=0)
    descartes: list[str]
    analise: SaidaInteligenciaMercado
    erro: str | None = None


class ResultadoPesquisaAssistida(OrquestradorSchema):
    diagnostico_id: str
    provedor: str
    paises_solicitados: int = Field(ge=1, le=3)
    paises_concluidos: int = Field(ge=0, le=3)
    paises_com_erro: int = Field(ge=0, le=3)
    resultados: list[PesquisaPaisResultado] = Field(min_length=1, max_length=3)
    score_geral_antes: float | None = Field(default=None, ge=0, le=100)
    score_geral_depois: float | None = Field(default=None, ge=0, le=100)
    pontuacao_preservada: bool
    executado_em: datetime
