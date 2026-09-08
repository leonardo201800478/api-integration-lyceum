"""
Carga completa Qstione.

Executa as cargas na ordem definida pelas dependências da Plataforma:

    01 IMP-016
    02 IMP-001
    03 IMP-002
    04 IMP-005
    05 IMP-006
    06 IMP-007
    07 IMP-008
    08 IMP-009
    09 IMP-010
    10 IMP-011
    11 IMP-013

IMPORTANTE
----------
Os importadores continuam independentes.

Este módulo apenas:

    1. executa o importador;
    2. lê a tabela resultante;
    3. seleciona somente os campos documentados;
    4. envia para a API;
    5. valida a resposta;
    6. passa para a próxima etapa.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass

# ============================================================================
# PATH
# ============================================================================

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ============================================================================
# IMPORTS DO PROJETO
# ============================================================================

from core.database import get_db_connection

from qstione.api.cliente import (
    CAMPOS_API,
    ClienteQstione,
)


# ============================================================================
# LOG
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

TAMANHO_LOTE = 500


# ============================================================================
# ETAPA
# ============================================================================

@dataclass(frozen=True)
class Etapa:
    """Representa uma etapa da carga completa."""

    numero: int
    transacao: str
    tabela: str
    importador: str


ETAPAS = (
    Etapa(
        1,
        "IMP-016",
        "imp_016_unidades_organizacionais",
        "qstione.importadores.imp_016_unidades_organizacionais",
    ),
    Etapa(
        2,
        "IMP-001",
        "imp_001_cursos",
        "qstione.importadores.imp_001_cursos",
    ),
    Etapa(
        3,
        "IMP-002",
        "imp_002_disciplina",
        "qstione.importadores.imp_002_disciplina",
    ),
    Etapa(
        4,
        "IMP-005",
        "imp_005_ofertas",
        "qstione.importadores.imp_005_ofertas",
    ),
    Etapa(
        5,
        "IMP-006",
        "imp_006_usuarios",
        "qstione.importadores.imp_006_usuarios",
    ),
    Etapa(
        6,
        "IMP-007",
        "imp_007_usuarios_cursos",
        "qstione.importadores.imp_007_usuarios_cursos",
    ),
    Etapa(
        7,
        "IMP-008",
        "imp_008_usuarios_disciplinas",
        "qstione.importadores.imp_008_usuarios_disciplinas",
    ),
    Etapa(
        8,
        "IMP-009",
        "imp_009_professores_ofertas",
        "qstione.importadores.imp_009_professores_ofertas",
    ),
    Etapa(
        9,
        "IMP-010",
        "imp_010_alunos",
        "qstione.importadores.imp_010_alunos",
    ),
    Etapa(
        10,
        "IMP-011",
        "imp_011_alunos_ofertas",
        "qstione.importadores.imp_011_alunos_ofertas",
    ),
    Etapa(
        11,
        "IMP-013",
        "imp_013_unidades_avaliacao",
        "qstione.importadores.imp_013_unidades_avaliacao",
    ),
)


# ============================================================================
# ORQUESTRADOR
# ============================================================================

class CargaCompletaQstione:
    """
    Executa todas as cargas Qstione em sequência.
    """

    def __init__(
        self,
        url: str,
        token: str,
        tamanho_lote: int = TAMANHO_LOTE,
    ):
        """
        Inicializa o processo.

        Parameters
        ----------
        url:
            Endpoint da API Qstione.

        token:
            Token da instituição.

        tamanho_lote:
            Quantidade máxima de registros por requisição.
        """

        self.cliente = ClienteQstione(
            url=url,
            token=token,
        )

        self.tamanho_lote = tamanho_lote

    # ------------------------------------------------------------------------
    # IMPORTADOR
    # ------------------------------------------------------------------------

    @staticmethod
    def executar_importador(
        etapa: Etapa,
    ):
        """
        Importa dinamicamente o módulo e executa seu importador.
        """

        modulo = __import__(
            etapa.importador,
            fromlist=["*"],
        )

        classes = [
            valor
            for valor in vars(modulo).values()
            if isinstance(valor, type)
            and valor.__module__ == modulo.__name__
            and valor.__name__.startswith("Importador")
        ]

        if not classes:
            raise RuntimeError(
                f"Nenhuma classe Importador encontrada em "
                f"{etapa.importador}"
            )

        classe = classes[0]

        instancia = classe()

        return instancia.executar_importacao()

    # ------------------------------------------------------------------------
    # LEITURA SQL
    # ------------------------------------------------------------------------

    @staticmethod
    def ler_tabela(
        tabela: str,
        campos: tuple[str, ...],
    ) -> list[dict]:
        """
        Lê da tabela somente os campos permitidos pela API.

        Não utiliza SELECT *.
        """

        # Proteção contra nomes arbitrários.
        if not tabela.replace("_", "").isalnum():
            raise ValueError(
                f"Nome de tabela inválido: {tabela}"
            )

        for campo in campos:
            if not campo.replace("_", "").isalnum():
                raise ValueError(
                    f"Campo inválido: {campo}"
                )

        lista_campos = ", ".join(
            f"[{campo}]"
            for campo in campos
        )

        sql = f"""
            SELECT {lista_campos}
            FROM dbo.[{tabela}]
        """

        with get_db_connection(
            database_name="qstione"
        ) as conn:

            rows = conn.execute(sql).fetchall()

        return [
            dict(
                zip(campos, row)
            )
            for row in rows
        ]

    # ------------------------------------------------------------------------
    # ENVIO
    # ------------------------------------------------------------------------

    def enviar_etapa(
        self,
        etapa: Etapa,
        registros: list[dict],
    ):
        """
        Divide a etapa em lotes e envia cada lote para a API.
        """

        total = len(registros)

        print(
            f"   Registros preparados: {total}"
        )

        if total == 0:
            print(
                "   ⚠️ Nenhum registro para enviar."
            )
            return True

        enviados = 0

        for inicio in range(
            0,
            total,
            self.tamanho_lote,
        ):
            lote = registros[
                inicio:
                inicio + self.tamanho_lote
            ]

            numero_lote = (
                inicio // self.tamanho_lote
            ) + 1

            print(
                f"   → Lote {numero_lote}: "
                f"{len(lote)} registros"
            )

            resultado = self.cliente.enviar(
                etapa.transacao,
                lote,
            )

            if not resultado.sucesso:

                print(
                    f"   ❌ API retornou "
                    f"codigoStatus="
                    f"{resultado.codigo_status}"
                )

                for erro in resultado.erros:
                    print(
                        "      "
                        f"registro="
                        f"{erro.get('numeroRegistro')}; "
                        f"excecao="
                        f"{erro.get('nomeExcecao')}; "
                        f"detalhes="
                        f"{erro.get('detalhesFalha')}"
                    )

                return False

            enviados += len(lote)

            print(
                f"   ✓ Lote processado: "
                f"{enviados}/{total}"
            )

        return True

    # ------------------------------------------------------------------------
    # ETAPA
    # ------------------------------------------------------------------------

    def executar_etapa(
        self,
        etapa: Etapa,
    ) -> bool:
        """
        Executa uma etapa completa.
        """

        print()
        print(
            "=" * 78
        )

        print(
            f"[{etapa.numero:02d}/11] "
            f"{etapa.transacao} "
            f"- {etapa.tabela}"
        )

        print(
            "=" * 78
        )

        print(
            "   Executando importador local..."
        )

        self.executar_importador(etapa)

        campos = CAMPOS_API[
            etapa.transacao
        ]

        print(
            "   Campos API:"
        )

        print(
            "      "
            + ", ".join(campos)
        )

        registros = self.ler_tabela(
            etapa.tabela,
            campos,
        )

        return self.enviar_etapa(
            etapa,
            registros,
        )

    # ------------------------------------------------------------------------
    # PROCESSO COMPLETO
    # ------------------------------------------------------------------------

    def executar(self) -> bool:
        """
        Executa todas as 11 etapas na ordem definida.
        """

        print()
        print(
            "=" * 78
        )
        print(
            " CARGA COMPLETA QSTIONE"
        )
        print(
            "=" * 78
        )

        for etapa in ETAPAS:

            sucesso = self.executar_etapa(
                etapa
            )

            if not sucesso:

                print()
                print(
                    "!" * 78
                )
                print(
                    f" PROCESSO INTERROMPIDO EM "
                    f"{etapa.transacao}"
                )
                print(
                    "!" * 78
                )

                return False

        print()
        print(
            "=" * 78
        )
        print(
            " CARGA COMPLETA CONCLUÍDA COM SUCESSO"
        )
        print(
            "=" * 78
        )

        return True


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    URL = os.environ.get(
        "QSTIONE_API_URL"
    )

    TOKEN = os.environ.get(
        "QSTIONE_TOKEN"
    )

    if not URL:
        raise RuntimeError(
            "Variável QSTIONE_API_URL não configurada."
        )

    if not TOKEN:
        raise RuntimeError(
            "Variável QSTIONE_TOKEN não configurada."
        )

    processo = CargaCompletaQstione(
        url=URL,
        token=TOKEN,
    )

    sucesso = processo.executar()

    sys.exit(
        0 if sucesso else 1
    )