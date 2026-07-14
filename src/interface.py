"""
Módulo principal da interface gráfica
Gerencia as abas, desenho de retângulos e orquestra os outros módulos
FLUXO: Modelo -> Modelos Salvos -> Anexar -> Mapear -> Extrair/Preencher -> Editar -> Gerar
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import os
import json

from config import (
    VERSAO, PASTA_APP, BACKUP_FILE, BACKUP_INTERVAL,
    LIGHT_THEME, DARK_THEME
)
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
    mostrar_modelo_salvo_sucesso,
    mostrar_modelo_ja_salvo
)
from ocr import extrair_texto_do_recorte
from anexo_pdf import pdf_para_imagem, pdf_suportado
from anexo_heic import heic_para_imagem, heic_suportado
from modelo_odt import extrair_placeholders_odt, gerar_odt_preenchido
from modelo_docx import extrair_placeholders_docx, gerar_docx_preenchido, docx_suportado
from modelos_salvos import listar_modelos, salvar_modelo, remover_modelo, carregar_modelo
from logger import log_info, log_erro, log_warning
from preferencias import carregar_preferencias, set_preferencia
from historico import adicionar_ao_historico, listar_historico
from validadores_extra import sugerir_validacao, validar_campo


class AppDocumentos:
    def __init__(self, root):
        self.root = root
        self.root.title(f"AutoDoc - v{VERSAO}")
        self.root.geometry("1280x820")
        self.root.minsize(900, 600)

        self.tema_atual = "cosmo"
        self.cores = dict(LIGHT_THEME)

        self.modelo_path = None
        self.modelo_tipo = None
        self.placeholders = []
        self.documentos_anexados = []
        self.mapeamento = {}
        self.lote_fontes = []
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

        self.zoom_level = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.is_panning = False

        self.undo_stack = []
        self.redo_stack = []

        self._criar_toolbar()
        self.criar_abas()
        self._configurar_atalhos()
        self._configurar_zoom_pan()
        self._iniciar_backup()
        self._restaurar_preferencias()
        self.root.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        log_info(f"App iniciado v{VERSAO}")

    # ============================================================
    # TOOLBAR SUPERIOR
    # ============================================================

    def _criar_toolbar(self):
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(fill=tk.X, padx=8, pady=(8, 0))

        ttk.Label(self.toolbar, text=f"v{VERSAO}",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=5)

        self.btn_modo_escuro = ttk.Button(
            self.toolbar, text="🌙 Modo Escuro",
            command=self._alternar_tema,
            bootstyle="secondary-outline", padding=(10, 4)
        )
        self.btn_modo_escuro.pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.toolbar, text="ℹ Sobre",
            command=self._mostrar_sobre,
            bootstyle="link", padding=(5, 4)
        ).pack(side=tk.RIGHT, padx=5)

    # ============================================================
    # ABAS
    # ============================================================

    def criar_abas(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.aba_modelo = ttk.Frame(self.notebook)
        self.aba_modelos_salvos = ttk.Frame(self.notebook)
        self.aba_anexos = ttk.Frame(self.notebook)
        self.aba_gerar = ttk.Frame(self.notebook)
        self.aba_historico = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_modelo, text="📄 Modelo")
        self.notebook.add(self.aba_modelos_salvos, text="📁 Modelos Salvos")
        self.notebook.add(self.aba_anexos, text="📎 Anexar e Mapear")
        self.notebook.add(self.aba_gerar, text="✨ Gerar Documento")
        self.notebook.add(self.aba_historico, text="📋 Histórico")

        self.criar_aba_modelo()
        self.criar_aba_modelos_salvos()
        self.criar_aba_anexos()
        self.criar_aba_gerar()
        self.criar_aba_historico()

    # ============================================================
    # ATALHOS DE TECLADO
    # ============================================================

    def _configurar_atalhos(self):
        self.root.bind_all('<Control-o>', lambda e: self.carregar_modelo())
        self.root.bind_all('<Control-O>', lambda e: self.carregar_modelo())
        self.root.bind_all('<Control-a>', lambda e: self.anexar_documento())
        self.root.bind_all('<Control-A>', lambda e: self.anexar_documento())
        self.root.bind_all('<Control-g>', lambda e: self.gerar_documento_preenchido())
        self.root.bind_all('<Control-G>', lambda e: self.gerar_documento_preenchido())
        self.root.bind_all('<Control-s>', lambda e: self.salvar_mapeamento())
        self.root.bind_all('<Control-S>', lambda e: self.salvar_mapeamento())
        self.root.bind_all('<Control-z>', lambda e: self._desfazer_retangulo())
        self.root.bind_all('<Control-Z>', lambda e: self._refazer_retangulo())
        self.root.bind_all('<Control-d>', lambda e: self._alternar_tema())
        self.root.bind_all('<Control-D>', lambda e: self._alternar_tema())
        self.root.bind_all('<Control-e>', lambda e: self._exportar_mapeamento())
        self.root.bind_all('<Control-E>', lambda e: self._exportar_mapeamento())
        self.root.bind_all('<Control-i>', lambda e: self._importar_mapeamento())
        self.root.bind_all('<Control-I>', lambda e: self._importar_mapeamento())
        self.root.bind('<Delete>', lambda e: self._remover_retangulo_selecionado())

    # ============================================================
    # ZOOM E PAN
    # ============================================================

    def _configurar_zoom_pan(self):
        pass

    def _bind_zoom_canvas(self):
        self.canvas.bind('<Control-Button-4>', lambda e: self._zoom(1.2))
        self.canvas.bind('<Control-Button-5>', lambda e: self._zoom(0.8))
        self.canvas.bind('<ButtonPress-2>', self._iniciar_pan)
        self.canvas.bind('<B2-Motion>', self._mover_pan)
        self.canvas.bind('<ButtonRelease-2>', self._finalizar_pan)

    def _zoom(self, fator):
        self.zoom_level *= fator
        self.zoom_level = max(0.2, min(self.zoom_level, 5.0))
        self._redesenhar_canvas_com_zoom()

    def _redesenhar_canvas_com_zoom(self):
        if not self.imagem_atual:
            return
        w = int(self.imagem_atual.width * self.zoom_level)
        h = int(self.imagem_atual.height * self.zoom_level)
        img = self.imagem_atual.resize((w, h), Image.Resampling.LANCZOS)
        self.imagem_exibida_img = img
        self.imagem_exibida = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, w, h))
        self.canvas.create_image(self.pan_offset_x, self.pan_offset_y,
                                 anchor=tk.NW, image=self.imagem_exibida)
        self._redesenhar_retangulos_no_canvas()

    def _iniciar_pan(self, event):
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="fleur")

    def _mover_pan(self, event):
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.pan_offset_x += dx
            self.pan_offset_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.canvas.move("all", dx, dy)

    def _finalizar_pan(self, event):
        self.is_panning = False
        self.canvas.config(cursor="")

    # ============================================================
    # TEMA (MODO ESCURO/CLARO)
    # ============================================================

    def _alternar_tema(self):
        novo = "cyborg" if self.tema_atual == "cosmo" else "cosmo"
        self.root.style.theme_use(novo)
        self.tema_atual = novo
        self.cores = dict(DARK_THEME if novo == "cyborg" else LIGHT_THEME)
        self._aplicar_cores_widgets()
        set_preferencia("tema", novo)
        self.btn_modo_escuro.config(
            text="☀ Modo Claro" if novo == "cyborg" else "🌙 Modo Escuro"
        )
        log_info(f"Tema alterado para: {novo}")

    def _aplicar_cores_widgets(self):
        c = self.cores
        for w in self._widgets_com_cores():
            try:
                w.configure(bg=c['listbox_bg'], fg=c['listbox_fg'],
                            selectbackground=c['select_bg'],
                            selectforeground=c['select_fg'])
            except Exception:
                pass

        try:
            self.canvas.configure(bg=c['canvas_bg'])
            self.canvas_historico.configure(bg=c['canvas_bg'])
        except Exception:
            pass

        try:
            self.text_preview.configure(bg=c['text_bg'], fg=c['text_fg'])
        except Exception:
            pass

    def _widgets_com_cores(self):
        widgets = []
        for attr in ['lista_placeholders', 'lista_placeholders_aba2',
                     'lista_documentos', 'lista_mapeamentos']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                widgets.append(getattr(self, attr))
        return widgets

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
            "2. O app encontrara automaticamente todos os campos a preencher\n"
            "3. Voce podera salvar o modelo na biblioteca para reutilizar depois\n"
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

        btn_carregar = ttk.Button(frame, text="📁 Carregar Modelo  [Ctrl+O]",
                                  command=self.carregar_modelo,
                                  bootstyle="success", padding=(30, 12))
        btn_carregar.pack(pady=10)

        self.frame_placeholders = ttk.LabelFrame(frame, text=" Placeholders Encontrados ")
        self.frame_placeholders.pack(fill=tk.BOTH, expand=True, padx=25, pady=5)

        self.lista_placeholders = tk.Listbox(self.frame_placeholders, height=8,
                                              font=("Helvetica", 11),
                                              bg=self.cores['listbox_bg'],
                                              fg=self.cores['listbox_fg'],
                                              selectbackground=self.cores['select_bg'],
                                              selectforeground=self.cores['select_fg'],
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

        prefs = carregar_preferencias()
        dir_inicial = prefs.get('ultimo_diretorio_modelo', os.path.expanduser("~"))

        caminho = filedialog.askopenfilename(
            title="Selecione o modelo (ODT ou DOCX)",
            filetypes=obter_filetypes_modelo(),
            initialdir=dir_inicial
        )
        if not caminho:
            return

        set_preferencia('ultimo_diretorio_modelo', os.path.dirname(caminho))

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
                    messagebox.showerror("Erro", "Suporte a DOCX nao disponivel")
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

                log_info(f"Modelo carregado: {caminho} ({len(self.placeholders)} placeholders)")
                self.notebook.select(self.aba_anexos)
            else:
                messagebox.showwarning("Aviso", "Nenhum placeholder {{...}} encontrado.")
                log_warning("Nenhum placeholder encontrado no modelo")

        except Exception as e:
            log_erro(f"Erro ao carregar modelo: {str(e)}")
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
            log_info(f"Modelo salvo na biblioteca: {nome}")
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
            "Os modelos salvos aqui ficam disponiveis para uso futuro sem precisar selecionar o arquivo novamente.\n"
            "Selecione um modelo na tabela e clique em 'Usar este modelo' para carrega-lo como template atual."
        )
        ttk.Label(frame_info, text=texto_info, font=("Helvetica", 10),
                  wraplength=1150).pack(anchor=tk.W)

        frame_botoes = ttk.Frame(frame)
        frame_botoes.pack(fill=tk.X, padx=25, pady=5)

        ttk.Button(frame_botoes, text="✅ Usar este modelo",
                   command=self.usar_modelo_salvo,
                   bootstyle="success", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame_botoes, text="🗑 Remover",
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
        self.tabela_modelos.heading("data", text="Data de Adicao")

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
            messagebox.showerror("Erro", "Arquivo do modelo nao encontrado.")
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

        log_info(f"Modelo carregado da biblioteca: {nome_modelo}")
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
            log_info(f"Modelo removido da biblioteca: {nome_modelo}")
        else:
            messagebox.showerror("Erro", mensagem)

    # ============================================================
    # ABA 3 - ANEXAR E MAPEAR
    # ============================================================

    def criar_aba_anexos(self):
        frame = self.aba_anexos

        frame_top = ttk.Frame(frame)
        frame_top.pack(pady=8, fill=tk.X, padx=10)

        btn_frame_left = ttk.Frame(frame_top)
        btn_frame_left.pack(side=tk.LEFT)

        ttk.Button(btn_frame_left, text="📷 Anexar Documento  [Ctrl+A]",
                   command=self.anexar_documento,
                   bootstyle="success", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame_left, text="🗑 Limpar Mapeamento",
                   command=self.limpar_mapeamento,
                   bootstyle="warning", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame_left, text="🗑 Limpar Lote",
                   command=self._limpar_lote_fontes,
                   bootstyle="warning-outline", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame_left, text="❌ Remover Documento  [Del]",
                   command=self.remover_documento,
                   bootstyle="danger", padding=(15, 8)).pack(side=tk.LEFT, padx=5)

        btn_frame_right = ttk.Frame(frame_top)
        btn_frame_right.pack(side=tk.RIGHT)

        ttk.Button(btn_frame_right, text="📤 Exportar  [Ctrl+E]",
                   command=self._exportar_mapeamento,
                   bootstyle="info-outline", padding=(10, 8)).pack(side=tk.LEFT, padx=3)

        ttk.Button(btn_frame_right, text="📥 Importar  [Ctrl+I]",
                   command=self._importar_mapeamento,
                   bootstyle="info-outline", padding=(10, 8)).pack(side=tk.LEFT, padx=3)

        ttk.Button(btn_frame_right, text="↩ Desfazer  [Ctrl+Z]",
                   command=self._desfazer_retangulo,
                   bootstyle="secondary-outline", padding=(10, 8)).pack(side=tk.LEFT, padx=3)

        instr_texto = "1. Clique no placeholder   |   2. Clique no documento   |   3. Desenhe o retangulo   |   4. Salvar Mapeamento  [Ctrl+S]"
        ttk.Label(frame, text=instr_texto,
                  bootstyle="danger", font=("Helvetica", 10, "bold"),
                  padding=(10, 6)).pack(fill=tk.X, padx=15)

        frame_duplo = ttk.Frame(frame)
        frame_duplo.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        frame_ph = ttk.LabelFrame(frame_duplo, text=" PLACEHOLDERS ")
        frame_ph.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.lista_placeholders_aba2 = tk.Listbox(frame_ph, height=10,
                                                   font=("Helvetica", 11),
                                                   bg=self.cores['listbox_bg'],
                                                   fg=self.cores['listbox_fg'],
                                                   selectbackground=self.cores['select_bg'],
                                                   selectforeground=self.cores['select_fg'],
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
                                            bg=self.cores['listbox_bg'],
                                            fg=self.cores['listbox_fg'],
                                            selectbackground=self.cores['select_bg'],
                                            selectforeground=self.cores['select_fg'],
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

        self.label_zoom = ttk.Label(frame_status,
                                     text="Zoom: 100%  (Ctrl+Scroll)",
                                     bootstyle="secondary",
                                     padding=(10, 3))
        self.label_zoom.pack(side=tk.RIGHT, padx=5)

        frame_img = ttk.Frame(frame)
        frame_img.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas = tk.Canvas(frame_img, bg=self.cores['canvas_bg'],
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

        self._bind_zoom_canvas()

        ttk.Button(frame, text="💾 SALVAR MAPEAMENTO  [Ctrl+S]",
                   command=self.salvar_mapeamento,
                   bootstyle="primary", padding=(30, 10)).pack(pady=5)

        self.frame_mapeamentos = ttk.LabelFrame(frame, text=" MAPEAMENTOS ")
        self.frame_mapeamentos.pack(fill=tk.X, padx=15, pady=5)

        self.lista_mapeamentos = tk.Listbox(self.frame_mapeamentos, height=5,
                                             font=("Helvetica", 10),
                                             bg=self.cores['listbox_bg'],
                                             fg=self.cores['listbox_fg'],
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
            self._atualizar_status_documento_lote(nome_doc)

    def carregar_imagem_para_mapeamento(self):
        if not self.imagem_atual:
            return

        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self._redesenhar_canvas_com_zoom()

    def _redesenhar_retangulos_no_canvas(self):
        for ph, dados in self.mapeamento.items():
            if dados['documento_path'] == self.documento_atual_path:
                escala_x = self.imagem_exibida_img.width / self.imagem_atual.width
                escala_y = self.imagem_exibida_img.height / self.imagem_atual.height
                x1 = dados['x1'] * escala_x + self.pan_offset_x
                y1 = dados['y1'] * escala_y + self.pan_offset_y
                x2 = dados['x2'] * escala_x + self.pan_offset_x
                y2 = dados['y2'] * escala_y + self.pan_offset_y
                self.canvas.create_rectangle(x1, y1, x2, y2, outline='#28a745', width=2)
                self.canvas.create_text(x1, y1-5, text=ph, fill='#28a745',
                                         anchor=tk.W, font=("Helvetica", 10, "bold"))

        for entry in self.lote_fontes:
            if entry['documento_path'] == self.documento_atual_path:
                escala_x = self.imagem_exibida_img.width / self.imagem_atual.width
                escala_y = self.imagem_exibida_img.height / self.imagem_atual.height
                for ph, dados in entry['mapeamento'].items():
                    x1 = dados['x1'] * escala_x + self.pan_offset_x
                    y1 = dados['y1'] * escala_y + self.pan_offset_y
                    x2 = dados['x2'] * escala_x + self.pan_offset_x
                    y2 = dados['y2'] * escala_y + self.pan_offset_y
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline='#28a745', width=2)
                    self.canvas.create_text(x1, y1-5, text=ph, fill='#28a745',
                                             anchor=tk.W, font=("Helvetica", 10, "bold"))

    def anexar_documento(self):
        if not self.placeholders:
            mostrar_aviso_sem_modelo()
            return

        if not mostrar_info_anexos(heic_suportado()):
            return

        prefs = carregar_preferencias()
        dir_inicial = prefs.get('ultimo_diretorio_anexo', os.path.expanduser("~"))

        caminho = filedialog.askopenfilename(
            filetypes=obter_filetypes_anexo(),
            initialdir=dir_inicial
        )
        if not caminho:
            return

        set_preferencia('ultimo_diretorio_anexo', os.path.dirname(caminho))

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
            log_info(f"Documento anexado: {caminho}")

        except Exception as e:
            log_erro(f"Erro ao anexar documento: {str(e)}")
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

        self.lote_fontes = [e for e in self.lote_fontes if e['documento_path'] != caminho_remover]

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
                    'documento_tipo': self.documento_tipo,
                    'x1': int((x1 - self.pan_offset_x) * escala_x),
                    'y1': int((y1 - self.pan_offset_y) * escala_y),
                    'x2': int((x2 - self.pan_offset_x) * escala_x),
                    'y2': int((y2 - self.pan_offset_y) * escala_y)
                }]

                self.canvas.itemconfig(self.retangulo_atual, outline='#0078D4', width=2)
                self.status_anexos.config(text=f"Retangulo para '{self.placeholder_atual}'. Clique em SALVAR.  [Ctrl+S]")
            else:
                self.canvas.delete(self.retangulo_atual)

            self.retangulo_atual = None

    def salvar_mapeamento(self):
        if not hasattr(self, 'retangulos_temp') or not self.retangulos_temp:
            messagebox.showwarning("Aviso", "Desenhe um retangulo primeiro!")
            return

        for ret in self.retangulos_temp:
            if ret['placeholder'] in self.mapeamento:
                self.undo_stack.append({
                    'action': 'update',
                    'placeholder': ret['placeholder'],
                    'old_data': dict(self.mapeamento[ret['placeholder']])
                })
            else:
                self.undo_stack.append({
                    'action': 'add',
                    'placeholder': ret['placeholder']
                })
            self.redo_stack.clear()

            self.mapeamento[ret['placeholder']] = {
                'documento_path': ret['documento_path'],
                'documento_tipo': ret['documento_tipo'],
                'x1': ret['x1'],
                'y1': ret['y1'],
                'x2': ret['x2'],
                'y2': ret['y2']
            }

            self._sincronizar_lote_fontes(ret)

        self.retangulos_temp = []
        self.atualizar_lista_placeholders_aba2()
        self.atualizar_lista_mapeamentos()

        if self.documento_atual_path and self.placeholder_atual:
            self.carregar_imagem_para_mapeamento()

        self.status_anexos.config(text=f"Mapeado: {self.placeholder_atual}")

    def _sincronizar_lote_fontes(self, ret):
        doc_path = ret['documento_path']
        mapping = {
            'x1': ret['x1'],
            'y1': ret['y1'],
            'x2': ret['x2'],
            'y2': ret['y2']
        }
        encontrado = False
        for entry in self.lote_fontes:
            if entry['documento_path'] == doc_path:
                entry['mapeamento'][ret['placeholder']] = mapping
                encontrado = True
                break
        if not encontrado:
            self.lote_fontes.append({
                'documento_path': doc_path,
                'documento_tipo': ret['documento_tipo'],
                'mapeamento': {ret['placeholder']: mapping}
            })

    def atualizar_lista_mapeamentos(self):
        self.lista_mapeamentos.delete(0, tk.END)
        for ph, dados in self.mapeamento.items():
            nome_doc = os.path.basename(dados['documento_path'])
            self.lista_mapeamentos.insert(tk.END, f"✓ {ph} → {nome_doc}")

        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            self.lista_mapeamentos.insert(tk.END, f"⚠ Pendentes: {', '.join(pendentes)}")

        if self.lote_fontes:
            self.lista_mapeamentos.insert(tk.END, "")
            self.lista_mapeamentos.insert(tk.END, f"--- LOTE: {len(self.lote_fontes)} documento(s) ---")
            for entry in self.lote_fontes:
                nome = os.path.basename(entry['documento_path'])
                mapeados = list(entry['mapeamento'].keys())
                self.lista_mapeamentos.insert(tk.END, f"  📄 {nome}: {mapeados}")

    def _atualizar_status_documento_lote(self, nome_doc):
        for entry in self.lote_fontes:
            if os.path.basename(entry['documento_path']) == nome_doc:
                mapeados = len(entry['mapeamento'])
                total = len(self.placeholders)
                self.status_documento_sel.config(
                    text=f"Documento: {nome_doc}  |  ({mapeados}/{total} placeholders)"
                )
                return

    def limpar_mapeamento(self):
        if messagebox.askyesno("Confirmar", "Limpar todo o mapeamento?"):
            self.mapeamento = {}
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.lote_fontes = []
            self.atualizar_lista_placeholders_aba2()
            self.atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()
            self.status_anexos.config(text="Mapeamento limpo")

    def _limpar_lote_fontes(self):
        if messagebox.askyesno("Confirmar", "Remover todos os mapeamentos do lote de documentos?"):
            self.lote_fontes = []
            self.atualizar_lista_mapeamentos()
            self.status_anexos.config(text="Lote de fontes limpo")

    # ============================================================
    # UNDO / REDO
    # ============================================================

    def _desfazer_retangulo(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nada para desfazer.")
            return

        action = self.undo_stack.pop()
        ph = action['placeholder']

        if action['action'] == 'add':
            self.redo_stack.append({
                'action': 'remove',
                'placeholder': ph,
                'old_data': dict(self.mapeamento.get(ph, {}))
            })
            if ph in self.mapeamento:
                del self.mapeamento[ph]
        elif action['action'] == 'update':
            self.redo_stack.append({
                'action': 'update',
                'placeholder': ph,
                'old_data': dict(self.mapeamento.get(ph, {}))
            })
            self.mapeamento[ph] = action['old_data']

        self.atualizar_lista_placeholders_aba2()
        self.atualizar_lista_mapeamentos()
        if self.documento_atual_path:
            self.carregar_imagem_para_mapeamento()
        self.status_anexos.config(text=f"Desfeito: {ph}")

    def _refazer_retangulo(self):
        if not self.redo_stack:
            messagebox.showinfo("Redo", "Nada para refazer.")
            return

        action = self.redo_stack.pop()
        ph = action['placeholder']

        if action['action'] == 'remove':
            self.undo_stack.append({
                'action': 'add',
                'placeholder': ph
            })
            if ph in self.mapeamento:
                del self.mapeamento[ph]
        elif action['action'] == 'update':
            self.undo_stack.append({
                'action': 'update',
                'placeholder': ph,
                'old_data': dict(self.mapeamento.get(ph, {}))
            })
            self.mapeamento[ph] = action['old_data']

        self.atualizar_lista_placeholders_aba2()
        self.atualizar_lista_mapeamentos()
        if self.documento_atual_path:
            self.carregar_imagem_para_mapeamento()
        self.status_anexos.config(text=f"Refeito: {ph}")

    def _remover_retangulo_selecionado(self):
        if self.placeholder_atual and self.placeholder_atual in self.mapeamento:
            self.undo_stack.append({
                'action': 'add',
                'placeholder': self.placeholder_atual,
                'old_data': dict(self.mapeamento[self.placeholder_atual])
            })
            self.redo_stack.clear()
            del self.mapeamento[self.placeholder_atual]
            self.atualizar_lista_placeholders_aba2()
            self.atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()
            self.status_anexos.config(text=f"Retangulo removido: {self.placeholder_atual}")

    # ============================================================
    # EXPORTAR / IMPORTAR MAPEAMENTO
    # ============================================================

    def _exportar_mapeamento(self):
        if not self.mapeamento:
            messagebox.showwarning("Aviso", "Nenhum mapeamento para exportar.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Exportar Mapeamento",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="mapeamento.json"
        )
        if not caminho:
            return

        export = {
            'modelo_path': self.modelo_path,
            'modelo_tipo': self.modelo_tipo,
            'placeholders': self.placeholders,
            'mapeamento': {},
            'lote_fontes': self.lote_fontes
        }
        for ph, dados in self.mapeamento.items():
            export['mapeamento'][ph] = {
                'documento_path': dados['documento_path'],
                'documento_tipo': dados['documento_tipo'],
                'x1': dados['x1'],
                'y1': dados['y1'],
                'x2': dados['x2'],
                'y2': dados['y2']
            }

        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exportado", f"Mapeamento salvo em:\n{caminho}")
            log_info(f"Mapeamento exportado: {caminho}")
        except Exception as e:
            log_erro(f"Erro ao exportar mapeamento: {str(e)}")
            messagebox.showerror("Erro", str(e))

    def _importar_mapeamento(self):
        caminho = filedialog.askopenfilename(
            title="Importar Mapeamento",
            filetypes=[("JSON", "*.json")]
        )
        if not caminho:
            return

        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('modelo_path') != self.modelo_path:
                if not messagebox.askyesno("Modelo diferente",
                                           "O mapeamento foi criado com outro modelo. Continuar?"):
                    return

            self.mapeamento = {}
            for ph, dados in data.get('mapeamento', {}).items():
                self.mapeamento[ph] = {
                    'documento_path': dados['documento_path'],
                    'documento_tipo': dados['documento_tipo'],
                    'x1': dados['x1'],
                    'y1': dados['y1'],
                    'x2': dados['x2'],
                    'y2': dados['y2']
                }

            self.lote_fontes = data.get('lote_fontes', [])

            self.undo_stack.clear()
            self.redo_stack.clear()
            self.atualizar_lista_placeholders_aba2()
            self.atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()

            messagebox.showinfo("Importado", f"Mapeamento carregado ({len(self.mapeamento)} campos)")
            log_info(f"Mapeamento importado: {caminho}")
        except Exception as e:
            log_erro(f"Erro ao importar mapeamento: {str(e)}")
            messagebox.showerror("Erro", f"Arquivo invalido: {str(e)}")

    # ============================================================
    # ABA 4 - GERAR DOCUMENTO
    # ============================================================

    def criar_aba_gerar(self):
        frame = self.aba_gerar

        ttk.Label(frame, text="Documento Final",
                  font=("Helvetica", 16, "bold")).pack(pady=(15, 5))

        ttk.Label(frame, text="Extraia dados via OCR, revise e gere o documento preenchido",
                  bootstyle="secondary", font=("Helvetica", 10)).pack(pady=(0, 10))

        self.frame_preview = ttk.LabelFrame(frame, text=" Dados Extraidos ")
        self.frame_preview.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        self.text_preview = tk.Text(self.frame_preview, height=15,
                                     font=("Helvetica", 11),
                                     bg=self.cores['text_bg'],
                                     fg=self.cores['text_fg'],
                                     relief="flat", borderwidth=1,
                                     highlightthickness=1,
                                     highlightcolor="#0078D4")
        self.text_preview.pack(fill=tk.BOTH, expand=True)

        frame_botoes_gerar = ttk.Frame(frame)
        frame_botoes_gerar.pack(pady=10)

        ttk.Button(frame_botoes_gerar, text="🔍 Extrair e Editar Dados",
                   command=self.extrair_e_editar_dados,
                   bootstyle="primary", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        ttk.Button(frame_botoes_gerar, text="✏️ Preencher Manualmente",
                   command=self.preencher_manualmente,
                   bootstyle="info", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        ttk.Button(frame_botoes_gerar, text="📄 Gerar Documento Preenchido  [Ctrl+G]",
                   command=self.gerar_documento_preenchido,
                   bootstyle="success", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        ttk.Button(frame_botoes_gerar, text="📚 Gerar em Lote (Modelos)",
                   command=self._processar_em_lote,
                   bootstyle="warning", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        ttk.Button(frame_botoes_gerar, text="📦 Gerar Lote de Documentos",
                   command=self._processar_lote_fontes,
                   bootstyle="primary", padding=(25, 12)).pack(side=tk.LEFT, padx=10)

        self.status_gerar = ttk.Label(frame, text="Aguardando extracao de dados...",
                                       bootstyle="secondary", anchor=tk.W,
                                       padding=(10, 5))
        self.status_gerar.pack(side=tk.BOTTOM, fill=tk.X)

    def extrair_e_editar_dados(self):
        if not self.mapeamento:
            messagebox.showwarning("Aviso", "Nenhum mapeamento realizado!")
            return

        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            msg = f"Placeholders nao mapeados:\n{', '.join(pendentes)}\n\nContinuar? (ficarao vazios)"
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
        log_info("Extracao de dados iniciada")

    def preencher_manualmente(self):
        if not self.placeholders:
            mostrar_aviso_sem_modelo()
            return

        dados_temp = {}
        for placeholder in self.placeholders:
            dados_temp[placeholder] = self.dados_extraidos.get(placeholder, "")

        self.abrir_janela_edicao(dados_temp)
        log_info("Preenchimento manual iniciado")

    def abrir_janela_edicao(self, dados_temp):
        self.janela_edicao = tk.Toplevel(self.root)
        self.janela_edicao.title("Editar Dados Extraidos")
        self.janela_edicao.geometry("700x600")
        self.janela_edicao.transient(self.root)
        self.janela_edicao.grab_set()

        ttk.Label(self.janela_edicao, text="Revise e corrija os dados extraidos pelo OCR",
                  font=("Helvetica", 13, "bold")).pack(pady=(15, 5))

        ttk.Label(self.janela_edicao,
                  text="As correcoes serao aplicadas em todas as ocorrencias do placeholder no documento",
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
        self.labels_validacao = {}

        for placeholder, valor in dados_temp.items():
            frame_campo = ttk.LabelFrame(scrollable_frame, text=placeholder)
            frame_campo.pack(fill=tk.X, pady=5, padx=5)

            entry = tk.Text(frame_campo, height=3,
                             font=("Helvetica", 11),
                             bg=self.cores['text_bg'],
                             fg=self.cores['text_fg'],
                             relief="flat", borderwidth=1,
                             highlightthickness=1,
                             highlightcolor="#0078D4")
            entry.insert(tk.END, valor)
            entry.pack(fill=tk.X, padx=5, pady=(5, 0))

            self.campos_entrada[placeholder] = entry

            tipo = sugerir_validacao(placeholder.lower())
            if tipo:
                label_val = ttk.Label(frame_campo, text=f"🔍 Validacao: {tipo}",
                                      bootstyle="secondary", font=("Helvetica", 9))
                label_val.pack(anchor=tk.W, padx=5, pady=(0, 5))
                self.labels_validacao[placeholder] = label_val

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
        erros = []

        for placeholder, entry in self.campos_entrada.items():
            texto = entry.get("1.0", tk.END).strip()
            valor = texto if texto else ""
            self.dados_extraidos[placeholder] = valor

            if valor:
                ok, msg = validar_campo(placeholder, valor)
                if not ok:
                    erros.append(f"{placeholder}: {msg}")

        if erros:
            msg = "Alguns campos tem dados invalidos:\n\n" + "\n".join(erros)
            msg += "\n\nDeseja corrigir antes de continuar?"
            if messagebox.askyesno("Validacao", msg):
                return

        self.janela_edicao.destroy()

        self.text_preview.delete(1.0, tk.END)
        for placeholder, valor in self.dados_extraidos.items():
            self.text_preview.insert(tk.END, f"📌 {placeholder}:\n   {valor}\n\n")

        self.status_gerar.config(text="Dados editados! Clique em 'Gerar Documento Preenchido'  [Ctrl+G]")
        self.notebook.select(self.aba_gerar)
        log_info("Dados extraidos e editados")

    def gerar_documento_preenchido(self):
        if not self.dados_extraidos:
            messagebox.showwarning("Aviso", "Extraia e edite os dados primeiro!")
            return

        if not self.modelo_path:
            mostrar_aviso_sem_modelo()
            return

        prefs = carregar_preferencias()
        dir_inicial = prefs.get('ultimo_diretorio_saida', os.path.expanduser("~"))

        ext_saida = ".odt" if self.modelo_tipo == 'odt' else ".docx"
        save_path = filedialog.asksaveasfilename(
            defaultextension=ext_saida,
            filetypes=[(ext_saida.upper().replace('.', ''), f"*{ext_saida}")],
            initialfile=f"documento_preenchido{ext_saida}",
            initialdir=dir_inicial
        )

        if not save_path:
            return

        set_preferencia('ultimo_diretorio_saida', os.path.dirname(save_path))

        try:
            if self.modelo_tipo == 'odt':
                gerar_odt_preenchido(self.modelo_path, self.dados_extraidos, save_path)
            else:
                if not docx_suportado():
                    raise Exception("DOCX nao suportado")
                gerar_docx_preenchido(self.modelo_path, self.dados_extraidos, save_path)

            mostrar_sucesso_geracao(save_path)
            self.status_gerar.config(text=f"Documento salvo: {os.path.basename(save_path)}")
            adicionar_ao_historico(self.modelo_path, self.modelo_tipo,
                                   save_path, len(self.dados_extraidos))
            self.atualizar_tabela_historico()
            log_info(f"Documento gerado: {save_path}")

        except Exception as e:
            log_erro(f"Erro ao gerar documento: {str(e)}")
            messagebox.showerror("Erro", str(e))

    def _processar_em_lote(self):
        if not self.dados_extraidos:
            messagebox.showwarning("Aviso", "Extraia e edite os dados primeiro!")
            return

        messagebox.showinfo("Em Lote",
                            "Selecione a pasta de modelos a processar.\n"
                            "Cada modelo sera preenchido com os mesmos dados.")

        pasta_modelos = filedialog.askdirectory(title="Selecione a pasta com modelos")
        if not pasta_modelos:
            return

        pasta_saida = filedialog.askdirectory(title="Selecione a pasta de saida")
        if not pasta_saida:
            return

        processados = 0
        erros_lote = []

        for arquivo in sorted(os.listdir(pasta_modelos)):
            if not (arquivo.endswith('.odt') or arquivo.endswith('.docx')):
                continue

            caminho = os.path.join(pasta_modelos, arquivo)
            ext = os.path.splitext(arquivo)[1].lower()

            try:
                saida = os.path.join(pasta_saida, f"preenchido_{arquivo}")

                if ext == '.odt':
                    gerar_odt_preenchido(caminho, self.dados_extraidos, saida)
                elif ext == '.docx':
                    if not docx_suportado():
                        erros_lote.append(f"{arquivo}: DOCX nao suportado")
                        continue
                    gerar_docx_preenchido(caminho, self.dados_extraidos, saida)

                processados += 1
                adicionar_ao_historico(caminho, ext.replace('.', ''),
                                       saida, len(self.dados_extraidos))
            except Exception as e:
                erros_lote.append(f"{arquivo}: {str(e)}")

        self.atualizar_tabela_historico()
        msg = f"Lote concluido!\n\nDocumentos processados: {processados}"
        if erros_lote:
            msg += f"\n\nErros:\n" + "\n".join(erros_lote)
        messagebox.showinfo("Lote Finalizado", msg)
        log_info(f"Processamento em lote: {processados} documentos")

    def _processar_lote_fontes(self):
        if not self.lote_fontes:
            messagebox.showwarning("Aviso", "Nenhum documento mapeado no lote!\n"
                                   "Na aba 'Anexar e Mapear', anexe varios documentos e mapeie os placeholders em cada um.")
            return

        if not self.modelo_path:
            messagebox.showwarning("Aviso", "Carregue um modelo primeiro!")
            return

        pasta_saida = filedialog.askdirectory(title="Selecione a pasta de saida para os documentos em lote")
        if not pasta_saida:
            return

        processados = 0
        erros_lote = []

        for entry in self.lote_fontes:
            doc_path = entry['documento_path']
            doc_nome = os.path.basename(doc_path)
            dados_temp = {}

            for placeholder in self.placeholders:
                if placeholder in entry['mapeamento']:
                    coords = entry['mapeamento'][placeholder]
                    try:
                        if entry['documento_tipo'] == 'pdf':
                            imagem = pdf_para_imagem(doc_path)
                        elif entry['documento_tipo'] == 'heic':
                            imagem = heic_para_imagem(doc_path)
                        else:
                            imagem = Image.open(doc_path)

                        dados_ocr = {
                            'x1': coords['x1'],
                            'y1': coords['y1'],
                            'x2': coords['x2'],
                            'y2': coords['y2']
                        }
                        texto = extrair_texto_do_recorte(imagem, dados_ocr)
                        dados_temp[placeholder] = texto if texto else ""
                    except Exception:
                        dados_temp[placeholder] = ""
                else:
                    dados_temp[placeholder] = ""

            try:
                ext = os.path.splitext(self.modelo_path)[1].lower()
                nome_base = os.path.splitext(doc_nome)[0]
                saida = os.path.join(pasta_saida, f"preenchido_{nome_base}{ext}")

                if ext == '.odt':
                    gerar_odt_preenchido(self.modelo_path, dados_temp, saida)
                elif ext == '.docx':
                    if not docx_suportado():
                        erros_lote.append(f"{doc_nome}: DOCX nao suportado")
                        continue
                    gerar_docx_preenchido(self.modelo_path, dados_temp, saida)
                else:
                    erros_lote.append(f"{doc_nome}: formato de modelo desconhecido")
                    continue

                processados += 1
                adicionar_ao_historico(self.modelo_path, self.modelo_tipo,
                                       saida, len([v for v in dados_temp.values() if v]))
            except Exception as e:
                erros_lote.append(f"{doc_nome}: {str(e)}")

        self.atualizar_tabela_historico()
        msg = f"Lote de documentos concluido!\n\nDocumentos processados: {processados}"
        if erros_lote:
            msg += f"\n\nErros:\n" + "\n".join(erros_lote)
        messagebox.showinfo("Lote Finalizado", msg)
        log_info(f"Processamento de lote de fontes: {processados} documentos")

    # ============================================================
    # ABA 5 - HISTORICO
    # ============================================================

    def criar_aba_historico(self):
        frame = self.aba_historico

        ttk.Label(frame, text="Historico de Documentos Gerados",
                  font=("Helvetica", 16, "bold")).pack(pady=(15, 5))

        ttk.Label(frame, text="Registro dos ultimos documentos gerados com o aplicativo",
                  bootstyle="secondary", font=("Helvetica", 10)).pack(pady=(0, 10))

        frame_botoes_hist = ttk.Frame(frame)
        frame_botoes_hist.pack(fill=tk.X, padx=25, pady=5)

        ttk.Button(frame_botoes_hist, text="🔄 Atualizar",
                   command=self.atualizar_tabela_historico,
                   bootstyle="secondary-outline", padding=(15, 8)).pack(side=tk.RIGHT, padx=5)

        canvas_hist_frame = ttk.Frame(frame)
        canvas_hist_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=5)

        self.canvas_historico = tk.Canvas(canvas_hist_frame, bg=self.cores['canvas_bg'],
                                           relief="flat", borderwidth=0,
                                           highlightthickness=0)
        scrollbar_hist = ttk.Scrollbar(canvas_hist_frame, orient=tk.VERTICAL,
                                        command=self.canvas_historico.yview)
        self.frame_scroll_hist = ttk.Frame(self.canvas_historico)

        self.frame_scroll_hist.bind("<Configure>",
                                    lambda e: self.canvas_historico.configure(
                                        scrollregion=self.canvas_historico.bbox("all")))
        self.canvas_historico.create_window((0, 0), window=self.frame_scroll_hist, anchor="nw")
        self.canvas_historico.configure(yscrollcommand=scrollbar_hist.set)

        self.canvas_historico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_hist.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_historico = ttk.Label(frame, text="",
                                           bootstyle="secondary", anchor=tk.W,
                                           padding=(10, 5))
        self.status_historico.pack(side=tk.BOTTOM, fill=tk.X)

        self.atualizar_tabela_historico()

    def atualizar_tabela_historico(self):
        for widget in self.frame_scroll_hist.winfo_children():
            widget.destroy()

        historico = listar_historico()

        if not historico:
            ttk.Label(self.frame_scroll_hist,
                      text="Nenhum documento gerado ainda.",
                      bootstyle="secondary", font=("Helvetica", 11)).pack(pady=20)
            self.status_historico.config(text="Historico vazio")
            return

        colunas_frame = ttk.Frame(self.frame_scroll_hist)
        colunas_frame.pack(fill=tk.X, padx=10, pady=(5, 2))

        ttk.Label(colunas_frame, text="Data", font=("Helvetica", 10, "bold"),
                  width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(colunas_frame, text="Modelo", font=("Helvetica", 10, "bold"),
                  width=30, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        ttk.Label(colunas_frame, text="Campos", font=("Helvetica", 10, "bold"),
                  width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(colunas_frame, text="Arquivo de Saida", font=("Helvetica", 10, "bold"),
                  width=40, anchor=tk.W).pack(side=tk.LEFT, padx=5)

        ttk.Separator(self.frame_scroll_hist, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        for item in historico:
            linha = ttk.Frame(self.frame_scroll_hist)
            linha.pack(fill=tk.X, padx=10, pady=2)

            data_str = item.get('data', '')[:10]
            modelo = item.get('modelo', '-')[:35]
            campos = str(item.get('num_campos_preenchidos', '-'))
            saida = os.path.basename(item.get('saida', '-'))[:40]

            ttk.Label(linha, text=data_str, width=12).pack(side=tk.LEFT, padx=5)
            ttk.Label(linha, text=modelo, width=30, anchor=tk.W).pack(side=tk.LEFT, padx=5)
            ttk.Label(linha, text=campos, width=8).pack(side=tk.LEFT, padx=5)
            ttk.Label(linha, text=saida, width=40, anchor=tk.W).pack(side=tk.LEFT, padx=5)

        self.status_historico.config(text=f"{len(historico)} documento(s) no historico")

    # ============================================================
    # BACKUP AUTOMATICO
    # ============================================================

    def _iniciar_backup(self):
        self._tentar_restaurar_backup()
        self._executar_backup()

    def _executar_backup(self):
        if self.mapeamento and self.modelo_path:
            backup = {
                'modelo_path': self.modelo_path,
                'modelo_tipo': self.modelo_tipo,
                'placeholders': self.placeholders,
                'mapeamento': {},
                'lote_fontes': self.lote_fontes
            }
            for ph, dados in self.mapeamento.items():
                backup['mapeamento'][ph] = {
                    'documento_path': dados['documento_path'],
                    'documento_tipo': dados['documento_tipo'],
                    'x1': dados['x1'],
                    'y1': dados['y1'],
                    'x2': dados['x2'],
                    'y2': dados['y2']
                }
            try:
                os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
                with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                    json.dump(backup, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        self.root.after(BACKUP_INTERVAL, self._executar_backup)

    def _tentar_restaurar_backup(self):
        if not os.path.exists(BACKUP_FILE):
            return
        try:
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            if backup.get('mapeamento'):
                if messagebox.askyesno("Backup encontrado",
                                       "Um backup de mapeamento foi encontrado.\nDeseja restaura-lo?"):
                    self.modelo_path = backup.get('modelo_path')
                    self.modelo_tipo = backup.get('modelo_tipo')
                    self.placeholders = backup.get('placeholders', [])

                    self.lista_placeholders.delete(0, tk.END)
                    for ph in self.placeholders:
                        self.lista_placeholders.insert(tk.END, ph)
                    self.atualizar_lista_placeholders_aba2()

                    self.mapeamento = {}
                    for ph, dados in backup['mapeamento'].items():
                        self.mapeamento[ph] = {
                            'documento_path': dados['documento_path'],
                            'documento_tipo': dados['documento_tipo'],
                            'x1': dados['x1'],
                            'y1': dados['y1'],
                            'x2': dados['x2'],
                            'y2': dados['y2']
                        }
                    self.lote_fontes = backup.get('lote_fontes', [])
                    self.atualizar_lista_mapeamentos()
                    self.status_modelo.config(text="Mapeamento restaurado do backup.")
                    self.status_anexos.config(text="Mapeamento restaurado. Continue de onde parou.")
                    log_info("Backup restaurado com sucesso")
        except Exception as e:
            log_warning(f"Falha ao restaurar backup: {str(e)}")

    # ============================================================
    # PREFERENCIAS E SOBRE
    # ============================================================

    def _restaurar_preferencias(self):
        prefs = carregar_preferencias()
        tema_salvo = prefs.get('tema', 'cosmo')
        if tema_salvo != self.tema_atual:
            self.root.style.theme_use(tema_salvo)
            self.tema_atual = tema_salvo
            self.cores = dict(DARK_THEME if tema_salvo == 'cyborg' else LIGHT_THEME)
            self.btn_modo_escuro.config(
                text="☀ Modo Claro" if tema_salvo == 'cyborg' else "🌙 Modo Escuro"
            )

        tamanho = prefs.get('tamanho_janela', '1280x820')
        try:
            self.root.geometry(tamanho)
        except Exception:
            pass

    def _ao_fechar(self):
        try:
            geo = self.root.geometry()
            set_preferencia('tamanho_janela', geo)
        except Exception:
            pass
        log_info("App finalizado")
        self.root.destroy()

    def _mostrar_sobre(self):
        messagebox.showinfo(
            "Sobre - AutoDoc",
            f"AutoDoc v{VERSAO}\n\n"
            "Automatize o preenchimento de documentos ODT/DOCX usando OCR.\n\n"
            "Desenvolvido por Adriano Anthony Jesus Azulay de Araujo\n"
            "E-mail: adrianoanthonymma16@gmail.com\n\n"
            "100% offline - Licenca proprietaria"
        )


if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = AppDocumentos(root)
    root.mainloop()
