"""
Sincronização completa da API Lyceum → banco db_lyceum
- Cria todas as tabelas
- Valida dados obrigatórios
- Usa apenas GET
"""

from core.config import config
from core.api_client import (
    AlunoAPIClient,
    CursoAPIClient,
    CurriculoAPIClient,
    DocenteAPIClient,
    DisciplinaAPIClient,
    TurmaAPIClient,
    TurmaDocenteAPIClient,
)

from models.ly_aluno import AlunoModel
from models.curso import CursoModel
from models.ly_curriculo import CurriculoModel
from models.docente import DocenteModel
from models.disciplina import DisciplinaModel
from models.turma import TurmaModel
from models.turma_docente import TurmaDocenteModel


# ==========================================================
# UTILITÁRIOS
# ==========================================================

def is_valid(data: dict, required_fields: list) -> bool:
    """
    Valida se todos os campos obrigatórios existem e não são vazios
    """
    for field in required_fields:
        if not data.get(field):
            return False
    return True


# ==========================================================
# CRIAÇÃO DAS TABELAS
# ==========================================================

def create_all_tables():
    """
    Cria todas as tabelas LY_* no banco db_lyceum
    """
    AlunoModel.create_table()
    CursoModel.create_table()
    CurriculoModel.create_table()
    DocenteModel.create_table()
    DisciplinaModel.create_table()
    TurmaModel.create_table()
    TurmaDocenteModel.create_table()


# ==========================================================
# SYNC CURSOS
# ==========================================================

def sync_cursos():
    client = CursoAPIClient()
    cursos = client.get_cursos()

    if not isinstance(cursos, list):
        raise RuntimeError(
            f"Resposta inválida para cursos: {type(cursos)}"
        )

    for curso in cursos:
        if not isinstance(curso, dict):
            continue

        if not is_valid(curso, ["curso", "nome"]):
            continue

        CursoModel.upsert(curso)


# ==========================================================
# SYNC CURRÍCULOS
# ==========================================================

def sync_curriculos():
    client = CurriculoAPIClient()
    curriculos = client.get_curriculos()

    for curriculo in curriculos:
        if not is_valid(curriculo, ["curriculo", "curso", "nome"]):
            continue
        CurriculoModel.upsert(curriculo)


# ==========================================================
# SYNC ALUNOS (unitário por matrícula)
# ==========================================================

def sync_alunos(matriculas: list[str]):
    client = AlunoAPIClient()

    for matricula in matriculas:
        aluno = client.get_aluno(matricula)
        if not aluno:
            continue

        if not is_valid(aluno, ["matricula", "nome"]):
            continue

        AlunoModel.upsert(aluno)


# ==========================================================
# SYNC DOCENTES
# ==========================================================

def sync_docentes(docentes: list[dict]):
    client = DocenteAPIClient()

    for d in docentes:
        if not is_valid(d, ["cpf", "numFunc"]):
            continue

        docente = client.get_docente(d["cpf"], d["numFunc"])
        if not docente:
            continue

        DocenteModel.upsert(docente)


# ==========================================================
# SYNC DISCIPLINAS
# ==========================================================

def sync_disciplinas(codigos: list[str]):
    client = DisciplinaAPIClient()

    for codigo in codigos:
        disciplina = client.get_disciplina(codigo)
        if not disciplina:
            continue

        if not is_valid(disciplina, ["disciplina", "nome"]):
            continue

        DisciplinaModel.upsert(disciplina)


# ==========================================================
# SYNC TURMAS
# ==========================================================

def sync_turmas(chaves: list[dict]):
    client = TurmaAPIClient()

    for chave in chaves:
        if not is_valid(
            chave,
            ["ano", "semestre", "disciplina", "turma"]
        ):
            continue

        turma = client.get_turma(
            chave["ano"],
            chave["semestre"],
            chave["disciplina"],
            chave["turma"],
        )

        if not turma:
            continue

        TurmaModel.upsert(turma)


# ==========================================================
# SYNC TURMA–DOCENTE
# ==========================================================

def sync_turma_docente(chaves: list[str]):
    client = TurmaDocenteAPIClient()

    for chave in chaves:
        registro = client.get_turma_docente(chave)
        if not registro:
            continue

        if not is_valid(
            registro,
            ["chave", "cpf", "numFunc", "ano", "semestre"]
        ):
            continue

        TurmaDocenteModel.upsert(registro)


# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================

def run():
    print("🔧 Criando tabelas...")
    create_all_tables()

    print("📘 Sincronizando cursos...")
    sync_cursos()

    print("📗 Sincronizando currículos...")
    sync_curriculos()

    print("👨‍🎓 Sincronizando alunos...")
    alunos = AlunoAPIClient().get_alunos()
    for aluno in alunos:
        if isinstance(aluno, dict):
            AlunoModel.upsert(aluno)

    print("👨‍🏫 Sincronizando docentes...")
    docentes = DocenteAPIClient().get_docentes()
    for docente in docentes:
        if isinstance(docente, dict):
            DocenteModel.upsert(docente)

    print("📚 Sincronizando disciplinas...")
    disciplinas = DisciplinaAPIClient().get_disciplinas()
    for d in disciplinas:
        if isinstance(d, dict):
            DisciplinaModel.upsert(d)

    print("🏫 Sincronizando turmas...")
    turmas = TurmaAPIClient().get_turmas()
    for t in turmas:
        if isinstance(t, dict):
            TurmaModel.upsert(t)

    print("👥 Sincronizando turma-docente...")
    vinculos = TurmaDocenteAPIClient().get_turmas_docentes()
    for v in vinculos:
        if isinstance(v, dict):
            TurmaDocenteModel.upsert(v)

    print("✅ Banco db_lyceum sincronizado com sucesso.")

if __name__ == "__main__":
    run()