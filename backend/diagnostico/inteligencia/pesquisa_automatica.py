from __future__ import annotations
from datetime import date
from diagnostico.inteligencia.busca.downloader import DownloaderSeguro
from diagnostico.inteligencia.busca.fabrica import criar_provedor_busca
from diagnostico.inteligencia.busca.schemas import ConsultaBusca
from diagnostico.inteligencia.fontes import carregar_catalogo,montar_consultas
from diagnostico.inteligencia.orquestrador import OrquestradorPesquisaAssistida
from diagnostico.inteligencia.pesquisa_automatica_schemas import (
    EstatisticaBuscaPais,ExecutarPesquisaAutomaticaRequest,ResultadoPesquisaAutomatica,
)

class ErroPesquisaAutomatica(ValueError): pass

class ServicoPesquisaAutomatica:
    def __init__(self,repositorio,provedor_ia,provedor_busca=None,downloader=None):
        self.repositorio=repositorio
        self.provedor_ia=provedor_ia
        self.provedor_busca=provedor_busca or criar_provedor_busca()
        self.downloader=downloader or DownloaderSeguro()
        self.catalogo=carregar_catalogo()

    def executar(self,diagnostico_id:str,opcoes:ExecutarPesquisaAutomaticaRequest|dict):
        op=opcoes if isinstance(opcoes,ExecutarPesquisaAutomaticaRequest) else ExecutarPesquisaAutomaticaRequest.model_validate(opcoes)
        sessao=self.repositorio.obter(diagnostico_id)
        if sessao is None: raise ErroPesquisaAutomatica('Sessão de diagnóstico não encontrada.')
        if sessao.get('resultado') is None: raise ErroPesquisaAutomatica('Calcule o diagnóstico determinístico antes da pesquisa automática.')
        escolhidos=sessao.get('mercados_escolhidos',[])
        if not 1<=len(escolhidos)<=3: raise ErroPesquisaAutomatica('A sessão deve possuir de um a três países selecionados.')
        fonte_por_codigo={f.codigo:f for f in self.catalogo.fontes}
        documentos_por_pais=[]; estatisticas=[]
        for iso3 in escolhidos:
            consultas=montar_consultas(self.catalogo,iso3,sessao['produto']['hs6'],sessao['produto']['descricao'])
            documentos=[]; falhas=[]; urls_vistas=set(); encontradas=0
            for consulta in consultas:
                try:
                    saida=self.provedor_busca.buscar(ConsultaBusca(
                        consulta=consulta.consulta_textual,
                        dominio_permitido=consulta.dominio_restrito,
                        limite=op.maximo_resultados_por_consulta,
                    ))
                except Exception as exc:
                    falhas.append(f'Busca {consulta.fonte_codigo}: {exc}'); continue
                for item in saida.resultados:
                    url=str(item.url)
                    if url in urls_vistas: continue
                    urls_vistas.add(url); encontradas+=1
                    fonte=fonte_por_codigo[consulta.fonte_codigo]
                    try:
                        baixado=self.downloader.baixar(url,fonte.dominios_permitidos)
                        documentos.append({
                            'fonte_codigo':fonte.codigo,
                            'url':baixado['url'],
                            'titulo':baixado['titulo'] or item.titulo,
                            'texto':baixado['texto'],
                            'consultado_em':date.today().isoformat(),
                            'idioma':None,
                        })
                    except Exception as exc:
                        falhas.append(f'Download {url}: {exc}')
            documentos_por_pais.append({'pais_iso3':iso3,'documentos':documentos})
            estatisticas.append(EstatisticaBuscaPais(
                pais_iso3=iso3,consultas_executadas=len(consultas),urls_encontradas=encontradas,
                documentos_baixados=len(documentos),falhas=falhas,
            ))
        pesquisa=OrquestradorPesquisaAssistida(self.repositorio,self.provedor_ia).executar(
            diagnostico_id,{'documentos_por_pais':documentos_por_pais}
        )
        return ResultadoPesquisaAutomatica(
            busca_provedor=self.provedor_busca.nome,estatisticas=estatisticas,pesquisa=pesquisa
        )
