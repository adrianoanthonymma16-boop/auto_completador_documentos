"""
Configurações e constantes do aplicativo
"""

import os

# Versão do app
VERSAO = "3.4"

# Pasta do usuário para salvar configurações
PASTA_APP = os.path.expanduser("~/.meu_app_documentos")

# Formatos suportados para MODELO (documento com placeholders)
MODELO_EXTENSOES = {
    '.odt': 'ODT (LibreOffice)',
    '.docx': 'DOCX (Microsoft Word)'
}

# Formatos suportados para DOCUMENTOS FONTE (anexos)
ANEXO_EXTENSOES = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.tiff': 'TIFF',
    '.pdf': 'PDF',
    '.webp': 'WEBP',
    '.heic': 'HEIC (iPhone)'
}

# Configurações do Tesseract
TESSERACT_LANG = 'por'
TESSERACT_CONFIG = '--psm 6'

# Configurações de pré-processamento OCR
OCR_RESIZE_FATOR = 3  # Aumenta a imagem em 3x
OCR_CLIPLIMIT = 3.0
OCR_TILE_GRID = (8, 8)

# Criar pasta do usuário se não existir
os.makedirs(PASTA_APP, exist_ok=True)