import ipaddress,socket
from urllib.parse import urlparse
class ErroURL(ValueError): pass
def validar_url(url,dominios,seguir_subdominios=True,resolver_dns=False):
    p=urlparse(str(url)); host=(p.hostname or '').lower().rstrip('.')
    if p.scheme!='https': raise ErroURL('Somente HTTPS é permitido.')
    if not host: raise ErroURL('URL sem domínio.')
    if host in {'localhost','localhost.localdomain'}: raise ErroURL('Endereço local bloqueado.')
    ok=any(host==d.lower().rstrip('.') or (seguir_subdominios and host.endswith('.'+d.lower().rstrip('.'))) for d in dominios)
    if not ok: raise ErroURL('Domínio não autorizado.')
    try:
        ips=[ipaddress.ip_address(host)]
    except ValueError:
        ips=[]
        if resolver_dns:
            ips=[ipaddress.ip_address(x[4][0]) for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)]
    if any(x.is_private or x.is_loopback or x.is_link_local or x.is_reserved or x.is_multicast for x in ips): raise ErroURL('IP privado ou local bloqueado.')
    return str(url)
