import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Externa
    API_BASE_URL = "https://unifoa.lyceum.com.br:443/api"
    API_USERNAME = "unifoa_integracao_crm_educa"
    API_PASSWORD = "L]~=0Hy-%XMy_EU"
    
    # Configurações gerais
    PAGE_SIZE = 100
    MAX_PAGES = 50
    DELAY_BETWEEN_REQUESTS = 0.1
    
    # Banco de dados
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")
    DB_NAME = os.getenv("DB_NAME", "dados_unifoa.db")
    
    @property
    def DATABASE_URL(self):
        if self.DB_TYPE == "sqlite":
            return f"sqlite:///{self.DB_NAME}"
        else:
            DB_HOST = os.getenv("DB_HOST", "localhost")
            DB_PORT = os.getenv("DB_PORT", "5432")
            DB_USER = os.getenv("DB_USER", "postgres")
            DB_PASSWORD = os.getenv("DB_PASSWORD", "")
            return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{self.DB_NAME}"

config = Config()