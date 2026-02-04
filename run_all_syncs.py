#!/usr/bin/env python3
"""
SCRIPT DE SINCRONIZAÇÃO UNIFICADO - VERSÃO FUNCIONAL
Executa todos os scripts de sincronização via importação direta (sem subprocess)
"""
import os
import sys
import time
import json
import logging
import importlib.util
from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import io

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ordem de execução dos scripts
SCRIPTS = [
    "sync_ly_cursos.py",
    "sync_ly_curriculos.py",
    "sync_ly_disciplinas.py",
    "sync_ly_alunos.py",
    "sync_ly_turmas.py",
    "sync_ly_docentes.py",
    "sync_ly_turma_docentes.py",
    "sync_ly_coordenacoes.py",
    "sync_ly_grades.py",
    "sync_ly_matriculas.py"
]

# Mapeamento de funções principais para cada script
SCRIPT_FUNCTIONS = {
    "sync_ly_cursos.py": "sincronizar_cursos",
    "sync_ly_curriculos.py": "sincronizar_curriculos",
    "sync_ly_disciplinas.py": "sincronizar_disciplinas",
    "sync_ly_alunos.py": "sync_alunos",
    "sync_ly_turmas.py": "sincronizar_turmas",
    "sync_ly_docentes.py": "sincronizar_docentes",
    "sync_ly_turma_docentes.py": "sincronizar_turma_docentes",
    "sync_ly_coordenacoes.py": "sincronizar_coordenacoes",
    "sync_ly_grades.py": "sincronizar_grades",
    "sync_ly_matriculas.py": "main"  # Este tem menu interativo
}

# Configurações
DELAY_BETWEEN_SCRIPTS = 3  # Segundos entre scripts

def setup_environment():
    """Configura o ambiente do projeto"""
    # Obter diretório raiz (um nível acima deste script)
    project_root = Path(__file__).parent.absolute()
    
    # Adicionar ao PYTHONPATH
    sys.path.insert(0, str(project_root))
    
    # Mudar para diretório do projeto
    os.chdir(project_root)
    
    logger.info(f"Ambiente configurado")
    logger.info(f"Diretório do projeto: {project_root}")
    
    return project_root

def import_and_execute_script(script_name: str, project_root: Path):
    """
    Importa e executa um script diretamente (sem subprocess)
    """
    script_path = project_root / "sync" / script_name
    start_time = time.time()
    
    logger.info(f"{'='*60}")
    logger.info(f"Iniciando: {script_name}")
    logger.info(f"{'='*60}")
    
    # Buffers para capturar output
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    try:
        # Verificar se arquivo existe
        if not script_path.exists():
            error_msg = f"Script não encontrado: {script_path}"
            logger.error(error_msg)
            return {
                "script": script_name,
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "elapsed_time": 0
            }
        
        # Carregar módulo dinamicamente
        module_name = script_name.replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None:
            error_msg = f"Não foi possível carregar especificação do módulo: {script_name}"
            logger.error(error_msg)
            return {
                "script": script_name,
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "elapsed_time": time.time() - start_time
            }
        
        module = importlib.util.module_from_spec(spec)
        
        # Executar módulo com redirecionamento de output
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Primeiro: executar o módulo (isso executa código de nível superior)
            spec.loader.exec_module(module)
            
            # Segundo: executar função principal específica
            function_name = SCRIPT_FUNCTIONS.get(script_name)
            
            # Tratamento especial para scripts com menu interativo
            if script_name == "sync_ly_matriculas.py":
                # Para matriculas, usamos a opção 1 (sincronizar tudo) automaticamente
                logger.info("Script de matrículas detectado - usando opção padrão (1)")
                
                # Mock do input para escolher opção 1 automaticamente
                import builtins
                original_input = builtins.input
                
                def mock_input(prompt=""):
                    if "Escolha uma opção" in prompt:
                        logger.info(f"Input automático: 1 (para: {prompt})")
                        return "1"
                    elif "Digite o ano" in prompt:
                        logger.info(f"Input automático: (vazio para todos)")
                        return ""
                    elif "Digite o semestre" in prompt:
                        logger.info(f"Input automático: (vazio para todos)")
                        return ""
                    else:
                        return ""
                
                builtins.input = mock_input
                
                try:
                    # Executar função main (que agora usará input mockado)
                    if hasattr(module, 'main'):
                        result = module.main()
                    else:
                        result = None
                finally:
                    # Restaurar input original
                    builtins.input = original_input
                    
            elif function_name and hasattr(module, function_name):
                # Executar função específica para outros scripts
                logger.info(f"Executando função: {function_name}")
                result = getattr(module, function_name)()
            else:
                # Se não houver função específica, módulo já foi executado
                result = None
        
        elapsed_time = time.time() - start_time
        
        # Capturar output
        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()
        
        # Determinar sucesso
        success = False
        if script_name == "sync_ly_matriculas.py":
            # Para matriculas, consideramos sucesso se não houver exceção
            success = result is not False
        elif result is None:
            # Se resultado for None, assume sucesso
            success = True
        elif isinstance(result, bool):
            success = result
        elif isinstance(result, dict):
            # Se for dicionário, verificar se tem indicador de sucesso
            success = result.get('success', True) if isinstance(result, dict) else True
        else:
            # Outros tipos são considerados sucesso
            success = True
        
        # Log do resultado
        if success:
            logger.info(f"✅ {script_name} - SUCESSO ({elapsed_time:.2f}s)")
            if stdout_output:
                # Mostrar últimas linhas do stdout
                lines = stdout_output.strip().split('\n')
                if lines:
                    logger.info(f"   Última saída: {lines[-1][:100]}")
        else:
            logger.error(f"❌ {script_name} - FALHA ({elapsed_time:.2f}s)")
            if stderr_output:
                lines = stderr_output.strip().split('\n')
                if lines:
                    logger.error(f"   Erro: {lines[-1][:200]}")
        
        return {
            "script": script_name,
            "success": success,
            "returncode": 0 if success else 1,
            "stdout": stdout_output,
            "stderr": stderr_output,
            "elapsed_time": elapsed_time,
            "has_stdout": bool(stdout_output.strip()),
            "has_stderr": bool(stderr_output.strip())
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Erro ao executar {script_name}: {str(e)}"
        logger.error(error_msg)
        
        # Capturar traceback
        import traceback
        tb_output = traceback.format_exc()
        
        return {
            "script": script_name,
            "success": False,
            "returncode": 1,
            "error": error_msg,
            "stdout": stdout_buffer.getvalue(),
            "stderr": stderr_buffer.getvalue() + "\n" + tb_output,
            "elapsed_time": elapsed_time,
            "has_stdout": bool(stdout_buffer.getvalue().strip()),
            "has_stderr": True
        }

def save_individual_log(result: dict, log_dir: Path):
    """Salva log individual para cada script"""
    script_stem = Path(result["script"]).stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{script_stem}_{timestamp}.log"
    
    log_content = f"""SCRIPT: {result['script']}
EXECUTADO EM: {datetime.now().isoformat()}
DURAÇÃO: {result.get('elapsed_time', 0):.2f} segundos
SUCESSO: {result.get('success', False)}
RETURNCODE: {result.get('returncode', 'N/A')}
ERROR: {result.get('error', 'Nenhum')}

{'='*60}
SAÍDA PADRÃO (stdout):
{'='*60}
{result.get('stdout', '')}

{'='*60}
SAÍDA DE ERRO (stderr):
{'='*60}
{result.get('stderr', '')}
"""
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        logger.debug(f"Log salvo: {log_file.name}")
    except Exception as e:
        logger.error(f"Erro ao salvar log {log_file}: {e}")
    
    return log_file

def generate_summary_report(results: list, log_dir: Path) -> Path:
    """Gera relatório JSON com resultados de todas as execuções"""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "run_id": datetime.now().strftime('%Y%m%d_%H%M%S'),
        "log_directory": str(log_dir),
        "total_scripts": len(results),
        "executed_scripts": len(results),
        "successful": sum(1 for r in results if r.get("success", False)),
        "failed": sum(1 for r in results if not r.get("success", True)),
        "timeouts": 0,  # Não aplicável nesta versão
        "success_rate": 0.0,
        "scripts": []
    }
    
    # Calcular taxa de sucesso
    if report_data["executed_scripts"] > 0:
        report_data["success_rate"] = (
            report_data["successful"] / report_data["executed_scripts"] * 100
        )
    
    # Adicionar detalhes de cada script
    for result in results:
        script_info = {
            "script": result.get("script", "unknown"),
            "success": result.get("success", False),
            "returncode": result.get("returncode", -1),
            "timeout": False,
            "elapsed_time": result.get("elapsed_time", 0),
            "has_stdout": result.get("has_stdout", False),
            "has_stderr": result.get("has_stderr", False)
        }
        report_data["scripts"].append(script_info)
    
    # Salvar relatório
    report_path = log_dir / "relatorio_completo.json"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Relatório salvo: {report_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar relatório: {e}")
        report_path = None
    
    return report_path

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🔄 SISTEMA DE SINCRONIZAÇÃO LYCEUM - VERSÃO DIRETA")
    print("="*70)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📋 Total de scripts: {len(SCRIPTS)}")
    print(f"⚡ Método: Importação direta (sem subprocess)")
    print("="*70)
    
    try:
        # Configurar ambiente
        project_root = setup_environment()
        
        # Criar diretório de logs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = project_root / "logs" / "execucoes" / timestamp
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório de logs: {log_dir}")
        
        results = []
        
        # Executar cada script na ordem definida
        for i, script_name in enumerate(SCRIPTS, 1):
            print(f"\n[{i}/{len(SCRIPTS)}] 🚀 Executando {script_name}...")
            
            # Executar script
            result = import_and_execute_script(script_name, project_root)
            results.append(result)
            
            # Salvar log individual
            save_individual_log(result, log_dir)
            
            # Aguardar entre execuções (exceto último)
            if i < len(SCRIPTS):
                time.sleep(DELAY_BETWEEN_SCRIPTS)
        
        # Gerar relatório consolidado
        print("\n" + "="*70)
        print("📊 GERANDO RELATÓRIO FINAL")
        print("="*70)
        
        report_path = generate_summary_report(results, log_dir)
        
        # Exibir resumo
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        print(f"\n📈 RESULTADOS:")
        print(f"   ✅ Sucessos: {successful}/{len(results)}")
        print(f"   ❌ Falhas: {failed}/{len(results)}")
        print(f"   📊 Taxa de sucesso: {(successful/len(results)*100):.1f}%")
        
        # Tempo total
        total_time = sum(r.get("elapsed_time", 0) for r in results)
        print(f"   ⏱️  Tempo total: {total_time:.1f}s")
        
        # Listar falhas (se houver)
        if failed > 0:
            print(f"\n🔴 SCRIPTS COM FALHA:")
            for result in results:
                if not result.get("success", True):
                    print(f"   ❌ {result['script']}")
                    if result.get("error"):
                        print(f"      Erro: {result['error'][:100]}...")
        
        print(f"\n📁 Logs salvos em: {log_dir}")
        if report_path:
            print(f"📄 Relatório JSON: {report_path}")
        
        print("\n" + "="*70)
        
        if failed == 0:
            print("🎉 TODAS AS SINCRONIZAÇÕES CONCLUÍDAS COM SUCESSO!")
            return True
        else:
            print(f"⚠️  {failed} SINCRONIZAÇÃO(ÕES) FALHARAM")
            return False
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado no executor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)