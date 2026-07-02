"""
Histórico de documentos gerados
"""

import os
import json
from datetime import datetime
from config import PASTA_APP

HISTORY_PATH = os.path.join(PASTA_APP, "historico.json")
MAX_ENTRIES = 50


def carregar_historico():
    if not os.path.exists(HISTORY_PATH):
        return []

    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def salvar_historico(historico):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(historico[-MAX_ENTRIES:], f, indent=2, ensure_ascii=False)


def adicionar_ao_historico(modelo_path, tipo_modelo, saida_path, num_campos):
    historico = carregar_historico()
    historico.append({
        "data": datetime.now().isoformat(),
        "modelo": os.path.basename(modelo_path),
        "tipo_modelo": tipo_modelo,
        "saida": saida_path,
        "num_campos_preenchidos": num_campos
    })
    salvar_historico(historico)


def listar_historico():
    return sorted(
        carregar_historico(),
        key=lambda h: h.get("data", ""),
        reverse=True
    )
