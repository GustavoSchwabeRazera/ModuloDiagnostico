from diagnostico.inteligencia.contratos import ProvedorInteligenciaDiagnostico
from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado, SaidaInteligenciaMercado


class ProvedorInteligenciaDesativado(ProvedorInteligenciaDiagnostico):
    nome = "DESATIVADO"

    def analisar(self, entrada: EntradaInteligenciaMercado) -> SaidaInteligenciaMercado:
        return SaidaInteligenciaMercado(
            pais_iso3=entrada.pais.iso3,
            status="INDISPONIVEL",
            resumo="A pesquisa assistida não está habilitada.",
            requisitos=[],
            nao_confirmados=[],
            alertas=[
                "A pesquisa assistida não está habilitada. O diagnóstico determinístico continua disponível."
            ],
            evidencias_disponiveis=[e.evidencia_id for e in entrada.evidencias],
        )
