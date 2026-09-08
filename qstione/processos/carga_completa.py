"""Orquestra a carga completa de dados do Lyceum para o Qstione."""

from __future__ import annotations

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
    Etapa(11, "IMP-013", "imp_013_unidades_avaliacao", "qstione.importadores.imp_013_unidades_avaliacao"),
)


class CargaCompletaQstione:
    """Executa as cargas em ordem e interrompe no primeiro erro."""

    def __init__(self, url: str = QSTIONE_BASE_URL, token: str = QSTIONE_TOKEN or "", tamanho_lote: int = TAMANHO_LOTE) -> None:
        if tamanho_lote < 1:
            raise ValueError("QSTIONE_TAMANHO_LOTE deve ser maior que zero.")
        self.cliente = ClienteQstione(url=url, token=token, timeout=QSTIONE_TIMEOUT, ssl_verify=QSTIONE_SSL_VERIFY)
        self.tamanho_lote = tamanho_lote

    @staticmethod
    def executar_importador(etapa: Etapa) -> None:
        if etapa.registro_fixo or not etapa.importador:
            return
        modulo = __import__(etapa.importador, fromlist=["*"])
        classes = [
            valor for valor in vars(modulo).values()
            if isinstance(valor, type)
            and valor.__module__ == modulo.__name__
            and valor.__name__.startswith("Importador")
        ]
        if not classes:
            raise RuntimeError(f"Nenhuma classe Importador encontrada em {etapa.importador}")
        classes[0]().executar_importacao()

    @staticmethod
    def ler_tabela(tabela: str, campos: tuple[str, ...]) -> list[dict]:
        if not tabela.replace("_", "").isalnum():
            raise ValueError(f"Nome de tabela inválido: {tabela}")
        if any(not campo.replace("_", "").isalnum() for campo in campos):
            raise ValueError("Um ou mais campos da API possuem nome inválido.")
        sql = f"SELECT {', '.join(f'[{campo}]' for campo in campos)} FROM dbo.[{tabela}]"
        with get_db_connection(database_name="qstione") as conn:
            rows = conn.execute(sql).fetchall()
        return [dict(zip(campos, row)) for row in rows]

    def enviar_etapa(self, etapa: Etapa, registros: list[dict]) -> bool:
        total = len(registros)
        print(f"   Registros preparados: {total}")

        if etapa.registro_fixo and total != 1:
            print(f"   ❌ IMP-016 deve conter exatamente 1 registro fixo; encontrados {total}.")
            return False
        if total == 0:
            print("   ⚠️ Nenhum registro para enviar.")
            return True

        for inicio in range(0, total, self.tamanho_lote):
            lote = registros[inicio:inicio + self.tamanho_lote]
            numero_lote = inicio // self.tamanho_lote + 1
            print(f"   → Lote {numero_lote}: {len(lote)} registros")
            resultado = self.cliente.enviar(etapa.transacao, lote)

            # Uma resposta A significa apenas aceitação. Como a próxima etapa
            # pode depender desta, não avançamos sem confirmação de conclusão.
            if resultado.assincrono:
                print(
                    "   ❌ Operação assíncrona aceita pela API "
                    f"(idRequisicao={resultado.id_requisicao}). "
                    "Carga interrompida para preservar a ordem das dependências."
                )
                return False

            if not resultado.sucesso:
                print(f"   ❌ API retornou codigoStatus={resultado.codigo_status} (HTTP {resultado.http_status}).")
                for erro in resultado.erros:
                    print(
                        "      "
                        f"registro={erro.get('numeroRegistro')}; "
                        f"excecao={erro.get('nomeExcecao')}; "
                        f"detalhes={erro.get('detalhesFalha')}"
                    )
                return False
            print(f"   ✓ Lote processado: {min(inicio + len(lote), total)}/{total}")
        return True

    def executar_etapa(self, etapa: Etapa) -> bool:
        print("\n" + "=" * 78)
        print(f"[{etapa.numero:02d}/11] {etapa.transacao} - {etapa.tabela}")
        print("=" * 78)

        if etapa.registro_fixo:
            print("   IMP-016: usando o único registro fixo já existente na tabela.")
        else:
            print("   Executando importador local...")
            self.executar_importador(etapa)

        campos = CAMPOS_API[etapa.transacao]
        print(f"   Campos API: {', '.join(campos)}")
        registros = self.ler_tabela(etapa.tabela, campos)
        return self.enviar_etapa(etapa, registros)

    def executar(self) -> bool:
        print("\n" + "=" * 78)
        print(" CARGA COMPLETA QSTIONE")
        print(" Protocolo: 1.2.10 | Dicionário: 1.15.0")
        print("=" * 78)
        try:
            for etapa in ETAPAS:
                if not self.executar_etapa(etapa):
                    print("\n" + "!" * 78)
                    print(f" PROCESSO INTERROMPIDO EM {etapa.transacao}")
                    print("!" * 78)
                    return False
        finally:
            self.cliente.close()
        print("\n" + "=" * 78)
        print(" CARGA COMPLETA CONCLUÍDA COM SUCESSO")
        print("=" * 78)
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    validar_configuracao_qstione()
    sys.exit(0 if CargaCompletaQstione().executar() else 1)
