# Meu App de Documentos &middot; [English](#english)

[![Version](https://img.shields.io/badge/version-3.8-blue)](https://github.com/adrianoanthonymma16-boop/auto_completador_documentos)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux-orange)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE.txt)

Automatize o preenchimento de documentos ODT/DOCX usando OCR com duas interfaces disponíveis: ttkbootstrap (leve) e CustomTkinter (moderna).

---

## Funcionalidades

- **Duas Interfaces** — Escolha entre ttkbootstrap (leve) ou CustomTkinter (visual moderno)
- **Modelos ODT/DOCX** — Placeholders `{{nome}}`, `{{cpf}}`, `{{data}}`
- **Preenchimento Manual** — Digite valores diretamente nos placeholders, sem precisar de OCR
- **OCR Inteligente** — Tesseract com pré-processamento avançado de imagem
- **Biblioteca de Modelos** — Salve e reutilize templates frequentes com um clique
- **Mapeamento Visual** — Desenhe retângulos nos campos para extração precisa
- **Modo Escuro** — Alternância instantânea com um botão (Ctrl+D)
- **Atalhos de Teclado** — Ctrl+O (modelo), Ctrl+A (anexar), Ctrl+G (gerar), Ctrl+S (salvar), Ctrl+Z (desfazer), Ctrl+E (exportar), Ctrl+I (importar)
- **Zoom e Pan** — Ctrl+Scroll para zoom, botão do meio para arrastar
- **Undo/Redo** — Desfaça e refaça retângulos de mapeamento
- **Validação de Dados** — CPF, data, email e telefone validados automaticamente
- **Exportar/Importar Mapeamento** — Salve e carregue configurações em JSON
- **Backup Automático** — Mapeamento salvo a cada 60 segundos — nunca perca seu trabalho
- **Histórico de Geração** — Registro completo dos documentos gerados
- **Processamento em Lote** — Preencha múltiplos documentos com os mesmos dados
- **100% Offline** — Sem nuvem, sem internet, seus dados nunca saem da máquina

---

## Requisitos

### Sistema

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself
```

### Python

```bash
pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx ttkbootstrap customtkinter
```

Ou use o script automático:

```bash
bash install_dependencies.sh
```

### Opcional — HEIC (iPhone)

```bash
sudo apt install -y libheif-dev
pip3 install pyheif
```

---

## Uso Rápido

```bash
# Interface ttkbootstrap (original)
python3 run.py

# Interface CustomTkinter (moderna)
python3 run_ctk.py
```

### Fluxo de Trabalho

1. **Modelo** — Carregue um ODT/DOCX com placeholders `{{...}}`
2. **Modelos Salvos** — (opcional) Salve na biblioteca para reuso
3. **Anexar e Mapear** — Anexe fotos/PDFs, desenhe retângulos nos campos
4. **Gerar Documento** — Extraia via OCR, revise, gere o documento final
5. **Histórico** — Consulte os documentos gerados anteriormente

---

## Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+O` | Carregar modelo |
| `Ctrl+A` | Anexar documento |
| `Ctrl+G` | Gerar documento preenchido |
| `Ctrl+S` | Salvar mapeamento |
| `Ctrl+Z` | Desfazer retângulo |
| `Ctrl+E` | Exportar mapeamento |
| `Ctrl+I` | Importar mapeamento |
| `Ctrl+D` | Alternar modo escuro/claro |
| `Delete` | Remover retângulo selecionado |
| `Ctrl+Scroll` | Zoom na imagem |
| `Botão Meio + Arrastar` | Mover imagem |

---

## Gerar Instalador

```bash
# Versão ttkbootstrap (original)
bash build_installer.sh

# Versão CustomTkinter (moderna)
bash build_installer_ctk.sh
```

Gera arquivos `.run` autoextraíveis para cada interface.

---

## Instalar

```bash
# ttkbootstrap
chmod +x MeuAppDocumentos-*.run
./MeuAppDocumentos-*.run

# CustomTkinter
chmod +x MeuAppDocumentosCTk-*.run
./MeuAppDocumentosCTk-*.run
```

Ambas as versões podem coexistir na mesma máquina — são instaladas em diretórios separados.

---

## Estrutura do Projeto

```
meu_app_documentos/
├── run.py                    # Entry point tkinter
├── run_ctk.py                # Entry point CustomTkinter
├── build_installer.sh         # Gera instalador .run (tkinter)
├── build_installer_ctk.sh     # Gera instalador .run (CustomTkinter)
├── install.sh                 # Instalador interno tkinter
├── install_ctk.sh             # Instalador interno CustomTkinter
├── install_dependencies.sh
├── iniciar.sh                 # Launcher tkinter
├── iniciar_ctk.sh             # Launcher CustomTkinter
├── desinstalar.sh             # Desinstalador tkinter
├── desinstalar_ctk.sh         # Desinstalador CustomTkinter
├── requirements.txt
├── .editorconfig
├── .gitattributes
├── LICENSE.txt
├── README.md
├── CHANGELOG.md
├── SECURITY.md
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
└── src/
    ├── config.py
    ├── validadores.py
    ├── validadores_extra.py
    ├── mensagens.py
    ├── i18n.py
    ├── logger.py
    ├── preferencias.py
    ├── historico.py
    ├── ocr.py
    ├── anexo_pdf.py
    ├── anexo_heic.py
    ├── modelo_odt.py
    ├── modelo_docx.py
    ├── modelos_salvos.py
    ├── interface.py            # GUI tkinter/ttkbootstrap
    └── interface_ctk.py        # GUI CustomTkinter
```

---

## Versões

### v3.8 (atual)
- **Interface CustomTkinter** — Nova GUI com visual moderno, scrollframes interativos e tema escuro/claro nativo
- **Instalador duplo** — Instale e use ambas as interfaces lado a lado (ttkbootstrap + CustomTkinter)
- **Preenchimento manual de placeholders** — Digite valores diretamente sem precisar de OCR ou documentos anexados
- `run_ctk.py` — Entry point para a interface CustomTkinter
- Scripts de build/install/desinstalar específicos para cada interface
- Nova dependência: `customtkinter >= 5.2.0`

### v3.7
- Preenchimento manual de placeholders (botão na aba Gerar)
- Correções e melhorias nos instaladores

### v3.6
- Modo escuro com botão interativo (Ctrl+D)
- Atalhos de teclado para todas as operações principais
- Zoom (Ctrl+Scroll) e Pan (botão do meio) no canvas
- Undo/Redo de retângulos
- Validação automática de CPF, data, email e telefone
- Exportar/Importar mapeamento em JSON
- Backup automático do mapeamento a cada 60 segundos
- Histórico de documentos gerados (nova aba)
- Processamento em lote de múltiplos modelos
- Persistência de preferências (tema, tamanho da janela, último diretório)
- Arquivos de projeto: requirements.txt, .editorconfig, .gitattributes, SECURITY.md, CHANGELOG.md
- GitHub Issue Templates (bug report, feature request)
- Sistema de logging em arquivo
- Módulo de internacionalização preparado
- Nova dependência: `ttkbootstrap`

### v3.5
- Interface moderna com **ttkbootstrap** (tema Cosmo)
- **Biblioteca de Modelos Salvos** — salve e reutilize templates
- Nova aba "Modelos Salvos" com tabela interativa
- Janela maior (1280x820), componentes estilizados
- Módulo `src/modelos_salvos.py`

### v3.4 (branch [`v3.4-legacy`](https://github.com/adrianoanthonymma16-boop/auto_completador_documentos/tree/v3.4-legacy))
- Interface tkinter tradicional
- Fluxo: Modelo → Anexar e Mapear (OCR) → Gerar Documento
- Suporte a ODT, DOCX, PDF, HEIC e imagens

---

## Contato

Adriano Anthony Jesus Azulay de Araujo  
E-mail: adrianoanthonymma16@gmail.com

---

## Licença

Software de código aberto sob a licença MIT. Veja o arquivo [LICENSE.txt](LICENSE.txt) para os termos completos.

<br>
<hr>
<br>

<a id="english"></a>

# My Document App &middot; [Português](#meu-app-de-documentos)

[![Version](https://img.shields.io/badge/version-3.8-blue)](https://github.com/adrianoanthonymma16-boop/auto_completador_documentos)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux-orange)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE.txt)

Automate ODT/DOCX document filling using OCR with two available interfaces: ttkbootstrap (lightweight) and CustomTkinter (modern).

---

## Features

- **Dual Interface** — Choose between ttkbootstrap (lightweight) or CustomTkinter (modern look)
- **ODT/DOCX Templates** — Placeholders `{{name}}`, `{{cpf}}`, `{{date}}`
- **Manual Filling** — Type values directly into placeholders, no OCR needed
- **Smart OCR** — Tesseract with advanced image pre-processing
- **Template Library** — Save and reuse frequent templates with one click
- **Visual Mapping** — Draw rectangles on fields for precise extraction
- **Dark Mode** — Instant toggle with a button (Ctrl+D)
- **Keyboard Shortcuts** — Ctrl+O (template), Ctrl+A (attach), Ctrl+G (generate), Ctrl+S (save), Ctrl+Z (undo), Ctrl+E (export), Ctrl+I (import)
- **Zoom and Pan** — Ctrl+Scroll to zoom, middle button to drag
- **Undo/Redo** — Undo and redo mapping rectangles
- **Data Validation** — CPF, date, email and phone validated automatically
- **Export/Import Mapping** — Save and load configurations in JSON
- **Automatic Backup** — Mapping saved every 60 seconds — never lose your work
- **Generation History** — Complete log of generated documents
- **Batch Processing** — Fill multiple documents with the same data
- **100% Offline** — No cloud, no internet, your data never leaves the machine

---

## Requirements

### System

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself
```

### Python

```bash
pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx ttkbootstrap customtkinter
```

Or use the automated script:

```bash
bash install_dependencies.sh
```

### Optional — HEIC (iPhone)

```bash
sudo apt install -y libheif-dev
pip3 install pyheif
```

---

## Quick Start

```bash
# ttkbootstrap interface (original)
python3 run.py

# CustomTkinter interface (modern)
python3 run_ctk.py
```

### Workflow

1. **Template** — Load an ODT/DOCX with `{{...}}` placeholders
2. **Saved Templates** — (optional) Save to library for reuse
3. **Attach and Map** — Attach photos/PDFs, draw rectangles on fields
4. **Generate Document** — Extract via OCR, review, generate the final document
5. **History** — Browse previously generated documents

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Load template |
| `Ctrl+A` | Attach document |
| `Ctrl+G` | Generate filled document |
| `Ctrl+S` | Save mapping |
| `Ctrl+Z` | Undo rectangle |
| `Ctrl+E` | Export mapping |
| `Ctrl+I` | Import mapping |
| `Ctrl+D` | Toggle dark/light mode |
| `Delete` | Remove selected rectangle |
| `Ctrl+Scroll` | Zoom image |
| `Middle Button + Drag` | Pan image |

---

## Build Installer

```bash
bash build_installer.sh
```

Generates a self-extracting `.run` file.

---

## Install

```bash
chmod +x MeuAppDocumentos-*.run
./MeuAppDocumentos-*.run
```

---

## Project Structure

```
meu_app_documentos/
├── run.py                    # Entry point tkinter
├── run_ctk.py                # Entry point CustomTkinter
├── build_installer.sh         # .run installer builder (tkinter)
├── build_installer_ctk.sh     # .run installer builder (CustomTkinter)
├── install.sh                 # Internal installer tkinter
├── install_ctk.sh             # Internal installer CustomTkinter
├── install_dependencies.sh
├── iniciar.sh                 # Launcher tkinter
├── iniciar_ctk.sh             # Launcher CustomTkinter
├── desinstalar.sh             # Uninstaller tkinter
├── desinstalar_ctk.sh         # Uninstaller CustomTkinter
├── requirements.txt
├── .editorconfig
├── .gitattributes
├── LICENSE.txt
├── README.md
├── CHANGELOG.md
├── SECURITY.md
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
└── src/
    ├── config.py
    ├── validadores.py
    ├── validadores_extra.py
    ├── mensagens.py
    ├── i18n.py
    ├── logger.py
    ├── preferencias.py
    ├── historico.py
    ├── ocr.py
    ├── anexo_pdf.py
    ├── anexo_heic.py
    ├── modelo_odt.py
    ├── modelo_docx.py
    ├── modelos_salvos.py
    ├── interface.py            # GUI tkinter/ttkbootstrap
    └── interface_ctk.py        # GUI CustomTkinter
```

---

## Versions

### v3.8 (current)
- **CustomTkinter Interface** — New GUI with modern look, interactive scrollframes and native dark/light theme
- **Dual installer** — Install and use both interfaces side by side (ttkbootstrap + CustomTkinter)
- **Manual placeholder filling** — Type values directly without OCR or attached documents
- `run_ctk.py` — Entry point for the CustomTkinter interface
- Separate build/install/uninstall scripts for each interface
- New dependency: `customtkinter >= 5.2.0`

### v3.7
- Manual placeholder filling (button in the Generate tab)
- Installer fixes and improvements

### v3.6
- Dark mode with interactive button (Ctrl+D)
- Keyboard shortcuts for all main operations
- Zoom (Ctrl+Scroll) and Pan (middle button) on canvas
- Undo/Redo of rectangles
- Automatic CPF, date, email and phone validation
- Export/Import mapping in JSON
- Automatic mapping backup every 60 seconds
- Generated documents history (new tab)
- Batch processing of multiple templates
- Preferences persistence (theme, window size, last directory)
- Project files: requirements.txt, .editorconfig, .gitattributes, SECURITY.md, CHANGELOG.md
- GitHub Issue Templates (bug report, feature request)
- File-based logging system
- Internationalization module prepared
- New dependency: `ttkbootstrap`

### v3.5
- Modern interface with **ttkbootstrap** (Cosmo theme)
- **Saved Templates Library** — save and reuse templates
- New "Saved Templates" tab with interactive table
- Larger window (1280x820), styled components
- Module `src/modelos_salvos.py`

### v3.4 (branch [`v3.4-legacy`](https://github.com/adrianoanthonymma16-boop/auto_completador_documentos/tree/v3.4-legacy))
- Traditional tkinter interface
- Flow: Template → Attach and Map (OCR) → Generate Document
- Support for ODT, DOCX, PDF, HEIC and images

---

## Contact

Adriano Anthony Jesus Azulay de Araujo  
E-mail: adrianoanthonymma16@gmail.com

---

## License

Open source software under the MIT license. See [LICENSE.txt](LICENSE.txt) for the full terms.
