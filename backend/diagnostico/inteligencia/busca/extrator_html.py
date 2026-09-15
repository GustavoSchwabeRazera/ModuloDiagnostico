import re
from bs4 import BeautifulSoup
def extrair_html(conteudo):
    soup=BeautifulSoup(conteudo,'html.parser')
    for tag in soup(['script','style','noscript','svg','nav','footer']): tag.decompose()
    titulo=soup.title.get_text(' ',strip=True) if soup.title else 'Documento sem título'
    raiz=soup.find('main') or soup.find('article') or soup.body or soup
    texto=re.sub(r'\s+',' ',raiz.get_text(' ',strip=True)).strip()
    return titulo,texto
