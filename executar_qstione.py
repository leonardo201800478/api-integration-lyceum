# executar.py
#!/usr/bin/env python3
"""
Script de execução do Gestor Qstione
"""

import sys
import os

# Adiciona o diretório atual ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qstione.main import main

if __name__ == "__main__":
    main()