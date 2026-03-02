📘 aluno-sync

Projeto de sincronização e consolidação de dados acadêmicos do Lyceum, com persistência local em SQLite, execução controlada, isolamento por endpoint e uso exclusivo do método HTTP GET.

Além dos syncs acadêmicos, o projeto inclui o módulo qstione, responsável pela extração, normalização e persistência de dados do sistema de questionários (avaliações).

🎯 Objetivos

Sincronizar dados do Lyceum de forma segura e auditável

Manter um espelho local confiável para análises e relatórios

Padronizar execução de múltiplos endpoints

Integrar dados acadêmicos + dados de questionários (Qstione)

🔐 Garantias de Segurança

✔ Apenas GET na API Lyceum
✔ Nenhuma escrita remota
✔ Banco exclusivamente local (SQLite)
✔ Execução isolada por módulo
✔ Logs completos por execução

markdown
# Aluno Sync

Sistema de sincronização de dados acadêmicos entre a API Lyceum e o banco de dados Qstione.

## 📌 Sobre o Projeto

Este projeto automatiza a extração, transformação e carga (ETL) de dados de alunos, ofertas, coordenadores e usuários a partir da API do Lyceum para as tabelas do sistema Qstione. Utiliza Python para consumir endpoints REST e inserir os dados no banco de dados PostgreSQL.

## 🚀 Começando

### Pré-requisitos

- Python 3.8 ou superior
- Acesso à API Lyceum (credenciais)
- Banco de dados PostgreSQL configurado

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/leonardo201800478/aluno-sync.git
   cd aluno-sync
Crie e ative um ambiente virtual:

bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
Instale as dependências:

bash
pip install -r requirements.txt
Configure as variáveis de ambiente (copie o arquivo de exemplo):

bash
cp .env.example .env
# Edite o .env com suas credenciais

aluno-sync/
│
├── core/                               # Infraestrutura base do projeto
│   ├── __init__.py
│   ├── api_client.py                  # Cliente HTTP (somente GET – Lyceum)
│   ├── config.py                      # Carregamento de variáveis (.env)
│   ├── database.py                    # Conexão e utilidades SQLite
│   └── logger.py                      # Configuração central de logs
│
├── backups/                           # Backups automáticos dos bancos
│
├── exportacoes/                       # Arquivos exportados (CSV / XLSX)
│
├── models/                            # Modelos SQLite – domínio Lyceum
│   ├── __init__.py
│   ├── ly_aluno.py
│   ├── ly_coordenacao.py
│   ├── ly_curso.py
│   ├── ly_curriculo.py
│   ├── ly_disciplina.py
│   ├── ly_turma.py
│   ├── ly_docente.py
│   ├── ly_turma_docente.py
│   ├── ly_grade.py
│   └── ly_matricula.py
│
├── sync/                              # Sincronizadores Lyceum
│   ├── __init__.py
│   ├── sync_ly_cursos.py
│   ├── sync_ly_curriculos.py
│   ├── sync_ly_disciplinas.py
│   ├── sync_ly_alunos.py
│   ├── sync_ly_turmas.py
│   ├── sync_ly_docentes.py
│   ├── sync_ly_turma_docentes.py
│   ├── sync_ly_coordenacoes.py
│   ├── sync_ly_grades.py
│   └── sync_ly_matriculas.py
│
├── qstione/                           # 🔴 Módulo de Questionários
│   │
│   ├── config/                        # Configurações e mapeamentos
│   │   └── tabelas.py                 # Definição de tabelas e schemas
│   │
│   ├── core/                          # Núcleo de regras do Qstione
│   │   ├── __init__.py
│   │   ├── transformacoes.py          # Normalização e transformação de dados
│   │   └── validacoes.py              # Validações de integridade
│   │
│   ├── exportadores/                  # Exportação de dados
│   │   ├── excel.py                   # Exportação XLSX
│   │   └── sql.py                     # Exportação SQL
│   │
│   ├── importadores/                  # Importação de dados externos
│   │   ├── imp_001_cursos.py
│   │   ├── imp_002_disciplinas.py
│   │   ├── imp_005_ofertas.py
│   │   ├── imp_006_usuarios.py
│   │   └── imp_007_usuarios_cursos.py
│   │
│   └── main.py                        # Entry-point do módulo Qstione
│
├── logs/
│   └── execucoes/                     # Logs estruturados por execução
│
├── venv/                              # Ambiente virtual (não versionado)
│
├── .gitignore
├── .env                               # Variáveis de ambiente (local)
├── .env.example                       # Modelo de configuração
├── requirements.txt                  # Dependências do projeto
├── run_all.py                         # Runner unificado Lyceum
├── lyceum.db                          # Banco SQLite Lyceum
├── qstione.db                         # Banco SQLite Qstione
└── README.md                          # Documentação principal

🔁 Módulo qstione — Visão Geral

O diretório qstione/ é um subprojeto interno, com:

Cliente próprio de API

Banco SQLite próprio ou compartilhado

Modelos independentes

Syncs independentes

Execução isolada do Lyceum

Função principal

Sincronizar questionários, perguntas, respostas e avaliações para análise pedagógica, indicadores institucionais e BI.

🔄 Fluxo do Qstione
API Qstione (GET)
        ↓
Validação de dados
        ↓
Normalização
        ↓
Persistência SQLite


✔ Sem dependência direta dos syncs Lyceum
✔ Pode ser executado isoladamente
✔ Pode ser integrado ao runner futuramente

▶️ Execução dos Syncs Lyceum
Individual
python sync/sync_ly_grades.py
python sync/sync_ly_docentes.py

Unificada
python run_all.py

▶️ Execução dos Syncs Qstione
python qstione/sync/sync_questionarios.py
python qstione/sync/sync_respostas.py

# Sincronizar todas as pessoas
python sync/sync_ly_pessoas.py

Módulo principal:
python qstione/main.py


⚠️ O Qstione não é executado pelo run_all.py por padrão
(decisão proposital para isolamento de domínio)

📐 Contrato Obrigatório dos Syncs Lyceum

Todos os arquivos sync_ly_*.py devem expor:

def run() -> bool:
    """
    Entry-point padrão para execução via runner
    """


True → sucesso

False → falha

main() não é chamado pelo runner

📊 Logs e Auditoria

Cada execução gera:

logs/execucoes/AAAAmmdd_HHMMSS/
├── sync_ly_alunos.json
├── sync_ly_grades.json
├── sync_ly_docentes.json
└── relatorio_final.json

⚙️ Configuração (.env)
LYCEUM_BASE_URL=https:
LYCEUM_USERNAME=usuario
LYCEUM_PASSWORD=senha

QSTIONE_BASE_URL=https:
QSTIONE_TOKEN=token

API_PAGE_START=0
API_PAGE_SIZE=500

📦 Dependências
requests>=2.31.0
pandas>=2.0.0
python-dotenv>=1.0.0
openpyxl>=3.1.5

🧪 Boas Práticas Aplicadas

Separação clara de domínios (Lyceum × Qstione)

Execução determinística

Zero side-effects em produção

Logs estruturados

Código auditável

Fácil extensão

🚀 Próximos Passos (Roadmap)

 Runner unificado opcional para Qstione

 Detecção de mudanças (hash)

 UPSERT incremental

 Exportação BI (CSV / Parquet)

 Dashboard de execução

👤 Autor

Leonardo da Silva Paiva
Analista de Sistemas / Desenvolvedor