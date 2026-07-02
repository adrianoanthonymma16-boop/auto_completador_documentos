# Changelog

All notable changes to this project will be documented in this file.

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
- Application logging system (~/.meu_app_documentos/app.log)
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
