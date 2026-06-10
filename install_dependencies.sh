#!/bin/bash
# Instalador de Dependências - Meu App de Documentos

echo "=========================================="
echo "  Instalando dependências do Meu App"
echo "=========================================="

# Detecta a distribuição
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Erro: Não foi possível detectar o sistema"
    exit 1
fi

echo "Sistema detectado: $OS"

# Instala dependências do sistema
case $OS in
    ubuntu|debian)
        echo "Instalando pacotes para Ubuntu/Debian..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself
        ;;
    *)
        echo "Distribuição não suportada automaticamente."
        echo "Instale manualmente: python3, pip, tk, tesseract, zenity, makeself"
        ;;
esac

# Instala dependências Python
echo "Instalando dependências Python..."
pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx

echo "=========================================="
echo "  Instalação concluída!"
echo "  Execute: python3 run.py"
echo "=========================================="
