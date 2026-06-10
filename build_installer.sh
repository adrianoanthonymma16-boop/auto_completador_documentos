#!/usr/bin/env bash
# =============================================================================
# build_installer.sh
# Gera o instalador.run auto-extraível usando makeself
#
# USO:
#   1. Coloque este script na raiz do projeto (junto com run.py e src/)
#   2. Execute: bash build_installer.sh
#   3. O arquivo "MeuAppDocumentos-v3.4-installer.run" será gerado
#
# REQUISITO:
#   sudo apt install makeself
# =============================================================================
set -e
APP_NAME="Meu App de Documentos"
APP_VERSION="3.4"
OUTPUT_FILE="MeuAppDocumentos-v${APP_VERSION}-installer.run"
BUILD_DIR="/tmp/meu_app_build_$$"
echo "=================================================="
echo "  Build do Instalador — $APP_NAME v$APP_VERSION"
echo "=================================================="
# Verifica makeself
if ! command -v makeself &>/dev/null; then
    echo ""
    echo "ERRO: makeself não encontrado."
    echo "Instale com: sudo apt install makeself"
    echo ""
    exit 1
fi
# Diretório do projeto (onde este script está)
PROJECT_DIR="$(dirname "$(realpath "$0")")"
echo ""
echo "[1/5] Preparando diretório de build em $BUILD_DIR..."
mkdir -p "$BUILD_DIR/src"
echo "[2/5] Copiando arquivos do app..."
# Arquivos da raiz
cp "$PROJECT_DIR/run.py"                          "$BUILD_DIR/"
# Módulos src/
cp "$PROJECT_DIR/src/config.py"                   "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/validadores.py"              "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/mensagens.py"                "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/ocr.py"                      "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/anexo_pdf.py"                "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/anexo_heic.py"               "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/modelo_odt.py"               "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/modelo_docx.py"              "$BUILD_DIR/src/"
cp "$PROJECT_DIR/src/interface.py"                "$BUILD_DIR/src/"
# Scripts de instalação e suporte
cp "$PROJECT_DIR/install.sh"                      "$BUILD_DIR/"
cp "$PROJECT_DIR/iniciar.sh"                      "$BUILD_DIR/"
cp "$PROJECT_DIR/desinstalar.sh"                  "$BUILD_DIR/"
cp "$PROJECT_DIR/LICENSE.txt"                     "$BUILD_DIR/"
# Ícone (se existir)
if [ -f "$PROJECT_DIR/icon.png" ]; then
    cp "$PROJECT_DIR/icon.png" "$BUILD_DIR/"
    echo "   ✓ Ícone personalizado incluído."
else
    echo "   ⚠ Ícone não encontrado — será usado ícone genérico do sistema."
fi
echo "[3/5] Ajustando permissões..."
chmod +x "$BUILD_DIR/install.sh"
chmod +x "$BUILD_DIR/iniciar.sh"
chmod +x "$BUILD_DIR/desinstalar.sh"
echo "[4/5] Gerando $OUTPUT_FILE com makeself..."
makeself \
    "$BUILD_DIR" \
    "$OUTPUT_FILE" \
    "$APP_NAME v$APP_VERSION" \
    "./install.sh"
echo "[5/5] Limpando arquivos temporários..."
rm -rf "$BUILD_DIR"
echo ""
echo "=================================================="
echo "  ✅ Instalador gerado com sucesso!"
echo "  📦 Arquivo: $OUTPUT_FILE"
echo "  📏 Tamanho: $(du -sh "$OUTPUT_FILE" | cut -f1)"
echo "=================================================="
echo ""
echo "Para testar a instalação:"
echo "  chmod +x $OUTPUT_FILE"
echo "  ./$OUTPUT_FILE"
echo ""
