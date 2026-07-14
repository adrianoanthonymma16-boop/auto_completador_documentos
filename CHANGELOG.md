# Changelog

All notable changes to this project will be documented in this file.

## [3.9.0] - 2026-07-14

### Added
- **Múltiplos modelos** — Botões "Anexar Individualmente" e "Anexar Vários" na aba Modelo
- **Placeholders unificados** — Placeholders iguais entre modelos são mesclados automaticamente
- **Lote de fontes** — Estrutura `self.lote_fontes` para mapear placeholders em vários documentos-fonte
- **Geração unificada** — Único botão "Gerar Documento" (Ctrl+G) cobre todos os cenários
- **Lista de modelos carregados** — Exibe modelos, placeholders e botão remover
- **Backup/Restore e Export/Import** — Incluem `modelos` e `lote_fontes`

### Fixed
- **Bug: `documento_tipo`** — Agora armazenado por retângulo (`finalizar_retangulo`), corrigindo OCR com múltiplos tipos de documento anexados

### Removed
- Botão "Gerar Documento Preenchido", "Gerar em Lote (Modelos)" e "Gerar Lote de Documentos" substituídos por um único "Gerar Documento"

## [3.8.0] - 2026-07-13

### Added
- Interface CustomTkinter com visual moderno (`interface_ctk.py`, `run_ctk.py`)
- CTkScrollableFrame para listas, CTkCanvas para desenho
- Temas Light/Dark nativos via `set_appearance_mode()`
- Instalador duplo — ambas interfaces podem coexistir (ttkbootstrap + CustomTkinter)
- Preenchimento manual de placeholders (digitação direta sem OCR)

## [3.7.0] - 2026-07-02

### Added
- Preenchimento manual de placeholders (botão na aba Gerar)
- Correções nos instaladores

## [3.6.0] - 2026-07-02

### Added
- Dark mode with interactive toggle button
- Keyboard shortcuts (Ctrl+O, Ctrl+A, Ctrl+G, Ctrl+S, Ctrl+Z, Delete)
- Canvas zoom (mouse wheel) and pan (drag)
- Drag & drop file support for models and attachments
- Undo/Redo for rectangle drawings
- Data validation for CPF, dates, and emails during editing
- Batch document generation
- Export/Import mapping configurations (JSON)
- Document preview in generation tab
- Automatic backup of mapping state
- Application logging system (~/.autodoc/app.log)
- Generation history tracking
- User preferences persistence (window size, last directory, theme)
- Project files: requirements.txt, .editorconfig, .gitattributes, SECURITY.md
- GitHub issue templates (bug report, feature request)
- Internationalization module prepared for future translations

### Changed
- Version bumped to 3.6.0
- Theme toggle between light (cosmo) and dark (cyborg)
- Improved window behavior — remembers size/position across sessions

## [3.5.0] - 2026-07-02

### Added
- Modern interface with ttkbootstrap (Cosmo theme)
- Model library — save and reuse templates without re-uploading
- New "Saved Models" tab with interactive table
- New module src/modelos_salvos.py for model persistence

### Changed
- Larger window (1280x820)
- Better styled components with Helvetica font
- Improved usability throughout all tabs

## [3.4.0] - 2026-07-01

### Added
- Initial release
- ODT/DOCX template support
- OCR via Tesseract with image preprocessing
- Document attachment (JPG, PNG, PDF, TIFF, HEIC, WEBP)
- Rectangle drawing for field mapping
- ODT/DOCX generation with placeholder replacement
- Traditional tkinter interface
