#!/usr/bin/env python3
"""
Versão alternativa que importa os módulos diretamente
(evita problemas de subprocess)
"""
import os
import sys
import time
import importlib.util
from datetime import datetime
from pathlib import Path

# Configurar caminhos
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Mapeamento de scripts para funções principais
SCRIPT_MAPPING = {
    "sync_ly_cursos.py": "sincronizar_cursos",
    "sync_ly_curriculos.py": "sincronizar_curriculos", 
    "sync_ly_disciplinas.py": "sincronizar_disciplinas",
    "sync_ly_alunos.py": "sync_alunos",
    "sync_ly_turmas.py": "sincronizar_turmas",
    "sync_ly_docentes.py": "sincronizar_docentes",
    "sync_ly_turma_docentes.py": "sincronizar_turma_docentes",
    "sync_ly_coordenacoes.py": "sincronizar_coordenacoes",
    "sync_ly_grades.py": "sincronizar_grades",
    "sync_ly_matriculas.py": "main"  # Este tem função main que pede input
}

def run_script_directly(script_name: str):
    """Importa e executa script diretamente"""
    print(f"\n{'='*60}")
    print(f"Executando: {script_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Construir caminho do módulo
        module_path = project_root / "sync" / script_name
        
        # Carregar módulo dinamicamente
        spec = importlib.util.spec_from_file_location(
            script_name.replace('.py', ''), 
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        
        # Executar módulo (isso executa o código de nível superior)
        spec.loader.exec_module(module)
        
        # Se tiver função principal específica, executá-la
        func_name = SCRIPT_MAPPING.get(script_name)
        if func_name and hasattr(module, func_name):
            print(f"Chamando função: {func_name}")
            result = getattr(module, func_name)()
        else:
            # Script já executou no exec_module
            result = True
        
        elapsed_time = time.time() - start_time
        print(f"✅ {script_name} concluído em {elapsed_time:.2f}s")
        
        return {
            "script": script_name,
            "success": True,
            "elapsed_time": elapsed_time
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ {script_name} falhou: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "script": script_name,
            "success": False,
            "error": str(e),
            "elapsed_time": elapsed_time
        }

# Executar todos os scripts
if __name__ == "__main__":
    print("Executando scripts diretamente (sem subprocess)...")
    
    for script_name in SCRIPT_MAPPING.keys():
        run_script_directly(script_name)
        time.sleep(2)  # Pausa entre scripts