# core/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

class Config:
    # API Lyceum - compatível com LYCEUM_* e API_* (fallback)
    LYCEUM_BASE_URL = (
        os.getenv("LYCEUM_BASE_URL") or os.getenv("API_BASE_URL")
    )
    LYCEUM_USERNAME = (
        os.getenv("LYCEUM_USERNAME") or os.getenv("API_USERNAME")
    )
    LYCEUM_PASSWORD = (
        os.getenv("LYCEUM_PASSWORD") or os.getenv("API_PASSWORD")
    )

    # DATABASE
    DB_NAME = os.getenv("DB_NAME", "lyceum")
    DB_LYCEUM_PATH = os.getenv("DB_LYCEUM_PATH", DB_NAME)

    # SQL Server (conexão)
    SQL_SERVER_HOST = os.getenv('SQL_SERVER_HOST', 'localhost')
    SQL_SERVER_PORT = os.getenv('SQL_SERVER_PORT', '1434')
    SQL_SERVER_USER = os.getenv('SQL_SERVER_USER', 'sa')
    SQL_SERVER_PASSWORD = os.getenv('SQL_SERVER_PASSWORD')
    SQL_SERVER_DRIVER = os.getenv('SQL_SERVER_DRIVER', '{ODBC Driver 18 for SQL Server}')
    SQL_SERVER_DATABASE_LYCEUM = os.getenv('SQL_SERVER_DATABASE_LYCEUM', 'lyceum')
    SQL_SERVER_DATABASE_QSTIONE = os.getenv('SQL_SERVER_DATABASE_QSTIONE', 'qstione')
    SQL_SERVER_DATABASE_LXP = os.getenv('SQL_SERVER_DATABASE_LXP', 'lxp')

    # Paginação da API
    API_PAGE_START = int(os.getenv("API_PAGE_START", 0))
    API_PAGE_SIZE = int(os.getenv("API_PAGE_SIZE", 100))
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))
    API_DELAY_BETWEEN_REQUESTS = float(os.getenv("API_DELAY_BETWEEN_REQUESTS", 0.1))

config = Config()