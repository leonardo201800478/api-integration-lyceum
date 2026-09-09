# Sync Lyceum V2

## Objetivo

A Sync V2 é uma nova camada de sincronização dos endpoints Lyceum, criada em paralelo à implementação existente em `sync/`.

O objetivo é melhorar a obtenção automática dos dados necessários ao Qstione sem alterar a carga Qstione que já foi validada.

## Princípio de segurança

A V2 **não substitui nem modifica automaticamente** os sincronizadores existentes.

Nesta primeira fase, os módulos V2 utilizam um adaptador de compatibilidade que chama a implementação legada. Isso cria uma superfície uniforme para testes e permite migrar endpoint por endpoint sem interromper a produção atual.

## Estrutura

```text
sync/                         # implementação existente e validada

sync_v2/
├── __init__.py
├── run.py                    # orquestrador V2
├── core/
│   ├── __init__.py
│   ├── legacy_adapter.py     # compatibilidade temporária
│   └── registry.py           # catálogo dos endpoints
└── endpoints/
    ├── aceit_contrato.py
    ├── alunos.py
    ├── coordenacoes.py
    ├── curriculos.py
    ├── cursos.py
    ├── disciplinas.py
    ├── docentes.py
    ├── grades.py
    ├── matriculas.py
    ├── pessoa_by_id.py
    ├── pessoas.py
    ├── pessoas_pendentes.py
    ├── provas.py
    ├── provas_disciplinas.py
    ├── turma_docentes.py
    └── turmas.py
```

## Endpoints cobertos

A V2 possui uma superfície individual para os endpoints que já existem no projeto:

| V2 | Origem atual | Situação |
|---|---|---|
| `pessoas` | `sync_ly_pessoas.py` | adaptador |
| `pessoas_pendentes` | `sync_ly_pessoas_pendentes.py` | adaptador |
| `pessoa_by_id` | `sync_ly_pessoa_by_id.py` | adaptador |
| `alunos` | `sync_ly_alunos.py` | adaptador |
| `docentes` | `sync_ly_docentes.py` | adaptador |
| `coordenacoes` | `sync_ly_coordenacoes.py` | adaptador |
| `cursos` | `sync_ly_cursos.py` | adaptador |
| `curriculos` | `sync_ly_curriculos.py` | adaptador |
| `disciplinas` | `sync_ly_disciplinas.py` | adaptador |
| `grades` | `sync_ly_grades.py` | adaptador |
| `turmas` | `sync_ly_turmas.py` | adaptador |
| `turma_docentes` | `sync_ly_turma_docentes.py` | adaptador |
| `matriculas` | `sync_ly_matriculas.py` | adaptador |
| `provas` | `sync_ly_provas.py` | adaptador |
| `provas_disciplinas` | `sync_ly_provas_disciplinas.py` | adaptador |
| `aceit_contrato` | `sync_ly_aceit_contrato.py` | adaptador |

## Execução

Todas as etapas:

```powershell
python -m sync_v2.run
```

Somente etapas específicas:

```powershell
python -m sync_v2.run --only alunos turmas turma_docentes
```

Modo completo para alunos:

```powershell
python -m sync_v2.run --only alunos --alunos-modo completo
```

## Arquitetura alvo

A V2 será evoluída para separar claramente:

```text
API Lyceum
    ↓
coleta/paginação
    ↓
checkpoint
    ↓
validação
    ↓
upsert local
    ↓
estado de sincronização
    ↓
base Lyceum local
    ↓
importadores Qstione
```

O Qstione deverá consumir somente a base local, sem depender de chamadas diretas à API Lyceum durante a carga.

## Melhorias planejadas por endpoint

Cada endpoint será avaliado individualmente para:

1. identificar o volume real retornado;
2. identificar a chave natural/primária;
3. verificar se existe `stamp_atualizacao` ou equivalente;
4. determinar se a API permite filtro por ano/período/chave;
5. reduzir chamadas desnecessárias;
6. implementar paginação resiliente;
7. implementar checkpoint independente;
8. fazer INSERT/UPDATE somente quando necessário;
9. registrar métricas de API, banco e duração;
10. tratar falhas sem perder o ponto de retomada;
11. evitar `SELECT` por registro;
12. utilizar processamento em lote quando seguro.

## Ordem de migração recomendada

A ordem deve considerar as dependências do Qstione e o custo das chamadas:

```text
1. pessoas
2. alunos
3. docentes
4. cursos
5. curriculos
6. disciplinas
7. coordenacoes
8. turmas
9. turma_docentes
10. matriculas
11. grades
12. provas
13. provas_disciplinas
14. aceite_contrato
```

A ordem acima é uma proposta técnica inicial e poderá ser ajustada após medir os endpoints.

## Regras importantes

### Não alterar o Qstione

A migração da sincronização Lyceum não deve alterar os importadores Qstione já validados.

### Não apagar dados sem contrato explícito

Um endpoint V2 não deve utilizar `DELETE`, `TRUNCATE` ou `FULL REFRESH` como padrão. A estratégia deve ser definida por endpoint depois da análise da origem.

### Inativação é outra fase

A ausência de um registro na resposta da API não deve ser interpretada automaticamente como inativação. A futura rotina de inativação será especificada separadamente.

### Checkpoint não substitui consistência

O checkpoint só pode avançar depois que os dados da página foram persistidos com sucesso.

## Estado atual

A V2 foi criada como **infraestrutura paralela e compatível**. Ainda não é considerada a sincronização de produção.

A próxima etapa é migrar o primeiro endpoint real para a arquitetura V2, medir desempenho e validar os resultados contra a implementação atual.

## Relação com o Qstione

A arquitetura final pretendida é:

```text
                 LYCEUM
                    │
                    ▼
             SYNC LYCEUM V2
                    │
                    ▼
          BASE LOCAL LYCEUM
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
       QSTIONE               LXP
      Importação             Exportação
```

A vantagem é que a sincronização da origem passa a ser independente das aplicações consumidoras.
