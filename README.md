# aluno-sync

Integração e sincronização de dados acadêmicos do **Lyceum** com os ambientes **Qstione** e **LXP**.

O projeto mantém uma arquitetura por domínios, com regras de filtro e transformação centralizadas, tabelas intermediárias para as cargas Qstione e execução modular ou completa.

> **Status atual:** a carga ativa Lyceum → Qstione via HTTP POST está concluída e validada para o período `2026.2`. A etapa de inativação de usuários e alunos permanece planejada para uma fase posterior.

## Domínios

- `core/` — infraestrutura compartilhada: configuração, banco, cliente HTTP e logging.
- `sync/` — sincronização das entidades do Lyceum.
- `qstione/` — preparação, transformação e envio das cargas para o Qstione.
- `lxp/` — integração/exportação para o LXP.
- `reports/` — relatórios e exportações.
- `docs/` — documentação funcional e técnica.

## Estrutura principal

```text
aluno-sync/
├── core/
├── models/
├── sync/
├── qstione/
│   ├── config/
│   ├── core/
│   ├── desativadores/
│   ├── exportadores/
│   ├── importadores/
│   └── nde/
├── lxp/
├── reports/
├── docs/
├── logs/
├── backups/
├── exportacoes/
├── executar_qstione.py
├── run_all.py
├── run_reports.py
├── requirements.txt
└── .env.example
```

Arquivos de banco local, logs, exportações e credenciais são artefatos de ambiente e não devem ser tratados como código-fonte ou documentação normativa.

## Qstione — carga ativa

A carga completa segue as dependências funcionais dos importadores:

```text
IMP-001  Cursos
   ↓
IMP-002  Disciplinas
   ↓
IMP-005  Ofertas
   ↓
IMP-006  Usuários
   ↓
IMP-007  Usuários × Cursos
   ↓
IMP-008  Usuários × Disciplinas
   ↓
IMP-009  Professores × Ofertas
   ↓
IMP-010  Alunos
   ↓
IMP-011  Alunos × Ofertas
   ↓
IMP-013  Unidades de avaliação
```

O `IMP-016` de unidades organizacionais pode fazer parte da preparação conforme a configuração do processo. O `IMP-012` não participa da carga atual.

### Filtros vigentes

Configurados em `qstione/config/filtros.py`:

```python
ANO_VIGENTE = 2026
PERIODOS_VIGENTES = ['2']
SEMESTRE_OFERTA_FIXO = '2026.2'
FACULDADES_INCLUIDAS = ['001', '007']
SITUACAO_TURMA_VALIDA = 'aberta'
```

### Regras críticas

**Turma compartilhada:** quando `LY_TURMA.curso` é `NULL` ou vazio, a integração utiliza o curso técnico `999` (`Turma Compartilhada`). O `999` só deve ser criado/utilizado quando houver turma compartilhada válida no período.

**IMP-006:** a população de usuários é a união de docentes com turmas elegíveis, coordenadores dos cursos/faculdades incluídos e membros ativos do NDE. Coordenadores e NDE não dependem de uma turma vigente para existir no cadastro de usuários.

**IMP-007:** o papel é global por usuário, com hierarquia `C > A > P`. `G` é administrativo/global e `O` não é produzido por esse importador. Um membro NDE ativo recebe `A`; se também for coordenador, `C` prevalece. O papel efetivo é propagado aos cursos aos quais o usuário possui vínculo válido.

## Execução

### Ambiente

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Configure o `.env` a partir de `.env.example` e mantenha tokens, senhas e URLs privadas fora do controle de versão.

### Carga completa Qstione

```powershell
python executar_qstione.py
```

### Importadores individuais

Cada etapa pode ser executada isoladamente para diagnóstico. Exemplos:

```powershell
python qstione/importadores/imp_006_usuarios.py
python qstione/importadores/imp_007_usuarios_cursos.py
python qstione/importadores/imp_010_alunos.py
python qstione/importadores/imp_011_alunos_ofertas.py
```

### Sincronização Lyceum

```powershell
python run_all.py
```

Os sincronizadores `sync/sync_ly_*.py` devem expor `run() -> bool` para integração com o runner.

## Validação da carga 2026.2

A execução validada mais recente concluiu todas as etapas sem erros. Os principais números registrados foram:

| Etapa | Resultado |
|---|---:|
| IMP-007 | 535 registros, 0 erros |
| IMP-010 | 4.893 relações aluno/curso, 0 erros |
| IMP-011 | 19.290 registros, 0 erros |
| IMP-013 | 11 registros, 0 erros |
| Carga completa | concluída com sucesso |

No IMP-007, a consolidação registrada foi `G=3`, `C=38`, `A=151`, `P=343`, totalizando 535 registros. O NDE teve 93 registros ativos, 63 usuários consolidados e nenhuma ocorrência terminando indevidamente como `P`.

## Documentação

A documentação normativa está em [`docs/`](docs/README.md):

- `docs/QSTIONE_CARGA_COMPLETA.md` — arquitetura, contrato, filtros, etapas e regras da carga.
- `docs/IMP_007_USUARIOS_CURSOS.md` — regra detalhada de papéis e vínculos.
- `docs/README.md` — índice documental e política de manutenção.

## Próxima fase

A carga ativa está encerrada para o escopo atual. A próxima evolução funcional será tratada separadamente:

1. identificação de usuários que deixaram de ser elegíveis;
2. identificação de alunos que deixaram de ser ativos;
3. definição do mecanismo de inativação aceito pelo Qstione;
4. tratamento de vínculos que também precisem ser inativados;
5. testes controlados antes de qualquer alteração destrutiva.

Até essa fase ser implementada, os importadores ativos não devem ser considerados responsáveis por inativação automática.

## Segurança

- Não versionar `.env`, tokens, senhas ou credenciais.
- Não executar scripts de inativação contra produção sem validação prévia.
- Preservar logs de execução para auditoria.
- Tratar `999` como código técnico da integração, nunca como alteração do cadastro acadêmico de origem.

## Autor

Leonardo da Silva Paiva  
Analista de Sistemas / Desenvolvedor
