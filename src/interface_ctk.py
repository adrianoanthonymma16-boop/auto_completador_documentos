"""
Modulo da interface grafica CustomTkinter
Mesma logica de negocios que interface.py, com visual moderno CTk
FLUXO: Modelo -> Modelos Salvos -> Anexar -> Mapear -> Extrair/Preencher -> Editar -> Gerar
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
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


class AppDocumentosCTK:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Meu App de Documentos - v{VERSAO} (CustomTkinter)")
        self.root.iconname("Meu App de Documentos")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = min(1320, screen_w - 40)
        win_h = min(860, screen_h - 80)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(960, 640)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

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
        self.documento_tipo = None

        self.zoom_level = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.is_panning = False

        self.undo_stack = []
        self.redo_stack = []

        self.placeholder_items_ctk = {}
        self.documento_items_ctk = {}
        self.modelo_table_rows = []

        self._criar_toolbar()
        self._criar_abas()
        self._configurar_atalhos()
        self._iniciar_backup()
        self._restaurar_preferencias()
        self.root.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        log_info(f"App CTk iniciado v{VERSAO}")

    # ============================================================
    # TOOLBAR SUPERIOR
    # ============================================================

    def _criar_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        self.toolbar.pack(fill=tk.X, padx=0, pady=0)

        ctk.CTkLabel(self.toolbar, text=f"v{VERSAO}  |  CustomTkinter",
                     font=("Helvetica", 11)).pack(side=tk.LEFT, padx=15, pady=8)

        self.btn_tema = ctk.CTkButton(
            self.toolbar, text="🌙 Modo Escuro",
            command=self._alternar_tema,
            width=130, height=30, corner_radius=8,
            fg_color="transparent", border_width=1, border_color="#555555"
        )
        self.btn_tema.pack(side=tk.RIGHT, padx=10, pady=5)

        ctk.CTkButton(
            self.toolbar, text="Sobre",
            command=self._mostrar_sobre,
            width=70, height=30, corner_radius=8,
            fg_color="transparent", text_color="#0078D4"
        ).pack(side=tk.RIGHT, padx=5, pady=5)

    # ============================================================
    # ABAS
    # ============================================================

    def _criar_abas(self):
        self.tabview = ctk.CTkTabview(self.root, corner_radius=10)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tabview.add("  Modelo  ")
        self.tabview.add("  Modelos Salvos  ")
        self.tabview.add("  Anexar e Mapear  ")
        self.tabview.add("  Gerar Documento  ")
        self.tabview.add("  Historico  ")

        self.aba_modelo = self.tabview.tab("  Modelo  ")
        self.aba_modelos_salvos = self.tabview.tab("  Modelos Salvos  ")
        self.aba_anexos = self.tabview.tab("  Anexar e Mapear  ")
        self.aba_gerar = self.tabview.tab("  Gerar Documento  ")
        self.aba_historico = self.tabview.tab("  Historico  ")

        self._criar_aba_modelo()
        self._criar_aba_modelos_salvos()
        self._criar_aba_anexos()
        self._criar_aba_gerar()
        self._criar_aba_historico()

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
    # TEMA
    # ============================================================

    def _alternar_tema(self):
        atual = ctk.get_appearance_mode()
        novo = "Dark" if atual == "Light" else "Light"
        ctk.set_appearance_mode(novo)
        set_preferencia("tema_ctk", novo.lower())
        self.btn_tema.configure(
            text="☀ Modo Claro" if novo == "Dark" else "🌙 Modo Escuro"
        )
        log_info(f"Tema CTk alterado para: {novo}")

    # ============================================================
    # ABA 1 - MODELO
    # ============================================================

    def _criar_aba_modelo(self):
        frame = self.aba_modelo
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Carregar Documento Modelo",
                     font=("Helvetica", 18, "bold")).pack(pady=(20, 5))

        info_frame = ctk.CTkFrame(frame, corner_radius=10, fg_color="transparent",
                                  border_width=1, border_color="#CCCCCC")
        info_frame.pack(fill=tk.X, padx=30, pady=(5, 15))

        texto_info = (
            "1. Selecione um documento ODT ou DOCX com placeholders {{nome_campo}}\n"
            "2. O app encontrara todos os campos a preencher\n"
            "3. Salve na biblioteca para reutilizar\n"
            "4. Anexe documentos-fonte ou preencha manualmente"
        )
        ctk.CTkLabel(info_frame, text=texto_info, font=("Helvetica", 11),
                     wraplength=1150, justify="left").pack(padx=15, pady=12, anchor="w")

        ctk.CTkButton(frame, text="Carregar Modelo  [Ctrl+O]",
                      command=self.carregar_modelo,
                      height=40, corner_radius=10, font=("Helvetica", 14, "bold"),
                      fg_color="#28a745", hover_color="#218838"
                      ).pack(pady=10)

        ctk.CTkLabel(frame, text="Placeholders Encontrados",
                     font=("Helvetica", 13, "bold")).pack(pady=(10, 2))

        self.scroll_ph_modelo = ctk.CTkScrollableFrame(frame, height=200, corner_radius=10)
        self.scroll_ph_modelo.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

        self.frame_salvar_btn = ctk.CTkFrame(frame, fg_color="transparent")
        self.btn_salvar_modelo = ctk.CTkButton(self.frame_salvar_btn,
                                               text="Salvar na Biblioteca",
                                               command=self.salvar_modelo_atual,
                                               height=35, corner_radius=10,
                                               fg_color="#0078D4", hover_color="#005a9e")
        self.btn_salvar_modelo.pack(pady=5)

        self.status_modelo = ctk.CTkLabel(frame, text="Aguardando carregamento do modelo...",
                                          font=("Helvetica", 10), text_color="gray")
        self.status_modelo.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

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

                for w in self.scroll_ph_modelo.winfo_children():
                    w.destroy()
                for ph in self.placeholders:
                    lbl = ctk.CTkLabel(self.scroll_ph_modelo, text=ph,
                                       font=("Helvetica", 12),
                                       anchor="w", padx=10, pady=3)
                    lbl.pack(fill=tk.X, pady=1)

                self._atualizar_lista_ph_mapeamento()

                nome_modelo = os.path.basename(caminho)
                self.status_modelo.configure(
                    text=f"Modelo carregado! {len(self.placeholders)} placeholders encontrados em: {nome_modelo}"
                )
                self.status_anexos.configure(text="Modelo carregado. Agora anexe documentos ou preencha manualmente.")

                if not self.frame_salvar_btn.winfo_ismapped():
                    self.frame_salvar_btn.pack(fill=tk.X, padx=30, pady=5,
                                               before=self.status_modelo)

                log_info(f"Modelo carregado (CTk): {caminho} ({len(self.placeholders)} placeholders)")
                self.tabview.set("  Anexar e Mapear  ")
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
            self._atualizar_tabela_modelos_salvos()
            log_info(f"Modelo salvo na biblioteca (CTk): {nome}")
        else:
            mostrar_modelo_ja_salvo(nome)

    # ============================================================
    # ABA 2 - MODELOS SALVOS
    # ============================================================

    def _criar_aba_modelos_salvos(self):
        frame = self.aba_modelos_salvos
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Biblioteca de Modelos",
                     font=("Helvetica", 18, "bold")).pack(pady=(20, 5))

        info_text = (
            "Modelos salvos ficam disponiveis para uso futuro sem precisar selecionar o arquivo novamente.\n"
            "Selecione um modelo e clique em 'Usar este modelo' para carrega-lo."
        )
        ctk.CTkLabel(frame, text=info_text, font=("Helvetica", 11),
                     text_color="gray", wraplength=1150).pack(pady=(0, 10))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=30, pady=5)

        ctk.CTkButton(btn_frame, text="Usar este modelo",
                      command=self._usar_modelo_salvo,
                      height=35, corner_radius=10,
                      fg_color="#28a745", hover_color="#218838").pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(btn_frame, text="Remover",
                      command=self._remover_modelo_salvo,
                      height=35, corner_radius=10,
                      fg_color="transparent", border_width=1,
                      border_color="#dc3545", text_color="#dc3545",
                      hover_color="#dc3545").pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(btn_frame, text="Atualizar lista",
                      command=self._atualizar_tabela_modelos_salvos,
                      height=35, corner_radius=10,
                      fg_color="transparent", border_width=1,
                      border_color="#888888").pack(side=tk.RIGHT, padx=5)

        self.tabela_modelos_frame = ctk.CTkScrollableFrame(frame, height=350, corner_radius=10)
        self.tabela_modelos_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

        self.status_modelos_salvos = ctk.CTkLabel(frame, text="Carregando modelos salvos...",
                                                   font=("Helvetica", 10), text_color="gray")
        self.status_modelos_salvos.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

        self._atualizar_tabela_modelos_salvos()

    def _atualizar_tabela_modelos_salvos(self):
        for w in self.tabela_modelos_frame.winfo_children():
            w.destroy()
        self.modelo_table_rows = []

        modelos = listar_modelos()

        col_header = ctk.CTkFrame(self.tabela_modelos_frame, fg_color="transparent", height=32)
        col_header.pack(fill=tk.X, padx=5, pady=(2, 0))
        ctk.CTkLabel(col_header, text="Nome do Modelo", font=("Helvetica", 11, "bold"),
                     width=340, anchor="w").pack(side=tk.LEFT, padx=8)
        ctk.CTkLabel(col_header, text="Tipo", font=("Helvetica", 11, "bold"),
                     width=60).pack(side=tk.LEFT, padx=8)
        ctk.CTkLabel(col_header, text="Campos", font=("Helvetica", 11, "bold"),
                     width=60).pack(side=tk.LEFT, padx=8)
        ctk.CTkLabel(col_header, text="Data", font=("Helvetica", 11, "bold"),
                     width=120).pack(side=tk.LEFT, padx=8)

        sep = ctk.CTkFrame(self.tabela_modelos_frame, height=2, fg_color="#CCCCCC", corner_radius=0)
        sep.pack(fill=tk.X, padx=5)

        if not modelos:
            ctk.CTkLabel(self.tabela_modelos_frame, text="Nenhum modelo salvo ainda.",
                         text_color="gray", font=("Helvetica", 12)).pack(pady=30)
            self.status_modelos_salvos.configure(
                text="Nenhum modelo salvo. Carregue um modelo na aba 'Modelo' e clique em 'Salvar na Biblioteca'."
            )
            return

        self.modelo_selecionado_id = None

        for m in modelos:
            row = ctk.CTkFrame(self.tabela_modelos_frame, fg_color="transparent", height=34)
            row.pack(fill=tk.X, padx=5, pady=1)

            nome = m.get('nome_original', 'Desconhecido')
            tipo = m.get('tipo', '-').upper()
            num = str(len(m.get('placeholders', [])))
            data_raw = m.get('data_adicao', '')
            data_formatada = data_raw[:10] if data_raw else '-'
            mid = m['id']

            def make_callback(rid, rframe):
                return lambda e=None: self._selecionar_linha_modelo(rid, rframe)

            row.bind("<Button-1>", make_callback(mid, row))
            for child in [row]:
                pass

            ctk.CTkLabel(row, text=nome[:40], width=340, anchor="w",
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)
            ctk.CTkLabel(row, text=tipo, width=60,
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)
            ctk.CTkLabel(row, text=num, width=60,
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)
            ctk.CTkLabel(row, text=data_formatada, width=120,
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)

            for lbl in row.winfo_children():
                lbl.bind("<Button-1>", make_callback(mid, row))

            self.modelo_table_rows.append({"id": mid, "frame": row})

        self.status_modelos_salvos.configure(
            text=f"{len(modelos)} modelo(s) salvo(s) na biblioteca."
        )

    def _selecionar_linha_modelo(self, mid, frame):
        for row_info in self.modelo_table_rows:
            if row_info["id"] == mid:
                row_info["frame"].configure(fg_color="#0078D4")
            else:
                row_info["frame"].configure(fg_color="transparent")
        self.modelo_selecionado_id = mid

    def _usar_modelo_salvo(self):
        if not getattr(self, 'modelo_selecionado_id', None):
            messagebox.showwarning("Aviso", "Clique em um modelo na tabela para seleciona-lo.")
            return

        modelo_id = self.modelo_selecionado_id
        caminho, tipo, placeholders = carregar_modelo(modelo_id)

        if caminho is None:
            messagebox.showerror("Erro", "Arquivo do modelo nao encontrado.")
            self._atualizar_tabela_modelos_salvos()
            return

        self.modelo_path = caminho
        self.modelo_tipo = tipo
        self.placeholders = placeholders

        for w in self.scroll_ph_modelo.winfo_children():
            w.destroy()
        for ph in self.placeholders:
            ctk.CTkLabel(self.scroll_ph_modelo, text=ph, font=("Helvetica", 12),
                         anchor="w", padx=10, pady=3).pack(fill=tk.X, pady=1)

        self._atualizar_lista_ph_mapeamento()

        nome_modelo = os.path.basename(caminho)
        self.status_modelo.configure(
            text=f"Modelo carregado da biblioteca! {len(self.placeholders)} placeholders em: {nome_modelo}"
        )
        self.status_anexos.configure(text="Modelo carregado. Agora anexe documentos ou preencha manualmente.")

        if not self.frame_salvar_btn.winfo_ismapped():
            self.frame_salvar_btn.pack(fill=tk.X, padx=30, pady=5,
                                       before=self.status_modelo)

        log_info(f"Modelo carregado da biblioteca (CTk): {nome_modelo}")
        self.tabview.set("  Anexar e Mapear  ")

    def _remover_modelo_salvo(self):
        if not getattr(self, 'modelo_selecionado_id', None):
            messagebox.showwarning("Aviso", "Clique em um modelo na tabela para seleciona-lo.")
            return

        modelo_id = self.modelo_selecionado_id
        if not messagebox.askyesno("Confirmar", "Remover este modelo da biblioteca?"):
            return

        sucesso, mensagem = remover_modelo(modelo_id)
        if sucesso:
            self.modelo_selecionado_id = None
            self._atualizar_tabela_modelos_salvos()
            messagebox.showinfo("Removido", "Modelo removido da biblioteca.")
        else:
            messagebox.showerror("Erro", mensagem)

    # ============================================================
    # ABA 3 - ANEXAR E MAPEAR
    # ============================================================

    def _criar_aba_anexos(self):
        frame = self.aba_anexos

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(pady=8, fill=tk.X, padx=15)

        btn_left = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_left.pack(side=tk.LEFT)

        ctk.CTkButton(btn_left, text="Anexar Documento  [Ctrl+A]",
                      command=self.anexar_documento,
                      height=35, corner_radius=10,
                      fg_color="#28a745", hover_color="#218838").pack(side=tk.LEFT, padx=3)

        ctk.CTkButton(btn_left, text="Limpar Mapeamento",
                      command=self.limpar_mapeamento,
                      height=35, corner_radius=10,
                      fg_color="#ffc107", hover_color="#e0a800",
                      text_color="black").pack(side=tk.LEFT, padx=3)

        ctk.CTkButton(btn_left, text="Remover Documento  [Del]",
                      command=self.remover_documento,
                      height=35, corner_radius=10,
                      fg_color="#dc3545", hover_color="#c82333").pack(side=tk.LEFT, padx=3)

        btn_right = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_right.pack(side=tk.RIGHT)

        ctk.CTkButton(btn_right, text="Exportar  [Ctrl+E]",
                      command=self._exportar_mapeamento,
                      height=30, corner_radius=8,
                      fg_color="transparent", border_width=1,
                      border_color="#0078D4", text_color="#0078D4",
                      hover_color="#0078D4").pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(btn_right, text="Importar  [Ctrl+I]",
                      command=self._importar_mapeamento,
                      height=30, corner_radius=8,
                      fg_color="transparent", border_width=1,
                      border_color="#0078D4", text_color="#0078D4",
                      hover_color="#0078D4").pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(btn_right, text="Desfazer  [Ctrl+Z]",
                      command=self._desfazer_retangulo,
                      height=30, corner_radius=8,
                      fg_color="transparent", border_width=1,
                      border_color="#888888",
                      hover_color="#888888").pack(side=tk.LEFT, padx=2)

        instr_text = "1. Clique no placeholder  |  2. Clique no documento  |  3. Desenhe o retangulo  |  4. Salvar Mapeamento [Ctrl+S]"
        ctk.CTkLabel(frame, text=instr_text,
                     font=("Helvetica", 11, "bold"), text_color="#dc3545").pack(
            fill=tk.X, padx=20, pady=6)

        dual_frame = ctk.CTkFrame(frame, fg_color="transparent")
        dual_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        dual_frame.grid_columnconfigure(0, weight=1)
        dual_frame.grid_columnconfigure(1, weight=1)

        ph_frame = ctk.CTkFrame(dual_frame, corner_radius=10, border_width=1, border_color="#CCCCCC")
        ph_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        ctk.CTkLabel(ph_frame, text="PLACEHOLDERS",
                     font=("Helvetica", 12, "bold")).pack(pady=(8, 2))

        self.scroll_ph_mapeamento = ctk.CTkScrollableFrame(ph_frame, height=180, corner_radius=8)
        self.scroll_ph_mapeamento.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        doc_frame = ctk.CTkFrame(dual_frame, corner_radius=10, border_width=1, border_color="#CCCCCC")
        doc_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        ctk.CTkLabel(doc_frame, text="DOCUMENTOS",
                     font=("Helvetica", 12, "bold")).pack(pady=(8, 2))

        self.scroll_documentos = ctk.CTkScrollableFrame(doc_frame, height=180, corner_radius=8)
        self.scroll_documentos.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        status_frame = ctk.CTkFrame(frame, fg_color="transparent")
        status_frame.pack(pady=5, fill=tk.X, padx=15)

        self.status_placeholder_sel = ctk.CTkLabel(status_frame,
                                                    text="Placeholder: NENHUM",
                                                    font=("Helvetica", 11, "bold"),
                                                    text_color="#0078D4")
        self.status_placeholder_sel.pack(side=tk.LEFT, padx=10)

        self.status_documento_sel = ctk.CTkLabel(status_frame,
                                                  text="Documento: NENHUM",
                                                  font=("Helvetica", 11, "bold"),
                                                  text_color="#28a745")
        self.status_documento_sel.pack(side=tk.RIGHT, padx=10)

        self.label_zoom = ctk.CTkLabel(status_frame,
                                       text="Zoom: 100%  (Ctrl+Scroll)",
                                       text_color="gray", font=("Helvetica", 10))
        self.label_zoom.pack(side=tk.RIGHT, padx=10)

        canvas_frame = ctk.CTkFrame(frame, corner_radius=10, border_width=1, border_color="#CCCCCC")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas = ctk.CTkCanvas(canvas_frame, bg="#E8E8E8",
                                     relief="flat", borderwidth=0,
                                     highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        scroll_y = ctk.CTkScrollbar(canvas_frame, orientation="vertical",
                                     command=self.canvas.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2), pady=2)
        self.canvas.configure(yscrollcommand=scroll_y.set)

        self.canvas.bind("<ButtonPress-1>", self.iniciar_retangulo)
        self.canvas.bind("<B1-Motion>", self.desenhar_retangulo)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_retangulo)
        self._bind_zoom_canvas()

        ctk.CTkButton(frame, text="SALVAR MAPEAMENTO  [Ctrl+S]",
                      command=self.salvar_mapeamento,
                      height=42, corner_radius=10, font=("Helvetica", 13, "bold"),
                      fg_color="#0078D4", hover_color="#005a9e").pack(pady=8)

        mapeamentos_frame = ctk.CTkFrame(frame, corner_radius=10, border_width=1, border_color="#CCCCCC")
        mapeamentos_frame.pack(fill=tk.X, padx=15, pady=5)

        ctk.CTkLabel(mapeamentos_frame, text="MAPEAMENTOS",
                     font=("Helvetica", 11, "bold")).pack(pady=(8, 2))

        self.scroll_mapeamentos = ctk.CTkScrollableFrame(mapeamentos_frame, height=100, corner_radius=8)
        self.scroll_mapeamentos.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_anexos = ctk.CTkLabel(frame, text="Aguardando modelo...",
                                           font=("Helvetica", 10), text_color="gray")
        self.status_anexos.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 8))

        self.retangulo_atual = None
        self.inicio_x = None
        self.inicio_y = None

    # ============================================================
    # LISTAS CTkScrollableFrame (placeholders, docs, mapeamentos)
    # ============================================================

    def _atualizar_lista_ph_mapeamento(self):
        for w in self.scroll_ph_mapeamento.winfo_children():
            w.destroy()
        self.placeholder_items_ctk = {}

        for ph in self.placeholders:
            prefix = "✓" if ph in self.mapeamento else "○"
            lbl = ctk.CTkLabel(self.scroll_ph_mapeamento,
                               text=f"{prefix}  {ph}",
                               font=("Helvetica", 12),
                               anchor="w", padx=12, pady=4)

            def make_cb(p):
                def cb(e):
                    self._selecionar_placeholder_ctk(p)
                return cb

            lbl.bind("<Button-1>", make_cb(ph))
            lbl.pack(fill=tk.X, pady=1)

            self.placeholder_items_ctk[ph] = lbl

    def _selecionar_placeholder_ctk(self, placeholder):
        self.placeholder_atual = placeholder
        self.status_placeholder_sel.configure(text=f"Placeholder: {placeholder}")
        for ph, lbl in self.placeholder_items_ctk.items():
            lbl.configure(fg_color="#0078D4" if ph == placeholder else "transparent")
        if self.documento_atual_path:
            self.carregar_imagem_para_mapeamento()

    def _atualizar_lista_documentos(self):
        for w in self.scroll_documentos.winfo_children():
            w.destroy()
        self.documento_items_ctk = {}

        for doc in self.documentos_anexados:
            lbl = ctk.CTkLabel(self.scroll_documentos,
                               text=doc['nome'],
                               font=("Helvetica", 12),
                               anchor="w", padx=12, pady=4)

            def make_cb(d):
                def cb(e):
                    self._selecionar_documento_ctk(d)
                return cb

            lbl.bind("<Button-1>", make_cb(doc))
            lbl.pack(fill=tk.X, pady=1)

            self.documento_items_ctk[doc['caminho']] = lbl

    def _selecionar_documento_ctk(self, doc):
        for doc_caminho, lbl in self.documento_items_ctk.items():
            lbl.configure(fg_color="#28a745" if doc_caminho == doc['caminho'] else "transparent")

        self.documento_atual_path = doc['caminho']
        self.imagem_atual = doc['imagem_original']
        self.documento_tipo = doc['tipo']
        self.status_documento_sel.configure(text=f"Documento: {doc['nome']}")

        if self.placeholder_atual:
            self.carregar_imagem_para_mapeamento()

    def _atualizar_lista_mapeamentos(self):
        for w in self.scroll_mapeamentos.winfo_children():
            w.destroy()

        for ph, dados in self.mapeamento.items():
            nome_doc = os.path.basename(dados['documento_path'])
            ctk.CTkLabel(self.scroll_mapeamentos,
                         text=f"✓ {ph}  →  {nome_doc}",
                         font=("Helvetica", 11),
                         anchor="w", padx=10, pady=3,
                         text_color="#28a745").pack(fill=tk.X, pady=1)

        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            ctk.CTkLabel(self.scroll_mapeamentos,
                         text=f"⚠ Pendentes: {', '.join(pendentes)}",
                         font=("Helvetica", 10),
                         anchor="w", padx=10, pady=3,
                         text_color="#ffc107").pack(fill=tk.X, pady=1)

    # ============================================================
    # ZOOM E PAN (idêntico ao interface.py)
    # ============================================================

    def _bind_zoom_canvas(self):
        self.canvas.bind('<Control-Button-4>', lambda e: self._zoom(1.2))
        self.canvas.bind('<Control-Button-5>', lambda e: self._zoom(0.8))
        self.canvas.bind('<ButtonPress-2>', self._iniciar_pan)
        self.canvas.bind('<B2-Motion>', self._mover_pan)
        self.canvas.bind('<ButtonRelease-2>', self._finalizar_pan)

    def _zoom(self, fator):
        self.zoom_level *= fator
        self.zoom_level = max(0.2, min(self.zoom_level, 5.0))
        self.label_zoom.configure(text=f"Zoom: {int(self.zoom_level * 100)}%  (Ctrl+Scroll)")
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

    def carregar_imagem_para_mapeamento(self):
        if not self.imagem_atual:
            return
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.label_zoom.configure(text="Zoom: 100%  (Ctrl+Scroll)")
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
                self.canvas.create_text(x1, y1 - 5, text=ph, fill='#28a745',
                                        anchor=tk.W, font=("Helvetica", 10, "bold"))

    # ============================================================
    # ANEXAR / REMOVER DOCUMENTOS
    # ============================================================

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

            self._atualizar_lista_documentos()
            self.status_anexos.configure(text=f"Anexado: {os.path.basename(caminho)}")
            log_info(f"Documento anexado (CTk): {caminho}")

        except Exception as e:
            log_erro(f"Erro ao anexar documento: {str(e)}")
            messagebox.showerror("Erro", str(e))

    def remover_documento(self):
        caminho_remover = None
        for i, doc in enumerate(self.documentos_anexados):
            if doc['caminho'] == self.documento_atual_path:
                caminho_remover = doc['caminho']
                self.documentos_anexados.pop(i)
                remover_ph = [ph for ph, dados in self.mapeamento.items()
                              if dados['documento_path'] == caminho_remover]
                for ph in remover_ph:
                    del self.mapeamento[ph]
                break

        if caminho_remover:
            self._atualizar_lista_documentos()
            self._atualizar_lista_ph_mapeamento()
            self._atualizar_lista_mapeamentos()

            if self.documento_atual_path == caminho_remover:
                self.documento_atual_path = None
                self.imagem_atual = None
                self.canvas.delete("all")

    # ============================================================
    # DESENHO DE RETANGULOS
    # ============================================================

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
                    'x1': int((x1 - self.pan_offset_x) * escala_x),
                    'y1': int((y1 - self.pan_offset_y) * escala_y),
                    'x2': int((x2 - self.pan_offset_x) * escala_x),
                    'y2': int((y2 - self.pan_offset_y) * escala_y)
                }]

                self.canvas.itemconfig(self.retangulo_atual, outline='#0078D4', width=2)
                self.status_anexos.configure(
                    text=f"Retangulo para '{self.placeholder_atual}'. Clique em SALVAR.  [Ctrl+S]"
                )
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
                'documento_tipo': self.documento_tipo,
                'x1': ret['x1'],
                'y1': ret['y1'],
                'x2': ret['x2'],
                'y2': ret['y2']
            }

        self.retangulos_temp = []
        self._atualizar_lista_ph_mapeamento()
        self._atualizar_lista_mapeamentos()

        if self.documento_atual_path and self.placeholder_atual:
            self.carregar_imagem_para_mapeamento()

        self.status_anexos.configure(text=f"Mapeado: {self.placeholder_atual}")

    def limpar_mapeamento(self):
        if messagebox.askyesno("Confirmar", "Limpar todo o mapeamento?"):
            self.mapeamento = {}
            self.undo_stack.clear()
            self.redo_stack.clear()
            self._atualizar_lista_ph_mapeamento()
            self._atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()
            self.status_anexos.configure(text="Mapeamento limpo")

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

        self._atualizar_lista_ph_mapeamento()
        self._atualizar_lista_mapeamentos()
        if self.documento_atual_path:
            self.carregar_imagem_para_mapeamento()
        self.status_anexos.configure(text=f"Desfeito: {ph}")

    def _refazer_retangulo(self):
        if not self.redo_stack:
            messagebox.showinfo("Redo", "Nada para refazer.")
            return

        action = self.redo_stack.pop()
        ph = action['placeholder']

        if action['action'] == 'remove':
            self.undo_stack.append({'action': 'add', 'placeholder': ph})
            if ph in self.mapeamento:
                del self.mapeamento[ph]
        elif action['action'] == 'update':
            self.undo_stack.append({
                'action': 'update',
                'placeholder': ph,
                'old_data': dict(self.mapeamento.get(ph, {}))
            })
            self.mapeamento[ph] = action['old_data']

        self._atualizar_lista_ph_mapeamento()
        self._atualizar_lista_mapeamentos()
        if self.documento_atual_path:
            self.carregar_imagem_para_mapeamento()
        self.status_anexos.configure(text=f"Refeito: {ph}")

    def _remover_retangulo_selecionado(self):
        if self.placeholder_atual and self.placeholder_atual in self.mapeamento:
            self.undo_stack.append({
                'action': 'add',
                'placeholder': self.placeholder_atual,
                'old_data': dict(self.mapeamento[self.placeholder_atual])
            })
            self.redo_stack.clear()
            del self.mapeamento[self.placeholder_atual]
            self._atualizar_lista_ph_mapeamento()
            self._atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()
            self.status_anexos.configure(text=f"Retangulo removido: {self.placeholder_atual}")

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
            'mapeamento': {}
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
            log_info(f"Mapeamento exportado (CTk): {caminho}")
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

            self.undo_stack.clear()
            self.redo_stack.clear()
            self._atualizar_lista_ph_mapeamento()
            self._atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()

            messagebox.showinfo("Importado", f"Mapeamento carregado ({len(self.mapeamento)} campos)")
            log_info(f"Mapeamento importado (CTk): {caminho}")
        except Exception as e:
            log_erro(f"Erro ao importar mapeamento: {str(e)}")
            messagebox.showerror("Erro", f"Arquivo invalido: {str(e)}")

    # ============================================================
    # ABA 4 - GERAR DOCUMENTO
    # ============================================================

    def _criar_aba_gerar(self):
        frame = self.aba_gerar
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Documento Final",
                     font=("Helvetica", 18, "bold")).pack(pady=(20, 5))

        ctk.CTkLabel(frame, text="Extraia dados via OCR, preencha manualmente, revise e gere o documento",
                     text_color="gray", font=("Helvetica", 11)).pack(pady=(0, 10))

        preview_frame = ctk.CTkFrame(frame, corner_radius=10, border_width=1, border_color="#CCCCCC")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        ctk.CTkLabel(preview_frame, text=" Dados Extraidos ",
                     font=("Helvetica", 12, "bold")).pack(pady=(8, 2))

        self.text_preview = ctk.CTkTextbox(preview_frame, height=200,
                                            corner_radius=8, font=("Helvetica", 12),
                                            border_width=1, border_color="#0078D4")
        self.text_preview.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Extrair e Editar Dados",
                      command=self.extrair_e_editar_dados,
                      height=42, corner_radius=10, font=("Helvetica", 13),
                      fg_color="#0078D4", hover_color="#005a9e").pack(side=tk.LEFT, padx=8)

        ctk.CTkButton(btn_frame, text="Preencher Manualmente",
                      command=self.preencher_manualmente,
                      height=42, corner_radius=10, font=("Helvetica", 13),
                      fg_color="#6f42c1", hover_color="#563d7c").pack(side=tk.LEFT, padx=8)

        ctk.CTkButton(btn_frame, text="Gerar Documento  [Ctrl+G]",
                      command=self.gerar_documento_preenchido,
                      height=42, corner_radius=10, font=("Helvetica", 13, "bold"),
                      fg_color="#28a745", hover_color="#218838").pack(side=tk.LEFT, padx=8)

        ctk.CTkButton(btn_frame, text="Gerar em Lote",
                      command=self._processar_em_lote,
                      height=42, corner_radius=10, font=("Helvetica", 13),
                      fg_color="#ffc107", hover_color="#e0a800",
                      text_color="black").pack(side=tk.LEFT, padx=8)

        self.status_gerar = ctk.CTkLabel(frame, text="Aguardando extracao de dados...",
                                          font=("Helvetica", 10), text_color="gray")
        self.status_gerar.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

    def extrair_e_editar_dados(self):
        if not self.mapeamento:
            messagebox.showwarning("Aviso", "Nenhum mapeamento realizado!")
            return

        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            msg = f"Placeholders nao mapeados:\n{', '.join(pendentes)}\n\nContinuar? (ficarao vazios)"
            if not messagebox.askyesno("Aviso", msg):
                self.tabview.set("  Anexar e Mapear  ")
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
        log_info("Extracao de dados iniciada (CTk)")

    def preencher_manualmente(self):
        if not self.placeholders:
            mostrar_aviso_sem_modelo()
            return

        dados_temp = {}
        for placeholder in self.placeholders:
            dados_temp[placeholder] = self.dados_extraidos.get(placeholder, "")

        self.abrir_janela_edicao(dados_temp)
        log_info("Preenchimento manual iniciado (CTk)")

    def abrir_janela_edicao(self, dados_temp):
        self.janela_edicao = ctk.CTkToplevel(self.root)
        self.janela_edicao.title("Editar Dados Extraidos")
        self.janela_edicao.geometry("700x600")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.janela_edicao.geometry(f"700x600+{(sw-700)//2}+{(sh-600)//2}")

        self.janela_edicao.transient(self.root)
        self.janela_edicao.grab_set()

        ctk.CTkLabel(self.janela_edicao, text="Revise e corrija os dados",
                     font=("Helvetica", 15, "bold")).pack(pady=(15, 5))

        ctk.CTkLabel(self.janela_edicao,
                     text="As correcoes serao aplicadas em todas as ocorrencias do placeholder no documento",
                     text_color="gray", font=("Helvetica", 10)).pack()

        scroll_frame = ctk.CTkScrollableFrame(self.janela_edicao, height=400, corner_radius=10)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.campos_entrada = {}
        self.labels_validacao = {}

        for placeholder, valor in dados_temp.items():
            campo_frame = ctk.CTkFrame(scroll_frame, corner_radius=8,
                                       border_width=1, border_color="#CCCCCC")
            campo_frame.pack(fill=tk.X, pady=4, padx=5)

            ctk.CTkLabel(campo_frame, text=placeholder,
                         font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))

            entry = ctk.CTkTextbox(campo_frame, height=50,
                                    corner_radius=6, font=("Helvetica", 12),
                                    border_width=1, border_color="#0078D4")
            entry.insert("1.0", valor)
            entry.pack(fill=tk.X, padx=8, pady=(2, 4))

            self.campos_entrada[placeholder] = entry

            tipo = sugerir_validacao(placeholder.lower())
            if tipo:
                label_val = ctk.CTkLabel(campo_frame,
                                         text=f"Validacao: {tipo}",
                                         text_color="gray",
                                         font=("Helvetica", 9))
                label_val.pack(anchor="w", padx=10, pady=(0, 6))
                self.labels_validacao[placeholder] = label_val

        btn_frame = ctk.CTkFrame(self.janela_edicao, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text="CONFIRMAR E GERAR",
                      command=self.salvar_dados_editados,
                      height=40, corner_radius=10,
                      fg_color="#28a745", hover_color="#218838",
                      font=("Helvetica", 13, "bold")).pack(side=tk.LEFT, padx=10)

        ctk.CTkButton(btn_frame, text="CANCELAR",
                      command=self.janela_edicao.destroy,
                      height=40, corner_radius=10,
                      fg_color="transparent", border_width=1,
                      border_color="#dc3545", text_color="#dc3545",
                      hover_color="#dc3545").pack(side=tk.LEFT, padx=10)

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

        self.text_preview.delete("1.0", tk.END)
        for placeholder, valor in self.dados_extraidos.items():
            self.text_preview.insert(tk.END, f"{placeholder}:\n   {valor}\n\n")

        self.status_gerar.configure(text="Dados editados! Clique em 'Gerar Documento'  [Ctrl+G]")
        self.tabview.set("  Gerar Documento  ")
        log_info("Dados extraidos e editados (CTk)")

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
            self.status_gerar.configure(text=f"Documento salvo: {os.path.basename(save_path)}")
            adicionar_ao_historico(self.modelo_path, self.modelo_tipo,
                                   save_path, len(self.dados_extraidos))
            self._atualizar_tabela_historico()
            log_info(f"Documento gerado (CTk): {save_path}")

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

        self._atualizar_tabela_historico()
        msg = f"Lote concluido!\n\nDocumentos processados: {processados}"
        if erros_lote:
            msg += f"\n\nErros:\n" + "\n".join(erros_lote)
        messagebox.showinfo("Lote Finalizado", msg)
        log_info(f"Processamento em lote (CTk): {processados} documentos")

    # ============================================================
    # ABA 5 - HISTORICO
    # ============================================================

    def _criar_aba_historico(self):
        frame = self.aba_historico
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Historico de Documentos Gerados",
                     font=("Helvetica", 18, "bold")).pack(pady=(20, 5))

        ctk.CTkLabel(frame, text="Registro dos ultimos documentos gerados com o aplicativo",
                     text_color="gray", font=("Helvetica", 11)).pack(pady=(0, 10))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=30, pady=5)

        ctk.CTkButton(btn_frame, text="Atualizar",
                      command=self._atualizar_tabela_historico,
                      height=30, corner_radius=8,
                      fg_color="transparent", border_width=1,
                      border_color="#888888",
                      hover_color="#888888").pack(side=tk.RIGHT, padx=5)

        self.scroll_historico = ctk.CTkScrollableFrame(frame, height=350, corner_radius=10)
        self.scroll_historico.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

        self.status_historico = ctk.CTkLabel(frame, text="",
                                              font=("Helvetica", 10), text_color="gray")
        self.status_historico.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

        self._atualizar_tabela_historico()

    def _atualizar_tabela_historico(self):
        for w in self.scroll_historico.winfo_children():
            w.destroy()

        historico = listar_historico()

        if not historico:
            ctk.CTkLabel(self.scroll_historico,
                         text="Nenhum documento gerado ainda.",
                         text_color="gray", font=("Helvetica", 13)).pack(pady=30)
            self.status_historico.configure(text="Historico vazio")
            return

        col_header = ctk.CTkFrame(self.scroll_historico, fg_color="transparent", height=30)
        col_header.pack(fill=tk.X, padx=5, pady=(2, 0))
        ctk.CTkLabel(col_header, text="Data", font=("Helvetica", 11, "bold"),
                     width=100).pack(side=tk.LEFT, padx=8)
        ctk.CTkLabel(col_header, text="Modelo", font=("Helvetica", 11, "bold"),
                     width=280, anchor="w").pack(side=tk.LEFT, padx=8)
        ctk.CTkLabel(col_header, text="Campos", font=("Helvetica", 11, "bold"),
                     width=60).pack(side=tk.LEFT, padx=8)
        ctk.CTkLabel(col_header, text="Arquivo de Saida", font=("Helvetica", 11, "bold"),
                     width=280, anchor="w").pack(side=tk.LEFT, padx=8)

        sep = ctk.CTkFrame(self.scroll_historico, height=2, fg_color="#CCCCCC", corner_radius=0)
        sep.pack(fill=tk.X, padx=5)

        for item in historico:
            row = ctk.CTkFrame(self.scroll_historico, fg_color="transparent", height=30)
            row.pack(fill=tk.X, padx=5, pady=1)

            data_str = item.get('data', '')[:10]
            modelo = item.get('modelo', '-')[:35]
            campos = str(item.get('num_campos_preenchidos', '-'))
            saida = os.path.basename(item.get('saida', '-'))[:35]

            ctk.CTkLabel(row, text=data_str, width=100,
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)
            ctk.CTkLabel(row, text=modelo, width=280, anchor="w",
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)
            ctk.CTkLabel(row, text=campos, width=60,
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)
            ctk.CTkLabel(row, text=saida, width=280, anchor="w",
                         font=("Helvetica", 11)).pack(side=tk.LEFT, padx=8)

        self.status_historico.configure(text=f"{len(historico)} documento(s) no historico")

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
                'mapeamento': {}
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

                    for w in self.scroll_ph_modelo.winfo_children():
                        w.destroy()
                    for ph in self.placeholders:
                        ctk.CTkLabel(self.scroll_ph_modelo, text=ph,
                                     font=("Helvetica", 12), anchor="w",
                                     padx=10, pady=3).pack(fill=tk.X, pady=1)
                    self._atualizar_lista_ph_mapeamento()

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
                    self._atualizar_lista_mapeamentos()
                    self.status_modelo.configure(text="Mapeamento restaurado do backup.")
                    self.status_anexos.configure(text="Mapeamento restaurado. Continue de onde parou.")
                    log_info("Backup restaurado com sucesso (CTk)")
        except Exception as e:
            log_warning(f"Falha ao restaurar backup: {str(e)}")

    # ============================================================
    # PREFERENCIAS E SOBRE
    # ============================================================

    def _restaurar_preferencias(self):
        prefs = carregar_preferencias()
        tema_salvo = prefs.get('tema_ctk', 'light')
        ctk.set_appearance_mode("Dark" if tema_salvo == "dark" else "Light")
        if tema_salvo == "dark":
            self.btn_tema.configure(text="☀ Modo Claro")

        tamanho = prefs.get('tamanho_janela_ctk')
        if tamanho:
            try:
                self.root.geometry(tamanho)
            except Exception:
                pass

    def _ao_fechar(self):
        try:
            geo = self.root.geometry()
            set_preferencia('tamanho_janela_ctk', geo)
        except Exception:
            pass
        log_info("App CTk finalizado")
        self.root.destroy()

    def _mostrar_sobre(self):
        messagebox.showinfo(
            "Sobre - Meu App de Documentos",
            f"Meu App de Documentos v{VERSAO} (CustomTkinter)\n\n"
            "Automatize o preenchimento de documentos ODT/DOCX usando OCR.\n\n"
            "Interface moderna com CustomTkinter\n"
            "Desenvolvido por Adriano Anthony Jesus Azulay de Araujo\n"
            "E-mail: adrianoanthonymma16@gmail.com\n\n"
            "100% offline - Licenca MIT"
        )
