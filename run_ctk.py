#!/usr/bin/env python3
"""
Meu App de Documentos - Entry Point CustomTkinter
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import customtkinter as ctk
from interface_ctk import AppDocumentosCTK

if __name__ == "__main__":
    root = ctk.CTk()
    app = AppDocumentosCTK(root)
    root.mainloop()
