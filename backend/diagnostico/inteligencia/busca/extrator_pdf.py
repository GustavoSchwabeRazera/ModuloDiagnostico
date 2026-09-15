from io import BytesIO
from pypdf import PdfReader
class ErroPDF(RuntimeError): pass
def extrair_pdf(conteudo,max_paginas=40,max_stream_bytes=20_000_000):
    reader=PdfReader(BytesIO(conteudo)); partes=[]
    for pagina in reader.pages[:max_paginas]:
        fluxo=pagina.get_contents()
        if fluxo is not None and len(fluxo.get_data())>max_stream_bytes: raise ErroPDF('Fluxo interno do PDF acima do limite.')
        texto=pagina.extract_text() or ''
        if texto.strip(): partes.append(texto.strip())
    final='\n'.join(partes).strip()
    if len(final)<10: raise ErroPDF('PDF sem texto extraível; OCR não está habilitado.')
    titulo=(reader.metadata.title if reader.metadata and reader.metadata.title else 'Documento PDF')
    return titulo,final
