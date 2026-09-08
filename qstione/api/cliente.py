"""Cliente HTTP para o protocolo de integração Qstione 1.2.10."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import requests

from qstione.config.qstione_config import (
    QSTIONE_SSL_VERIFY,
    QSTIONE_TIMEOUT,
)


logger = logging.getLogger(__name__)

VERSAO_PROTOCOLO = "1.2.10"
FORMATO_OPERACAO = "JSON"

# Os nomes abaixo são os nomes efetivamente enviados no JSON.
# "periodo" corresponde ao campo definido como "Período" no dicionário.
CAMPOS_API: dict[str, tuple[str, ...]] = {
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
        "periodo",
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
    "IMP-016": (
        "codigoUnidade",
        "nomeCurto",
        "nomeLongo",
        "codigoUnidadeGestora",
    ),
}


@dataclass
class ResultadoAPI:
    """Resultado normalizado de uma mensagem de retorno Qstione."""

    codigo_status: str | None
    id_requisicao: str | None
    modo_execucao: str | None
    quantidade_registros_erro: int = 0
    erros: list[dict[str, Any]] = field(default_factory=list)
    http_status: int | None = None
    corpo_bruto: Any = None

    @property
    def sucesso(self) -> bool:
        return self.codigo_status == "0"

    @property
    def assincrono(self) -> bool:
        return self.modo_execucao == "A"


class ClienteQstione:
    """Cliente para envio das transações de importação ao Qstione."""

    def __init__(
        self,
        url: str,
        token: str,
        timeout: int = QSTIONE_TIMEOUT,
        ssl_verify: bool = QSTIONE_SSL_VERIFY,
    ) -> None:
        if not url:
            raise ValueError("URL da API Qstione não informada.")
        if not token:
            raise ValueError("Token Qstione não informado.")

        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.ssl_verify = ssl_verify
        self.session = requests.Session()

    @staticmethod
    def _normalizar_headers(headers: requests.structures.CaseInsensitiveDict) -> dict[str, str]:
        return {str(k).lower(): str(v) for k, v in headers.items()}

    @staticmethod
    def _parse_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _ler_corpo_resposta(self, response: requests.Response) -> Any:
        if not response.content:
            return []

        try:
            return json.loads(response.content.decode("iso-8859-1"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                return response.json()
            except ValueError:
                return response.text

    def enviar(
        self,
        codigo_transacao: str,
        registros: list[dict[str, Any]],
    ) -> ResultadoAPI:
        """Envia uma operação seguindo exatamente o protocolo Qstione."""

        if codigo_transacao not in CAMPOS_API:
            raise ValueError(f"Transação não suportada pelo cliente: {codigo_transacao}")

        if not isinstance(registros, list):
            raise TypeError("O corpo da operação deve ser uma lista JSON.")

        campos = CAMPOS_API[codigo_transacao]
        payload: list[dict[str, Any]] = []

        for indice, registro in enumerate(registros):
            if not isinstance(registro, dict):
                raise TypeError(f"Registro {indice} não é um objeto JSON.")

            desconhecidos = set(registro) - set(campos)
            if desconhecidos:
                raise ValueError(
                    f"{codigo_transacao} registro {indice}: campos não previstos: "
                    f"{sorted(desconhecidos)}"
                )

            # Campos opcionais nulos são omitidos. Campos presentes com valor
            # são preservados exatamente como vieram da tabela.
            payload.append({
                campo: registro[campo]
                for campo in campos
                if campo in registro and registro[campo] is not None
            })

        body_text = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        body = body_text.encode("iso-8859-1")

        headers = {
            "versaoProtocolo": VERSAO_PROTOCOLO,
            "tokenIdInstituicao": self.token,
            "codigoTransacao": codigo_transacao,
            "formatoOperacao": FORMATO_OPERACAO,
            "quantidadeRegistros": str(len(payload)),
            "Content-Type": "application/json; charset=ISO-8859-1",
            "Accept": "application/json",
        }

        logger.info(
            "Qstione POST | transacao=%s | registros=%d | url=%s",
            codigo_transacao,
            len(payload),
            self.url,
        )

        try:
            response = self.session.post(
                self.url,
                data=body,
                headers=headers,
                timeout=self.timeout,
                verify=self.ssl_verify,
            )
        except requests.RequestException as exc:
            logger.exception("Falha HTTP na transação %s", codigo_transacao)
            return ResultadoAPI(
                codigo_status=None,
                id_requisicao=None,
                modo_execucao=None,
                erros=[{
                    "numeroRegistro": -1,
                    "nomeExcecao": "ErroHTTP",
                    "detalhesFalha": str(exc),
                }],
                http_status=None,
            )

        response_headers = self._normalizar_headers(response.headers)
        corpo = self._ler_corpo_resposta(response)

        codigo_status = response_headers.get("codigostatus")
        id_requisicao = response_headers.get("idrequisicao")
        modo_execucao = response_headers.get("modoexecucao")
        quantidade_erros = self._parse_int(
            response_headers.get("quantidaderegistroserro"),
            0,
        )

        # O protocolo devolve os registros de erro diretamente no corpo,
        # sem wrapper "registrosErro".
        erros = corpo if isinstance(corpo, list) else []

        if codigo_status is None and response.status_code >= 400:
            codigo_status = "1"
            if not erros:
                erros = [{
                    "numeroRegistro": -1,
                    "nomeExcecao": "HTTPError",
                    "detalhesFalha": (
                        f"HTTP {response.status_code}: "
                        f"{str(corpo)[:500]}"
                    ),
                }]

        resultado = ResultadoAPI(
            codigo_status=codigo_status,
            id_requisicao=id_requisicao,
            modo_execucao=modo_execucao,
            quantidade_registros_erro=quantidade_erros,
            erros=erros,
            http_status=response.status_code,
            corpo_bruto=corpo,
        )

        logger.info(
            "Qstione retorno | transacao=%s | HTTP=%s | status=%s | "
            "id=%s | modo=%s | erros=%d",
            codigo_transacao,
            response.status_code,
            resultado.codigo_status,
            resultado.id_requisicao,
            resultado.modo_execucao,
            resultado.quantidade_registros_erro,
        )

        return resultado

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "ClienteQstione":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
