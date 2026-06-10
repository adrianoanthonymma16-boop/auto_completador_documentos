"""
Módulo para converter HEIC (fotos iPhone) em imagem PIL
"""

import os
from PIL import Image

# Tenta importar pyheif
try:
    import pyheif
    HEIC_SUPORTADO = True
except ImportError:
    HEIC_SUPORTADO = False


def heic_para_imagem(caminho_heic):
    """
    Converte arquivo HEIC para imagem PIL
    
    Args:
        caminho_heic (str): Caminho do arquivo HEIC
    
    Returns:
        PIL.Image: Imagem convertida
    
    Raises:
        Exception: Se pyheif não estiver instalado
    """
    if not HEIC_SUPORTADO:
        raise Exception("Suporte a HEIC não disponível. Instale: sudo apt install libheif-dev && pip install pyheif")
    
    if not os.path.exists(caminho_heic):
        raise Exception(f"Arquivo não encontrado: {caminho_heic}")
    
    # Lê o arquivo HEIC
    heif_file = pyheif.read(caminho_heic)
    
    # Converte para PIL Image
    imagem = Image.frombytes(
        heif_file.mode,
        (heif_file.size[0], heif_file.size[1]),
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride
    )
    
    return imagem


def heic_suportado():
    """Retorna True se suporte a HEIC está disponível"""
    return HEIC_SUPORTADO