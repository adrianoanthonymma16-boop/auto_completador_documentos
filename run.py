#!/usr/bin/env python3
"""
Meu App de Documentos - Ponto de Entrada
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import ttkbootstrap as ttk
from interface import AppDocumentos

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = AppDocumentos(root)
    root.mainloop()
