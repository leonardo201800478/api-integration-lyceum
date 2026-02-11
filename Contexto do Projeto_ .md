# Contexto do Projeto: `aluno-sync`

## 1. Título do Projeto

`aluno-sync`

## 2. Visão Geral do Projeto

O `aluno-sync` é um sistema de sincronização e consolidação de dados acadêmicos. Seu objetivo principal é extrair informações do sistema Lyceum (via API) e de um sistema de questionários (Qstione), persistindo-as localmente em bancos de dados SQLite. O projeto foi concebido com foco em segurança, auditabilidade e isolamento, garantindo que apenas operações de leitura (GET) sejam realizadas nas APIs externas e que todos os dados sejam armazenados e processados localmente. Ele serve como um espelho local confiável para análises, relatórios e integração de dados acadêmicos com dados de questionários.

## 3. Tecnologias Utilizadas

*   **Linguagem**: Python 3.x
*   **Bibliotecas Principais**: `requests`, `pandas`, `python-dotenv`, `openpyxl`, `sqlite3` (embutido)
*   **Banco de Dados**: SQLite (para persistência local)
*   **Gerenciamento de Dependências**: `requirements.txt`
*   **Configuração**: Variáveis de ambiente (`.env`)

## 4. Estrutura do Repositório

O repositório é organizado de forma modular, com os seguintes diretórios e arquivos chave:

```
aluno-sync/
├── core/                               # Infraestrutura base do projeto
│   ├── api_client.py                  # Cliente HTTP (somente GET – Lyceum)
│   ├── config.py                      # Carregamento de variáveis (.env)
│   ├── database.py                    # Conexão e utilidades SQLite
│   └── logger.py                      # Configuração central de logs
├── models/                            # Modelos SQLite – domínio Lyceum
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
├── sync/                              # Sincronizadores Lyceum
│   ├── sync_ly_alunos.py
│   ├── sync_ly_coordenacoes.py
│   ├── sync_ly_cursos.py
│   ├── sync_ly_curriculos.py
│   ├── sync_ly_disciplinas.py
│   ├── sync_ly_docentes.py
│   ├── sync_ly_grades.py
│   ├── sync_ly_matriculas.py
│   └── sync_ly_turmas.py
├── qstione/                           # Módulo de Questionários (subprojeto interno)
│   ├── config/                        # Configurações e mapeamentos (e.g., tabelas.py)
│   ├── core/                          # Núcleo de regras do Qstione (transformacoes.py, validacoes.py)
│   ├── exportadores/                  # Exportação de dados (excel.py, sql.py)
│   ├── importadores/                  # Importação de dados externos (e.g., imp_001_cursos.py)
│   └── main.py                        # Entry-point do módulo Qstione
├── backups/                           # Backups automáticos dos bancos
├── exportacoes/                       # Arquivos exportados (CSV / XLSX)
├── logs/                              # Logs estruturados por execução
├── .env.example                       # Modelo de configuração
├── requirements.txt                  # Dependências do projeto
├── run_all_syncs.py                   # Runner unificado Lyceum
├── lyceum.db                          # Banco SQLite Lyceum
└── qstione.db                         # Banco SQLite Qstione
```

## 5. Componentes Principais e Funcionalidades

### 5.1 Sincronização Lyceum

*   **`core/api_client.py`**: Implementa `BaseAPIClient` para interagir com a API Lyceum. Suporta autenticação Basic Auth e paginação automática. A `APIClientFactory` garante sessões isoladas para diferentes tipos de clientes (e.g., `CursoAPIClient`, `AlunoAPIClient`).
*   **`core/database.py`**: Fornece um `contextmanager` (`get_db_connection`) para gerenciar conexões SQLite, garantindo `commit` e `close` automáticos. Funções auxiliares para `execute_query`, `fetch_all` e `fetch_one`.
*   **`models/ly_*.py`**: Cada arquivo representa um modelo de dados (e.g., `AlunoModel` em `ly_aluno.py`) que define a estrutura da tabela SQLite correspondente. Inclui métodos estáticos para `create_table`, `_normalize_value` (para conversão de tipos e limpeza de dados), `upsert` (INSERT OR UPDATE) e `delete_obsoletos`.
*   **`sync/sync_ly_*.py`**: Scripts responsáveis pela lógica de sincronização de cada entidade. Eles utilizam o `api_client` para buscar dados, os `models` para persistir no `lyceum.db`, e suportam modos de execução `completo` (sincroniza tudo e remove dados não mais presentes na API) e `incremental` (atualiza/insere com base em `stamp_atualizacao`).
*   **`run_all_syncs.py`**: Script unificado para executar todos os sincronizadores do Lyceum em sequência.

### 5.2 Módulo Qstione

*   **`qstione/main.py`**: Ponto de entrada principal para o módulo Qstione. Orquestra as operações de importação e exportação.
*   **`qstione/importadores/imp_*.py`**: Classes como `ImportadorUsuarios` (`imp_006_usuarios.py`) são responsáveis por obter dados (do banco Lyceum ou outras fontes), transformá-los e importá-los para o `qstione.db`.
*   **`qstione/core/transformacoes.py` e `qstione/core/validacoes.py`**: Contêm funções utilitárias para normalizar (e.g., `converter_minusculas`, `truncar_texto`) e validar (e.g., `validar_email`, `validar_matricula`) os dados antes da persistência.
*   **`qstione/exportadores/excel.py` e `qstione/exportadores/sql.py`**: Classes para exportar os dados processados do `qstione.db` para formatos como planilhas Excel e arquivos SQL de backup.
*   **`qstione.db`**: Banco de dados SQLite separado para os dados do sistema de questionários.

## 6. Regras de Negócio e Restrições Importantes

*   **APIs Externas (Lyceum)**: Apenas requisições HTTP `GET` são permitidas. Nenhuma operação de escrita remota é autorizada.
*   **Persistência de Dados**: Todos os dados são persistidos localmente em bancos de dados SQLite (`lyceum.db` e `qstione.db`).
*   **Isolamento**: O módulo `qstione` é um subprojeto interno e pode ser executado isoladamente. Ele não é executado por `run_all_syncs.py` por padrão, uma decisão proposital para isolamento de domínio.
*   **Contrato dos Syncs Lyceum**: Todos os scripts em `sync/` devem expor uma função `run() -> bool` que retorna `True` para sucesso e `False` para falha.
*   **Logs**: Cada execução gera logs detalhados em `logs/execucoes/` para auditoria e depuração.
*   **Configuração**: Credenciais de API e outras configurações sensíveis são carregadas de um arquivo `.env` e acessadas via `core.config.config`.

## 7. Instruções para a IA

Ao interagir com este projeto, a IA deve:

1.  **Priorizar a Segurança**: Manter a restrição de apenas `GET` para APIs externas e a persistência local dos dados.
2.  **Respeitar a Modularidade**: Entender a separação de responsabilidades entre `core`, `models`, `sync` e `qstione`. Modificações devem ser feitas dentro do contexto apropriado de cada módulo.
3.  **Utilizar as Ferramentas Existentes**: Reutilizar o `api_client`, `database` e os modelos existentes sempre que possível para manter a consistência.
4.  **Considerar Modos de Sincronização**: Ao implementar novas sincronizações ou modificar as existentes, levar em conta os modos `completo` e `incremental`.
5.  **Manter a Auditabilidade**: Garantir que quaisquer novas funcionalidades ou modificações gerem logs adequados para rastreamento e depuração.
6.  **Validar e Normalizar Dados**: Ao lidar com novas fontes de dados ou campos, aplicar validações e transformações consistentes, seguindo os padrões já estabelecidos no módulo `qstione/core`.
7.  **Testar Alterações**: Embora não haja uma estrutura de testes explícita, a IA deve considerar a criação de testes (unitários e de integração) para quaisquer reparos ou novas integrações para garantir a estabilidade do sistema.
8.  **Documentar**: Atualizar docstrings e a documentação do projeto (`readme.txt` ou outros arquivos relevantes) para refletir quaisquer alterações ou novas funcionalidades.

## 8. Pontos de Atenção e Melhoria (para referência da IA)

*   **Testes**: A ausência de testes unitários e de integração é uma lacuna. A IA deve considerar a implementação de testes para garantir a robustez do código, especialmente em funções críticas de sincronização e transformação.
*   **Tratamento de Erros**: Melhorar a granularidade do tratamento de exceções, diferenciando tipos de erros e implementando lógicas de recuperação mais específicas.
*   **Documentação Inline**: Adicionar docstrings mais detalhadas para funções e classes, explicando a lógica e o propósito.
*   **Otimização de Performance**: Para grandes volumes de dados, explorar otimizações como processamento assíncrono ou em lotes para chamadas de API e operações de banco de dados.
*   **Gerenciamento de Esquema de BD**: Para futuras evoluções, considerar uma ferramenta de migração de banco de dados para gerenciar alterações de esquema de forma mais controlada.
*   **Validação de Dados na Camada `sync`**: Implementar validações de dados mais rigorosas nos scripts de sincronização do Lyceum antes da persistência, similar ao que é feito no módulo Qstione.

Este prompt deve fornecer à IA um entendimento abrangente do projeto `aluno-sync`, permitindo que ela atue de forma eficaz em tarefas de reparo, manutenção e desenvolvimento de novas funcionalidades ou integrações.
