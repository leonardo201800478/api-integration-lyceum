markdown
# 📘 aluno-sync

Projeto de sincronização e consolidação de dados acadêmicos do **Lyceum**, com persistência local em SQLite, execução controlada e uso exclusivo do método HTTP GET.  
O projeto integra dados de diferentes fontes (Lyceum, Qstione e LXP) para fornecer uma base local confiável para análises e relatórios.

## 🎯 Objetivos
- Sincronizar dados do Lyceum de forma segura e auditável.
- Manter um espelho local confiável para análises e relatórios.
- Padronizar a execução de múltiplos endpoints.
- Integrar dados acadêmicos + dados de questionários (Qstione) + dados LXP.

## 🔐 Garantias de Segurança
✔️ Apenas GET na API Lyceum  
✔️ Nenhuma escrita remota  
✔️ Banco exclusivamente local (SQLite)  
✔️ Execução isolada por módulo  
✔️ Logs completos por execução  

## 📁 Estrutura do Projeto (Atualizada)

Abaixo está a organização completa dos diretórios e arquivos, conforme a versão mais recente do projeto.
aluno-sync/
│
├── core/ # Infraestrutura base do projeto
│ ├── init.py
│ ├── api_client.py # Cliente HTTP (somente GET – Lyceum)
│ ├── config.py # Carregamento de variáveis (.env)
│ ├── database.py # Conexão e utilidades SQLite
│ └── logger.py # Configuração central de logs
│
├── models/ # Modelos SQLite – domínio Lyceum
│ ├── init.py
│ ├── ly_aluno.py
│ ├── ly_coordenacao.py
│ ├── ly_curriculo.py
│ ├── ly_curso.py
│ ├── ly_disciplina.py
│ ├── ly_docente.py
│ ├── ly_grade.py
│ ├── ly_matricula.py
│ ├── ly_pessoa.py
│ ├── ly_prova.py
│ ├── ly_prova_discip.py
│ ├── ly_turma.py
│ └── ly_turma_docente.py
│
├── sync/ # Sincronizadores individuais Lyceum
│ ├── init.py
│ ├── sync_ly_alunos.py
│ ├── sync_ly_coordenacoes.py
│ ├── sync_ly_curriculos.py
│ ├── sync_ly_cursos.py
│ ├── sync_ly_disciplinas.py
│ ├── sync_ly_docentes.py
│ ├── sync_ly_grades.py
│ ├── sync_ly_matriculas.py
│ ├── sync_ly_pessoa_by_id.py # Sincroniza pessoa específica + alunos
│ ├── sync_ly_pessoas.py # Sincroniza todas as pessoas
│ ├── sync_ly_provas.py
│ ├── sync_ly_provas_disciplinas.py
│ ├── sync_ly_turma_docentes.py
│ └── sync_ly_turmas.py
│
├── lxp/ # Módulo de integração com dados LXP
│ ├── config/
│ │ ├── init.py
│ │ ├── filtros.py
│ │ └── mapeamentos.py
│ ├── core/
│ │ ├── init.py
│ │ ├── crud_course.py
│ │ └── exportador.py
│ ├── exportadores/
│ │ ├── init.py
│ │ ├── exp_001_cursos.py
│ │ ├── exp_002_curriculum.py
│ │ ├── exp_003_enrollment.py
│ │ ├── exp_004_desenturmar_alunos__.py
│ │ ├── exp_004_turmas.py
│ │ ├── exp_005_matriculas.py
│ │ └── exp_006_pessoas.py
│ ├── init.py
│ ├── main.py # Entry-point do módulo LXP
│ └── README.md
│
├── qstione/ # Módulo de questionários (Qstione)
│ ├── config/
│ │ ├── criar_tabelas_qstone.sql
│ │ ├── filtros.py
│ │ └── tabelas.py
│ ├── core/
│ │ ├── transformacoes.py
│ │ ├── utils_db.py
│ │ └── validacoes.py
│ ├── desativadores/
│ │ ├── des_001_cursos.py
│ │ └── desativador_base.py
│ ├── exportadores/
│ │ ├── ExportadorSQL/
│ │ ├── excel.py
│ │ └── sql.py
│ ├── importadores/
│ │ ├── imp_001_cursos.py
│ │ ├── imp_002_disciplina.py
│ │ ├── imp_003_objetivos.py
│ │ ├── imp_004_referencias.py
│ │ ├── imp_005_ofertas.py
│ │ ├── imp_006_usuarios.py
│ │ ├── imp_007_usuarios_cursos.py
│ │ └── imp_008_usuarios_disciplinas.py
│ └── main.py # Entry-point do módulo Qstione
│
├── reports/ # Geradores de relatórios e exporters
│ ├── exporters/
│ │ ├── init.py
│ │ ├── base.py
│ │ ├── excel_exporter.py
│ │ ├── pdf_exporter.py
│ │ └── xml_exporter.py
│ ├── generators/
│ │ ├── init.py
│ │ ├── gerar_relatorio_alunos.py
│ │ └── gerar_relatorio_contatos_completo.py
│ ├── queries/
│ │ ├── init.py
│ │ ├── relatorio_alunos.py
│ │ └── relatorio_contatos_filtros.py
│ └── sync_pessoas.py # Verifica e sincroniza pessoas faltantes
│
├── backups/ # Backups automáticos dos bancos
├── exportacoes/ # Arquivos exportados (CSV / XLSX)
├── logs/ # Logs estruturados por execução
│ └── execucoes/
│
├── .env # Variáveis de ambiente (local)
├── .env.example # Modelo de configuração
├── .gitignore
├── ARQUITETURA.md
├── README.md # Documentação principal
├── requirements.txt # Dependências
├── run_all.py # Runner unificado Lyceum
├── executar_qstione.py # Entry-point simplificado para o Qstione
├── run_reports.py # Executa todos os relatórios
├── run_relatorio_contatos.py # Gera relatório de contatos
├── test_conexao.py
├── teste.py
├── lyceum.db # Banco SQLite Lyceum (criado em execução)
├── qstione.db # Banco SQLite Qstione (criado em execução)
└── esquema de montagem da view VW_aluno.txt

text

## 🚀 Começando

### Pré-requisitos
- Python 3.8 ou superior
- Acesso à API Lyceum (credenciais)
- Acesso à API Qstione (token)
- Banco SQLite (criado automaticamente)

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
Configure as variáveis de ambiente:

bash
cp .env.example .env
# Edite o .env com suas credenciais
⚙️ Configuração (.env)
ini
# Lyceum
LYCEUM_BASE_URL=https://api.lyceum.exemplo
LYCEUM_USERNAME=usuario
LYCEUM_PASSWORD=senha

# Qstione
QSTIONE_BASE_URL=https://api.qstione.exemplo
QSTIONE_TOKEN=seu_token

# Paginação da API
API_PAGE_START=0
API_PAGE_SIZE=500
API_TIMEOUT=30
API_DELAY_BETWEEN_REQUESTS=0.1
▶️ Execução dos Principais Scripts
Todos os comandos devem ser executados na raiz do projeto com o ambiente virtual ativado.

🔄 Sincronização de Pessoas (Lyceum)
bash
# Sincronizar todas as pessoas (endpoint /v2/tabela/pessoas)
python sync/sync_ly_pessoas.py

# Sincronizar uma pessoa específica pelo ID (inclui alunos vinculados)
python sync/sync_ly_pessoa_by_id.py 12345

# Verificar pessoas em LY_ALUNO que não estão em LY_PESSOA e sincronizá-las
python reports/sync_pessoas.py
📋 Sincronização de Outras Entidades Lyceum
bash
python sync/sync_ly_alunos.py
python sync/sync_ly_coordenacoes.py
python sync/sync_ly_curriculos.py
python sync/sync_ly_cursos.py
python sync/sync_ly_disciplinas.py
python sync/sync_ly_docentes.py
python sync/sync_ly_grades.py
python sync/sync_ly_matriculas.py
python sync/sync_ly_provas.py
python sync/sync_ly_provas_disciplinas.py
python sync/sync_ly_turma_docentes.py
python sync/sync_ly_turmas.py
🚀 Runner Unificado (Lyceum)
bash
# Executa todos os sincronizadores Lyceum que implementam a função run()
python run_all.py
🧩 Módulo LXP
bash
# Executa o fluxo principal do LXP
python lxp/main.py
📊 Módulo Qstione (Questionários)
bash
# Executa o fluxo completo do Qstione (via entry-point simplificado)
python executar_qstione.py

# Ou, de forma modular:
python qstione/main.py
📑 Relatórios e Exportações
bash
# Gera relatório de alunos (XML e PDF)
python reports/generators/gerar_relatorio_alunos.py

# Gera relatório completo de contatos (HTML, Excel, PDF)
python run_relatorio_contatos.py

# Executa todos os relatórios disponíveis
python run_reports.py
📐 Contrato Obrigatório dos Syncs Lyceum
Todos os arquivos sync_ly_*.py devem expor a função:

python
def run() -> bool:
    """Executa a sincronização e retorna True em caso de sucesso."""
Isso garante que o runner run_all.py possa executá‑los de forma padronizada.

📊 Logs e Auditoria
Cada execução gera logs estruturados na pasta logs/execucoes/YYYYMMDD_HHMMSS/, com um arquivo JSON por sincronizador e um relatório final.

🧪 Boas Práticas Aplicadas
Separação clara de domínios (Lyceum × Qstione × LXP)

Execução determinística e isolada

Zero side‑effects em produção

Logs estruturados e código auditável

Fácil extensão para novos endpoints

🚀 Roadmap (Próximos Passos)
Runner unificado para Qstione

Detecção de mudanças (hash) para sincronização incremental

UPSERT em lote para melhor performance

Exportação para BI (CSV/Parquet)

Dashboard de monitoramento das execuções

👤 Autor
Leonardo da Silva Paiva
Analista de Sistemas / Desenvolvedor