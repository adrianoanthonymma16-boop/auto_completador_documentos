"""
Módulo de OCR (Optical Character Recognition)
Responsável por pré-processar imagens e extrair texto usando Tesseract
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
from config import OCR_RESIZE_FATOR, OCR_CLIPLIMIT, OCR_TILE_GRID, TESSERACT_LANG, TESSERACT_CONFIG


def preprocessar_imagem(imagem_pil):
    """
    Pré-processa a imagem para melhorar a leitura do OCR
    
    Etapas:
    1. Converte PIL para OpenCV
    2. Aumenta resolução (resize)
    3. Converte para escala de cinza
    4. Aplica CLAHE para contraste local
    5. Binarização OTSU (preto e branco)
    
    Args:
        imagem_pil (PIL.Image): Imagem original
    
    Returns:
        numpy.ndarray: Imagem processada em preto e branco
    """
    # Converte PIL para OpenCV (RGB para BGR)
    img = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)
    
    # Aumenta resolução
    h, w = img.shape[:2]
    img = cv2.resize(img, (w * OCR_RESIZE_FATOR, h * OCR_RESIZE_FATOR), 
                      interpolation=cv2.INTER_CUBIC)
    
    # Escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # CLAHE (Contraste Local Adaptativo)
    clahe = cv2.createCLAHE(clipLimit=OCR_CLIPLIMIT, tileGridSize=OCR_TILE_GRID)
    gray = clahe.apply(gray)
    
    # Binarização OTSU (preto e branco)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary


def extrair_texto_da_regiao(imagem_pil):
    """
    Extrai texto de uma região da imagem usando Tesseract
    
    Args:
        imagem_pil (PIL.Image): Imagem da região a ser processada
    
    Returns:
        str: Texto extraído (limpo)
    """
    # Pré-processa
    imagem_processada = preprocessar_imagem(imagem_pil)
    
    # Aplica OCR
    texto = pytesseract.image_to_string(
        imagem_processada, 
        lang=TESSERACT_LANG, 
        config=TESSERACT_CONFIG
    )
    
    # Limpa o texto
    texto = texto.strip()
    texto = texto.replace('\n', ' ')
    texto = ' '.join(texto.split())
    
    return texto if len(texto) > 2 else ""


def extrair_texto_do_recorte(imagem_original, coordenadas):
    """
    Extrai texto de um recorte específico da imagem
    
    Args:
        imagem_original (PIL.Image): Imagem completa
        coordenadas (dict): {'x1':, 'y1':, 'x2':, 'y2':}
    
    Returns:
        str: Texto extraído
    """
    # Recorta a região
    regiao = imagem_original.crop((
        coordenadas['x1'], 
        coordenadas['y1'], 
        coordenadas['x2'], 
        coordenadas['y2']
    ))
    
    # Extrai texto
    return extrair_texto_da_regiao(regiao)