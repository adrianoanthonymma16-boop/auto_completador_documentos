#!/usr/bin/env bash
# =============================================================================
# Meu App de Documentos — Inicializador
# =============================================================================

APP_DIR="$(dirname "$(realpath "$0")")"

# Garante que dependências pip do usuário estão no PATH
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$APP_DIR/src:$PYTHONPATH"

cd "$APP_DIR"

# Verifica python3
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

# Inicia o app
python3 "$APP_DIR/run.py" "$@"
