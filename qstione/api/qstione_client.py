"""
Cliente HTTP para comunicação com a Plataforma Qstione.

Baseado na especificação:
    Qstione - Especificações da Interface de Comunicação
    Plataforma x IE - versão 1.2.10

Responsabilidades:
    - montar os headers obrigatórios;
    - serializar o array JSON;
    - utilizar POST/HTTPS;
    - utilizar ISO-8859-1;
    - enviar somente os campos definidos pela transação;
    - interpretar a mensagem de retorno;
    - diferenciar sucesso, validação e execução;
    - preservar os erros retornados pela Qstione.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import requests


logger = logging.getLogger(__name__)


# ============================================================================
# ESPECIFICAÇÃO DA API
# ============================================================================

VERSAO_PROTOCOLO = "1.2.10"
FORMATO_OPERACAO = "JSON"


# ============================================================================
# SCHEMAS OFICIAIS
# ============================================================================

CAMPOS_API = {
    "IMP-016": (
        "codigoUnidade",
        "nomeCurto",
        "nomeLongo",
        "codigoUnidadeGestora",
    ),

    "IMP-001": (
        "codigoCurso",
        "nomeCurso",
        "quantPeriodos",
        "codigoUnidadeOrganizacional",
    ),

    "IMP-002": (
        "codigoDisciplina",
        "nomeDisciplina",
        "codigoCurso",
        "Período",
    ),

    "IMP-005": (
        "codigoOferta",
        "nomeOferta",
        "codigoDisciplina",
        "semestreOferta",
        "codigoTipoOferta",
        "codigoOfertaOrigem",
        "turno",
        "codigoIdentificacaoAVA",
    ),

    "IMP-006": (
        "matriculaUsuario",
        "codigoUsuario",
        "emailUsuario",
        "nomeUsuario",
    ),

    "IMP-007": (
        "codigoCurso",
        "emailUsuario",
        "papelUsuario",
    ),

    "IMP-008": (
        "codigoDisciplina",
        "emailUsuario",
    ),

    "IMP-009": (
        "codigoOferta",
        "emailProfessor",
    ),

    "IMP-010": (
        "matriculaAluno",
        "nomeAluno",
        "emailAluno",
        "codigoCurso",
        "turno",
        "codigoIdentificacaoAVA",
    ),

    "IMP-011": (
        "codigoOferta",
        "matriculaAluno",
        "codigoCurso",
    ),

    "IMP-013": (
        "codigoUnidade",
        "nomeUnidade",
        "codigoCurso",
        "codigoDisciplina",
        "ordemExibicao",
        "codigoAgrupamento",
    ),
}


# ============================================================================
# RESULTADO
# ============================================================================

@dataclass
class ResultadoAPI:
    """Representa o resultado de uma requisição à API Qstione."""

    codigo_status: int
    modo_execucao: str
    id_requisicao: int
    quantidade_erros: int
    erros: list[dict[str, Any]]
    status_http: int

    @property
    def sucesso(self) -> bool:
        """Retorna True quando a operação foi executada com sucesso."""
        return self.codigo_status == 0

    @property
    def falha_validacao(self) -> bool:
        """Retorna True quando a Qstione rejeitou a validação."""
        return self.codigo_status == 2

    @property
    def falha_execucao(self) -> bool:
        """Retorna True quando houve falha durante a execução."""
        return self.codigo_status == 3


# ============================================================================
# CLIENTE
# ============================================================================

class ClienteQstione:
    """
    Cliente responsável pela comunicação com a Plataforma Qstione.

    A classe não conhece as tabelas SQL. Ela recebe registros já
    transformados para o formato da API.
    """

    def __init__(
        self,
        url: str,
        token: str,
        timeout: int = 120,
        verificar_ssl: bool = True,
    ):
        """
        Inicializa o cliente.

        Parameters
        ----------
        url:
            URL do endpoint Qstione.

        token:
            Token de identificação da instituição.

        timeout:
            Timeout da requisição em segundos.

        verificar_ssl:
            Define se o certificado HTTPS será validado.
        """

        self.url = url
        self.token = token
        self.timeout = timeout
        self.verificar_ssl = verificar_ssl

        self.session = requests.Session()

    # ------------------------------------------------------------------------
    # PAYLOAD
    # ------------------------------------------------------------------------

    @staticmethod
    def preparar_registro(
        transacao: str,
        registro: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Remove qualquer coluna que não pertença ao schema oficial da API.

        Essa função é uma barreira de segurança:
        mesmo que a tabela SQL possua dezenas de colunas auxiliares,
        somente os campos documentados para a transação serão enviados.
        """

        if transacao not in CAMPOS_API:
            raise ValueError(
                f"Transação não possui schema definido: {transacao}"
            )

        campos_permitidos = CAMPOS_API[transacao]

        return {
            campo: registro[campo]
            for campo in campos_permitidos
            if campo in registro
        }

    # ------------------------------------------------------------------------
    # LOTE
    # ------------------------------------------------------------------------

    def preparar_lote(
        self,
        transacao: str,
        registros: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Prepara todos os registros do lote.

        Nenhuma chave fora do schema da transação é preservada.
        """

        return [
            self.preparar_registro(transacao, registro)
            for registro in registros
        ]

    # ------------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------------

    def enviar(
        self,
        transacao: str,
        registros: list[dict[str, Any]],
    ) -> ResultadoAPI:
        """
        Envia um lote para a Plataforma Qstione.

        O body é diretamente o array JSON, conforme a documentação.
        """

        if not registros:
            return ResultadoAPI(
                codigo_status=0,
                modo_execucao="S",
                id_requisicao=0,
                quantidade_erros=0,
                erros=[],
                status_http=200,
            )

        payload = self.preparar_lote(
            transacao,
            registros,
        )

        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("iso-8859-1")

        headers = {
            "versaoProtocolo": VERSAO_PROTOCOLO,
            "tokenIdInstituicao": self.token,
            "codigoTransacao": transacao,
            "formatoOperacao": FORMATO_OPERACAO,
            "quantidadeRegistros": str(len(payload)),
            "Content-Type": "application/json",
        }

        logger.info(
            "Enviando %s | registros=%d",
            transacao,
            len(payload),
        )

        response = self.session.post(
            self.url,
            headers=headers,
            data=body,
            timeout=self.timeout,
            verify=self.verificar_ssl,
        )

        return self._interpretar_resposta(response)

    # ------------------------------------------------------------------------
    # RESPOSTA
    # ------------------------------------------------------------------------

    @staticmethod
    def _interpretar_resposta(
        response: requests.Response,
    ) -> ResultadoAPI:
        """
        Interpreta os headers e o body da resposta Qstione.
        """

        try:
            codigo_status = int(
                response.headers.get("codigoStatus", "1")
            )
        except ValueError:
            codigo_status = 1

        try:
            modo_execucao = response.headers.get(
                "modoExecucao",
                "S",
            )
        except Exception:
            modo_execucao = "S"

        try:
            id_requisicao = int(
                response.headers.get(
                    "idRequisicao",
                    "0",
                )
            )
        except ValueError:
            id_requisicao = 0

        try:
            quantidade_erros = int(
                response.headers.get(
                    "quantidadeRegistrosErro",
                    "0",
                )
            )
        except ValueError:
            quantidade_erros = 0

        erros = []

        if response.content:
            try:
                dados = json.loads(
                    response.content.decode("iso-8859-1")
                )

                if isinstance(dados, list):
                    erros = dados

            except Exception:
                logger.exception(
                    "Não foi possível interpretar registrosErro."
                )

        return ResultadoAPI(
            codigo_status=codigo_status,
            modo_execucao=modo_execucao,
            id_requisicao=id_requisicao,
            quantidade_erros=quantidade_erros,
            erros=erros,
            status_http=response.status_code,
        )