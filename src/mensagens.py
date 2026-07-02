"""
Pop-ups informativos para o usuário
"""

import tkinter as tk
from tkinter import messagebox
from config import MODELO_EXTENSOES, ANEXO_EXTENSOES


def mostrar_info_modelos():
    """Pop-up informativo sobre formatos de modelo"""
    
    # Monta a lista de formatos
    formatos = "\n".join([f"✅ {ext.upper()} → {nome}" for ext, nome in MODELO_EXTENSOES.items()])
    
    msg = f"""📄 FORMATOS ACEITOS PARA O MODELO:

{formatos}

❌ Outros formatos (TXT, PDF, etc.) NÃO são suportados

─────────────────────────────

O documento DEVE conter placeholders no formato {{nome_campo}}

Exemplo:
  {{nome_militar}}
  {{cpf}}
  {{data_nascimento}}

─────────────────────────────
Deseja continuar?"""
    
    return messagebox.askyesno("Formatos Suportados - Modelo", msg)


def mostrar_info_anexos(heic_disponivel=False):
    """Pop-up informativo sobre formatos de anexos"""
    
    formatos = []
    for ext, nome in ANEXO_EXTENSOES.items():
        if ext == '.heic' and not heic_disponivel:
            formatos.append(f"⚠️ {ext.upper()} → NÃO DISPONÍVEL (instale libheif e pyheif)")
        else:
            formatos.append(f"✅ {ext.upper()} → {nome}")
    
    lista_formatos = "\n".join(formatos)
    
    msg = f"""📷 FORMATOS ACEITOS PARA ANEXOS:

{lista_formatos}

❌ BMP, GIF, Outros → NÃO são suportados

─────────────────────────────

Dica para melhor resultado no OCR:
• Use imagens nítidas e bem iluminadas
• Evite fotos borradas ou com sombra
• PDFs escaneados funcionam bem

─────────────────────────────
Deseja continuar?"""
    
    return messagebox.askyesno("Formatos Suportados - Anexos", msg)


def mostrar_erro_formato(ext, tipo='modelo'):
    """Pop-up de erro quando formato não é suportado"""
    if tipo == 'modelo':
        suportados = ", ".join(MODELO_EXTENSOES.keys())
        msg = f"Formato {ext} não é suportado.\n\nUse: {suportados}"
    else:
        suportados = ", ".join(ANEXO_EXTENSOES.keys())
        msg = f"Formato {ext} não é suportado.\n\nUse: {suportados}"
    
    messagebox.showerror("Formato não suportado", msg)


def mostrar_aviso_sem_modelo():
    messagebox.showwarning("Aviso", "Carregue um modelo ODT/DOCX primeiro!")


def mostrar_aviso_sem_placeholders():
    messagebox.showwarning("Aviso", "Desenhe pelo menos um retângulo primeiro!")


def mostrar_aviso_sem_extração():
    messagebox.showwarning("Aviso", "Extraia os dados primeiro!")


def mostrar_sucesso_geracao(caminho):
    messagebox.showinfo("Sucesso", f"Documento gerado!\n{caminho}")


def mostrar_info_modelos_salvos():
    msg = """📁 BIBLIOTECA DE MODELOS

Aqui ficam armazenados os modelos que você já usou.

Ao salvar um modelo, ele fica disponível para uso futuro
sem precisar selecionar o arquivo novamente.

• Clique em "Usar este modelo" para carregá-lo como template atual
• O modelo será preenchido com os placeholders encontrados
• Você pode remover modelos que não usa mais

─────────────────────────────
Deseja continuar?"""
    return messagebox.askyesno("Modelos Salvos", msg)


def mostrar_modelo_salvo_sucesso(nome):
    messagebox.showinfo("Salvo", f"Modelo '{nome}' salvo na biblioteca.\nAcesse na aba 'Modelos Salvos'.")


def mostrar_modelo_ja_salvo(nome):
    messagebox.showwarning("Já salvo", f"O modelo '{nome}' já está na biblioteca.")