"""
Módulo de persistência de modelos salvos
Gerencia o armazenamento, listagem, carregamento e remoção de templates
"""

import os
import json
import shutil
import uuid
from datetime import datetime

from config import PASTA_MODELOS, REGISTRO_MODELOS


def _carregar_registros():
    if not os.path.exists(REGISTRO_MODELOS):
        return []
    try:
        with open(REGISTRO_MODELOS, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            return dados.get('modelos', [])
    except (json.JSONDecodeError, IOError):
        return []


def _salvar_registros(modelos):
    os.makedirs(PASTA_MODELOS, exist_ok=True)
    with open(REGISTRO_MODELOS, 'w', encoding='utf-8') as f:
        json.dump({'modelos': modelos}, f, indent=2, ensure_ascii=False)


def listar_modelos():
    return sorted(_carregar_registros(), key=lambda m: m.get('data_adicao', ''), reverse=True)


def salvar_modelo(caminho_original, tipo, placeholders):
    modelos = _carregar_registros()

    nome_original = os.path.basename(caminho_original)

    for m in modelos:
        if m.get('nome_original') == nome_original:
            return False, "Um modelo com este nome já está salvo."

    modelo_id = uuid.uuid4().hex[:12]
    nome_arquivo = f"{modelo_id}_{nome_original}"
    destino = os.path.join(PASTA_MODELOS, nome_arquivo)

    shutil.copy2(caminho_original, destino)

    modelos.append({
        'id': modelo_id,
        'nome_original': nome_original,
        'arquivo_salvo': nome_arquivo,
        'tipo': tipo,
        'placeholders': placeholders,
        'data_adicao': datetime.now().isoformat()
    })

    _salvar_registros(modelos)
    return True, "Modelo salvo com sucesso."


def remover_modelo(modelo_id):
    modelos = _carregar_registros()
    modelo = None

    for m in modelos:
        if m['id'] == modelo_id:
            modelo = m
            break

    if modelo is None:
        return False, "Modelo não encontrado."

    caminho_arquivo = os.path.join(PASTA_MODELOS, modelo['arquivo_salvo'])
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)

    modelos = [m for m in modelos if m['id'] != modelo_id]
    _salvar_registros(modelos)
    return True, "Modelo removido."


def carregar_modelo(modelo_id):
    modelos = _carregar_registros()
    for m in modelos:
        if m['id'] == modelo_id:
            caminho = os.path.join(PASTA_MODELOS, m['arquivo_salvo'])
            if os.path.exists(caminho):
                return caminho, m['tipo'], m['placeholders']
            return None, None, None
    return None, None, None
