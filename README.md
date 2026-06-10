# 📄 Meu App de Documentos

Automatize o preenchimento de documentos ODT/DOCX usando OCR.

Carregue um modelo com placeholders ({{nome}}, {{cpf}}), anexe fotos/PDFs de documentos, desenhe retângulos nos campos e gere documentos prontos.

Formatos: modelo (ODT/DOCX) | fontes (JPG, PNG, PDF, TIFF, HEIC, WEBP)
Plataforma: Linux (Ubuntu/Debian)
Offline - sem nuvem, sem internet

---

## Requisitos

Instale as dependências:

sudo apt update
sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself

pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx

Opcional (HEIC do iPhone):
sudo apt install -y libheif-dev
pip3 install pyheif

---

## Executar

python3 run.py

---

## Gerar instalador

bash build_installer.sh

---

## Instalar

chmod +x MeuAppDocumentos-*.run
./MeuAppDocumentos-*.run

---

## Estrutura do projeto

meu_app_documentos/
├── run.py
├── build_installer.sh
├── install.sh
├── iniciar.sh
├── desinstalar.sh
├── LICENSE.txt
└── src/
    ├── config.py
    ├── validadores.py
    ├── mensagens.py
    ├── ocr.py
    ├── anexo_pdf.py
    ├── anexo_heic.py
    ├── modelo_odt.py
    ├── modelo_docx.py
    └── interface.py

---

## Contato

Adriano Anthony Jesus Azulay de Araujo
E-mail: adrianoanthonymma16@gmail.com

---

## Licença

Software proprietário. Veja o arquivo LICENSE.txt para os termos completos.

## 🚀 Instalação rápida (para desenvolvedores)

Se você clonou o repositório fonte, execute o comando abaixo para instalar **todas as dependências automaticamente**:

```bash
bash install_dependencies.sh