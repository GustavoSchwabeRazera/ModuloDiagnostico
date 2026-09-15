import os,warnings
from diagnostico.inteligencia.busca.provedor_desativado import ProvedorBuscaDesativado
from diagnostico.inteligencia.busca.provedor_searxng import ProvedorBuscaSearXNG
def criar_provedor_busca(nome=None):
    n=(nome or os.getenv("EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR","DESATIVADO")).strip().upper()
    if n=="DESATIVADO": return ProvedorBuscaDesativado()
    if n=="SEARXNG": return ProvedorBuscaSearXNG()
    warnings.warn(f"Provedor de busca '{n}' indisponível; usando DESATIVADO.",RuntimeWarning,stacklevel=2)
    return ProvedorBuscaDesativado()
