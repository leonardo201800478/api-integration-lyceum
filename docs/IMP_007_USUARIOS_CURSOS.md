# IMP-007 — Usuários × Cursos

## 1. Objetivo

O `IMP-007` gera os vínculos entre usuários e cursos exigidos pelo Qstione:

```text
codigoCurso
emailUsuario
papelUsuario
```

`codigoCurso` representa o vínculo necessário com cada curso. `papelUsuario` é global por usuário e não deve variar entre os cursos do mesmo usuário.

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

## 4. Regra específica do NDE — A prevalece sobre P

Membro ativo do NDE possui papel `A`.

Essa regra é **global** e não fica restrita ao curso registrado no NDE.

Exemplo do problema corrigido:

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

### 4.2 Normalização do NDE

A consulta de `imp_nde_membros` considera o status ativo de forma normalizada:

```sql
UPPER(LTRIM(RTRIM(CAST(status AS NVARCHAR(10))))) = 'S'
```

Também são normalizados `codigoCurso` e `emailMembro` antes da consolidação.

E-mails NDE inválidos ou cursos inválidos são registrados no log e não entram no resultado.

### 4.3 Validação de integridade

Após a consolidação, o importador verifica que:

- nenhum usuário identificado como NDE ativo terminou com `P`;
- nenhum usuário NDE ativo ficou sem registro final;
- usuários NDE + Professor são contabilizados como promoção `P -> A` no log.

Se uma dessas condições for violada, a execução gera erro de integridade em vez de produzir uma carga incorreta silenciosamente.

## 5. Fontes

### Professor — `P`

Origem: `LY_TURMA_DOCENTE`, considerando as turmas válidas do período vigente.

### Coordenador — `C`

Origem: `LY_COORDENACAO`.

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

## 8. Exemplos de aceite

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

## 9. Critérios de aceite

O IMP-007 está correto quando:

- cada usuário possui somente um papel efetivo;
- `C` prevalece sobre `A` e `P`;
- `A` prevalece sobre `P`;
- membro NDE ativo nunca termina como `P`;
- `A` é propagado para todos os cursos do usuário;
- cursos de professor não são descartados quando o usuário é NDE ou coordenador;
- `999` somente aparece mediante vínculo real com turma compartilhada;
- o resultado final não contém simultaneamente `C`, `A` e/ou `P` para o mesmo usuário;
- o payload contém os campos definidos pelo IMP-007.

## 10. Regra resumida

> **O papel do usuário é global. A hierarquia é `C > A > P`. Portanto, qualquer vínculo NDE ativo torna o usuário `A` em todos os seus cursos, salvo quando ele também possui `C`, situação em que `C` prevalece.**
