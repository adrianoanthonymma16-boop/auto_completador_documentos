#!/usr/bin/env python3
"""
Meu App de Documentos - Ponto de Entrada
"""

import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importa e executa a interface
from interface import AppDocumentos
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = AppDocumentos(root)
    root.mainloop()