"""
Módulo principal da interface gráfica - VERSÃO COMPLETA
Gerencia as abas, desenho de retângulos e orquestra os outros módulos
FLUXO: Modelo → Modelos Salvos → Anexar documentos → Mapear → Extrair → Editar → Gerar
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import os

from config import VERSAO
from validadores import (
    validar_extensao,
    obter_filetypes_modelo,
    obter_filetypes_anexo
)
from mensagens import (
    mostrar_info_modelos,
    mostrar_info_anexos,
    mostrar_erro_formato,
    mostrar_aviso_sem_modelo,
    mostrar_sucesso_geracao,
    mostrar_info_modelos_salvos,
    mostrar_modelo_salvo_sucesso,
    mostrar_modelo_ja_salvo
)
from ocr import extrair_texto_do_recorte
from anexo_pdf import pdf_para_imagem, pdf_suportado
from anexo_heic import heic_para_imagem, heic_suportado
from modelo_odt import extrair_placeholders_odt, gerar_odt_preenchido
from modelo_docx import extrair_placeholders_docx, gerar_docx_preenchido, docx_suportado
from modelos_salvos import listar_modelos, salvar_modelo, remover_modelo, carregar_modelo


class AppDocumentos:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Meu App de Documentos - v{VERSAO}")
        self.root.geometry("1280x820")

        self.modelo_path = None
        self.modelo_tipo = None
        self.placeholders = []

        self.documentos_anexados = []

        self.mapeamento = {}

        self.placeholder_atual = None
        self.documento_atual_path = None
        self.imagem_atual = None
        self.imagem_exibida = None
        self.imagem_exibida_img = None

        self.retangulo_atual = None
        self.inicio_x = None
        self.inicio_y = None
        self.retangulos_temp = []

        self.dados_extraidos = {}

        self.frame_salvar_modelo = None
        self.btn_salvar_modelo = None

        self.criar_abas()

    def criar_abas(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.aba_modelo = ttk.Frame(self.notebook)
        self.aba_modelos_salvos = ttk.Frame(self.notebook)
        self.aba_anexos = ttk.Frame(self.notebook)
        self.aba_gerar = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_modelo, text="📄 Modelo")
        self.notebook.add(self.aba_modelos_salvos, text="📁 Modelos Salvos")
        self.notebook.add(self.aba_anexos, text="📎 Anexar e Mapear")
        self.notebook.add(self.aba_gerar, text="✨ Gerar Documento")

        self.criar_aba_modelo()
        self.criar_aba_modelos_salvos()
        self.criar_aba_anexos()
        self.criar_aba_gerar()

    # ============================================================
    # ABA 1 - MODELO
    # ============================================================

    def criar_aba_modelo(self):
        frame = self.aba_modelo

        ttk.Label(frame, text="Carregar Documento Modelo",
                  font=("Helvetica", 16, "bold")).pack(pady=(15, 5))

        frame_info = ttk.LabelFrame(frame, text=" Como funciona ")
        frame_info.pack(fill=tk.X, padx=25, pady=(5, 15), ipady=10)

        texto_info = (
            "1. Selecione um documento ODT ou DOCX que contenha placeholders no formato {{nome_campo}}\n"
            "2. O app encontrará automaticamente todos os campos a preencher\n"
            "3. Você poderá salvar o modelo na biblioteca para reutilizar depois\n"
            "4. Em seguida, anexe documentos-fonte e mapeie cada placeholder"
        )
        ttk.Label(frame_info, text=texto_info, font=("Helvetica", 10),
                  wraplength=1150).pack(anchor=tk.W)

        frame_formatos = ttk.LabelFrame(frame, text=" Formatos aceitos ")
        frame_formatos.pack(fill=tk.X, padx=25, pady=(0, 15))

        texto_fmt = (
            "ODT (LibreOffice Writer)    |    DOCX (Microsoft Word)\n"
            "Placeholders devem usar chaves duplas:    Ex: {{nome}}, {{cpf}}, {{data_nascimento}}"
        )
        ttk.Label(frame_formatos, text=texto_fmt, font=("Helvetica", 10),
                  wraplength=1150).pack(anchor=tk.W)

        btn_carregar = ttk.Button(frame, text="📁 Carregar Modelo",
                                  command=self.carregar_modelo,
                                  bootstyle="success", padding=(30, 12))
        btn_carregar.pack(pady=10)

        self.frame_placeholders = ttk.LabelFrame(frame, text=" Placeholders Encontrados ")
        self.frame_placeholders.pack(fill=tk.BOTH, expand=True, padx=25, pady=5)

        self.lista_placeholders = tk.Listbox(self.frame_placeholders, height=8,
                                              font=("Helvetica", 11),
                                              bg="#ffffff", fg="#333333",
                                              selectbackground="#0078D4",
                                              selectforeground="#ffffff",
                                              relief="flat", borderwidth=1,
                                              highlightthickness=1,
                                              highlightcolor="#0078D4")
        self.lista_placeholders.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(self.frame_placeholders, orient=tk.VERTICAL,
                                command=self.lista_placeholders.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_placeholders.config(yscrollcommand=scroll.set)

        self.frame_salvar_modelo = ttk.Frame(frame)

        self.btn_salvar_modelo = ttk.Button(self.frame_salvar_modelo,
                                             text="💾 Salvar na Biblioteca",
                                             command=self.salvar_modelo_atual,
                                             bootstyle="info", padding=(20, 8))
        self.btn_salvar_modelo.pack(pady=5)

        self.status_modelo = ttk.Label(frame, text="Aguardando carregamento do modelo...",
                                        bootstyle="secondary", anchor=tk.W,
                                        padding=(10, 5))
        self.status_modelo.pack(side=tk.BOTTOM, fill=tk.X)

    def carregar_modelo(self):
        if not mostrar_info_modelos():
            return

        caminho = filedialog.askopenfilename(
            title="Selecione o modelo (ODT ou DOCX)",
            filetypes=obter_filetypes_modelo()
        )
        if not caminho:
            return

        valido, ext, msg = validar_extensao(caminho, 'modelo')
        if not valido:
            mostrar_erro_formato(ext, 'modelo')
            return

        try:
            placeholders = set()

            if ext == '.odt':
                placeholders = extrair_placeholders_odt(caminho)
                self.modelo_tipo = 'odt'
            elif ext == '.docx':
                if not docx_suportado():
                    messagebox.showerror("Erro", "Suporte a DOCX não disponível")
                    return
                placeholders = extrair_placeholders_docx(caminho)
                self.modelo_tipo = 'docx'

            if placeholders:
                self.placeholders = sorted(list(placeholders))
                self.modelo_path = caminho

                self.lista_placeholders.delete(0, tk.END)
                for ph in self.placeholders:
                    self.lista_placeholders.insert(tk.END, ph)

                self.atualizar_lista_placeholders_aba2()

                nome_modelo = os.path.basename(caminho)
                self.status_modelo.config(
                    text=f"Modelo carregado! {len(self.placeholders)} placeholders encontrados em: {nome_modelo}"
                )
                self.status_anexos.config(text="Modelo carregado. Agora anexe documentos para mapear.")

                if not self.frame_salvar_modelo.winfo_ismapped():
                    self.frame_salvar_modelo.pack(fill=tk.X, padx=25, pady=5,
                                                   before=self.status_modelo)

                self.notebook.select(self.aba_anexos)
            else:
                messagebox.showwarning("Aviso", "Nenhum placeholder {{...}} encontrado.")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {str(e)}")

    def salvar_modelo_atual(self):
        if not self.modelo_path or not self.placeholders:
            mostrar_aviso_sem_modelo()
            return

        nome = os.path.basename(self.modelo_path)
        sucesso, mensagem = salvar_modelo(self.modelo_path, self.modelo_tipo, self.placeholders)

        if sucesso:
            mostrar_modelo_salvo_sucesso(nome)
            self.atualizar_lista_modelos_salvos()
        else:
            mostrar_modelo_ja_salvo(nome)

    # ============================================================
    # ABA 2 - MODELOS SALVOS
    # ============================================================

    def criar_aba_modelos_salvos(self):
        frame = self.aba_modelos_salvos

        ttk.Label(frame, text="Biblioteca de Modelos",
                  font=("Helvetica", 16, "bold")).pack(pady=(15, 5))

        frame_info = ttk.LabelFrame(frame, text=" Como usar ")
        frame_info.pack(fill=tk.X, padx=25, pady=(5, 15))

        texto_info = (
            "Os modelos salvos aqui ficam disponíveis para uso futuro sem precisar selecionar o arquivo novamente.\n"
            "Selecione um modelo na tabela e clique em 'Usar este modelo' para carregá-lo como template atual."
        )
        ttk.Label(frame_info, text=texto_info, font=("Helvetica", 10),
                  wraplength=1150).pack(anchor=tk.W)

        frame_botoes = ttk.Frame(frame)
        frame_botoes.pack(fill=tk.X, padx=25, pady=5)

        ttk.Button(frame_botoes, text="✅ Usar este modelo",
                   command=self.usar_modelo_salvo,
                   bootstyle="success", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame_botoes, text="🗑️ Remover",
                   command=self.remover_modelo_salvo,
                   bootstyle="danger-outline", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame_botoes, text="🔄 Atualizar lista",
                   command=self.atualizar_lista_modelos_salvos,
                   bootstyle="secondary-outline", padding=(15, 8)).pack(side=tk.RIGHT, padx=5)

        frame_tabela = ttk.LabelFrame(frame, text=" Modelos Salvos ")
        frame_tabela.pack(fill=tk.BOTH, expand=True, padx=25, pady=5)

        colunas = ("nome", "tipo_ext", "num_campos", "data")
        self.tabela_modelos = ttk.Treeview(frame_tabela, columns=colunas,
                                            show="headings", height=12,
                                            selectmode="browse",
                                            bootstyle="primary")

        self.tabela_modelos.heading("nome", text="Nome do Modelo")
        self.tabela_modelos.heading("tipo_ext", text="Tipo")
        self.tabela_modelos.heading("num_campos", text="Campos")
        self.tabela_modelos.heading("data", text="Data de Adição")

        self.tabela_modelos.column("nome", width=400, minwidth=200)
        self.tabela_modelos.column("tipo_ext", width=80, minwidth=60, anchor=tk.CENTER)
        self.tabela_modelos.column("num_campos", width=80, minwidth=60, anchor=tk.CENTER)
        self.tabela_modelos.column("data", width=160, minwidth=120, anchor=tk.CENTER)

        self.tabela_modelos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_tabela = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL,
                                       command=self.tabela_modelos.yview)
        scroll_tabela.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabela_modelos.configure(yscrollcommand=scroll_tabela.set)

        self.tabela_modelos.bind("<Double-1>", lambda e: self.usar_modelo_salvo())

        self.status_modelos_salvos = ttk.Label(frame,
                                                text="Carregando modelos salvos...",
                                                bootstyle="secondary", anchor=tk.W,
                                                padding=(10, 5))
        self.status_modelos_salvos.pack(side=tk.BOTTOM, fill=tk.X)

        self.atualizar_lista_modelos_salvos()

    def atualizar_lista_modelos_salvos(self):
        for item in self.tabela_modelos.get_children():
            self.tabela_modelos.delete(item)

        modelos = listar_modelos()

        if not modelos:
            self.tabela_modelos.insert("", tk.END,
                                       values=("Nenhum modelo salvo", "-", "-", ""))
            self.status_modelos_salvos.config(
                text="Nenhum modelo salvo ainda. Carregue um modelo na aba 'Modelo' e clique em 'Salvar na Biblioteca'."
            )
            return

        for m in modelos:
            nome = m.get('nome_original', 'Desconhecido')
            tipo = m.get('tipo', '-').upper()
            num = str(len(m.get('placeholders', [])))
            data_raw = m.get('data_adicao', '')
            data_formatada = data_raw[:10] if data_raw else '-'

            self.tabela_modelos.insert("", tk.END, iid=m['id'],
                                       values=(nome, tipo, num, data_formatada))

        self.status_modelos_salvos.config(
            text=f"{len(modelos)} modelo(s) salvo(s) na biblioteca."
        )

    def usar_modelo_salvo(self):
        selecao = self.tabela_modelos.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um modelo na tabela primeiro.")
            return

        modelo_id = selecao[0]
        caminho, tipo, placeholders = carregar_modelo(modelo_id)

        if caminho is None:
            messagebox.showerror("Erro", "Arquivo do modelo não encontrado.")
            self.atualizar_lista_modelos_salvos()
            return

        self.modelo_path = caminho
        self.modelo_tipo = tipo
        self.placeholders = placeholders

        self.lista_placeholders.delete(0, tk.END)
        for ph in self.placeholders:
            self.lista_placeholders.insert(tk.END, ph)

        self.atualizar_lista_placeholders_aba2()

        nome_modelo = os.path.basename(caminho)
        self.status_modelo.config(
            text=f"Modelo carregado da biblioteca! {len(self.placeholders)} placeholders em: {nome_modelo}"
        )
        self.status_anexos.config(text="Modelo carregado da biblioteca. Agora anexe documentos.")

        if not self.frame_salvar_modelo.winfo_ismapped():
            self.frame_salvar_modelo.pack(fill=tk.X, padx=25, pady=5,
                                           before=self.status_modelo)

        self.notebook.select(self.aba_anexos)

    def remover_modelo_salvo(self):
        selecao = self.tabela_modelos.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um modelo na tabela primeiro.")
            return

        modelo_id = selecao[0]
        item = self.tabela_modelos.item(modelo_id)
        nome_modelo = item['values'][0] if item['values'] else ""

        if not messagebox.askyesno("Confirmar", f"Remover '{nome_modelo}' da biblioteca?"):
            return

        sucesso, mensagem = remover_modelo(modelo_id)
        if sucesso:
            self.atualizar_lista_modelos_salvos()
            messagebox.showinfo("Removido", f"Modelo '{nome_modelo}' removido da biblioteca.")
        else:
            messagebox.showerror("Erro", mensagem)

    # ============================================================
    # ABA 3 - ANEXAR E MAPEAR
    # ============================================================

    def criar_aba_anexos(self):
        frame = self.aba_anexos

        frame_top = ttk.Frame(frame)
        frame_top.pack(pady=8, fill=tk.X, padx=10)

        ttk.Button(frame_top, text="📷 Anexar Documento",
                   command=self.anexar_documento,
                   bootstyle="success", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame_top, text="🗑️ Limpar Mapeamento",
                   command=self.limpar_mapeamento,
                   bootstyle="warning", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame_top, text="❌ Remover Documento",
                   command=self.remover_documento,
                   bootstyle="danger", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        instr_texto = "1. Clique no placeholder   |   2. Clique no documento   |   3. Desenhe o retângulo   |   4. Salvar Mapeamento"
        ttk.Label(frame, text=instr_texto,
                  bootstyle="danger", font=("Helvetica", 10, "bold"),
                  padding=(10, 6)).pack(fill=tk.X, padx=15)

        frame_duplo = ttk.Frame(frame)
        frame_duplo.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        frame_ph = ttk.LabelFrame(frame_duplo, text=" PLACEHOLDERS ")
        frame_ph.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.lista_placeholders_aba2 = tk.Listbox(frame_ph, height=10,
                                                   font=("Helvetica", 11),
                                                   bg="#ffffff", fg="#333333",
                                                   selectbackground="#0078D4",
                                                   selectforeground="#ffffff",
                                                   relief="flat", borderwidth=1,
                                                   highlightthickness=1,
                                                   highlightcolor="#0078D4")
        self.lista_placeholders_aba2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lista_placeholders_aba2.bind('<<ListboxSelect>>', self.selecionar_placeholder_aba2)

        scroll_ph = ttk.Scrollbar(frame_ph, orient=tk.VERTICAL,
                                   command=self.lista_placeholders_aba2.yview)
        scroll_ph.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_placeholders_aba2.config(yscrollcommand=scroll_ph.set)

        frame_doc = ttk.LabelFrame(frame_duplo, text=" DOCUMENTOS ")
        frame_doc.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        self.lista_documentos = tk.Listbox(frame_doc, height=10,
                                            font=("Helvetica", 11),
                                            bg="#ffffff", fg="#333333",
                                            selectbackground="#0078D4",
                                            selectforeground="#ffffff",
                                            relief="flat", borderwidth=1,
                                            highlightthickness=1,
                                            highlightcolor="#0078D4")
        self.lista_documentos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lista_documentos.bind('<<ListboxSelect>>', self.selecionar_documento_aba2)

        scroll_doc = ttk.Scrollbar(frame_doc, orient=tk.VERTICAL,
                                    command=self.lista_documentos.yview)
        scroll_doc.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_documentos.config(yscrollcommand=scroll_doc.set)

        frame_status = ttk.Frame(frame)
        frame_status.pack(pady=5, fill=tk.X, padx=15)

        self.status_placeholder_sel = ttk.Label(frame_status,
                                                 text="Placeholder: NENHUM",
                                                 bootstyle="primary",
                                                 padding=(10, 3))
        self.status_placeholder_sel.pack(side=tk.LEFT, padx=5)

        self.status_documento_sel = ttk.Label(frame_status,
                                               text="Documento: NENHUM",
                                               bootstyle="success",
                                               padding=(10, 3))
        self.status_documento_sel.pack(side=tk.RIGHT, padx=5)

        frame_img = ttk.Frame(frame)
        frame_img.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas = tk.Canvas(frame_img, bg='#F0F0F0',
                                 relief="flat", borderwidth=0,
                                 highlightthickness=1,
                                 highlightbackground="#CCCCCC")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(frame_img, orient=tk.VERTICAL,
                                  command=self.canvas.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scroll_y.set)

        self.canvas.bind("<ButtonPress-1>", self.iniciar_retangulo)
        self.canvas.bind("<B1-Motion>", self.desenhar_retangulo)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_retangulo)

        ttk.Button(frame, text="💾 SALVAR MAPEAMENTO",
                   command=self.salvar_mapeamento,
                   bootstyle="primary", padding=(30, 10)).pack(pady=5)

        self.frame_mapeamentos = ttk.LabelFrame(frame, text=" MAPEAMENTOS ")
        self.frame_mapeamentos.pack(fill=tk.X, padx=15, pady=5)

        self.lista_mapeamentos = tk.Listbox(self.frame_mapeamentos, height=5,
                                             font=("Helvetica", 10),
                                             bg="#ffffff", fg="#333333",
                                             relief="flat", borderwidth=1)
        self.lista_mapeamentos.pack(fill=tk.BOTH, expand=True)

        self.status_anexos = ttk.Label(frame, text="Aguardando modelo...",
                                        bootstyle="secondary", anchor=tk.W,
                                        padding=(10, 5))
        self.status_anexos.pack(side=tk.BOTTOM, fill=tk.X)

        self.retangulo_atual = None
        self.inicio_x = None
        self.inicio_y = None

    def atualizar_lista_placeholders_aba2(self):
        self.lista_placeholders_aba2.delete(0, tk.END)
        for ph in self.placeholders:
            if ph in self.mapeamento:
                self.lista_placeholders_aba2.insert(tk.END, f"✓ {ph}")
            else:
                self.lista_placeholders_aba2.insert(tk.END, f"○ {ph}")

    def atualizar_lista_documentos(self):
        self.lista_documentos.delete(0, tk.END)
        for doc in self.documentos_anexados:
            self.lista_documentos.insert(tk.END, doc['nome'])

    def selecionar_placeholder_aba2(self, event):
        selecao = self.lista_placeholders_aba2.curselection()
        if selecao:
            texto = self.lista_placeholders_aba2.get(selecao[0])
            placeholder = texto[2:] if texto[0] in ['✓', '○'] else texto
            self.placeholder_atual = placeholder
            self.status_placeholder_sel.config(text=f"Placeholder: {placeholder}")
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()

    def selecionar_documento_aba2(self, event):
        selecao = self.lista_documentos.curselection()
        if selecao:
            nome_doc = self.lista_documentos.get(selecao[0])
            for doc in self.documentos_anexados:
                if doc['nome'] == nome_doc:
                    self.documento_atual_path = doc['caminho']
                    self.imagem_atual = doc['imagem_original']
                    self.documento_tipo = doc['tipo']
                    self.status_documento_sel.config(text=f"Documento: {nome_doc}")
                    break
            if self.placeholder_atual:
                self.carregar_imagem_para_mapeamento()

    def carregar_imagem_para_mapeamento(self):
        if not self.imagem_atual:
            return

        largura, altura = self.imagem_atual.size
        nova_largura = min(800, largura)
        nova_altura = int(altura * (nova_largura / largura))
        self.imagem_exibida_img = self.imagem_atual.resize(
            (nova_largura, nova_altura), Image.Resampling.LANCZOS
        )
        self.imagem_exibida = ImageTk.PhotoImage(self.imagem_exibida_img)

        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, nova_largura, nova_altura))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.imagem_exibida)

        for ph, dados in self.mapeamento.items():
            if dados['documento_path'] == self.documento_atual_path:
                escala_x = self.imagem_exibida_img.width / self.imagem_atual.width
                escala_y = self.imagem_exibida_img.height / self.imagem_atual.height
                x1 = dados['x1'] * escala_x
                y1 = dados['y1'] * escala_y
                x2 = dados['x2'] * escala_x
                y2 = dados['y2'] * escala_y
                self.canvas.create_rectangle(x1, y1, x2, y2, outline='#28a745', width=2)
                self.canvas.create_text(x1, y1-5, text=ph, fill='#28a745',
                                         anchor=tk.W, font=("Helvetica", 10, "bold"))

    def anexar_documento(self):
        if not self.placeholders:
            mostrar_aviso_sem_modelo()
            return

        if not mostrar_info_anexos(heic_suportado()):
            return

        caminho = filedialog.askopenfilename(filetypes=obter_filetypes_anexo())
        if not caminho:
            return

        valido, ext, msg = validar_extensao(caminho, 'anexo')
        if not valido:
            mostrar_erro_formato(ext, 'anexo')
            return

        try:
            if ext == '.pdf':
                imagem = pdf_para_imagem(caminho)
                tipo = 'pdf'
            elif ext == '.heic':
                imagem = heic_para_imagem(caminho)
                tipo = 'heic'
            else:
                imagem = Image.open(caminho)
                tipo = 'imagem'

            self.documentos_anexados.append({
                'caminho': caminho,
                'nome': os.path.basename(caminho),
                'tipo': tipo,
                'imagem_original': imagem
            })

            self.atualizar_lista_documentos()
            self.status_anexos.config(text=f"Anexado: {os.path.basename(caminho)}")

        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def remover_documento(self):
        selecao = self.lista_documentos.curselection()
        if not selecao:
            return

        nome_doc = self.lista_documentos.get(selecao[0])
        caminho_remover = None
        for i, doc in enumerate(self.documentos_anexados):
            if doc['nome'] == nome_doc:
                caminho_remover = doc['caminho']
                self.documentos_anexados.pop(i)
                remover_ph = [ph for ph, dados in self.mapeamento.items()
                              if dados['documento_path'] == caminho_remover]
                for ph in remover_ph:
                    del self.mapeamento[ph]
                break

        self.atualizar_lista_documentos()
        self.atualizar_lista_placeholders_aba2()
        self.atualizar_lista_mapeamentos()

        if self.documento_atual_path == caminho_remover:
            self.documento_atual_path = None
            self.imagem_atual = None
            self.canvas.delete("all")

    def iniciar_retangulo(self, event):
        if self.placeholder_atual and self.imagem_atual:
            self.inicio_x = self.canvas.canvasx(event.x)
            self.inicio_y = self.canvas.canvasy(event.y)
            self.retangulo_atual = self.canvas.create_rectangle(
                self.inicio_x, self.inicio_y, self.inicio_x, self.inicio_y,
                outline='#dc3545', width=2, dash=(4, 4)
            )

    def desenhar_retangulo(self, event):
        if self.retangulo_atual:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.retangulo_atual, self.inicio_x, self.inicio_y, x, y)

    def finalizar_retangulo(self, event):
        if self.retangulo_atual and self.placeholder_atual and self.imagem_atual:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)

            x1 = min(self.inicio_x, x)
            y1 = min(self.inicio_y, y)
            x2 = max(self.inicio_x, x)
            y2 = max(self.inicio_y, y)

            if (x2 - x1) > 10 and (y2 - y1) > 10:
                escala_x = self.imagem_atual.width / self.imagem_exibida_img.width
                escala_y = self.imagem_atual.height / self.imagem_exibida_img.height

                self.retangulos_temp = [{
                    'placeholder': self.placeholder_atual,
                    'documento_path': self.documento_atual_path,
                    'x1': int(x1 * escala_x),
                    'y1': int(y1 * escala_y),
                    'x2': int(x2 * escala_x),
                    'y2': int(y2 * escala_y)
                }]

                self.canvas.itemconfig(self.retangulo_atual, outline='#0078D4', width=2)
                self.status_anexos.config(text=f"Retângulo para '{self.placeholder_atual}'. Clique em SALVAR.")
            else:
                self.canvas.delete(self.retangulo_atual)

            self.retangulo_atual = None

    def salvar_mapeamento(self):
        if not hasattr(self, 'retangulos_temp') or not self.retangulos_temp:
            messagebox.showwarning("Aviso", "Desenhe um retângulo primeiro!")
            return

        for ret in self.retangulos_temp:
            self.mapeamento[ret['placeholder']] = {
                'documento_path': ret['documento_path'],
                'documento_tipo': self.documento_tipo,
                'x1': ret['x1'],
                'y1': ret['y1'],
                'x2': ret['x2'],
                'y2': ret['y2']
            }

        self.retangulos_temp = []
        self.atualizar_lista_placeholders_aba2()
        self.atualizar_lista_mapeamentos()

        if self.documento_atual_path and self.placeholder_atual:
            self.carregar_imagem_para_mapeamento()

        self.status_anexos.config(text=f"Mapeado: {self.placeholder_atual}")

    def atualizar_lista_mapeamentos(self):
        self.lista_mapeamentos.delete(0, tk.END)
        for ph, dados in self.mapeamento.items():
            nome_doc = os.path.basename(dados['documento_path'])
            self.lista_mapeamentos.insert(tk.END, f"✓ {ph} → {nome_doc}")

        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            self.lista_mapeamentos.insert(tk.END, f"⚠ Pendentes: {', '.join(pendentes)}")

    def limpar_mapeamento(self):
        if messagebox.askyesno("Confirmar", "Limpar todo o mapeamento?"):
            self.mapeamento = {}
            self.atualizar_lista_placeholders_aba2()
            self.atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()
            self.status_anexos.config(text="Mapeamento limpo")

    # ============================================================
    # ABA 4 - GERAR DOCUMENTO
    # ============================================================

    def criar_aba_gerar(self):
        frame = self.aba_gerar

        ttk.Label(frame, text="Documento Final",
                  font=("Helvetica", 16, "bold")).pack(pady=(15, 5))

        ttk.Label(frame, text="Extraia dados via OCR, revise e gere o documento preenchido",
                  bootstyle="secondary", font=("Helvetica", 10)).pack(pady=(0, 10))

        self.frame_preview = ttk.LabelFrame(frame, text=" Dados Extraídos ")
        self.frame_preview.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        self.text_preview = tk.Text(self.frame_preview, height=15,
                                     font=("Helvetica", 11),
                                     bg="#ffffff", fg="#333333",
                                     relief="flat", borderwidth=1,
                                     highlightthickness=1,
                                     highlightcolor="#0078D4")
        self.text_preview.pack(fill=tk.BOTH, expand=True)

        frame_botoes_gerar = ttk.Frame(frame)
        frame_botoes_gerar.pack(pady=10)

        ttk.Button(frame_botoes_gerar, text="🔍 Extrair e Editar Dados",
                   command=self.extrair_e_editar_dados,
                   bootstyle="primary", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        ttk.Button(frame_botoes_gerar, text="📄 Gerar Documento Preenchido",
                   command=self.gerar_documento_preenchido,
                   bootstyle="success", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        self.status_gerar = ttk.Label(frame, text="Aguardando extração de dados...",
                                       bootstyle="secondary", anchor=tk.W,
                                       padding=(10, 5))
        self.status_gerar.pack(side=tk.BOTTOM, fill=tk.X)

    def extrair_e_editar_dados(self):
        if not self.mapeamento:
            messagebox.showwarning("Aviso", "Nenhum mapeamento realizado!")
            return

        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            msg = f"Placeholders não mapeados:\n{', '.join(pendentes)}\n\nContinuar? (ficarão vazios)"
            if not messagebox.askyesno("Aviso", msg):
                self.notebook.select(self.aba_anexos)
                return

        dados_temp = {}
        for placeholder in self.placeholders:
            if placeholder in self.mapeamento:
                dados = self.mapeamento[placeholder]
                try:
                    if dados['documento_tipo'] == 'pdf':
                        imagem = pdf_para_imagem(dados['documento_path'])
                    elif dados['documento_tipo'] == 'heic':
                        imagem = heic_para_imagem(dados['documento_path'])
                    else:
                        imagem = Image.open(dados['documento_path'])

                    texto = extrair_texto_do_recorte(imagem, dados)
                    dados_temp[placeholder] = texto if texto else ""
                except Exception:
                    dados_temp[placeholder] = ""
            else:
                dados_temp[placeholder] = ""

        self.abrir_janela_edicao(dados_temp)

    def abrir_janela_edicao(self, dados_temp):
        self.janela_edicao = tk.Toplevel(self.root)
        self.janela_edicao.title("Editar Dados Extraídos")
        self.janela_edicao.geometry("700x600")
        self.janela_edicao.transient(self.root)
        self.janela_edicao.grab_set()

        ttk.Label(self.janela_edicao, text="Revise e corrija os dados extraídos pelo OCR",
                  font=("Helvetica", 13, "bold")).pack(pady=(15, 5))

        ttk.Label(self.janela_edicao,
                  text="As correções serão aplicadas em todas as ocorrências do placeholder no documento",
                  bootstyle="info", padding=(10, 5)).pack()

        frame_campos = ttk.Frame(self.janela_edicao)
        frame_campos.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas_campos = tk.Canvas(frame_campos, bg='#F5F5F5',
                                   relief="flat", borderwidth=0,
                                   highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_campos, orient=tk.VERTICAL,
                                   command=canvas_campos.yview)
        scrollable_frame = ttk.Frame(canvas_campos)

        scrollable_frame.bind("<Configure>",
                              lambda e: canvas_campos.configure(
                                  scrollregion=canvas_campos.bbox("all")))
        canvas_campos.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_campos.configure(yscrollcommand=scrollbar.set)

        canvas_campos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.campos_entrada = {}

        for placeholder, valor in dados_temp.items():
            frame_campo = ttk.LabelFrame(scrollable_frame, text=placeholder)
            frame_campo.pack(fill=tk.X, pady=5, padx=5)

            entry = tk.Text(frame_campo, height=3,
                             font=("Helvetica", 11),
                             bg="#ffffff", fg="#333333",
                             relief="flat", borderwidth=1,
                             highlightthickness=1,
                             highlightcolor="#0078D4")
            entry.insert(tk.END, valor)
            entry.pack(fill=tk.X, padx=5, pady=5)

            self.campos_entrada[placeholder] = entry

        frame_botoes_edicao = ttk.Frame(self.janela_edicao)
        frame_botoes_edicao.pack(pady=15)

        ttk.Button(frame_botoes_edicao, text="✅ CONFIRMAR E GERAR",
                   command=self.salvar_dados_editados,
                   bootstyle="success", padding=(25, 10)).pack(side=tk.LEFT, padx=10)

        ttk.Button(frame_botoes_edicao, text="❌ CANCELAR",
                   command=self.janela_edicao.destroy,
                   bootstyle="danger", padding=(25, 10)).pack(side=tk.LEFT, padx=10)

    def salvar_dados_editados(self):
        self.dados_extraidos = {}

        for placeholder, entry in self.campos_entrada.items():
            texto = entry.get("1.0", tk.END).strip()
            self.dados_extraidos[placeholder] = texto if texto else ""

        self.janela_edicao.destroy()

        self.text_preview.delete(1.0, tk.END)
        for placeholder, valor in self.dados_extraidos.items():
            self.text_preview.insert(tk.END, f"📌 {placeholder}:\n   {valor}\n\n")

        self.status_gerar.config(text="Dados editados! Clique em 'Gerar Documento Preenchido'")
        self.notebook.select(self.aba_gerar)

    def gerar_documento_preenchido(self):
        if not self.dados_extraidos:
            messagebox.showwarning("Aviso", "Extraia e edite os dados primeiro!")
            return

        if not self.modelo_path:
            mostrar_aviso_sem_modelo()
            return

        ext_saida = ".odt" if self.modelo_tipo == 'odt' else ".docx"
        save_path = filedialog.asksaveasfilename(
            defaultextension=ext_saida,
            filetypes=[(ext_saida.upper().replace('.', ''), f"*{ext_saida}")],
            initialfile=f"documento_preenchido{ext_saida}"
        )

        if not save_path:
            return

        try:
            if self.modelo_tipo == 'odt':
                gerar_odt_preenchido(self.modelo_path, self.dados_extraidos, save_path)
            else:
                if not docx_suportado():
                    raise Exception("DOCX não suportado")
                gerar_docx_preenchido(self.modelo_path, self.dados_extraidos, save_path)

            mostrar_sucesso_geracao(save_path)
            self.status_gerar.config(text=f"Documento salvo: {os.path.basename(save_path)}")

        except Exception as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = AppDocumentos(root)
    root.mainloop()
