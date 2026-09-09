# Integração Lyceum → Qstione

## 1. Objetivo

Este documento descreve o objetivo, a organização, as regras de negócio e o fluxo de processamento do módulo `qstione` do projeto `aluno-sync`.

A finalidade da integração é transformar dados acadêmicos obtidos do ambiente Lyceum em registros compatíveis com os importadores do Qstione, persistindo primeiro os dados em uma base intermediária local e, posteriormente, enviando-os à API do Qstione.

A arquitetura separa claramente três responsabilidades:

1. **Lyceum** — fonte acadêmica de origem.
2. **Base Qstione local** — camada intermediária de consolidação, transformação e auditoria.
3. **API Qstione** — destino da carga externa.

O princípio fundamental é: **não inventar dados acadêmicos reais para preencher lacunas da origem**. Quando o Qstione exige uma chave obrigatória que não existe no Lyceum para uma situação específica, utiliza-se uma representação técnica explicitamente documentada.

---

## 2. Princípios de arquitetura

### 2.1 Fonte de verdade

Os dados acadêmicos devem ser derivados da estrutura do Lyceum sincronizada para o ambiente local. A integração não deve utilizar o Qstione como fonte de verdade para reconstruir dados acadêmicos.

### 2.2 Camada intermediária

Os registros de cada IMP são gravados em tabelas `imp_XXX_*` no banco destinado ao Qstione. Essa camada permite:

- inspecionar os dados antes do envio;
- repetir uma etapa sem consultar novamente toda a origem;
- auditar transformações;
- detectar erros de validação;
- manter cada importador independente.

### 2.3 Importadores independentes

Cada `imp_XXX_*.py` deve poder ser executado diretamente pelo VS Code/terminal, sem depender da execução prévia de outro script Python.

A dependência entre etapas é **de dados e ordem de carga**, não de chamada entre módulos.

### 2.4 Ordem da carga

A ordem respeita as dependências funcionais do Qstione:

```text
IMP-016  Unidades organizacionais
    ↓
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

O `IMP-012` não participa da carga atual, pois foi descontinuado na especificação utilizada pelo projeto.

---

## 3. Contrato da API Qstione

A comunicação com o Qstione utiliza HTTP POST.

A requisição deve possuir os cabeçalhos definidos pelo protocolo, incluindo:

- `versaoProtocolo`;
- `tokenIdInstituicao`;
- `codigoTransacao`;
- `formatoOperacao`;
- `quantidadeRegistros`.

O corpo da requisição é diretamente um **array JSON** dos registros da etapa. Não deve existir um objeto externo envolvendo a lista.

O protocolo utiliza `application/json` com charset ISO-8859-1. O cliente da integração normaliza caracteres Unicode incompatíveis antes da codificação, evitando falhas de transmissão causadas por pontuação tipográfica ou outros caracteres fora do conjunto ISO-8859-1.

Os códigos de status do processamento devem ser tratados conforme o protocolo:

| Código | Significado |
|---|---|
| `0` | Processamento bem-sucedido |
| `1` | Falha antes do processamento |
| `2` | Falha de validação |
| `3` | Falha de execução |

Em processamento assíncrono, a conclusão pode exigir o tratamento do retorno final conforme o protocolo.

---

## 4. Configuração central

Os filtros letivos ficam centralizados em:

```text
qstione/config/filtros.py
```

Atualmente a configuração registrada no projeto contempla:

```python
ANO_VIGENTE = 2026
PERIODOS_VIGENTES = ['2']
SEMESTRE_OFERTA_FIXO = '2026.2'
FACULDADES_INCLUIDAS = ['001', '007']
SITUACAO_TURMA_VALIDA = 'aberta'
```

Ao mudar o período letivo, a configuração central deve ser revisada antes da execução da carga.

---

# 5. Regra especial: turmas compartilhadas

## 5.1 Problema de origem

Uma turma compartilhada pode atender alunos de mais de um curso. Nessa situação, a origem Lyceum pode não informar `LY_TURMA.curso`, mantendo o campo `NULL` ou vazio.

O Qstione, entretanto, exige `codigoCurso` em entidades que dependem do contexto de curso.

Não é correto escolher arbitrariamente um dos cursos atendidos pela turma, pois isso perderia a característica compartilhada da turma e poderia vincular disciplinas, alunos ou professores ao curso errado.

## 5.2 Representação técnica

Foi estabelecido o seguinte contrato de integração:

```text
codigoCurso = 999
nomeCurso   = Turma Compartilhada
```

O código `999` é **sintético e exclusivo da camada de integração**. Ele não representa um curso acadêmico real cadastrado no Lyceum.

## 5.3 Quando o 999 deve existir

O `999` não deve ser criado incondicionalmente.

Ele é criado no `IMP-001` somente quando existir pelo menos uma turma válida do período vigente com:

```sql
LY_TURMA.curso IS NULL
```

ou curso vazio após normalização.

A turma deve obedecer aos mesmos filtros de período, situação e faculdade utilizados pelo processo de disciplinas.

Assim:

```text
Existe turma compartilhada vigente?
        │
   ┌────┴────┐
   │         │
  SIM       NÃO
   │         │
   ▼         ▼
criar 999  não criar 999
```

Isso evita poluir o Qstione com um curso sintético quando ele não possui uso no período.

## 5.4 Quantidade de períodos

O contrato do `IMP-001` exige `quantPeriodos`.

Como o curso `999` não é um curso acadêmico real e, portanto, não possui duração curricular no Lyceum, o valor técnico utilizado é:

```text
quantPeriodos = 1
```

Esse valor existe exclusivamente para satisfazer o contrato do importador e **não deve ser interpretado como a duração acadêmica de uma graduação ou curso técnico**.

---

# 6. IMP-001 — Cursos

Arquivo:

```text
qstione/importadores/imp_001_cursos.py
```

## Objetivo

Produzir o catálogo de cursos que será utilizado pelas demais etapas do Qstione.

## Origem

Cursos reais:

```text
LY_CURSO
   +
LY_CURRICULO
```

A consulta considera cursos ativos e os filtros institucionais definidos pelo projeto.

## Transformações

O importador:

1. consulta os cursos ativos;
2. obtém o currículo mais recente;
3. utiliza `prazo_ideal` para `quantPeriodos`;
4. aplica o de-para de cursos;
5. consolida códigos equivalentes;
6. valida código, nome e quantidade de períodos;
7. grava o resultado em `imp_001_cursos`;
8. acrescenta o curso sintético `999` quando houver turma compartilhada vigente.

## Exemplo

```text
Lyceum:
curso = 141

Integração:
141 → 056

Qstione:
056 / DESIGN
```

Para uma turma sem curso:

```text
Lyceum:
LY_TURMA.curso = NULL

Integração:
NULL → 999

Qstione:
999 / Turma Compartilhada
```

---

# 7. IMP-002 — Disciplinas

Arquivo:

```text
qstione/importadores/imp_002_disciplina.py
```

## Fonte de verdade

A existência da turma válida em `LY_TURMA` determina quais disciplinas devem ser consideradas para a carga.

São utilizados os filtros:

- ano vigente;
- período vigente;
- situação de turma válida;
- faculdades incluídas.

## Regra de curso

O curso original da turma deve ser preservado durante as consultas à grade.

Exemplo:

```text
LY_TURMA.curso = 141
       ↓
consulta LY_GRADE com curso = 141
       ↓
unificação 141 → 056
```

A unificação antes da consulta da grade poderia eliminar a correspondência correta com a origem.

## Turma compartilhada

Para:

```text
NULL
''
999
```

o contexto é normalizado para:

```text
999 / Turma Compartilhada
```

Não se deve tentar consultar `LY_GRADE` com o curso `999`, pois esse código é sintético e não pertence à origem acadêmica.

---

# 8. Contexto de curso das disciplinas

Uma mesma disciplina pode existir em contextos de curso distintos.

A lógica de geração do código de disciplina considera o curso unificado, de forma que o contexto seja preservado.

Conceitualmente:

```text
DISC001 + 056
DISC001 + 999
```

representam contextos distintos.

Isso é especialmente importante para disciplinas presentes simultaneamente em cursos reais e em turmas compartilhadas.

---

# 9. IMP-005 — Ofertas

Responsável por transformar as ofertas/turmas em registros compatíveis com o Qstione.

Campos principais:

```text
codigoOferta
nomeOferta
codigoDisciplina
semestreOferta
codigoTipoOferta
codigoOfertaOrigem
turno
codigoIdentificacaoAVA
```

A etapa depende do catálogo de cursos e disciplinas já consolidado.

---

# 10. IMP-006 — Usuários

Responsável pela carga de usuários.

Campos principais:

```text
matriculaUsuario
codigoUsuario
emailUsuario
nomeUsuario
```

A regra de origem e filtros de docentes/alunos deve permanecer alinhada às etapas posteriores de relacionamento.

---

# 11. IMP-007 — Usuários × Cursos

Relaciona usuários aos cursos.

Campos:

```text
codigoCurso
emailUsuario
papelUsuario
```

Quando o usuário estiver associado a uma turma compartilhada, o relacionamento deve utilizar o código técnico `999`, nunca um curso escolhido arbitrariamente.

---

# 12. IMP-008 — Usuários × Disciplinas

Relaciona usuários às disciplinas:

```text
codigoDisciplina
emailUsuario
```

A disciplina já deve carregar o contexto correto de curso produzido no `IMP-002`.

---

# 13. IMP-009 — Professores × Ofertas

Relaciona professor e oferta:

```text
codigoOferta
emailProfessor
```

O relacionamento deve preservar a oferta produzida para a turma correta, inclusive quando a origem representa uma turma compartilhada.

---

# 14. IMP-010 — Alunos

Campos principais:

```text
matriculaAluno
nomeAluno
emailAluno
codigoCurso
turno
codigoIdentificacaoAVA
```

A regra de domínio de e-mail e demais transformações específicas devem permanecer nos importadores correspondentes e não ser duplicadas no orquestrador.

---

# 15. IMP-011 — Alunos × Ofertas

Relaciona aluno e oferta:

```text
codigoOferta
matriculaAluno
codigoCurso
```

A regra de curso compartilhado é especialmente relevante aqui: quando a origem indicar uma turma sem curso, o relacionamento deve utilizar `999` para satisfazer o contrato do Qstione sem atribuir falsamente o aluno a um curso real.

---

# 16. IMP-013 — Unidades de avaliação

Campos:

```text
codigoUnidade
nomeUnidade
codigoCurso
codigoDisciplina
ordemExibicao
codigoAgrupamento
```

A etapa utiliza o contexto de curso/disciplinas já consolidado.

---

# 17. O que não deve ser feito

### Não criar 999 sempre

O registro só deve existir quando houver uso no período vigente.

### Não alterar LY_CURSO para criar 999

O código `999` pertence à camada de integração. Não se deve inserir um curso artificial no cadastro acadêmico de origem.

### Não escolher um curso real para turma compartilhada

Isso distorce a relação acadêmica e pode gerar inconsistências nas etapas de alunos, professores, disciplinas e ofertas.

### Não consultar LY_GRADE usando 999

`999` não é um curso de origem.

### Não substituir o código original antes das consultas de origem

Códigos alternativos devem ser pesquisados na origem antes da unificação.

---

# 18. Execução

A carga completa é executada pelo processo:

```bash
python executar_qstione.py
```

Ou pelo processo específico da carga completa, quando disponível no ambiente.

Um importador individual pode ser executado diretamente, por exemplo:

```bash
python qstione/importadores/imp_001_cursos.py
python qstione/importadores/imp_002_disciplina.py
```

A execução individual é útil para diagnóstico e validação de uma etapa sem repetir toda a carga.

---

# 19. Diagnóstico do curso 999

Antes da carga completa, o `IMP-001` deve apresentar uma indicação semelhante a:

```text
🔗 Curso sintético 999 criado: Turma Compartilhada
```

Quando não houver turma compartilhada válida:

```text
ℹ️ Nenhuma turma compartilhada vigente encontrada; curso 999 não será criado.
```

Após a execução, a tabela intermediária pode ser conferida com:

```sql
SELECT
    codigoCurso,
    nomeCurso,
    quantPeriodos,
    codigoUnidadeOrganizacional
FROM imp_001_cursos
WHERE codigoCurso = '999';
```

Resultado esperado quando houver turma compartilhada:

```text
999 | Turma Compartilhada | 1 | 4000000001
```

---

# 20. Critérios de aceite

Uma carga é considerada corretamente organizada quando:

- cursos reais vêm da origem Lyceum;
- códigos equivalentes são consolidados pelo de-para definido;
- `999` aparece somente quando há turma compartilhada vigente;
- `999` possui o nome `Turma Compartilhada`;
- disciplinas de turmas compartilhadas utilizam `codigoCurso=999`;
- não existe tentativa de localizar `999` em `LY_GRADE`;
- relacionamentos posteriores preservam `999` quando o contexto é compartilhado;
- a carga respeita a ordem das dependências;
- erros da API interrompem a carga quando impedem a consistência da etapa;
- os dados intermediários podem ser auditados antes do envio;
- cada importador continua executável de forma independente.

---

# 21. Manutenção futura

Ao alterar a integração, seguir esta ordem:

1. verificar a especificação vigente do Qstione;
2. verificar a estrutura real das tabelas Lyceum utilizadas;
3. confirmar a regra de negócio;
4. alterar o filtro central quando a mudança for comum às etapas;
5. alterar o importador específico quando a regra for exclusiva;
6. atualizar a documentação;
7. executar o importador isoladamente;
8. conferir a tabela intermediária;
9. executar a etapa contra o Sandbox;
10. somente então executar a carga completa.

Toda nova regra sintética ou de-para deve ser documentada com sua origem, motivo, impacto e condição de aplicação.
