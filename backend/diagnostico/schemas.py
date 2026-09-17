from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

NCM = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{8}$")]
HS6 = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]
ISO3 = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Z]{3}$"),
]

FaixaConfianca = Literal["LIMITADA", "MODERADA", "ALTA"]
TipoOportunidade = Literal[
    "MERCADO_ATUAL_COM_WITS",
    "NOVA_OPORTUNIDADE_WITS",
    "HISTORICO_SEM_WITS",
]
StatusResposta = Literal[
    "CONCLUIDO",
    "EM_ANDAMENTO",
    "NAO_INICIADO",
    "NAO_SEI",
    "NAO_SE_APLICA",
]
Criticidade = Literal["BLOQUEADOR", "ESSENCIAL", "RECOMENDADO"]
NivelProntidao = Literal[
    "INICIAL",
    "EM_PREPARACAO",
    "QUASE_PRONTA",
    "PRONTA_PARA_PROSPECTAR",
]
PrioridadeAcao = Literal["ALTA", "MEDIA", "BAIXA"]
StatusPesquisa = Literal[
    "NAO_EXECUTADA",
    "EM_PROCESSAMENTO",
    "CONCLUIDA",
    "CONCLUIDA_COM_RESSALVAS",
    "INDISPONIVEL",
    "ERRO",
]


class DiagnosticoSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ProdutoDiagnostico(DiagnosticoSchema):
    ncm: NCM | None = None
    hs6: HS6
    descricao: str = Field(min_length=3, max_length=1000)

    @field_validator("ncm", "hs6", mode="before")
    @classmethod
    def manter_apenas_digitos(cls, valor):
        if valor is None:
            return None
        return "".join(caractere for caractere in str(valor) if caractere.isdigit())

    @model_validator(mode="after")
    def validar_compatibilidade_ncm_hs6(self):
        if self.ncm is not None and not self.ncm.startswith(self.hs6):
            raise ValueError("O HS6 deve corresponder aos seis primeiros dígitos da NCM.")
        return self


class MercadoBasico(DiagnosticoSchema):
    iso3: ISO3
    nome: str = Field(min_length=2, max_length=200)
    ranking_personalizado: int = Field(ge=1, le=20)
    ranking_global_no_hs6: int = Field(ge=1)
    score_exportai: float = Field(ge=0, le=100)
    faixa_confianca: FaixaConfianca
    tipo_oportunidade: TipoOportunidade


class EntradaModuloBasico(DiagnosticoSchema):
    produto: ProdutoDiagnostico
    mercados_basico: list[MercadoBasico] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validar_mercados_unicos(self):
        iso3 = [mercado.iso3 for mercado in self.mercados_basico]
        rankings = [mercado.ranking_personalizado for mercado in self.mercados_basico]
        if len(iso3) != len(set(iso3)):
            raise ValueError("Os mercados do Módulo Básico não podem repetir ISO3.")
        if len(rankings) != len(set(rankings)):
            raise ValueError("O ranking personalizado não pode ter posições repetidas.")
        if sorted(rankings) != list(range(1, len(rankings) + 1)):
            raise ValueError("O ranking personalizado deve começar em 1 e não possuir lacunas.")
        return self


class CriarDiagnosticoRequest(EntradaModuloBasico):
    mercados_escolhidos: list[ISO3] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validar_selecao(self):
        if len(self.mercados_escolhidos) != len(set(self.mercados_escolhidos)):
            raise ValueError("A seleção do Diagnóstico não pode repetir países.")
        disponiveis = {mercado.iso3 for mercado in self.mercados_basico}
        ausentes = [iso3 for iso3 in self.mercados_escolhidos if iso3 not in disponiveis]
        if ausentes:
            raise ValueError(
                "Os países escolhidos devem existir no resultado do Módulo Básico: "
                + ", ".join(ausentes)
            )
        return self


class AtualizarMercadosRequest(DiagnosticoSchema):
    mercados_escolhidos: list[ISO3] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validar_sem_duplicacoes(self):
        if len(self.mercados_escolhidos) != len(set(self.mercados_escolhidos)):
            raise ValueError("A seleção do Diagnóstico não pode repetir países.")
        return self


class AcaoPendente(DiagnosticoSchema):
    titulo: str = Field(min_length=3, max_length=300)
    descricao: str = Field(min_length=3, max_length=2000)
    prioridade: PrioridadeAcao


class ItemChecklist(DiagnosticoSchema):
    codigo: str = Field(pattern=r"^[A-Z0-9_]+$")
    versao: str
    dimensao: str = Field(pattern=r"^[A-Z0-9_]+$")
    ordem: int = Field(ge=1)
    pergunta: str = Field(min_length=5, max_length=1000)
    explicacao: str = Field(min_length=5, max_length=2000)
    criticidade: Criticidade
    peso: int = Field(ge=1)
    aplicabilidade: str
    ativo: bool
    acao_quando_pendente: AcaoPendente


class CatalogoChecklist(DiagnosticoSchema):
    versao: str
    dimensoes: list[str] = Field(min_length=1)
    itens: list[ItemChecklist] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_catalogo(self):
        codigos = [item.codigo for item in self.itens]
        if len(codigos) != len(set(codigos)):
            raise ValueError("O catálogo contém códigos de item duplicados.")
        dimensoes = set(self.dimensoes)
        invalidas = sorted({item.dimensao for item in self.itens} - dimensoes)
        if invalidas:
            raise ValueError("Itens usam dimensões não declaradas: " + ", ".join(invalidas))
        for dimensao in dimensoes:
            ordens = [item.ordem for item in self.itens if item.dimensao == dimensao]
            if len(ordens) != len(set(ordens)):
                raise ValueError(f"Há ordens duplicadas na dimensão {dimensao}.")
        return self


class RespostaChecklist(DiagnosticoSchema):
    item_codigo: str = Field(pattern=r"^[A-Z0-9_]+$")
    status: StatusResposta
    observacao: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def exigir_justificativa_para_nao_se_aplica(self):
        if self.status == "NAO_SE_APLICA" and not self.observacao:
            raise ValueError("Informe uma justificativa para NAO_SE_APLICA.")
        return self


class RegistrarRespostasRequest(DiagnosticoSchema):
    catalogo_versao: str
    respostas: list[RespostaChecklist] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_itens_unicos(self):
        codigos = [resposta.item_codigo for resposta in self.respostas]
        if len(codigos) != len(set(codigos)):
            raise ValueError("Cada item do checklist deve possuir apenas uma resposta.")
        return self


class ScoreDimensao(DiagnosticoSchema):
    dimensao: str
    score: float = Field(ge=0, le=100)
    itens_aplicaveis: int = Field(ge=0)
    itens_concluidos: int = Field(ge=0)


class BloqueadorDiagnostico(DiagnosticoSchema):
    codigo: str
    status: StatusResposta
    mensagem: str


class AcaoPlano(DiagnosticoSchema):
    ordem: int = Field(ge=1)
    item_codigo: str
    dimensao: str
    criticidade: Criticidade
    status: StatusResposta
    titulo: str
    descricao: str
    prioridade: PrioridadeAcao


class PesquisaMercadoResumo(DiagnosticoSchema):
    pais_iso3: ISO3
    status: StatusPesquisa = "NAO_EXECUTADA"
    requisitos_confirmados: int = Field(default=0, ge=0)
    requisitos_com_ressalvas: int = Field(default=0, ge=0)
    nao_confirmados: int = Field(default=0, ge=0)


class ResultadoDiagnostico(DiagnosticoSchema):
    catalogo_versao: str
    score_geral: float = Field(ge=0, le=100)
    nivel: NivelProntidao
    scores_dimensoes: list[ScoreDimensao]
    possui_bloqueadores: bool
    bloqueadores: list[BloqueadorDiagnostico]
    plano_acao: list[AcaoPlano]
    pesquisas_mercado: list[PesquisaMercadoResumo] = Field(max_length=3)
    alerta_vendas: str | None = None
    bloqueia_modulo_vendas: Literal[False] = False

    @model_validator(mode="after")
    def validar_coerencia_bloqueadores(self):
        if self.possui_bloqueadores != bool(self.bloqueadores):
            raise ValueError("possui_bloqueadores deve refletir a lista de bloqueadores.")
        return self
