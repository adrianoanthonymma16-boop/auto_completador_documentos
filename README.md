# Meu App de Documentos

[![Versão](https://img.shields.io/badge/versão-3.6-blue)](https://github.com/adrianoanthonymma16-boop/auto_completador_documentos)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/plataforma-Linux-orange)](https://ubuntu.com/)
[![Licença](https://img.shields.io/badge/licença-Proprietária-red)](LICENSE.txt)

Automatize o preenchimento de documentos ODT/DOCX usando OCR com uma interface moderna e produtiva.

---

## Funcionalidades

- **Modelos ODT/DOCX** — Placeholders `{{nome}}`, `{{cpf}}`, `{{data}}`
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
pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx ttkbootstrap
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
python3 run.py
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
bash build_installer.sh
```

Gera um arquivo `.run` autoextraível.

---

## Instalar

```bash
chmod +x MeuAppDocumentos-*.run
./MeuAppDocumentos-*.run
```

---

## Estrutura do Projeto

```
meu_app_documentos/
├── run.py
├── build_installer.sh
├── install.sh
├── install_dependencies.sh
├── iniciar.sh
├── desinstalar.sh
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
    └── interface.py
```

---

## Versões

### v3.6 (atual)
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

Software proprietário. Veja o arquivo [LICENSE.txt](LICENSE.txt) para os termos completos.
