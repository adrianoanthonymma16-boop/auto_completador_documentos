#!/usr/bin/env bash
# =============================================================================
# Meu App de Documentos — Desinstalador
# =============================================================================

APP_NAME="Meu App de Documentos"
INSTALL_DIR="$(dirname "$(realpath "$0")")"

# Verifica zenity
if ! command -v zenity &>/dev/null; then
    echo "Desinstalar: removendo $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    echo "Pronto."
    exit 0
fi

# Confirmação
zenity --question \
    --title="Desinstalar $APP_NAME" \
    --text="Tem certeza que deseja remover o <b>$APP_NAME</b>?\n\nA pasta de instalação será apagada:\n<tt>$INSTALL_DIR</tt>" \
    --ok-label="Sim, remover" \
    --cancel-label="Cancelar" \
    --width=420 2>/dev/null

if [ $? -ne 0 ]; then
    exit 0
fi

# Remove atalho da área de trabalho
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
DESKTOP_FILE="$DESKTOP_DIR/meu-app-documentos.desktop"
[ -f "$DESKTOP_FILE" ] && rm -f "$DESKTOP_FILE"

# Remove entrada do menu
MENU_FILE="$HOME/.local/share/applications/meu-app-documentos.desktop"
[ -f "$MENU_FILE" ] && rm -f "$MENU_FILE"

# Atualiza cache do menu
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# Remove a pasta de instalação inteira
rm -rf "$INSTALL_DIR"

zenity --info \
    --title="Desinstalação concluída" \
    --text="✅ <b>$APP_NAME</b> foi removido com sucesso." \
    --width=350 2>/dev/null

exit 0
