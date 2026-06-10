#!/usr/bin/env bash
# =============================================================================
# Meu App de Documentos — Instalador Interno
# Executado automaticamente pelo .run auto-extraível
# =============================================================================

APP_NAME="Meu App de Documentos"
APP_VERSION="3.4"
APP_EXEC="meu-app-documentos"
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
LICENSE_FILE="$SCRIPT_DIR/LICENSE.txt"

# -----------------------------------------------------------------------------
# UTILITÁRIOS
# -----------------------------------------------------------------------------

check_zenity() {
    if ! command -v zenity &>/dev/null; then
        echo "ERRO: zenity não encontrado. Instale com: sudo apt install zenity"
        exit 1
    fi
}

abort() {
    zenity --error \
        --title="Instalação cancelada" \
        --text="$1" \
        --width=380 2>/dev/null
    exit 1
}

# -----------------------------------------------------------------------------
# PASSO 0 — Verifica zenity
# -----------------------------------------------------------------------------

check_zenity

# -----------------------------------------------------------------------------
# PASSO 1 — BOAS-VINDAS
# -----------------------------------------------------------------------------

zenity --info \
    --title="Bem-vindo ao $APP_NAME" \
    --text="<b>$APP_NAME v$APP_VERSION</b>\n\nEste assistente irá guiá-lo pela instalação do app.\n\n• Instalação das dependências Python\n• Verificação do Tesseract OCR\n• Criação de atalhos no Desktop e no Menu\n\nClique em <b>OK</b> para continuar." \
    --ok-label="Continuar" \
    --width=450 2>/dev/null

[ $? -ne 0 ] && exit 0

# -----------------------------------------------------------------------------
# PASSO 2 — LICENÇA
# -----------------------------------------------------------------------------

LICENSE_TEXT="$(cat "$LICENSE_FILE" 2>/dev/null || echo 'Arquivo de licença não encontrado.')"

zenity --text-info \
    --title="Contrato de Licença — $APP_NAME" \
    --filename="$LICENSE_FILE" \
    --checkbox="Li e aceito os termos da licença" \
    --ok-label="Aceitar e Continuar" \
    --cancel-label="Recusar" \
    --width=620 --height=480 2>/dev/null

[ $? -ne 0 ] && abort "Você precisa aceitar a licença para instalar o $APP_NAME."

# -----------------------------------------------------------------------------
# PASSO 3 — ESCOLHA DA PASTA DE INSTALAÇÃO
# -----------------------------------------------------------------------------

INSTALL_DIR=$(zenity --file-selection \
    --directory \
    --title="Escolha a pasta de instalação" \
    --filename="$HOME/" \
    --ok-label="Instalar aqui" \
    --width=600 2>/dev/null)

[ $? -ne 0 ] && exit 0
[ -z "$INSTALL_DIR" ] && abort "Nenhuma pasta selecionada."

INSTALL_DIR="$INSTALL_DIR/$APP_EXEC"

# -----------------------------------------------------------------------------
# PASSO 4 — VERIFICAÇÕES E INSTALAÇÃO (com barra de progresso)
# -----------------------------------------------------------------------------

(
echo "5"
echo "# Criando pasta de instalação..."
sleep 0.3

mkdir -p "$INSTALL_DIR/src" || { echo "# ERRO: Não foi possível criar $INSTALL_DIR"; exit 1; }

echo "10"
echo "# Copiando arquivos do aplicativo..."
sleep 0.3

# Copia arquivos
cp "$SCRIPT_DIR/run.py"            "$INSTALL_DIR/"
cp "$SCRIPT_DIR/iniciar.sh"        "$INSTALL_DIR/"
cp "$SCRIPT_DIR/desinstalar.sh"    "$INSTALL_DIR/"
cp "$SCRIPT_DIR/LICENSE.txt"       "$INSTALL_DIR/"

# Copia src/
cp "$SCRIPT_DIR/src/"*.py         "$INSTALL_DIR/src/" 2>/dev/null || true

echo "20"
echo "# Ajustando permissões..."
chmod +x "$INSTALL_DIR/iniciar.sh"
chmod +x "$INSTALL_DIR/desinstalar.sh"
sleep 0.2

echo "30"
echo "# Verificando Python 3..."
if ! command -v python3 &>/dev/null; then
    echo "# ERRO: Python 3 não encontrado no sistema!"
    sleep 1
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo "# Encontrado: $PYTHON_VERSION"
sleep 0.3

echo "40"
echo "# Verificando pip..."
if ! python3 -m pip --version &>/dev/null; then
    echo "# pip não encontrado — tentando instalar..."
    sudo apt-get install -y python3-pip 2>/dev/null || true
fi
sleep 0.3

echo "50"
echo "# Instalando Pillow (com suporte a ImageTk)..."
sudo apt-get install -y python3-pil python3-pil.imagetk 2>/dev/null || true
sleep 0.5

echo "60"
echo "# Instalando OpenCV..."
sudo apt-get install -y python3-opencv 2>/dev/null || true
sleep 0.5

echo "70"
echo "# Instalando pytesseract..."
sudo pip3 install pytesseract --break-system-packages 2>/dev/null || true
sleep 0.3

echo "75"
echo "# Instalando python-docx e pypdfium2..."
sudo pip3 install python-docx pypdfium2 --break-system-packages 2>/dev/null || true
sleep 0.5

echo "78"
echo "# Verificando Tesseract OCR..."
if ! command -v tesseract &>/dev/null; then
    echo "# Tesseract não encontrado — instalando via apt..."
    sudo apt-get install -y tesseract-ocr tesseract-ocr-por 2>/dev/null || true
else
    echo "# Tesseract já instalado."
fi
sleep 0.4

echo "85"
echo "# Configurando ícone..."

# Copia ícone (genérico se não houver personalizado)
if [ -f "$SCRIPT_DIR/icon.png" ]; then
    cp "$SCRIPT_DIR/icon.png" "$INSTALL_DIR/icon.png"
    ICON_PATH="$INSTALL_DIR/icon.png"
else
    # Usa ícone genérico do sistema
    ICON_PATH="accessories-text-editor"
fi
sleep 0.2

echo "90"
echo "# Criando atalho no Desktop..."

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
DESKTOP_FILE="$DESKTOP_DIR/meu-app-documentos.desktop"

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Preenche documentos ODT/DOCX usando OCR
Exec=bash "$INSTALL_DIR/iniciar.sh"
Icon=$ICON_PATH
Terminal=false
Categories=Office;Utility;
StartupNotify=true
DESKTOP

chmod +x "$DESKTOP_FILE"

# Marca como confiável no GNOME (ignora erro se não disponível)
gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true

echo "95"
echo "# Criando entrada no menu do sistema..."

mkdir -p "$HOME/.local/share/applications"
MENU_FILE="$HOME/.local/share/applications/meu-app-documentos.desktop"

cat > "$MENU_FILE" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Preenche documentos ODT/DOCX usando OCR
Exec=bash "$INSTALL_DIR/iniciar.sh"
Icon=$ICON_PATH
Terminal=false
Categories=Office;Utility;
StartupNotify=true
DESKTOP

chmod +x "$MENU_FILE"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "100"
echo "# Instalação concluída!"
sleep 0.3

) | zenity --progress \
    --title="Instalando $APP_NAME..." \
    --text="Iniciando instalação..." \
    --percentage=0 \
    --auto-close \
    --width=480 2>/dev/null

# Verifica se o processo de instalação terminou com sucesso
if [ $? -ne 0 ]; then
    abort "A instalação foi interrompida ou ocorreu um erro.\n\nVerifique se você tem conexão com a internet e tente novamente."
fi

# -----------------------------------------------------------------------------
# PASSO 5 — CONCLUSÃO
# -----------------------------------------------------------------------------

zenity --info \
    --title="Instalação concluída! 🎉" \
    --text="<b>$APP_NAME v$APP_VERSION</b> foi instalado com sucesso!\n\n📁 Local: <tt>$INSTALL_DIR</tt>\n\n🖥️ Um atalho foi criado na sua <b>Área de Trabalho</b> e no <b>Menu de Aplicativos</b>.\n\nPara desinstalar, execute o arquivo <tt>desinstalar.sh</tt> na pasta de instalação.\n\n<b>Clique duas vezes no ícone para iniciar o app!</b>" \
    --ok-label="Fechar" \
    --width=480 2>/dev/null

exit 0