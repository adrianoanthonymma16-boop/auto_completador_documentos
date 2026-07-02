"""
Módulo de internacionalização
Extrai strings da interface para facilitar traduções futuras
"""

TEXTO = {
    "pt": {
        "app_titulo": "Meu App de Documentos",
        "aba_modelo": "Modelo",
        "aba_modelos_salvos": "Modelos Salvos",
        "aba_anexos": "Anexar e Mapear",
        "aba_gerar": "Gerar Documento",
        "aba_historico": "Historico",
        "btn_carregar_modelo": "Carregar Modelo",
        "btn_salvar_biblioteca": "Salvar na Biblioteca",
        "btn_anexar": "Anexar Documento",
        "btn_limpar": "Limpar Mapeamento",
        "btn_remover_doc": "Remover Documento",
        "btn_salvar_mapeamento": "SALVAR MAPEAMENTO",
        "btn_extrair": "Extrair e Editar Dados",
        "btn_gerar": "Gerar Documento Preenchido",
        "btn_confirmar": "CONFIRMAR E GERAR",
        "btn_cancelar": "CANCELAR",
        "btn_modo_escuro": "Modo Escuro",
        "btn_modo_claro": "Modo Claro",
        "btn_exportar_mapeamento": "Exportar Mapeamento",
        "btn_importar_mapeamento": "Importar Mapeamento",
        "status_aguardando_modelo": "Aguardando carregamento do modelo...",
        "status_aguardando_extracao": "Aguardando extração de dados...",
        "msg_nenhum_placeholder": "Nenhum placeholder {{...}} encontrado.",
        "msg_desenhe_retangulo": "Desenhe um retângulo primeiro!",
        "msg_nenhum_mapeamento": "Nenhum mapeamento realizado!",
        "msg_extraia_primeiro": "Extraia e edite os dados primeiro!",
        "msg_carregue_modelo": "Carregue um modelo ODT/DOCX primeiro!",
        "titulo_edicao": "Editar Dados Extraídos",
        "instrucao_mapeamento": "1. Clique no placeholder   |   2. Clique no documento   |   3. Desenhe o retângulo   |   4. Salvar Mapeamento",
    }
}


def get_texto(chave, idioma="pt"):
    return TEXTO.get(idioma, TEXTO["pt"]).get(chave, chave)
