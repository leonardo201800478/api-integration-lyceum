# IMP-007 — Usuários × Cursos

## 1. Objetivo

O `IMP-007` gera os vínculos entre usuários e cursos exigidos pelo Qstione:

```text
codigoCurso
emailUsuario
papelUsuario
```

`codigoCurso` representa o vínculo necessário com cada curso. `papelUsuario` é global por usuário e não deve variar entre os cursos do mesmo usuário.

O `IMP-006` é responsável por garantir a existência cadastral do usuário antes do envio do `IMP-007`. Por isso, coordenadores e membros ativos do NDE devem ser incluídos no `IMP-006` mesmo quando não possuem turma vigente.

## 2. Hierarquia de papéis

A hierarquia definitiva é:

```text
C > A > P
```

- `C` = Coordenador de curso;
- `A` = Avaliador de Questões, proveniente de vínculo NDE;
- `P` = Professor;
- `G` = Gestor da Plataforma, administrativo/global e fora da hierarquia docente;
- `O` não é produzido por este importador.

## 3. Regra global

O processo deve:

1. reunir todos os cursos aos quais o usuário possui vínculo válido;
2. determinar o maior papel do usuário;
3. aplicar esse papel a todos os cursos reunidos.

Exemplo:

```text
056 → C
065 → P
079 → P
```

Resultado:

```text
056 → C
065 → C
079 → C
```

### 3.1 Coordenador sem turma

O vínculo de coordenação vem de `LY_COORDENACAO` e não depende de `LY_TURMA_DOCENTE`.

Assim, um coordenador de curso elegível deve:

1. existir no `IMP-006`;
2. receber vínculo com o curso no `IMP-007`;
3. receber papel `C`.

A ausência de turma/disciplina docente não é motivo para eliminar o coordenador.

## 4. Regra específica do NDE — A prevalece sobre P

Membro ativo do NDE possui papel `A`.

Essa regra é **global** e não fica restrita ao curso registrado no NDE.

Exemplo:

```text
NDE:
006 → A

Docência:
017 → P
044 → P
059 → P
```

Resultado obrigatório:

```text
006 → A
017 → A
044 → A
059 → A
```

Portanto, um membro do NDE **nunca pode terminar como `P`** no resultado do IMP-007 quando o vínculo NDE ativo foi identificado.

### 4.1 Ordem de processamento

O importador registra os vínculos NDE como candidatos `A` antes da consolidação final. Depois calcula o papel efetivo global:

```text
se possui C → C
senão se possui A → A
senão se possui P → P
```

Assim, `A` sempre substitui `P` para o usuário inteiro.

### 4.2 NDE no IMP-006

A população do `IMP-006` é a união de:

```text
docentes de turmas elegíveis
        UNION
coordenadores de cursos elegíveis
        UNION
membros ativos do NDE
```

O NDE é identificado por `imp_nde_membros`, com status ativo `S`, e seus dados cadastrais são resolvidos em `LY_DOCENTE` pelo `mailbox`.

A inclusão no `IMP-006` é cadastral: **não deve inventar um curso ou turma para o usuário**. Os vínculos de curso são responsabilidade do `IMP-007`.

### 4.3 Normalização do NDE

A consulta de `imp_nde_membros` considera o status ativo de forma normalizada:

```sql
UPPER(LTRIM(RTRIM(CAST(status AS NVARCHAR(10))))) = 'S'
```

Também são normalizados `codigoCurso` e `emailMembro` antes da consolidação.

E-mails NDE inválidos ou não localizados em `LY_DOCENTE` são registrados no log e não devem produzir cadastro incompleto.

### 4.4 Validação de integridade

Após a consolidação, o importador verifica que:

- nenhum usuário identificado como NDE ativo terminou com `P`;
- nenhum usuário NDE ativo ficou sem registro final;
- usuários NDE + Professor são contabilizados como promoção `P -> A` no log.

Se uma dessas condições for violada, a execução gera erro de integridade em vez de produzir uma carga incorreta silenciosamente.

## 5. Fontes

### Professor — `P`

Origem: `LY_TURMA_DOCENTE`, considerando as turmas válidas do período vigente.

### Coordenador — `C`

Origem: `LY_COORDENACAO`, considerando os cursos das faculdades configuradas.

### Avaliador — `A`

Origem: `imp_nde_membros`, somente membros com status ativo `S` após normalização.

### Gestor — `G`

Usuário administrativo fixo definido pela configuração existente.

## 6. União dos cursos

Para um usuário com vínculos em diferentes fontes:

```text
cursos = cursos_P ∪ cursos_A ∪ cursos_C
```

O papel máximo é então aplicado à união.

Isso evita que os cursos de docência sejam perdidos quando o usuário também é NDE ou coordenador.

## 7. Curso 999

`999` é um código técnico para representar turma compartilhada quando `LY_TURMA.curso` é `NULL` ou vazio.

O `IMP-007` somente inclui `999` quando existe vínculo real com turma compartilhada. Não é permitido adicionar `999` artificialmente a todos os usuários.

O `999` não deve ser interpretado como curso acadêmico real.

## 8. Relação IMP-006 → IMP-007

A sequência correta é:

```text
IMP-006
  cadastro do usuário
       ↓
IMP-007
  vínculo usuário × curso × papel
```

Essa separação é obrigatória para o caso de coordenadores sem turma e NDE sem turma.

O erro anteriormente observado no Qstione — usuário não cadastrado na plataforma — ocorria quando o `IMP-006` não contemplava uma origem de usuário necessária ao `IMP-007`. A população foi corrigida para contemplar coordenação e NDE independentemente de turma.

## 9. Exemplos de aceite

### NDE + Professor

```text
Origem:
006 → A
017 → P
044 → P

Resultado:
006 → A
017 → A
044 → A
```

### NDE + Coordenador + Professor

```text
Origem:
006 → A
056 → C
065 → P

Resultado:
006 → C
056 → C
065 → C
```

### Coordenador sem turma

```text
LY_COORDENACAO:
curso 056 → usuário X

LY_TURMA_DOCENTE:
nenhum vínculo vigente para X

Resultado:
IMP-006 → usuário X existe
IMP-007 → 056 / X / C
```

### Somente Professor

```text
056 → P
065 → P
```

permanece:

```text
056 → P
065 → P
```

## 10. Critérios de aceite

O IMP-007 está correto quando:

- cada usuário possui somente um papel efetivo;
- `C` prevalece sobre `A` e `P`;
- `A` prevalece sobre `P`;
- membro NDE ativo nunca termina como `P`;
- `A` é propagado para todos os cursos do usuário;
- coordenador de curso elegível é processado mesmo sem turma docente;
- cursos de professor não são descartados quando o usuário é NDE ou coordenador;
- `999` somente aparece mediante vínculo real com turma compartilhada;
- o resultado final não contém simultaneamente `C`, `A` e/ou `P` para o mesmo usuário;
- o usuário já existe no cadastro do `IMP-006` antes do envio do `IMP-007`;
- o payload contém os campos definidos pelo IMP-007;
- a API retorna processamento sem erros para os registros válidos.

## 11. Validação realizada — 2026.2

Na execução validada do período `2026.2`:

```text
Coordenadores encontrados:              23
Vínculos docente/turma:                487
NDE ativos:                             93
Usuários NDE consolidados:              63
NDE promovidos P → A:                   60
NDE terminando como P:                   0

G = 3
C = 38
A = 151
P = 343
TOTAL = 535
INSERIDOS = 535
ERROS = 0
```

A execução foi concluída sem os erros anteriores de usuários de coordenação não cadastrados.

## 12. Regra resumida

> **O papel do usuário é global. A hierarquia é `C > A > P`. Portanto, qualquer vínculo NDE ativo torna o usuário `A` em todos os seus cursos, salvo quando ele também possui `C`, situação em que `C` prevalece. Coordenadores e membros NDE devem existir no IMP-006 independentemente de possuírem turma vigente.**
