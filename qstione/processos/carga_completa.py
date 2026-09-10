"""Orquestra a carga completa de dados do Lyceum para o Qstione."""

from __future__ import annotations

import importlib
import logging
import os
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import get_db_connection
from qstione.api.cliente import CAMPOS_API, ClienteQstione
from qstione.config.qstione_config import (
    QSTIONE_BASE_URL,
    QSTIONE_TOKEN,
    QSTIONE_SSL_VERIFY,
    QSTIONE_TIMEOUT,
    validar_configuracao_qstione,
)

logger = logging.getLogger(__name__)
TAMANHO_LOTE = int(os.getenv("QSTIONE_TAMANHO_LOTE", "500"))


@dataclass(frozen=True)
class Etapa:
    numero: int
    transacao: str
    tabela: str
    importador: str | None = None
    registro_fixo: bool = False


# IMP-016 utiliza exclusivamente o registro fixo já existente na tabela.
# IMP-012 permanece fora da carga: a transação foi descontinuada na especificação.
ETAPAS = (
    Etapa(1, "IMP-016", "imp_016_unidades_organizacionais", registro_fixo=True),
    Etapa(2, "IMP-001", "imp_001_cursos", "qstione.importadores.imp_001_cursos"),
    Etapa(3, "IMP-002", "imp_002_disciplina", "qstione.importadores.imp_002_disciplina"),
    Etapa(4, "IMP-005", "imp_005_ofertas", "qstione.importadores.imp_005_ofertas"),
    Etapa(5, "IMP-006", "imp_006_usuarios", "qstione.importadores.imp_006_usuarios"),
    Etapa(6, "IMP-007", "imp_007_usuarios_cursos", "qstione.importadores.imp_007_usuarios_cursos"),
    Etapa(7, "IMP-008", "imp_008_usuarios_disciplinas", "qstione.importadores.imp_008_usuarios_disciplinas"),
    Etapa(8, "IMP-009", "imp_009_professores_ofertas", "qstione.importadores.imp_009_professores_ofertas"),
    Etapa(9, "IMP-010", "imp_010_alunos", "qstione.importadores.imp_010_alunos"),
    Etapa(10, "IMP-011", "imp_011_alunos_ofertas", "qstione.importadores.imp_011_alunos_ofertas"),
    Etapa(11, "IMP-013", "imp_013_unidades_avaliacao", "qstione.importadores.imp_013_unidades_avaliacao_regras"),
)


class CargaCompletaQstione:
    """Executa as cargas em ordem e interrompe no primeiro erro."""

    def __init__(
        self,
        url: str = QSTIONE_BASE_URL,
        token: str = QSTIONE_TOKEN or "",
        tamanho_lote: int = TAMANHO_LOTE,
    ) -> None:
        if tamanho_lote < 1:
            raise ValueError("QSTIONE_TAMANHO_LOTE deve ser maior que zero.")
        self.cliente = ClienteQstione(
            url=url,
            token=token,
            timeout=QSTIONE_TIMEOUT,
            ssl_verify=QSTIONE_SSL_VERIFY,
        )
        self.tamanho_lote = tamanho_lote

    @staticmethod
    def executar_importador(etapa: Etapa) -> None:
        if etapa.registro_fixo or not etapa.importador:
            return
        modulo = importlib.import_module(etapa.importador)
        classes = [
            valor for valor in vars(modulo).values()
            if isinstance(valor, type)
            and valor.__module__ == modulo.__name__
            and valor.__name__.startswith("Importador")
        ]
        if not classes:
            raise RuntimeError(f"Nenhuma classe Importador encontrada em {etapa.importador}")
        if len(classes) > 1:
            raise RuntimeError(
                f"Mais de uma classe Importador encontrada em {etapa.importador}: "
                f"{', '.join(cls.__name__ for cls in classes)}"
            )
        classes[0]().executar_importacao()

    @staticmethod
    def ler_tabela(tabela: str, campos: tuple[str, ...]) -> list[dict]:
        if not tabela.replace("_", "").isalnum():
            raise ValueError(f"Nome de tabela inválido: {tabela}")
        if any(not campo.replace("_", "").isalnum() for campo in campos):
            raise ValueError("Um ou mais campos da API possuem nome inválido.")
        colunas = ", ".join("[" + campo + "]" for campo in campos)
        sql = "SELECT " + colunas + " FROM dbo.[" + tabela + "]"
        with get_db_connection(database_name="qstione") as conn:
            rows = conn.execute(sql).fetchall()
        return [dict(zip(campos, row)) for row in rows]

    @staticmethod
    def _validar_tabela_e_colunas(tabela: str, campos: tuple[str, ...]) -> int:
        """Valida a estrutura sem alterar dados e retorna a quantidade de registros."""
        if not tabela.replace("_", "").isalnum():
            raise ValueError(f"Nome de tabela inválido: {tabela}")
        if any(not campo.replace("_", "").isalnum() for campo in campos):
            raise ValueError("Um ou mais campos da API possuem nome inválido.")

        with get_db_connection(database_name="qstione") as conn:
            tabela_existe = conn.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = ?
                  AND TABLE_TYPE = 'BASE TABLE'
                """,
                (tabela,),
            ).fetchone()
            if tabela_existe is None:
                raise RuntimeError(f"Tabela dbo.{tabela} não existe.")

            placeholders = ",".join("?" for _ in campos)
            rows = conn.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = ?
                  AND COLUMN_NAME IN (""" + placeholders + ")",
                (tabela, *campos),
            ).fetchall()
            existentes = {row[0] for row in rows}
            ausentes = [campo for campo in campos if campo not in existentes]
            if ausentes:
                raise RuntimeError(
                    f"Tabela dbo.{tabela}: campos ausentes: {', '.join(ausentes)}"
                )

            # Não usar f-string para montar este identificador: além de desnecessário,
            # evita ambiguidades do parser em diferentes versões do Python.
            sql_count = "SELECT COUNT(*) FROM dbo.[" + tabela + "]"
            return conn.execute(sql_count).fetchone()[0]

    @staticmethod
    def _validar_importador_importavel(etapa: Etapa) -> None:
        if etapa.registro_fixo or not etapa.importador:
            return
        modulo = importlib.import_module(etapa.importador)
        classes = [
            valor for valor in vars(modulo).values()
            if isinstance(valor, type)
            and valor.__module__ == modulo.__name__
            and valor.__name__.startswith("Importador")
        ]
        if len(classes) != 1:
            raise RuntimeError(
                f"{etapa.transacao}: esperado exatamente 1 classe Importador em "
                f"{etapa.importador}; encontradas {len(classes)}."
            )
        if not hasattr(classes[0], "executar_importacao"):
            raise RuntimeError(
                f"{etapa.transacao}: {classes[0].__name__} não possui executar_importacao()."
            )

    def preflight(self) -> bool:
        """Valida configuração, módulos e tabelas sem executar nenhum importador."""
        print("\n" + "=" * 78)
        print(" PREFLIGHT — CARGA COMPLETA QSTIONE")
        print(" Nenhum importador será executado e nenhum dado será alterado.")
        print("=" * 78)

        falhas = []
        try:
            validar_configuracao_qstione()
            print("✓ Configuração Qstione válida")
        except Exception as exc:
            falhas.append(f"Configuração Qstione: {exc}")

        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print(f"Tamanho do lote: {self.tamanho_lote}")

        try:
            with get_db_connection(database_name="lyceum") as conn:
                conn.execute("SELECT 1").fetchone()
            print("✓ Conectividade com banco Lyceum")
        except Exception as exc:
            falhas.append(f"Banco Lyceum: {exc}")

        try:
            with get_db_connection(database_name="qstione") as conn:
                conn.execute("SELECT 1").fetchone()
            print("✓ Conectividade com banco Qstione")
        except Exception as exc:
            falhas.append(f"Banco Qstione: {exc}")

        for etapa in ETAPAS:
            try:
                self._validar_importador_importavel(etapa)
                quantidade = self._validar_tabela_e_colunas(
                    etapa.tabela,
                    CAMPOS_API[etapa.transacao],
                )
                if etapa.registro_fixo and quantidade != 1:
                    raise RuntimeError(
                        f"IMP-016 deve conter exatamente 1 registro fixo; encontrados {quantidade}."
                    )
                if not etapa.registro_fixo and quantidade == 0:
                    raise RuntimeError("Tabela sem registros para a carga.")
                print(f"✓ {etapa.transacao}: tabela/colunas OK | registros atuais={quantidade}")
            except Exception as exc:
                falhas.append(f"{etapa.transacao}: {exc}")
                print(f"✗ {etapa.transacao}: {exc}")

        try:
            self.cliente.session.get(
                self.cliente.url,
                timeout=self.cliente.timeout,
                verify=self.cliente.ssl_verify,
            )
            print("✓ Endpoint Qstione acessível")
        except Exception as exc:
            # GET pode ser recusado pelo endpoint sem significar indisponibilidade do POST.
            print(f"⚠ Endpoint GET não validado: {exc}")
            print("  A conectividade final será validada pelo POST da carga.")

        if falhas:
            print("\n" + "=" * 78)
            print(" PREFLIGHT FALHOU")
            for falha in falhas:
                print(f"- {falha}")
            return False

        print("\n" + "=" * 78)
        print(" PREFLIGHT OK")
        print("=" * 78)
        return True

    def enviar_etapa(self, etapa: Etapa) -> bool:
        registros = self.ler_tabela(etapa.tabela, CAMPOS_API[etapa.transacao])
        if not registros:
            if etapa.registro_fixo:
                raise RuntimeError("IMP-016 precisa possuir o registro fixo configurado.")
            logger.warning("%s: tabela sem registros; etapa ignorada.", etapa.transacao)
            return True

        total = len(registros)
        for inicio in range(0, total, self.tamanho_lote):
            lote = registros[inicio:inicio + self.tamanho_lote]
            numero_lote = (inicio // self.tamanho_lote) + 1
            total_lotes = (total + self.tamanho_lote - 1) // self.tamanho_lote
            print(
                f"\n[{etapa.transacao}] lote {numero_lote}/{total_lotes} "
                f"({len(lote)} registros)"
            )
            resultado = self.cliente.enviar(etapa.transacao, lote)
            if not resultado.sucesso:
                print(f"✗ {etapa.transacao}: falha na API (status={resultado.codigo_status})")
                for erro in resultado.erros:
                    print(
                        f"  registro={erro.get('numeroRegistro')} | "
                        f"{erro.get('nomeExcecao')}: {erro.get('detalhesFalha')}"
                    )
                return False
            if resultado.assincrono:
                print(
                    f"✗ {etapa.transacao}: API respondeu modo assíncrono; "
                    "a carga completa exige confirmação síncrona."
                )
                return False
            print(f"✓ {etapa.transacao}: lote processado com sucesso")
        return True

    def executar(self) -> bool:
        print("\n" + "=" * 78)
        print(" CARGA COMPLETA LYCEUM → QSTIONE")
        print("=" * 78)
        print(f"Endpoint: {self.cliente.url}")
        print(f"Tamanho do lote: {self.tamanho_lote}")

        for etapa in ETAPAS:
            print(f"\n{'-' * 78}\nETAPA {etapa.numero}/{len(ETAPAS)} — {etapa.transacao}\n{'-' * 78}")
            try:
                if etapa.registro_fixo:
                    registros = self.ler_tabela(etapa.tabela, CAMPOS_API[etapa.transacao])
                    if len(registros) != 1:
                        raise RuntimeError(
                            f"IMP-016 deve conter exatamente 1 registro fixo; encontrados {len(registros)}."
                        )
                else:
                    self.executar_importador(etapa)
                if not self.enviar_etapa(etapa):
                    print(f"\n✗ Carga interrompida em {etapa.transacao}.")
                    return False
            except Exception:
                logger.exception("Erro durante %s", etapa.transacao)
                print(f"\n✗ Carga interrompida em {etapa.transacao}.")
                return False

        print("\n" + "=" * 78)
        print(" CARGA COMPLETA CONCLUÍDA COM SUCESSO")
        print("=" * 78)
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    validar_configuracao_qstione()
    if "--preflight" in sys.argv:
        carga = CargaCompletaQstione()
        try:
            sys.exit(0 if carga.preflight() else 1)
        finally:
            carga.cliente.close()
    sys.exit(0 if CargaCompletaQstione().executar() else 1)
