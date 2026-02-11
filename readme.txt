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

🧱 Estrutura Completa do Projeto
aluno-sync/
│
├── core/                      # Infraestrutura base
│   ├── api_client.py          # Cliente HTTP (GET-only)
│   └── config.py              # Configuração (.env)
│
├── models/                    # Modelos SQLite (Lyceum)
│   ├── base.py
│   ├── ly_aluno.py
│   ├── ly_curso.py
│   ├── ly_curriculo.py
│   ├── ly_disciplina.py
│   ├── ly_turma.py
│   ├── ly_docente.py
│   ├── ly_turma_docente.py
│   ├── ly_grade.py
│   └── ly_matricula.py
│
├── sync/                      # Sincronizadores Lyceum
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
├── qstione/                   # 🔴 MÓDULO DE QUESTIONÁRIOS
│   ├── core/                  # Infraestrutura própria
│   │   ├── api_client.py      # Cliente GET Qstione
│   │   └── config.py
│   │
│   ├── models/                # Modelos SQLite (Qstione)
│   │   ├── base.py
│   │   ├── questionario.py
│   │   ├── pergunta.py
│   │   ├── resposta.py
│   │   └── avaliacao.py
│   │
│   ├── sync/                  # Syncs Qstione
│   │   ├── sync_questionarios.py
│   │   ├── sync_perguntas.py
│   │   ├── sync_respostas.py
│   │   └── sync_avaliacoes.py
│   │
│   └── README.md              # Documentação específica Qstione
│
├── logs/
│   └── execucoes/             # Logs por execução
│
├── run_all.py                 # Runner unificado
├── requirements.txt
├── .env.example
└── README.md

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