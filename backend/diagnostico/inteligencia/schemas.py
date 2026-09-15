from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, model_validator

ISO3 = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Z]{3}$")]
NCM = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{8}$")]
HS6 = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]

TipoFonte = Literal[
    "OFICIAL",
    "GOVERNAMENTAL_COMPLEMENTAR",
    "ORGANISMO_INTERNACIONAL",
    "PRIVADA_COMPLEMENTAR",
]
CategoriaRequisito = Literal[
    "CERTIFICACOES",
    "LICENCAS",
    "ROTULAGEM",
    "EMBALAGEM",
    "DOCUMENTACAO",
    "RESTRICOES",
    "AUTORIDADES",
    "OUTROS",
]
Obrigatoriedade = Literal[
    "OBRIGATORIO",
    "POSSIVELMENTE_OBRIGATORIO",
    "VOLUNTARIO",
    "NAO_DETERMINADO",
]
StatusEvidencia = Literal[
    "CONFIRMADO_EM_FONTE_OFICIAL",
    "ENCONTRADO_EM_FONTE_COMPLEMENTAR",
    "NAO_CONFIRMADO",
]
Aplicabilidade = Literal[
    "APLICAVEL",
    "POSSIVELMENTE_APLICAVEL",
    "NAO_DETERMINADA",
]
StatusAnalise = Literal[
    "CONCLUIDA",
    "CONCLUIDA_COM_RESSALVAS",
    "INDISPONIVEL",
    "ERRO",
]


class InteligenciaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProdutoPesquisa(InteligenciaSchema):
    ncm: NCM
    hs6: HS6
    descricao: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validar_ncm_hs6(self):
        if not self.ncm.startswith(self.hs6):
            raise ValueError("O HS6 deve corresponder aos seis primeiros dígitos da NCM.")
        return self


class PaisPesquisa(InteligenciaSchema):
    iso3: ISO3
    nome: str = Field(min_length=2, max_length=200)


class EvidenciaMercado(InteligenciaSchema):
    evidencia_id: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9._-]+$")
    fonte_titulo: str = Field(min_length=3, max_length=500)
    fonte_url: HttpUrl
    tipo_fonte: TipoFonte
    consultado_em: date
    trecho: str = Field(min_length=10, max_length=10000)
    idioma: str | None = Field(default=None, min_length=2, max_length=20)


class EntradaInteligenciaMercado(InteligenciaSchema):
    produto: ProdutoPesquisa
    pais: PaisPesquisa
    evidencias: list[EvidenciaMercado] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validar_evidencias_unicas(self):
        ids = [e.evidencia_id for e in self.evidencias]
        if len(ids) != len(set(ids)):
            raise ValueError("Os identificadores das evidências não podem se repetir.")
        return self


class RequisitoMercado(InteligenciaSchema):
    categoria: CategoriaRequisito
    titulo: str = Field(min_length=3, max_length=500)
    descricao: str = Field(min_length=10, max_length=3000)
    obrigatoriedade: Obrigatoriedade
    status_evidencia: StatusEvidencia
    aplicabilidade: Aplicabilidade
    autoridade: str | None = Field(default=None, max_length=500)
    fontes_ids: list[str] = Field(min_length=1, max_length=10)


class SaidaInteligenciaMercado(InteligenciaSchema):
    pais_iso3: ISO3
    status: StatusAnalise
    resumo: str = Field(min_length=3, max_length=4000)
    requisitos: list[RequisitoMercado] = Field(default_factory=list, max_length=100)
    nao_confirmados: list[str] = Field(default_factory=list, max_length=100)
    alertas: list[str] = Field(default_factory=list, max_length=50)
    evidencias_disponiveis: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validar_referencias(self):
        disponiveis = set(self.evidencias_disponiveis)
        for requisito in self.requisitos:
            ausentes = set(requisito.fontes_ids) - disponiveis
            if ausentes:
                raise ValueError(
                    f"O requisito '{requisito.titulo}' referencia evidências inexistentes: "
                    + ", ".join(sorted(ausentes))
                )
        if self.status == "INDISPONIVEL" and self.requisitos:
            raise ValueError("Uma análise indisponível não pode conter requisitos.")
        return self
