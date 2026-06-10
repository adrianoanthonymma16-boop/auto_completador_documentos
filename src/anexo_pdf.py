"""
Módulo para converter PDF em imagem (primeira página)
"""

import os
from PIL import Image

# Tenta importar pypdfium2
try:
    import pypdfium2 as pdfium
    PDF_SUPORTADO = True
except ImportError:
    PDF_SUPORTADO = False


def pdf_para_imagem(caminho_pdf):
    """
    Converte a primeira página de um PDF para imagem PIL
    
    Args:
        caminho_pdf (str): Caminho do arquivo PDF
    
    Returns:
        PIL.Image: Primeira página como imagem
    
    Raises:
        Exception: Se pypdfium2 não estiver instalado ou PDF inválido
    """
    if not PDF_SUPORTADO:
        raise Exception("Suporte a PDF não disponível. Instale: pip install pypdfium2")
    
    if not os.path.exists(caminho_pdf):
        raise Exception(f"Arquivo não encontrado: {caminho_pdf}")
    
    # Abre o PDF
    pdf = pdfium.PdfDocument(caminho_pdf)
    
    if len(pdf) == 0:
        pdf.close()
        raise Exception("PDF vazio")
    
    # Pega a primeira página
    page = pdf[0]
    
    # Renderiza como imagem (scale=2 = aproximadamente 150 DPI)
    bitmap = page.render(scale=2)
    imagem = bitmap.to_pil()
    
    pdf.close()
    
    return imagem


def pdf_suportado():
    """Retorna True se suporte a PDF está disponível"""
    return PDF_SUPORTADO