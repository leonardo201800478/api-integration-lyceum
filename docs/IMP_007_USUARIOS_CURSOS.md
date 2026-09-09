# IMP-007 — Usuários × Cursos

## 1. Objetivo

O `IMP-007` gera os vínculos entre usuários e cursos exigidos pelo Qstione.

O contrato da etapa possui somente estes campos de negócio:

```text
codigoCurso
emailUsuario
papelUsuario
```

O ponto central da implementação é que **`codigoCurso` e `papelUsuario` têm comportamentos diferentes**:

- `codigoCurso` é um vínculo necessário para cada curso em que o usuário está inserido;
- `papelUsuario` é um **papel único por usuário**, e não um papel independente por curso.

Essa diferença é uma limitação/comportamento do Qstione que a integração precisa respeitar.

---

## 2. Regra definitiva de negócio

Para cada usuário, o processo deve:

1. reunir todos os cursos aos quais ele possui vínculo válido;
2. identificar o maior papel que ele possui;
3. aplicar esse papel máximo a **todos os cursos reunidos no passo 1**.

A hierarquia docente é:

```text
C > A > P
```

Onde:

- `C` = Coordenador de curso;
- `A` = Avaliador de Questões;
- `P` = Professor.

O papel `G` (Gestor da Plataforma) é administrativo, fixo/global e não participa da hierarquia docente `C > A > P`.

O papel `O` (Operador de Documentos) não é produzido pela lógica docente deste importador.

---

## 3. Por que a hierarquia é global por usuário

O Qstione exige o vínculo do usuário com cada curso em que ele está inserido, mas não permite representar corretamente um papel diferente para o mesmo usuário em cursos diferentes.

Portanto, esta lógica é **incorreta**:

```text
Usuário X
056 → C
065 → P
079 → P
```

Se o usuário for coordenador no curso 056, o resultado correto é:

```text
Usuário X
056 → C
065 → C
079 → C
```

O mesmo vale para avaliadores.

Se o usuário for avaliador em qualquer vínculo NDE e também professor em outros cursos:

```text
Usuário Y
006 → A
017 → P
044 → P
059 → P
```

o resultado correto é:

```text
Usuário Y
006 → A
017 → A
044 → A
059 → A
```

Portanto, **o papel máximo encontrado em qualquer vínculo do usuário é propagado para todos os cursos aos quais ele possui vínculo**.

---

## 4. Fontes utilizadas

### 4.1 Professor — `P`

A origem é `LY_TURMA_DOCENTE`, considerando as turmas válidas do período vigente.

O curso é obtido de `LY_TURMA.curso`.

Quando a turma é compartilhada e `LY_TURMA.curso` é `NULL` ou vazio, a integração utiliza `999`.

### 4.2 Coordenador — `C`

A origem é `LY_COORDENACAO`.

O vínculo de coordenador com um curso determina que o usuário possui o papel `C`.

Esse papel não fica restrito ao curso em que a coordenação foi identificada: depois da consolidação global, `C` é propagado para todos os cursos aos quais o usuário possui vínculo válido.

Isso é necessário porque o Qstione trata o papel do usuário como único, embora exija `codigoCurso` em cada relacionamento.

### 4.3 Avaliador — `A`

A origem é `imp_nde_membros`.

O vínculo no NDE determina que o usuário possui o papel `A`.

Depois da consolidação global, `A` é propagado para todos os cursos aos quais o usuário possui vínculo válido, inclusive cursos provenientes de vínculos docentes.

O papel `A` não deve ser reduzido para `P` em nenhum curso quando `A` for o maior papel do usuário.

### 4.4 Gestor — `G`

O usuário administrativo fixo definido pela integração recebe `G` conforme a configuração existente.

Por ser um papel administrativo/global, ele não é submetido à hierarquia docente `C > A > P`.

---

## 5. Algoritmo de consolidação

A implementação deve pensar no usuário antes de pensar no registro final.

### Etapa 1 — reunir candidatos

Para cada e-mail:

```text
P → conjunto de cursos de docência
C → conjunto de cursos de coordenação
A → conjunto de cursos do NDE
```

### Etapa 2 — formar a união dos cursos

```text
cursos_do_usuario = cursos_P ∪ cursos_C ∪ cursos_A
```

Essa união é fundamental.

Não se deve utilizar somente os cursos associados ao papel máximo.

### Etapa 3 — determinar o papel máximo

```text
se possui C → C
senão se possui A → A
senão se possui P → P
```

### Etapa 4 — propagar

Para cada curso em `cursos_do_usuario`:

```text
codigoCurso = curso
emailUsuario = usuário
papelUsuario = papel_máximo
```

Exemplo:

```text
P: 065, 079
A: 056

União:
056, 065, 079

Papel máximo:
A

Saída:
056 / usuário / A
065 / usuário / A
079 / usuário / A
```

---

## 6. Regra do curso 999

O `999` é um código sintético da integração para representar **turma compartilhada**.

Ele não representa um curso acadêmico real do Lyceum.

A origem é:

```text
LY_TURMA.curso = NULL
ou
LY_TURMA.curso = ''
```

Nessa situação:

```text
curso da origem → 999
```

O `IMP-007` deve incluir `999` somente quando o usuário possuir efetivamente vínculo com uma turma/curso que tenha sido normalizado para `999`.

**Não é permitido acrescentar `999` artificialmente a todos os coordenadores, avaliadores ou professores.**

Exemplo correto:

```text
Professor X
056 → P
999 → P   ← somente se houver turma compartilhada real
```

Exemplo incorreto:

```text
Professor X
056 → P
999 → P   ← sem qualquer vínculo com turma compartilhada
```

---

## 7. Consequências da regra

### Coordenador em um curso e professor em outro

```text
Origem:
056 → C
065 → P
079 → P

IMP-007:
056 → C
065 → C
079 → C
```

### Avaliador em um curso e professor em outros

```text
Origem:
006 → A
017 → P
044 → P
059 → P

IMP-007:
006 → A
017 → A
044 → A
059 → A
```

### Coordenador + avaliador + professor

```text
Origem:
056 → C
065 → A
079 → P

IMP-007:
056 → C
065 → C
079 → C
```

### Somente professor

```text
Origem:
056 → P
065 → P

IMP-007:
056 → P
065 → P
```

### Nenhum papel conflitante

O usuário permanece com `P` nos cursos em que possui vínculo docente.

---

## 8. O que NÃO deve ser feito

Não aplicar papel independentemente por curso:

```text
056 → C
065 → P
```

Não descartar cursos de professor quando o usuário é avaliador:

```text
A → somente cursos do NDE  ❌
```

O correto é:

```text
A → todos os cursos do usuário  ✓
```

Não criar `999` por padrão para cada usuário.

Não alterar o significado de `codigoCurso`: ele continua representando o curso do vínculo, inclusive `999` quando o vínculo veio de turma compartilhada.

---

## 9. Estrutura da tabela

A tabela intermediária `imp_007_usuarios_cursos` deve permitir a combinação:

```text
(codigoCurso, emailUsuario, papelUsuario)
```

A chave primária utilizada pelo importador é composta por esses três campos.

Isso garante que a estrutura da tabela seja compatível com a multiplicidade de cursos por usuário e com a representação explícita do papel no registro enviado ao Qstione.

---

## 10. Critérios de aceite

O `IMP-007` só deve ser considerado correto quando todos os critérios abaixo forem satisfeitos:

- cada usuário possui somente um papel efetivo;
- `C` sempre prevalece sobre `A` e `P`;
- `A` sempre prevalece sobre `P`;
- um coordenador em qualquer curso é `C` em todos os seus cursos vinculados;
- um avaliador em qualquer vínculo NDE é `A` em todos os seus cursos vinculados, salvo se possuir `C`;
- cursos de professor não são descartados quando o papel máximo é `A` ou `C`;
- `999` somente aparece quando houver vínculo real com turma compartilhada ou regra administrativa explícita;
- não existe usuário com `C`, `A` e/ou `P` simultaneamente no resultado final;
- o payload contém somente os campos definidos para o IMP-007.

---

## 11. Resumo da regra

A regra pode ser resumida em uma frase:

> **O Qstione exige um vínculo por usuário e curso, mas o papel é único por usuário; portanto, determina-se o maior papel do usuário pela hierarquia `C > A > P` e esse papel é propagado para todos os cursos aos quais o usuário possui vínculo válido.**
