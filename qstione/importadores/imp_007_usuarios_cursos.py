"""
qstione/importadores/imp_007_usuarios_cursos.py

Importador IMP-007 - Usuários x Cursos para o Qstione.

REGRA FUNDAMENTAL DO QSTIONE
----------------------------
O Qstione exige que cada vínculo de usuário seja informado com um
codigoCurso, porém o papelUsuario NÃO é independente por curso. O papel é
único por usuário dentro da integração.

Portanto, a consolidação ocorre em duas etapas:

1. Reunir TODOS os cursos aos quais o usuário possui vínculo válido;
2. Determinar o MAIOR papel do usuário pela hierarquia e propagar esse papel
   para TODOS esses cursos.

Hierarquia funcional:
    C > A > P

G é um papel administrativo fixo/global e não participa da hierarquia docente.
O = Operador de Documentos não é produzido por este importador.

Exemplo obrigatório:
    usuário é C no curso 056 e P nos cursos 065 e 079
    -> IMP-007 deve gerar C em 056, 065 e 079.

Outro exemplo:
    usuário é A no NDE de 006 e P nos cursos 017, 044 e 059
    -> IMP-007 deve gerar A em 006, 017, 044 e 059.

Assim, NÃO existe papel por curso. O curso define o vínculo exigido pelo
Qstione; o papel é o maior papel efetivo do usuário e é propagado para todos
os cursos aos quais ele está vinculado.

CURSO 999
---------
O código 999 representa exclusivamente uma turma compartilhada da origem
Lyceum (LY_TURMA.curso NULL/vazio). Ele só deve aparecer para um usuário se
esse usuário possuir efetivamente vínculo com uma turma compartilhada ou
outra regra explícita que produza 999. O importador NÃO deve acrescentar 999
artificialmente a todos os usuários C, A ou P.
"""

from __future__ import annotations

import logging
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import get_db_connection
from qstione.core.transformacoes import converter_minusculas
from qstione.config.filtros import (
    ANO_VIGENTE,
    PERIODOS_VIGENTES,
    FACULDADES_INCLUIDAS,
    SITUACAO_TURMA_VALIDA,
)
from qstione.importadores.imp_002_disciplina import MAPEAMENTO_CURSOS

logger = logging.getLogger("imp_007_usuarios_cursos")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

CURSO_COMPARTILHADO = "999"
PAPEL_GERAL = "G"
PAPEL_COORDENADOR = "C"
PAPEL_AVALIADOR = "A"
PAPEL_PROFESSOR = "P"
PAPEIS_VALIDOS = {PAPEL_GERAL, PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR}

# Menor número = maior prioridade.
PRIORIDADE_PAPEIS = {
    PAPEL_COORDENADOR: 1,
    PAPEL_AVALIADOR: 2,
    PAPEL_PROFESSOR: 3,
}

USUARIO_GERAL = "camila.felicio@foa.org.br"
USUARIO_COORDENADOR = "gildo.bernardo@foa.org.br"


class ImportadorUsuariosCursos:
    """Importa e consolida usuários x cursos conforme a regra global de papel."""

    NOME_TABELA = "imp_007_usuarios_cursos"

    def __init__(self):
        if not PERIODOS_VIGENTES:
            raise ValueError("PERIODOS_VIGENTES não pode estar vazio.")
        if not FACULDADES_INCLUIDAS:
            raise ValueError("FACULDADES_INCLUIDAS não pode estar vazio.")
        self.periodos_placeholders = ",".join("?" for _ in PERIODOS_VIGENTES)
        self.faculdades_placeholders = ",".join("?" for _ in FACULDADES_INCLUIDAS)
        logger.info("=" * 80)
        logger.info("Inicializando imp_007_usuarios_cursos")
        logger.info("ANO_VIGENTE=%s", ANO_VIGENTE)
        logger.info("PERIODOS_VIGENTES=%s", PERIODOS_VIGENTES)
        logger.info("FACULDADES_INCLUIDAS=%s", FACULDADES_INCLUIDAS)
        logger.info("SITUACAO_TURMA_VALIDA=%s", SITUACAO_TURMA_VALIDA)
        logger.info("Regra de papel: C > A > P | papel efetivo global por usuário")
        logger.info("G = administrativo fixo/global")
        logger.info("=")

    @staticmethod
    def _validar_email(email: Any) -> bool:
        if email is None:
            return False
        email = str(email).strip()
        if not email or "@" not in email or " " in email:
            return False
        partes = email.split("@")
        return len(partes) == 2 and bool(partes[0]) and "." in partes[1]

    @staticmethod
    def _validar_codigo_curso(codigo: Any) -> bool:
        if codigo is None:
            return False
        codigo = str(codigo).strip()
        return bool(codigo) and len(codigo) <= 30

    @staticmethod
    def _validar_papel(papel: Any) -> bool:
        return papel is not None and str(papel).strip().upper() in PAPEIS_VALIDOS

    @staticmethod
    def _curso_unificado(curso: Any) -> Tuple[str, str]:
        if curso is None:
            return CURSO_COMPARTILHADO, "Turma Compartilhada"
        curso = str(curso).strip()
        if not curso or curso == CURSO_COMPARTILHADO:
            return CURSO_COMPARTILHADO, "Turma Compartilhada"
        mapeamento = MAPEAMENTO_CURSOS.get(curso)
        if not mapeamento:
            return curso, curso
        codigo, nome = mapeamento
        codigo = str(codigo).strip()
        nome = str(nome).strip()
        return (codigo or curso), (nome or codigo or curso)

    def _tabela_existe(self, nome_tabela: str) -> bool:
        with get_db_connection(database_name="qstione") as conn:
            row = conn.execute(
                """SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                   WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'""",
                (nome_tabela,),
            ).fetchone()
        return row is not None

    def _indice_existe(self, nome_indice: str) -> bool:
        try:
            with get_db_connection(database_name="qstione") as conn:
                row = conn.execute(
                    """SELECT 1 FROM sys.indexes
                       WHERE name = ? AND object_id = OBJECT_ID(?)""",
                    (nome_indice, self.NOME_TABELA),
                ).fetchone()
            return row is not None
        except Exception:
            return False

    def _garantir_chave_primaria(self) -> None:
        """Garante PK composta por curso + e-mail + papel."""
        with get_db_connection(database_name="qstione") as conn:
            row = conn.execute(
                """
                SELECT kc.name
                FROM sys.key_constraints kc
                INNER JOIN sys.index_columns ic
                    ON ic.object_id = kc.parent_object_id
                   AND ic.index_id = kc.unique_index_id
                INNER JOIN sys.columns c
                    ON c.object_id = ic.object_id
                   AND c.column_id = ic.column_id
                WHERE kc.parent_object_id = OBJECT_ID(?)
                  AND kc.type = 'PK'
                GROUP BY kc.name
                HAVING COUNT(*) = 3
                   AND SUM(CASE WHEN c.name = 'codigoCurso' THEN 1 ELSE 0 END) = 1
                   AND SUM(CASE WHEN c.name = 'emailUsuario' THEN 1 ELSE 0 END) = 1
                   AND SUM(CASE WHEN c.name = 'papelUsuario' THEN 1 ELSE 0 END) = 1
                """,
                (self.NOME_TABELA,),
            ).fetchone()
            if row:
                return
            old = conn.execute(
                """SELECT kc.name FROM sys.key_constraints kc
                   WHERE kc.parent_object_id = OBJECT_ID(?) AND kc.type = 'PK'""",
                (self.NOME_TABELA,),
            ).fetchone()
            if old:
                conn.execute(f"ALTER TABLE {self.NOME_TABELA} DROP CONSTRAINT [{old[0]}]")
            conn.execute(
                f"""ALTER TABLE {self.NOME_TABELA}
                    ADD CONSTRAINT PK_imp_007_usuarios_cursos
                    PRIMARY KEY (codigoCurso, emailUsuario, papelUsuario)"""
            )
            conn.commit()
            logger.info("🔧 PK do IMP-007 ajustada para (codigoCurso, emailUsuario, papelUsuario).")

    def _criar_tabela(self) -> None:
        if not self._tabela_existe(self.NOME_TABELA):
            with get_db_connection(database_name="qstione") as conn:
                conn.execute(
                    f"""
                    CREATE TABLE {self.NOME_TABELA} (
                        codigoCurso NVARCHAR(30) NOT NULL,
                        emailUsuario NVARCHAR(100) NOT NULL,
                        papelUsuario NVARCHAR(1) NOT NULL,
                        data_criacao DATETIME2 DEFAULT GETDATE(),
                        data_atualizacao DATETIME2 DEFAULT GETDATE(),
                        CONSTRAINT PK_imp_007_usuarios_cursos
                            PRIMARY KEY (codigoCurso, emailUsuario, papelUsuario)
                    )
                    """
                )
                conn.commit()
            logger.info("🆕 Tabela %s criada.", self.NOME_TABELA)
        else:
            self._garantir_chave_primaria()
        self._criar_indices()

    def _criar_indices(self) -> None:
        indices = [
            ("idx_usuarios_cursos_email", f"CREATE INDEX idx_usuarios_cursos_email ON {self.NOME_TABELA}(emailUsuario)"),
            ("idx_usuarios_cursos_curso", f"CREATE INDEX idx_usuarios_cursos_curso ON {self.NOME_TABELA}(codigoCurso)"),
            ("idx_usuarios_cursos_papel", f"CREATE INDEX idx_usuarios_cursos_papel ON {self.NOME_TABELA}(papelUsuario)"),
        ]
        for nome, sql in indices:
            if self._indice_existe(nome):
                continue
            try:
                with get_db_connection(database_name="qstione") as conn:
                    conn.execute(sql)
                    conn.commit()
            except Exception as exc:
                logger.warning("Não foi possível criar índice %s: %s", nome, exc)

    def obter_coordenadores(self) -> Dict[Tuple[str, str], bool]:
        sql = f"""
            SELECT DISTINCT co.num_func, co.curso
            FROM LY_COORDENACAO co
            INNER JOIN LY_CURSO c ON c.curso = co.curso
            WHERE c.faculdade IN ({self.faculdades_placeholders})
        """
        try:
            with get_db_connection(database_name="lyceum") as conn:
                rows = conn.execute(sql, tuple(FACULDADES_INCLUIDAS)).fetchall()
        except Exception:
            logger.exception("Erro ao consultar LY_COORDENACAO.")
            return {}
        resultado = {}
        for num_func, curso in rows:
            if num_func is None:
                continue
            curso_unificado, _ = self._curso_unificado(curso)
            resultado[(str(num_func).strip(), curso_unificado)] = True
        logger.info("👤 Coordenadores encontrados: %d", len(resultado))
        return resultado

    def obter_docentes_turmas(self) -> List[Tuple[Any, Any, Any]]:
        sql = f"""
            SELECT DISTINCT td.num_func, d.mailbox, t.curso
            FROM LY_TURMA_DOCENTE td
            INNER JOIN LY_TURMA t
                ON t.ano = td.ano
               AND t.semestre = td.periodo
               AND t.turma = td.turma
               AND t.disciplina = td.disciplina
            LEFT JOIN LY_CURSO c ON c.curso = t.curso
            INNER JOIN LY_DOCENTE d ON d.num_func = td.num_func
            WHERE td.ano = ?
              AND td.periodo IN ({self.periodos_placeholders})
              AND t.sit_turma = ?
              AND (t.curso IS NULL OR LTRIM(RTRIM(t.curso)) = '' OR c.faculdade IN ({self.faculdades_placeholders}))
              AND (d.ativo = 'S' OR d.ativo IS NULL)
              AND d.mailbox IS NOT NULL
              AND LTRIM(RTRIM(d.mailbox)) <> ''
            ORDER BY td.num_func, t.curso, d.mailbox
        """
        params = [ANO_VIGENTE, *PERIODOS_VIGENTES, SITUACAO_TURMA_VALIDA, *FACULDADES_INCLUIDAS]
        try:
            with get_db_connection(database_name="lyceum") as conn:
                rows = conn.execute(sql, tuple(params)).fetchall()
        except Exception:
            logger.exception("Erro ao consultar LY_TURMA_DOCENTE.")
            return []
        logger.info("👨‍🏫 Vínculos docente/turma encontrados: %d", len(rows))
        return rows

    def obter_membros_nde(self) -> List[Tuple[Any, Any]]:
        sql = """
            SELECT DISTINCT codigoCurso, emailMembro
            FROM imp_nde_membros
            WHERE codigoCurso IS NOT NULL
              AND LTRIM(RTRIM(CAST(codigoCurso AS NVARCHAR(30)))) <> ''
              AND emailMembro IS NOT NULL
              AND LTRIM(RTRIM(emailMembro)) <> ''
              AND status = 'S'
        """
        try:
            with get_db_connection(database_name="qstione") as conn:
                rows = conn.execute(sql).fetchall()
        except Exception:
            logger.exception("Erro ao consultar imp_nde_membros.")
            return []
        logger.info("👥 Avaliadores NDE encontrados: %d", len(rows))
        return rows

    def _obter_email_docente(self, num_func: Any) -> Optional[str]:
        try:
            with get_db_connection(database_name="lyceum") as conn:
                row = conn.execute(
                    "SELECT mailbox FROM LY_DOCENTE WHERE num_func = ?",
                    (num_func,),
                ).fetchone()
            return self._normalizar_email(row[0]) if row and row[0] else None
        except Exception:
            logger.exception("Erro obtendo mailbox do docente %s.", num_func)
            return None

    def _normalizar_email(self, email: Any) -> Optional[str]:
        if email is None:
            return None
        email = converter_minusculas(str(email).strip())
        return email if self._validar_email(email) else None

    def _adicionar_candidato(
        self,
        candidatos: Dict[str, Dict[str, Set[str]]],
        email: Any,
        papel: str,
        curso: Any,
        origem: str,
    ) -> None:
        email = self._normalizar_email(email)
        papel = str(papel).strip().upper() if papel is not None else ""
        if not email or not self._validar_papel(papel):
            if email and papel not in PAPEIS_VALIDOS:
                logger.warning("Papel inválido ignorado: %s | email=%s | origem=%s", papel, email, origem)
            return
        curso_unificado, _ = self._curso_unificado(curso)
        if not self._validar_codigo_curso(curso_unificado):
            logger.warning("Código de curso inválido ignorado: %s | email=%s", curso_unificado, email)
            return
        candidatos[email][papel].add(curso_unificado)

    def transformar_dados(
        self,
        docentes_turmas: List[Tuple[Any, Any, Any]],
        coordenadores: Dict[Tuple[str, str], bool],
        membros_nde: List[Tuple[Any, Any]],
    ) -> List[Dict[str, str]]:
        """
        Consolida por usuário e só depois gera os vínculos.

        Regra: o maior papel encontrado para o usuário é propagado para a
        UNIÃO de todos os cursos aos quais esse usuário possui vínculo.
        """
        candidatos: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: {
                PAPEL_COORDENADOR: set(),
                PAPEL_AVALIADOR: set(),
                PAPEL_PROFESSOR: set(),
            }
        )

        # P/C: cada vínculo docente/turma gera o curso real ao qual o usuário
        # está ligado. Se ele também for coordenador daquele curso, o vínculo
        # recebe C como candidato; caso contrário, recebe P.
        for num_func, email, curso in docentes_turmas:
            if num_func is None:
                continue
            curso_unificado, _ = self._curso_unificado(curso)
            chave_coord = (str(num_func).strip(), curso_unificado)
            papel = PAPEL_COORDENADOR if chave_coord in coordenadores else PAPEL_PROFESSOR
            self._adicionar_candidato(candidatos, email, papel, curso, "LY_COORDENACAO" if papel == PAPEL_COORDENADOR else "LY_TURMA_DOCENTE")

        # Coordenadores também entram mesmo que não possuam turma docente no
        # período, pois LY_COORDENACAO é fonte própria do papel C.
        for (num_func, curso), _ in coordenadores.items():
            email = self._obter_email_docente(num_func)
            if email:
                self._adicionar_candidato(candidatos, email, PAPEL_COORDENADOR, curso, "LY_COORDENACAO")

        # A: os cursos registrados no NDE também são vínculos de curso que
        # precisam ser preservados. Se o usuário também possuir cursos como P,
        # a consolidação abaixo unirá todos eles e propagará A para todos.
        for curso, email in membros_nde:
            self._adicionar_candidato(candidatos, email, PAPEL_AVALIADOR, curso, "NDE")

        # G: usuário administrativo fixo. Mantemos seus cursos efetivamente
        # encontrados nas fontes e, quando não houver nenhum, 999 como vínculo
        # técnico mínimo para a carga administrativa existente.
        email_geral = self._normalizar_email(USUARIO_GERAL)
        if email_geral:
            cursos_geral = set()
            for cursos in candidatos[email_geral].values():
                cursos_geral.update(cursos)
            if not cursos_geral:
                cursos_geral.add(CURSO_COMPARTILHADO)
            candidatos[email_geral][PAPEL_GERAL] = cursos_geral

        # Usuário especial já existente na integração. A regra global continua
        # valendo: seus cursos efetivos são todos consolidados como C.
        email_coord_especial = self._normalizar_email(USUARIO_COORDENADOR)
        if email_coord_especial:
            cursos_coord = set()
            for papel in (PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR):
                cursos_coord.update(candidatos[email_coord_especial].get(papel, set()))
            if cursos_coord:
                candidatos[email_coord_especial][PAPEL_COORDENADOR].update(cursos_coord)

        registros: List[Dict[str, str]] = []
        estatisticas = defaultdict(int)

        # AQUI está a regra crítica: o papel efetivo é definido uma única vez
        # por usuário. Depois, o mesmo papel é aplicado a TODOS os cursos que
        # compõem a união dos vínculos desse usuário.
        for email, papeis in sorted(candidatos.items()):
            if email == email_geral and "G" in papeis:
                papel_efetivo = PAPEL_GERAL
                cursos = set(papeis[PAPEL_GERAL])
            elif papeis[PAPEL_COORDENADOR]:
                papel_efetivo = PAPEL_COORDENADOR
                cursos = set().union(*[v for k, v in papeis.items() if k in {PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR}])
            elif papeis[PAPEL_AVALIADOR]:
                papel_efetivo = PAPEL_AVALIADOR
                cursos = set().union(*[v for k, v in papeis.items() if k in {PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR}])
            elif papeis[PAPEL_PROFESSOR]:
                papel_efetivo = PAPEL_PROFESSOR
                cursos = set(papeis[PAPEL_PROFESSOR])
            else:
                continue

            for curso in sorted(cursos):
                registros.append({
                    "codigoCurso": curso,
                    "emailUsuario": email,
                    "papelUsuario": papel_efetivo,
                })
                estatisticas[papel_efetivo] += 1

        registros.sort(key=lambda r: (r["codigoCurso"], r["emailUsuario"], r["papelUsuario"]))
        logger.info("=" * 80)
        logger.info("📊 RESULTADO DA CONSOLIDAÇÃO")
        logger.info("   G = %d", estatisticas[PAPEL_GERAL])
        logger.info("   C = %d", estatisticas[PAPEL_COORDENADOR])
        logger.info("   A = %d", estatisticas[PAPEL_AVALIADOR])
        logger.info("   P = %d", estatisticas[PAPEL_PROFESSOR])
        logger.info("   TOTAL = %d", len(registros))
        logger.info("   Regra: papel máximo global propagado para todos os cursos do usuário")
        logger.info("=" * 80)
        return registros

    def importar_para_qstione(self, dados_transformados: List[Dict[str, str]]) -> Dict[str, int]:
        self._criar_tabela()
        inseridos = 0
        erros = 0
        try:
            with get_db_connection(database_name="qstione") as conn:
                conn.execute(f"DELETE FROM {self.NOME_TABELA}")
                cursor = conn.cursor()
                for registro in dados_transformados:
                    try:
                        cursor.execute(
                            f"""INSERT INTO {self.NOME_TABELA}
                               (codigoCurso, emailUsuario, papelUsuario, data_criacao, data_atualizacao)
                               VALUES (?, ?, ?, GETDATE(), GETDATE())""",
                            (registro["codigoCurso"], registro["emailUsuario"], registro["papelUsuario"]),
                        )
                        inseridos += 1
                    except Exception as exc:
                        erros += 1
                        logger.error(
                            "Erro ao inserir: curso=%s | email=%s | papel=%s | erro=%s",
                            registro["codigoCurso"], registro["emailUsuario"], registro["papelUsuario"], exc,
                        )
                conn.commit()
        except Exception:
            logger.exception("Erro durante a reconstrução da tabela %s.", self.NOME_TABELA)
            return {
                "total_inseridos": 0,
                "total_atualizados": 0,
                "total_erros": len(dados_transformados),
                "total_processados": len(dados_transformados),
            }
        logger.info("Importação concluída: inseridos=%d | erros=%d", inseridos, erros)
        return {
            "total_inseridos": inseridos,
            "total_atualizados": 0,
            "total_erros": erros,
            "total_processados": len(dados_transformados),
        }

    def executar_importacao(self) -> List[Dict[str, str]]:
        logger.info("=" * 100)
        logger.info("🚀 INÍCIO DA IMPORTAÇÃO imp_007_usuarios_cursos")
        logger.info("=" * 100)
        coordenadores = self.obter_coordenadores()
        docentes_turmas = self.obter_docentes_turmas()
        membros_nde = self.obter_membros_nde()
        dados_transformados = self.transformar_dados(docentes_turmas, coordenadores, membros_nde)
        resultado = self.importar_para_qstione(dados_transformados)
        logger.info(
            "📋 RESUMO FINAL | docentes=%d | coordenadores=%d | NDE=%d | processados=%d | inseridos=%d | erros=%d",
            len(docentes_turmas), len(coordenadores), len(membros_nde),
            resultado["total_processados"], resultado["total_inseridos"], resultado["total_erros"],
        )
        return dados_transformados


if __name__ == "__main__":
    try:
        ImportadorUsuariosCursos().executar_importacao()
    except Exception:
        logger.exception("Falha fatal na execução do imp_007_usuarios_cursos.")
        raise
