import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

class Config:
    # API
    LYCEUM_BASE_URL = os.getenv("API_BASE_URL")
    LYCEUM_USERNAME = os.getenv("API_USERNAME")
    LYCEUM_PASSWORD = os.getenv("API_PASSWORD")

    # DATABASE
    DB_NAME = os.getenv("DB_NAME", "lyceum.db")
    DB_LYCEUM_PATH = os.getenv("DB_LYCEUM_PATH", DB_NAME)  # Adicionado

    # PAGINAÇÃO
    API_PAGE_START = int(os.getenv("API_PAGE_START", 0))
    API_PAGE_SIZE = int(os.getenv("API_PAGE_SIZE", 100))
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))
    API_DELAY_BETWEEN_REQUESTS = float(os.getenv("API_DELAY_BETWEEN_REQUESTS", 0.1))  # Adicionado

config = Config()