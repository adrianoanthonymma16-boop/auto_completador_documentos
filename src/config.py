"""
Configurações e constantes do aplicativo
"""

import os

# Versão do app
VERSAO = "3.6"

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
OCR_RESIZE_FATOR = 3
OCR_CLIPLIMIT = 3.0
OCR_TILE_GRID = (8, 8)

# Pasta de modelos salvos
PASTA_MODELOS = os.path.join(PASTA_APP, 'modelos')
REGISTRO_MODELOS = os.path.join(PASTA_MODELOS, 'registros.json')

# Arquivo de log
LOG_FILE = os.path.join(PASTA_APP, 'app.log')

# Backup automático
BACKUP_FILE = os.path.join(PASTA_APP, 'backup.json')
BACKUP_INTERVAL = 60000  # ms (60 segundos)

# Histórico
HISTORY_FILE = os.path.join(PASTA_APP, 'historico.json')
MAX_HISTORY = 50

# Preferências
PREFS_FILE = os.path.join(PASTA_APP, 'prefs.json')

# Cores tema claro
LIGHT_THEME = {
    'canvas_bg': '#F0F0F0',
    'listbox_bg': '#ffffff',
    'listbox_fg': '#333333',
    'text_bg': '#ffffff',
    'text_fg': '#333333',
    'select_bg': '#0078D4',
    'select_fg': '#ffffff',
}

# Cores tema escuro
DARK_THEME = {
    'canvas_bg': '#2B2B2B',
    'listbox_bg': '#3C3C3C',
    'listbox_fg': '#E0E0E0',
    'text_bg': '#3C3C3C',
    'text_fg': '#E0E0E0',
    'select_bg': '#005A9E',
    'select_fg': '#ffffff',
}

# Criar pastas do usuário se não existirem
os.makedirs(PASTA_APP, exist_ok=True)
os.makedirs(PASTA_MODELOS, exist_ok=True)