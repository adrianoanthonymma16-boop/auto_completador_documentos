#!/usr/bin/env bash
# =============================================================================
# Meu App de Documentos (CustomTkinter) — Inicializador
# =============================================================================

APP_DIR="$(dirname "$(realpath "$0")")"

export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$APP_DIR/src:$PYTHONPATH"

cd "$APP_DIR"

if ! command -v python3 &>/dev/null; then
    if command -v zenity &>/dev/null; then
        zenity --error \
            --title="Erro — Python não encontrado" \
            --text="Python 3 não foi encontrado no sistema.\n\nInstale com:\n<tt>sudo apt install python3</tt>" \
            --width=380 2>/dev/null
    else
        echo "ERRO: Python 3 não encontrado. Instale com: sudo apt install python3"
    fi
    exit 1
fi

python3 "$APP_DIR/run_ctk.py" "$@"
