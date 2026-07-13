#!/usr/bin/env bash
# =============================================================================
# Meu App de Documentos (CustomTkinter) — Build do Instalador .run
# =============================================================================
set -e

APP_NAME="Meu App de Documentos (CustomTkinter)"
APP_VERSION="3.8"
OUTPUT_FILE="MeuAppDocumentosCTk-v${APP_VERSION}-installer.run"
BUILD_DIR="/tmp/meu_app_ctk_build_$$"

echo "=================================================="
echo "  Build do Instalador CTk — $APP_NAME v$APP_VERSION"
echo "=================================================="

if ! command -v makeself &>/dev/null; then
    echo ""
    echo "ERRO: makeself não encontrado."
    echo "Instale com: sudo apt install makeself"
    echo ""
    exit 1
fi

PROJECT_DIR="$(dirname "$(realpath "$0")")"

echo ""
echo "[1/5] Preparando diretório de build em $BUILD_DIR..."
mkdir -p "$BUILD_DIR/src"

echo "[2/5] Copiando arquivos do app..."
cp "$PROJECT_DIR/run_ctk.py"                       "$BUILD_DIR/"
cp "$PROJECT_DIR/src/config.py"                    "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/validadores.py"               "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/validadores_extra.py"         "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/mensagens.py"                 "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/i18n.py"                      "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/logger.py"                    "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/preferencias.py"              "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/historico.py"                 "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/ocr.py"                       "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/anexo_pdf.py"                 "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/anexo_heic.py"                "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/modelo_odt.py"                "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/modelo_docx.py"               "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/modelos_salvos.py"            "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/interface_ctk.py"             "$BUILD_DIR/src/"
cp "$PROJECT_DIR/install_ctk.sh"                   "$BUILD_DIR/"
cp "$PROJECT_DIR/iniciar_ctk.sh"                   "$BUILD_DIR/"
cp "$PROJECT_DIR/desinstalar_ctk.sh"               "$BUILD_DIR/"
cp "$PROJECT_DIR/LICENSE.txt"                      "$BUILD_DIR/"

if [ -f "$PROJECT_DIR/icon.png" ]; then
    cp "$PROJECT_DIR/icon.png" "$BUILD_DIR/"
    echo "   ✓ Ícone personalizado incluído."
else
    echo "   ⚠ Ícone não encontrado — será usado ícone genérico do sistema."
fi

echo "[3/5] Ajustando permissões..."
chmod +x "$BUILD_DIR/install_ctk.sh"
chmod +x "$BUILD_DIR/iniciar_ctk.sh"
chmod +x "$BUILD_DIR/desinstalar_ctk.sh"

echo "[4/5] Gerando $OUTPUT_FILE com makeself..."
makeself \
    "$BUILD_DIR" \
    "$OUTPUT_FILE" \
    "$APP_NAME v$APP_VERSION" \
    "./install_ctk.sh"

echo "[5/5] Limpando arquivos temporários..."
rm -rf "$BUILD_DIR"

echo ""
echo "=================================================="
echo "  ✅ Instalador CTk gerado com sucesso!"
echo "  📦 Arquivo: $OUTPUT_FILE"
echo "  📏 Tamanho: $(du -sh "$OUTPUT_FILE" | cut -f1)"
echo "=================================================="
echo ""
echo "Para testar a instalação:"
echo "  chmod +x $OUTPUT_FILE"
echo "  ./$OUTPUT_FILE"
echo ""
