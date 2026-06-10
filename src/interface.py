"""
Módulo principal da interface gráfica - VERSÃO COMPLETA
Gerencia as abas, desenho de retângulos e orquestra os outros módulos
FLUXO: Modelo → Anexar documentos → Mapear (dois cliques) → Extrair → Editar → Gerar
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os

# Importa os módulos criados
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
    mostrar_sucesso_geracao
)
from ocr import extrair_texto_do_recorte
from anexo_pdf import pdf_para_imagem, pdf_suportado
from anexo_heic import heic_para_imagem, heic_suportado
from modelo_odt import extrair_placeholders_odt, gerar_odt_preenchido
from modelo_docx import extrair_placeholders_docx, gerar_docx_preenchido, docx_suportado


class AppDocumentos:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Meu App de Documentos - v{VERSAO}")
        self.root.geometry("1200x750")
        
        # Dados do modelo
        self.modelo_path = None
        self.modelo_tipo = None
        self.placeholders = []
        
        # Dados dos documentos anexados
        self.documentos_anexados = []
        
        # Mapeamento
        self.mapeamento = {}
        
        # Estado atual
        self.placeholder_atual = None
        self.documento_atual_path = None
        self.imagem_atual = None
        self.imagem_exibida = None
        self.imagem_exibida_img = None
        
        # Variáveis de desenho
        self.retangulo_atual = None
        self.inicio_x = None
        self.inicio_y = None
        self.retangulos_temp = []
        
        # Dados extraídos
        self.dados_extraidos = {}
        
        self.criar_abas()
        
    def criar_abas(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.aba_modelo = ttk.Frame(self.notebook)
        self.aba_anexos = ttk.Frame(self.notebook)
        self.aba_gerar = ttk.Frame(self.notebook)
        
        self.notebook.add(self.aba_modelo, text="📄 1. Modelo (ODT/DOCX)")
        self.notebook.add(self.aba_anexos, text="📎 2. Anexar e Mapear")
        self.notebook.add(self.aba_gerar, text="✨ 3. Gerar Documento")
        
        self.criar_aba_modelo()
        self.criar_aba_anexos()
        self.criar_aba_gerar()
    
    # ============================================================
    # ABA 1 - MODELO
    # ============================================================
    
    def criar_aba_modelo(self):
        frame = self.aba_modelo
        
        tk.Label(frame, text="Carregar Documento Modelo (ODT ou DOCX)", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(frame, text="O documento deve conter placeholders no formato {{nome_campo}}", 
                 fg="blue").pack()
        
        btn_carregar = tk.Button(frame, text="📁 Carregar Modelo", 
                                  command=self.carregar_modelo,
                                  bg="#4CAF50", fg="white", padx=20, pady=10, 
                                  font=("Arial", 12))
        btn_carregar.pack(pady=20)
        
        self.frame_placeholders = tk.LabelFrame(frame, text="Placeholders Encontrados", 
                                                 padx=10, pady=10)
        self.frame_placeholders.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.lista_placeholders = tk.Listbox(self.frame_placeholders, height=8, 
                                              font=("Arial", 10))
        self.lista_placeholders.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll = tk.Scrollbar(self.frame_placeholders, orient=tk.VERTICAL, 
                              command=self.lista_placeholders.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_placeholders.config(yscrollcommand=scroll.set)
        
        self.status_modelo = tk.Label(frame, text="Aguardando carregamento do modelo...", 
                                       bd=1, relief=tk.SUNKEN, anchor=tk.W)
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
                
                self.status_modelo.config(text=f"✅ Modelo carregado! {len(self.placeholders)} placeholders.")
                self.status_anexos.config(text=f"✅ Modelo carregado. Agora anexe documentos.")
                
                self.notebook.select(self.aba_anexos)
            else:
                messagebox.showwarning("Aviso", "Nenhum placeholder {{...}} encontrado.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {str(e)}")
    
    # ============================================================
    # ABA 2 - ANEXAR E MAPEAR
    # ============================================================
    
    def criar_aba_anexos(self):
        frame = self.aba_anexos
        
        frame_top = tk.Frame(frame)
        frame_top.pack(pady=5, fill=tk.X)
        
        btn_anexar = tk.Button(frame_top, text="📷 Anexar Documento", 
                                command=self.anexar_documento,
                                bg="#4CAF50", fg="white", padx=10)
        btn_anexar.pack(side=tk.LEFT, padx=5)
        
        btn_limpar = tk.Button(frame_top, text="🗑️ Limpar Mapeamento", 
                                command=self.limpar_mapeamento,
                                bg="#FF9800", fg="white", padx=10)
        btn_limpar.pack(side=tk.LEFT, padx=5)
        
        btn_remover = tk.Button(frame_top, text="❌ Remover Documento", 
                                 command=self.remover_documento,
                                 bg="#f44336", fg="white", padx=10)
        btn_remover.pack(side=tk.LEFT, padx=5)
        
        instr = tk.Label(frame, text="✏️ 1. Clique placeholder | 2. Clique documento | 3. Desenhe retângulo | 4. Salvar", 
                         fg="red", font=("Arial", 9, "bold"))
        instr.pack(pady=5)
        
        frame_duplo = tk.Frame(frame)
        frame_duplo.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Placeholders
        frame_ph = tk.LabelFrame(frame_duplo, text="PLACEHOLDERS", padx=5, pady=5)
        frame_ph.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.lista_placeholders_aba2 = tk.Listbox(frame_ph, height=10, font=("Arial", 10))
        self.lista_placeholders_aba2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lista_placeholders_aba2.bind('<<ListboxSelect>>', self.selecionar_placeholder_aba2)
        
        scroll_ph = tk.Scrollbar(frame_ph, orient=tk.VERTICAL, command=self.lista_placeholders_aba2.yview)
        scroll_ph.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_placeholders_aba2.config(yscrollcommand=scroll_ph.set)
        
        # Documentos
        frame_doc = tk.LabelFrame(frame_duplo, text="DOCUMENTOS", padx=5, pady=5)
        frame_doc.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.lista_documentos = tk.Listbox(frame_doc, height=10, font=("Arial", 10))
        self.lista_documentos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lista_documentos.bind('<<ListboxSelect>>', self.selecionar_documento_aba2)
        
        scroll_doc = tk.Scrollbar(frame_doc, orient=tk.VERTICAL, command=self.lista_documentos.yview)
        scroll_doc.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_documentos.config(yscrollcommand=scroll_doc.set)
        
        # Status
        frame_status = tk.Frame(frame)
        frame_status.pack(pady=5, fill=tk.X, padx=10)
        
        self.status_placeholder_sel = tk.Label(frame_status, text="📌 Placeholder: NENHUM", fg="blue")
        self.status_placeholder_sel.pack(side=tk.LEFT, padx=5)
        
        self.status_documento_sel = tk.Label(frame_status, text="📄 Documento: NENHUM", fg="green")
        self.status_documento_sel.pack(side=tk.RIGHT, padx=5)
        
        # Canvas
        frame_img = tk.Frame(frame)
        frame_img.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(frame_img, bg='lightgray')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll_y = tk.Scrollbar(frame_img, orient=tk.VERTICAL, command=self.canvas.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scroll_y.set)
        
        self.canvas.bind("<ButtonPress-1>", self.iniciar_retangulo)
        self.canvas.bind("<B1-Motion>", self.desenhar_retangulo)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_retangulo)
        
        btn_salvar = tk.Button(frame, text="💾 SALVAR MAPEAMENTO", 
                                command=self.salvar_mapeamento,
                                bg="#2196F3", fg="white", padx=20, pady=5)
        btn_salvar.pack(pady=5)
        
        # Lista de mapeamentos
        self.frame_mapeamentos = tk.LabelFrame(frame, text="MAPEAMENTOS", padx=10, pady=5)
        self.frame_mapeamentos.pack(fill=tk.X, padx=10, pady=5)
        
        self.lista_mapeamentos = tk.Listbox(self.frame_mapeamentos, height=6)
        self.lista_mapeamentos.pack(fill=tk.BOTH, expand=True)
        
        self.status_anexos = tk.Label(frame, text="Aguardando modelo...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
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
            self.status_placeholder_sel.config(text=f"📌 Placeholder: {placeholder}")
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
                    self.status_documento_sel.config(text=f"📄 Documento: {nome_doc}")
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
                self.canvas.create_rectangle(x1, y1, x2, y2, outline='green', width=2)
                self.canvas.create_text(x1, y1-5, text=ph, fill='green', anchor=tk.W)
    
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
            self.status_anexos.config(text=f"✅ Anexado: {os.path.basename(caminho)}")
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))
    
    def remover_documento(self):
        selecao = self.lista_documentos.curselection()
        if not selecao:
            return
        
        nome_doc = self.lista_documentos.get(selecao[0])
        for i, doc in enumerate(self.documentos_anexados):
            if doc['nome'] == nome_doc:
                caminho_remover = doc['caminho']
                self.documentos_anexados.pop(i)
                remover_ph = [ph for ph, dados in self.mapeamento.items() if dados['documento_path'] == caminho_remover]
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
                outline='red', width=2, dash=(4, 4)
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
                
                self.canvas.itemconfig(self.retangulo_atual, outline='blue', width=2)
                self.status_anexos.config(text=f"🔵 Retângulo para '{self.placeholder_atual}'. Clique em SALVAR.")
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
        
        self.status_anexos.config(text=f"✅ Mapeado: {self.placeholder_atual}")
    
    def atualizar_lista_mapeamentos(self):
        self.lista_mapeamentos.delete(0, tk.END)
        for ph, dados in self.mapeamento.items():
            nome_doc = os.path.basename(dados['documento_path'])
            self.lista_mapeamentos.insert(tk.END, f"✓ {ph} → {nome_doc}")
        
        pendentes = [ph for ph in self.placeholders if ph not in self.mapeamento]
        if pendentes:
            self.lista_mapeamentos.insert(tk.END, f"⚠️ Pendentes: {', '.join(pendentes)}")
    
    def limpar_mapeamento(self):
        if messagebox.askyesno("Confirmar", "Limpar todo o mapeamento?"):
            self.mapeamento = {}
            self.atualizar_lista_placeholders_aba2()
            self.atualizar_lista_mapeamentos()
            if self.documento_atual_path:
                self.carregar_imagem_para_mapeamento()
            self.status_anexos.config(text="🗑️ Mapeamento limpo")
    
    # ============================================================
    # ABA 3 - GERAR DOCUMENTO
    # ============================================================
    
    def criar_aba_gerar(self):
        frame = self.aba_gerar
        
        tk.Label(frame, text="Documento Final", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.frame_preview = tk.LabelFrame(frame, text="Dados Extraídos", padx=10, pady=10)
        self.frame_preview.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.text_preview = tk.Text(self.frame_preview, height=15, font=("Arial", 10))
        self.text_preview.pack(fill=tk.BOTH, expand=True)
        
        btn_extrair = tk.Button(frame, text="🔍 Extrair e Editar Dados", 
                                 command=self.extrair_e_editar_dados,
                                 bg="#2196F3", fg="white", padx=20, pady=10)
        btn_extrair.pack(pady=5)
        
        btn_gerar = tk.Button(frame, text="📄 Gerar Documento Preenchido", 
                               command=self.gerar_documento_preenchido,
                               bg="#4CAF50", fg="white", padx=20, pady=10)
        btn_gerar.pack(pady=5)
        
        self.status_gerar = tk.Label(frame, text="Aguardando...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
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
        self.janela_edicao.title("✏️ Editar Dados Extraídos")
        self.janela_edicao.geometry("650x550")
        self.janela_edicao.transient(self.root)
        self.janela_edicao.grab_set()
        
        tk.Label(self.janela_edicao, text="Revise e corrija os dados extraídos", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self.janela_edicao, text="As correções vão para todas as ocorrências do placeholder", 
                 fg="blue").pack()
        
        frame_campos = tk.Frame(self.janela_edicao)
        frame_campos.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas_campos = tk.Canvas(frame_campos)
        scrollbar = tk.Scrollbar(frame_campos, orient=tk.VERTICAL, command=canvas_campos.yview)
        scrollable_frame = tk.Frame(canvas_campos)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas_campos.configure(scrollregion=canvas_campos.bbox("all")))
        canvas_campos.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_campos.configure(yscrollcommand=scrollbar.set)
        
        canvas_campos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.campos_entrada = {}
        
        for placeholder, valor in dados_temp.items():
            frame_campo = tk.LabelFrame(scrollable_frame, text=placeholder, padx=10, pady=5)
            frame_campo.pack(fill=tk.X, pady=5)
            
            entry = tk.Text(frame_campo, height=3, font=("Arial", 10))
            entry.insert(tk.END, valor)
            entry.pack(fill=tk.X, padx=5, pady=5)
            
            self.campos_entrada[placeholder] = entry
        
        frame_botoes = tk.Frame(self.janela_edicao)
        frame_botoes.pack(pady=10)
        
        btn_confirmar = tk.Button(frame_botoes, text="✅ CONFIRMAR E GERAR", 
                                   command=self.salvar_dados_editados,
                                   bg="#4CAF50", fg="white", padx=20, pady=5)
        btn_confirmar.pack(side=tk.LEFT, padx=10)
        
        btn_cancelar = tk.Button(frame_botoes, text="❌ CANCELAR", 
                                  command=self.janela_edicao.destroy,
                                  bg="#f44336", fg="white", padx=20, pady=5)
        btn_cancelar.pack(side=tk.LEFT, padx=10)
    
    def salvar_dados_editados(self):
        """Salva os dados editados e gera o documento"""
        self.dados_extraidos = {}
        
        for placeholder, entry in self.campos_entrada.items():
            texto = entry.get("1.0", tk.END).strip()
            self.dados_extraidos[placeholder] = texto if texto else ""
        
        self.janela_edicao.destroy()
        
        # Mostra preview na aba 3
        self.text_preview.delete(1.0, tk.END)
        for placeholder, valor in self.dados_extraidos.items():
            self.text_preview.insert(tk.END, f"📌 {placeholder}:\n   {valor}\n\n")
        
        self.status_gerar.config(text="✅ Dados editados! Clique em 'Gerar Documento Preenchido'")
        self.notebook.select(self.aba_gerar)
    
    def gerar_documento_preenchido(self):
        """Gera o documento final ODT ou DOCX"""
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
            self.status_gerar.config(text=f"✅ {os.path.basename(save_path)}")
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AppDocumentos(root)
    root.mainloop()