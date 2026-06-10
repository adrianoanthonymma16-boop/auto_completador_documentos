"""
Módulo para ler e escrever arquivos ODT (LibreOffice)
"""

import re
import zipfile
import xml.etree.ElementTree as ET
import shutil
import tempfile
import os


def extrair_placeholders_odt(caminho_odt):
    """
    Extrai todos os placeholders {{...}} de um arquivo ODT
    
    Args:
        caminho_odt (str): Caminho do arquivo ODT
    
    Returns:
        set: Conjunto de placeholders encontrados
    """
    placeholders = set()
    
    with zipfile.ZipFile(caminho_odt, 'r') as odt:
        with odt.open('content.xml') as content:
            tree = ET.parse(content)
            root = tree.getroot()
            
            for elem in root.iter():
                if elem.text:
                    matches = re.findall(r'\{\{([^}]+)\}\}', elem.text)
                    for match in matches:
                        placeholders.add(match.strip())
    
    return placeholders


def gerar_odt_preenchido(caminho_modelo, dados, caminho_saida):
    """
    Gera um novo ODT com os placeholders substituídos
    
    Args:
        caminho_modelo (str): Caminho do arquivo modelo ODT
        dados (dict): Dicionário {placeholder: valor}
        caminho_saida (str): Onde salvar o novo arquivo
    """
    # Copia o modelo
    shutil.copy2(caminho_modelo, caminho_saida)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extrai o ODT
        with zipfile.ZipFile(caminho_saida, 'r') as odt_in:
            odt_in.extractall(tmpdir)
        
        # Lê e modifica o content.xml
        content_path = os.path.join(tmpdir, 'content.xml')
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substitui placeholders
        for placeholder, valor in dados.items():
            content = content.replace(f"{{{{{placeholder}}}}}", valor)
        
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Recompacta
        with zipfile.ZipFile(caminho_saida, 'w') as odt_out:
            for root_dir, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    odt_out.write(file_path, arcname)