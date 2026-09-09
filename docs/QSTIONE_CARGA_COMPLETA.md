# Integração Lyceum → Qstione

## 1. Status

**Carga ativa via HTTP POST: FINALIZADA e validada para 2026.2.**

A carga completa foi executada com sucesso, sem erros nas etapas registradas. A inativação de usuários e alunos não faz parte deste escopo e será tratada em fase posterior.

## 2. Arquitetura

```text
Lyceum
  │
  │ dados acadêmicos
  ▼
Base intermediária Qstione
  │
  │ transformação/validação
  ▼
API Qstione — HTTP POST
```

O Lyceum é a fonte de verdade acadêmica. As tabelas `imp_XXX_*` funcionam como camada intermediária de consolidação, transformação e auditoria.

Cada importador pode ser executado individualmente. A dependência entre etapas é de dados e ordem de carga, não de chamada entre scripts.

## 3. Configuração vigente

Arquivo: `qstione/config/filtros.py`

```python
ANO_VIGENTE = 2026
PERIODOS_VIGENTES = ['2']
SEMESTRE_OFERTA_FIXO = '2026.2'
FACULDADES_INCLUIDAS = ['001', '007']
SITUACAO_TURMA_VALIDA = 'aberta'
```

Ao mudar o período, revisar a configuração central antes de executar a carga.

## 4. Contrato da API

As cargas externas utilizam HTTP POST para o endpoint configurado do Qstione.

O corpo é um array JSON diretamente, sem objeto externo envolvendo a lista. Os cabeçalhos e campos de protocolo são montados pelo cliente da integração conforme a configuração/protocolo utilizado pelo projeto.

O processamento é considerado bem-sucedido quando a API retorna `HTTP 200` com `status=0` e `erros=0` para a carga enviada.

Os importadores trabalham em lotes para controlar tamanho de requisição e permitir identificação precisa de falhas.

## 5. Ordem funcional da carga

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

O `IMP-012` não participa da carga atual. O `IMP-016` é tratado conforme a configuração do processo e não deve ser confundido com as etapas ativas acima.

## 6. Regra de turma compartilhada

Quando `LY_TURMA.curso` é `NULL` ou vazio, a turma é considerada compartilhada.

A representação técnica é:

```text
codigoCurso = 999
nomeCurso   = Turma Compartilhada
```

O `999` é sintético e pertence à camada de integração. Não é um curso acadêmico real do Lyceum.

O código `999` somente deve existir/utilizado quando houver turma compartilhada válida no período. Não se deve escolher arbitrariamente um curso real para representar uma turma compartilhada.

Também não se deve consultar tabelas acadêmicas de origem usando `999` como se fosse um curso real.

## 7. IMP-001 — Cursos

Origem principal: `LY_CURSO` e estruturas curriculares relacionadas.

Responsabilidades:

- selecionar cursos elegíveis;
- aplicar o mapeamento de cursos;
- validar dados necessários ao Qstione;
- criar o curso técnico `999` quando houver turma compartilhada vigente.

## 8. IMP-002 — Disciplinas

Responsável pela carga de disciplinas no contexto correto de curso.

O código original da origem deve ser utilizado nas consultas ao Lyceum antes da aplicação do de-para. O código unificado é aplicado na etapa de transformação.

Para turma compartilhada, o contexto final utiliza `999`, sem tentar tratar esse código como curso acadêmico na origem.

## 9. IMP-005 — Ofertas

Transforma turmas/ofertas válidas em registros de oferta do Qstione, preservando o vínculo com disciplina, curso e período.

## 10. IMP-006 — Usuários

O `IMP-006` garante a existência dos usuários necessários às etapas seguintes.

A população final é a união de:

```text
docentes com turma elegível
        UNION
coordenadores dos cursos elegíveis
        UNION
membros ativos do NDE
```

### 10.1 Docentes

São derivados de `LY_TURMA_DOCENTE` associado a `LY_TURMA`, considerando ano, período, situação de turma e faculdades configuradas.

### 10.2 Coordenadores

São derivados de `LY_COORDENACAO` associado a `LY_CURSO` e `LY_DOCENTE`.

**Não é necessário que o coordenador tenha turma docente vigente.**

### 10.3 NDE

São derivados de `imp_nde_membros`, considerando somente membros ativos (`status = S` após normalização). O e-mail do NDE é utilizado para localizar o cadastro em `LY_DOCENTE.mailbox`.

**Não é necessário que o membro NDE tenha turma vigente.**

### 10.4 Deduplicação

O `NUM_FUNC` identifica o usuário. Um usuário presente em mais de uma origem deve produzir um único cadastro no `IMP-006`.

### 10.5 Responsabilidade

O `IMP-006` cadastra o usuário. Não deve inventar curso, turma ou papel para satisfazer etapas posteriores.

## 11. IMP-007 — Usuários × Cursos

Campos principais:

```text
codigoCurso
emailUsuario
papelUsuario
```

O papel é global por usuário.

Hierarquia:

```text
C > A > P
```

- `C` — Coordenador;
- `A` — Avaliador de Questões, derivado de NDE;
- `P` — Professor;
- `G` — Gestor administrativo/global;
- `O` — não produzido pelo importador.

Para o usuário, o maior papel identificado é aplicado aos cursos aos quais ele possui vínculo válido.

Exemplo:

```text
056 → C
065 → P
079 → P
```

resultado:

```text
056 → C
065 → C
079 → C
```

### 11.1 NDE

Membro NDE ativo recebe `A` globalmente.

Se também possuir `P`, ocorre promoção:

```text
P → A
```

Se também possuir `C`:

```text
C > A > P
```

e o resultado é `C` para todos os cursos consolidados.

Um NDE ativo não pode terminar como `P`.

### 11.2 Coordenador sem turma

Um coordenador pode existir somente em `LY_COORDENACAO`, sem `LY_TURMA_DOCENTE` vigente. Nesse caso:

```text
IMP-006 → cadastra usuário
IMP-007 → cria vínculo com curso + papel C
```

Esse comportamento é obrigatório.

### 11.3 Curso 999

O `999` só aparece no relacionamento de usuário quando o usuário possui vínculo real originado de turma compartilhada. Não deve ser adicionado universalmente.

## 12. IMP-008 — Usuários × Disciplinas

Relaciona usuários às disciplinas já consolidadas pelo `IMP-002`.

## 13. IMP-009 — Professores × Ofertas

Relaciona professores às ofertas correspondentes às turmas processadas.

## 14. IMP-010 — Alunos

Considera alunos elegíveis conforme as regras do importador, incluindo a regra de situação ativa e as transformações específicas de e-mail e curso.

A relação aluno/curso deve preservar o contexto `999` quando a origem for turma compartilhada.

## 15. IMP-011 — Alunos × Ofertas

Relaciona alunos às ofertas das turmas elegíveis. Para turmas compartilhadas, utiliza o curso técnico `999` quando exigido pelo contrato.

## 16. IMP-013 — Unidades de avaliação

Carga das unidades de avaliação vinculadas ao contexto de curso/disciplina já consolidado.

## 17. Resultado de validação 2026.2

A execução final validada apresentou:

```text
IMP-007
  coordenadores encontrados = 23
  vínculos docente/turma    = 487
  NDE ativos                = 93
  NDE consolidados          = 63
  NDE promovidos P → A      = 60
  NDE terminando como P     = 0
  G                         = 3
  C                         = 38
  A                         = 151
  P                         = 343
  TOTAL                     = 535
  INSERIDOS                 = 535
  ERROS                     = 0

IMP-010
  relações aluno/curso = 4.893
  inseridos             = 4.893
  erros                 = 0

IMP-011
  registros = 19.290
  erros     = 0

IMP-013
  registros = 11
  erros     = 0
```

A carga completa foi concluída com sucesso.

## 18. Critérios de aceite da carga ativa

A carga ativa é considerada finalizada quando:

- os filtros vigentes são aplicados de forma centralizada;
- cursos e disciplinas respeitam os mapeamentos definidos;
- `999` somente é usado para turma compartilhada real;
- usuários necessários ao `IMP-007` existem no `IMP-006`;
- coordenadores não dependem de turma vigente;
- NDE ativo não depende de turma vigente;
- `C > A > P` é respeitado;
- NDE ativo não termina como `P`;
- o papel efetivo é global por usuário;
- a API aceita os lotes sem erros;
- a execução completa termina sem erro.

## 19. Logs e auditoria

Os importadores registram informações de execução em `logs/`. Os logs são úteis para conferir filtros, quantidades, promoções NDE, erros de API e resultados das etapas.

Credenciais, tokens e dados de ambiente não devem ser registrados em documentação ou versionados.

## 20. Execução

Carga completa:

```powershell
python executar_qstione.py
```

Diagnóstico individual:

```powershell
python qstione/importadores/imp_006_usuarios.py
python qstione/importadores/imp_007_usuarios_cursos.py
```

Os importadores individuais devem continuar executáveis independentemente para diagnóstico.

## 21. Próxima fase — Inativação

A carga ativa está encerrada. A inativação será tratada separadamente.

Escopo planejado:

1. identificar usuários que deixaram de ser elegíveis;
2. identificar alunos que deixaram de ser ativos;
3. identificar vínculos que precisam ser inativados;
4. confirmar no contrato Qstione o mecanismo correto de inativação;
5. implementar e testar sem exclusão física indevida;
6. adicionar auditoria e somente depois integrar ao fluxo automático.

**Até essa fase ser implementada, a carga ativa não deve ser interpretada como rotina de inativação.**
