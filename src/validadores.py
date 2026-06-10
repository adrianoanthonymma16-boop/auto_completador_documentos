"""
Validação de formatos de arquivo
"""

import os
from config import MODELO_EXTENSOES, ANEXO_EXTENSOES


def validar_extensao(caminho, tipo='modelo'):
    """
    Valida se a extensão do arquivo é suportada
    
    Args:
        caminho (str): Caminho do arquivo
        tipo (str): 'modelo' ou 'anexo'
    
    Returns:
        tuple: (valido, extensao, mensagem)
    """
    ext = os.path.splitext(caminho)[1].lower()
    
    if tipo == 'modelo':
        if ext in MODELO_EXTENSOES:
            return True, ext, f"Formato {MODELO_EXTENSOES[ext]} suportado"
        else:
            suportados = ", ".join(MODELO_EXTENSOES.keys())
            return False, ext, f"Formato {ext} não suportado. Use: {suportados}"
    
    elif tipo == 'anexo':
        if ext in ANEXO_EXTENSOES:
            return True, ext, f"Formato {ANEXO_EXTENSOES[ext]} suportado"
        else:
            suportados = ", ".join(ANEXO_EXTENSOES.keys())
            return False, ext, f"Formato {ext} não suportado. Use: {suportados}"
    
    return False, None, "Tipo de validação inválido"


def obter_filetypes_modelo():
    """Retorna os filetypes para o filedialog de modelo"""
    return [
        ("Documentos modelo", "*.odt *.docx"),
        ("ODT (LibreOffice)", "*.odt"),
        ("DOCX (Microsoft Word)", "*.docx")
    ]


def obter_filetypes_anexo():
    """Retorna os filetypes para o filedialog de anexo"""
    filetypes = [
        ("Documentos fonte", "*.jpg *.jpeg *.png *.tiff *.pdf *.webp"),
        ("Imagens", "*.jpg *.jpeg *.png *.tiff *.webp"),
        ("PDF", "*.pdf"),
    ]
    return filetypes