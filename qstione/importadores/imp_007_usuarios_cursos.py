"""
qstione/importadores/imp_007_usuarios_cursos.py

Importador IMP-007 - Usuários x Cursos para o Qstione.

REGRA FUNDAMENTAL
-----------------
O Qstione exige codigoCurso em cada vínculo, mas papelUsuario é global por
usuário. A hierarquia é C > A > P. Assim, um usuário que seja membro do NDE
(A) e também docente (P) deve ser A em TODOS os seus cursos.

G é administrativo/global e não participa da hierarquia C > A > P.
O não é produzido por este importador.

999 representa somente vínculo real com turma compartilhada.
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

USUARIO_GERAL = "camila.felicio@foa.org.br"
USUARIO_COORDENADOR = "gildo.bernardo@foa.org.br"


class ImportadorUsuariosCursos:
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
        logger.info("ANO_VIGENTE=%s | PERIODOS=%s | FACULDADES=%s", ANO_VIGENTE, PERIODOS_VIGENTES, FACULDADES_INCLUIDAS)
        logger.info("Regra de papel: C > A > P | papel global por usuário")
        logger.info("=" * 80)

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

    def _normalizar_email(self, email: Any) -> Optional[str]:
        if email is None:
            return None
        email = converter_minusculas(str(email).strip())
        return email if self._validar_email(email) else None

    def _tabela_existe(self, nome_tabela: str) -> bool:
        with get_db_connection(database_name="qstione") as conn:
            row = conn.execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'",
                (nome_tabela,),
            ).fetchone()
        return row is not None

    def _indice_existe(self, nome_indice: str) -> bool:
        try:
            with get_db_connection(database_name="qstione") as conn:
                row = conn.execute(
                    "SELECT 1 FROM sys.indexes WHERE name = ? AND object_id = OBJECT_ID(?)",
                    (nome_indice, self.NOME_TABELA),
                ).fetchone()
            return row is not None
        except Exception:
            return False

    def _garantir_chave_primaria(self) -> None:
        with get_db_connection(database_name="qstione") as conn:
            row = conn.execute(
                """
                SELECT kc.name
                FROM sys.key_constraints kc
                INNER JOIN sys.index_columns ic
                    ON ic.object_id = kc.parent_object_id AND ic.index_id = kc.unique_index_id
                INNER JOIN sys.columns c
                    ON c.object_id = ic.object_id AND c.column_id = ic.column_id
                WHERE kc.parent_object_id = OBJECT_ID(?) AND kc.type = 'PK'
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
                "SELECT kc.name FROM sys.key_constraints kc WHERE kc.parent_object_id = OBJECT_ID(?) AND kc.type = 'PK'",
                (self.NOME_TABELA,),
            ).fetchone()
            if old:
                conn.execute(f"ALTER TABLE {self.NOME_TABELA} DROP CONSTRAINT [{old[0]}]")
            conn.execute(
                f"ALTER TABLE {self.NOME_TABELA} ADD CONSTRAINT PK_imp_007_usuarios_cursos PRIMARY KEY (codigoCurso, emailUsuario, papelUsuario)"
            )
            conn.commit()

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
                        CONSTRAINT PK_imp_007_usuarios_cursos PRIMARY KEY (codigoCurso, emailUsuario, papelUsuario)
                    )
                    """
                )
                conn.commit()
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
                ON t.ano = td.ano AND t.semestre = td.periodo AND t.turma = td.turma AND t.disciplina = td.disciplina
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
        """Retorna somente NDE ativos, normalizando status, curso e e-mail."""
        sql = """
            SELECT DISTINCT
                LTRIM(RTRIM(CAST(codigoCurso AS NVARCHAR(30)))) AS codigoCurso,
                LTRIM(RTRIM(CAST(emailMembro AS NVARCHAR(100)))) AS emailMembro
            FROM imp_nde_membros
            WHERE codigoCurso IS NOT NULL
              AND LTRIM(RTRIM(CAST(codigoCurso AS NVARCHAR(30)))) <> ''
              AND emailMembro IS NOT NULL
              AND LTRIM(RTRIM(CAST(emailMembro AS NVARCHAR(100)))) <> ''
              AND UPPER(LTRIM(RTRIM(CAST(status AS NVARCHAR(10))))) = 'S'
        """
        try:
            with get_db_connection(database_name="qstione") as conn:
                rows = conn.execute(sql).fetchall()
        except Exception:
            logger.exception("Erro ao consultar imp_nde_membros.")
            return []

        validos: List[Tuple[Any, Any]] = []
        invalidos = 0
        for curso, email in rows:
            email_normalizado = self._normalizar_email(email)
            if not email_normalizado:
                invalidos += 1
                logger.warning("NDE ignorado por e-mail inválido: curso=%s | email=%s", curso, email)
                continue
            curso_unificado, _ = self._curso_unificado(curso)
            if not self._validar_codigo_curso(curso_unificado):
                invalidos += 1
                logger.warning("NDE ignorado por curso inválido: curso=%s | email=%s", curso, email_normalizado)
                continue
            validos.append((curso_unificado, email_normalizado))

        logger.info("👥 NDE ativos encontrados: %d | válidos: %d | descartados: %d", len(rows), len(validos), invalidos)
        return validos

    def _obter_email_docente(self, num_func: Any) -> Optional[str]:
        try:
            with get_db_connection(database_name="lyceum") as conn:
                row = conn.execute("SELECT mailbox FROM LY_DOCENTE WHERE num_func = ?", (num_func,)).fetchone()
            return self._normalizar_email(row[0]) if row and row[0] else None
        except Exception:
            logger.exception("Erro obtendo mailbox do docente %s.", num_func)
            return None

    def _adicionar_candidato(
        self,
        candidatos: Dict[str, Dict[str, Set[str]]],
        email: Any,
        papel: str,
        curso: Any,
        origem: str,
    ) -> bool:
        email = self._normalizar_email(email)
        papel = str(papel).strip().upper() if papel is not None else ""
        if not email or not self._validar_papel(papel):
            if email and papel not in PAPEIS_VALIDOS:
                logger.warning("Papel inválido ignorado: %s | email=%s | origem=%s", papel, email, origem)
            return False
        curso_unificado, _ = self._curso_unificado(curso)
        if not self._validar_codigo_curso(curso_unificado):
            logger.warning("Código de curso inválido ignorado: %s | email=%s | origem=%s", curso_unificado, email, origem)
            return False
        candidatos[email][papel].add(curso_unificado)
        return True

    def transformar_dados(
        self,
        docentes_turmas: List[Tuple[Any, Any, Any]],
        coordenadores: Dict[Tuple[str, str], bool],
        membros_nde: List[Tuple[Any, Any]],
    ) -> List[Dict[str, str]]:
        candidatos: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: {
                PAPEL_COORDENADOR: set(),
                PAPEL_AVALIADOR: set(),
                PAPEL_PROFESSOR: set(),
            }
        )

        # Primeiro todos os vínculos P/C.
        for num_func, email, curso in docentes_turmas:
            if num_func is None:
                continue
            curso_unificado, _ = self._curso_unificado(curso)
            chave_coord = (str(num_func).strip(), curso_unificado)
            papel = PAPEL_COORDENADOR if chave_coord in coordenadores else PAPEL_PROFESSOR
            self._adicionar_candidato(
                candidatos, email, papel, curso,
                "LY_COORDENACAO" if papel == PAPEL_COORDENADOR else "LY_TURMA_DOCENTE",
            )

        # Coordenadores sem turma docente também são incluídos.
        for (num_func, curso), _ in coordenadores.items():
            email = self._obter_email_docente(num_func)
            if email:
                self._adicionar_candidato(candidatos, email, PAPEL_COORDENADOR, curso, "LY_COORDENACAO")

        # IMPORTANTE: NDE é registrado separadamente e ANTES da consolidação.
        # Isso garante que A nunca seja perdido para P.
        emails_nde: Set[str] = set()
        for curso, email in membros_nde:
            email_normalizado = self._normalizar_email(email)
            if not email_normalizado:
                continue
            if self._adicionar_candidato(candidatos, email_normalizado, PAPEL_AVALIADOR, curso, "NDE"):
                emails_nde.add(email_normalizado)

        logger.info("👥 Usuários NDE efetivamente consolidados como candidatos A: %d", len(emails_nde))

        # Usuário administrativo fixo.
        email_geral = self._normalizar_email(USUARIO_GERAL)
        if email_geral:
            cursos_geral = set()
            for cursos in candidatos[email_geral].values():
                cursos_geral.update(cursos)
            if not cursos_geral:
                cursos_geral.add(CURSO_COMPARTILHADO)
            candidatos[email_geral][PAPEL_GERAL] = cursos_geral

        # Usuário coordenador especial existente na integração.
        email_coord_especial = self._normalizar_email(USUARIO_COORDENADOR)
        if email_coord_especial:
            cursos_coord = set()
            for papel in (PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR):
                cursos_coord.update(candidatos[email_coord_especial].get(papel, set()))
            if cursos_coord:
                candidatos[email_coord_especial][PAPEL_COORDENADOR].update(cursos_coord)

        registros: List[Dict[str, str]] = []
        estatisticas = defaultdict(int)
        nde_promovidos = 0

        for email, papeis in sorted(candidatos.items()):
            if email == email_geral and papeis.get(PAPEL_GERAL):
                papel_efetivo = PAPEL_GERAL
                cursos = set(papeis[PAPEL_GERAL])
            elif papeis[PAPEL_COORDENADOR]:
                papel_efetivo = PAPEL_COORDENADOR
                cursos = set().union(*[
                    papeis[k] for k in (PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR)
                ])
            elif papeis[PAPEL_AVALIADOR]:
                papel_efetivo = PAPEL_AVALIADOR
                cursos = set().union(*[
                    papeis[k] for k in (PAPEL_COORDENADOR, PAPEL_AVALIADOR, PAPEL_PROFESSOR)
                ])
            elif papeis[PAPEL_PROFESSOR]:
                papel_efetivo = PAPEL_PROFESSOR
                cursos = set(papeis[PAPEL_PROFESSOR])
            else:
                continue

            if email in emails_nde and papel_efetivo == PAPEL_AVALIADOR and papeis[PAPEL_PROFESSOR]:
                nde_promovidos += 1
                logger.info(
                    "⬆️ NDE: %s promovido de P para A | cursos consolidados=%d",
                    email, len(cursos),
                )

            for curso in sorted(cursos):
                registros.append({
                    "codigoCurso": curso,
                    "emailUsuario": email,
                    "papelUsuario": papel_efetivo,
                })
                estatisticas[papel_efetivo] += 1

        # Integridade: nenhum NDE ativo pode terminar como P.
        resultado_por_email: Dict[str, str] = {}
        for registro in registros:
            resultado_por_email[registro["emailUsuario"]] = registro["papelUsuario"]
        nde_com_p = [email for email in emails_nde if resultado_por_email.get(email) == PAPEL_PROFESSOR]
        nde_sem_resultado = [email for email in emails_nde if email not in resultado_por_email]
        if nde_com_p:
            raise RuntimeError(f"Integridade IMP-007: NDE terminou como P: {nde_com_p}")
        if nde_sem_resultado:
            raise RuntimeError(f"Integridade IMP-007: NDE sem registro final: {nde_sem_resultado}")

        registros.sort(key=lambda r: (r["codigoCurso"], r["emailUsuario"], r["papelUsuario"]))
        logger.info("=" * 80)
        logger.info("📊 RESULTADO DA CONSOLIDAÇÃO")
        logger.info("   G = %d", estatisticas[PAPEL_GERAL])
        logger.info("   C = %d", estatisticas[PAPEL_COORDENADOR])
        logger.info("   A = %d", estatisticas[PAPEL_AVALIADOR])
        logger.info("   P = %d", estatisticas[PAPEL_PROFESSOR])
        logger.info("   NDE promovidos P -> A = %d", nde_promovidos)
        logger.info("   NDE sem P no resultado final = %d", len(nde_com_p))
        logger.info("   TOTAL = %d", len(registros))
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
