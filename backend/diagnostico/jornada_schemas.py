from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProdutoJornada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ncm: str | None = None
    hs6: str
    descricao: str = Field(min_length=3, max_length=500)

    @field_validator("ncm", mode="before")
    @classmethod
    def validar_ncm(cls, value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        value = re.sub(r"\D", "", value)
        if len(value) != 8:
            raise ValueError("NCM deve conter 8 dígitos.")
        return value

    @field_validator("hs6")
    @classmethod
    def validar_hs6(cls, value: str) -> str:
        value = re.sub(r"\D", "", value)
        if len(value) != 6:
            raise ValueError("HS6 deve conter 6 dígitos.")
        return value

    @model_validator(mode="after")
    def validar_relacao(self):
        if self.ncm is not None and not self.ncm.startswith(self.hs6):
            raise ValueError("HS6 deve corresponder aos seis primeiros dígitos da NCM.")
        return self


class MercadoJornada(BaseModel):
    model_config = ConfigDict(extra="allow")
    iso3: str
    nome: str = Field(min_length=2, max_length=120)
    ranking_personalizado: int = Field(ge=1, le=20)
    ranking_global_no_hs6: int | None = Field(default=None, ge=1)
    score_exportai: float = Field(ge=0, le=100)
    faixa_confianca: str
    tipo_oportunidade: str

    @field_validator("iso3")
    @classmethod
    def validar_iso3(cls, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", value):
            raise ValueError("ISO3 deve ter três letras.")
        return value


class CriarJornadaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    produto: ProdutoJornada
    mercados_basico: list[MercadoJornada] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validar_mercados(self):
        iso3 = [m.iso3 for m in self.mercados_basico]
        rankings = [m.ranking_personalizado for m in self.mercados_basico]
        if len(iso3) != len(set(iso3)):
            raise ValueError("Mercados do Básico não podem repetir ISO3.")
        if len(rankings) != len(set(rankings)):
            raise ValueError("Rankings personalizados não podem se repetir.")
        return self


class CriarJornadaResponse(BaseModel):
    journey_id: str
    resume_token: str
    status: str
    expira_em: datetime


class SelecionarMercadosRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mercados_escolhidos: list[str] = Field(min_length=1, max_length=3)

    @field_validator("mercados_escolhidos")
    @classmethod
    def validar_lista(cls, values: list[str]) -> list[str]:
        normalized = [v.strip().upper() for v in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Mercados escolhidos não podem se repetir.")
        if any(not re.fullmatch(r"[A-Z]{3}", v) for v in normalized):
            raise ValueError("Cada mercado deve ser um ISO3 válido.")
        return normalized


class AssociarDiagnosticoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnostico_id: str = Field(min_length=36, max_length=36)


class JornadaPublica(BaseModel):
    journey_id: str
    status: str
    produto: dict
    mercados_basico: list[dict]
    mercados_escolhidos: list[str]
    diagnostico_id: str | None
    criado_em: datetime
    atualizado_em: datetime
    ultimo_acesso_em: datetime | None
    expira_em: datetime


class PrepararDiagnosticoResponse(BaseModel):
    journey_id: str
    diagnostico_payload: dict
    status: Literal["PRONTA_PARA_DIAGNOSTICO"]
