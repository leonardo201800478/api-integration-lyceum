import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Script para executar todas as sincronizações em sequência
com tratamento de erros e relatório consolidado
"""
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path

SCRIPTS = [
    "sync/sync_ly_cursos.py",
    "sync/sync_ly_curriculos.py",
    "sync/sync_ly_disciplinas.py",
    "sync/sync_ly_alunos.py",
    "sync/sync_ly_turmas.py",
    "sync/sync_ly_docentes.py",
    "sync/sync_ly_turma_docentes.py",
    
]

def run_script(script_path):
    """Executa um script de sincronização e retorna o resultado"""
    print(f"\n{'='*60}")
    print(f"🚀 Executando: {script_path}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hora de timeout máximo por script
        )
        
        return {
            "script": script_path,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            "script": script_path,
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout expired (3600 seconds)",
            "success": False
        }
    except Exception as e:
        return {
            "script": script_path,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def main():
    """Executa todas as sincronizações e gera relatório"""
    print("🔄 INICIANDO SINCRONIZAÇÃO COMPLETA DO SISTEMA")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📋 Total de scripts: {len(SCRIPTS)}")
    
    # Criar diretório para logs
    log_dir = Path("logs/execucoes")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    resultados = []
    sucessos = 0
    falhas = 0
    
    for script in SCRIPTS:
        if Path(script).exists():
            resultado = run_script(script)
            resultados.append(resultado)
            
            if resultado["success"]:
                sucessos += 1
                print(f"✅ {script}: SUCESSO")
            else:
                falhas += 1
                print(f"❌ {script}: FALHA (code: {resultado['returncode']})")
                
                # Log de erro detalhado
                if resultado["stderr"]:
                    print(f"   Erro: {resultado['stderr'][:200]}...")
        else:
            print(f"⚠️  Script não encontrado: {script}")
    
    # Gerar relatório consolidado
    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "total_scripts": len(SCRIPTS),
        "executed_scripts": len(resultados),
        "successful": sucessos,
        "failed": falhas,
        "success_rate": (sucessos / len(resultados) * 100) if resultados else 0,
        "results": resultados
    }
    
    # Salvar relatório
    relatorio_path = log_dir / f"relatorio_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2, default=str)
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📊 RELATÓRIO FINAL DA EXECUÇÃO")
    print(f"{'='*60}")
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Falhas: {falhas}")
    print(f"📈 Taxa de sucesso: {relatorio['success_rate']:.1f}%")
    print(f"📄 Relatório salvo em: {relatorio_path}")
    print(f"{'='*60}")
    
    if falhas == 0:
        print("🎉 TODAS AS SINCRONIZAÇÕES CONCLUÍDAS COM SUCESSO!")
    else:
        print(f"⚠️  {falhas} sincronização(ões) falharam. Verifique os logs.")
    
    return falhas == 0

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)