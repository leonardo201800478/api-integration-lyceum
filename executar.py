#!/usr/bin/env python3
"""
Script de execução principal para o projeto Qstione
"""

import sys
import os
import importlib.util

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

# Verificar dependências
if importlib.util.find_spec("openpyxl") is None:
    print("Instalando dependências...")
    os.system("pip install openpyxl")

# Executar gestor principal
from qstione.main import main

if __name__ == "__main__":
    main()