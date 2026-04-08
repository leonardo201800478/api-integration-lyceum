# core/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def _parse_ssl_verify(value: str) -> bool | str:
    """
    Interpreta o valor de LYCEUM_SSL_VERIFY:
      - "false" → False  (desabilita verificação SSL)
      - "true"  → True   (verifica com bundle padrão do sistema)
      - qualquer outro   → string com caminho para o arquivo .crt
    """
    if value.lower() == "false":
        return False
    if value.lower() == "true":
        return True
    return value  # caminho para bundle .crt personalizado


class Config:
    # API Lyceum - compatível com LYCEUM_* e API_* (fallback)
    LYCEUM_BASE_URL: str | None = (
        os.getenv("LYCEUM_BASE_URL") or os.getenv("API_BASE_URL")
    )
    LYCEUM_USERNAME: str | None = (
        os.getenv("LYCEUM_USERNAME") or os.getenv("API_USERNAME")
    )
    LYCEUM_PASSWORD: str | None = (
        os.getenv("LYCEUM_PASSWORD") or os.getenv("API_PASSWORD")
    )

    # Verificação SSL
    # false  → desabilita (útil em dev / rede interna)
    # true   → verifica normalmente
    # <path> → usa bundle .crt personalizado (ex: lyceum_ca_bundle.crt)
    LYCEUM_SSL_VERIFY: bool | str = _parse_ssl_verify(
        os.getenv("LYCEUM_SSL_VERIFY", "true")
    )

    # DATABASE
    DB_NAME: str = os.getenv("DB_NAME", "lyceum")
    DB_LYCEUM_PATH: str = os.getenv("DB_LYCEUM_PATH", DB_NAME)

    # SQL Server (conexão)
    SQL_SERVER_HOST: str = os.getenv("SQL_SERVER_HOST", "localhost")
    SQL_SERVER_PORT: str = os.getenv("SQL_SERVER_PORT", "1434")
    SQL_SERVER_USER: str = os.getenv("SQL_SERVER_USER", "sa")
    SQL_SERVER_PASSWORD: str | None = os.getenv("SQL_SERVER_PASSWORD")
    SQL_SERVER_DRIVER: str = os.getenv(
        "SQL_SERVER_DRIVER", "{ODBC Driver 18 for SQL Server}"
    )
    SQL_SERVER_DATABASE_LYCEUM: str = os.getenv("SQL_SERVER_DATABASE_LYCEUM", "lyceum")
    SQL_SERVER_DATABASE_QSTIONE: str = os.getenv("SQL_SERVER_DATABASE_QSTIONE", "qstione")
    SQL_SERVER_DATABASE_LXP: str = os.getenv("SQL_SERVER_DATABASE_LXP", "lxp")

    # Paginação da API
    API_PAGE_START: int = int(os.getenv("API_PAGE_START", 0))
    API_PAGE_SIZE: int = int(os.getenv("API_PAGE_SIZE", 100))
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", 30))
    API_DELAY_BETWEEN_REQUESTS: float = float(os.getenv("API_DELAY_BETWEEN_REQUESTS", 0.1))


config = Config()