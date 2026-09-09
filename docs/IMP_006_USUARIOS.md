# IMP-006 — Usuários

## Objetivo

Cadastrar na camada intermediária e enviar ao Qstione os usuários necessários para as demais relações da integração.

## População final

O `IMP-006` deve considerar a união de três origens:

```text
docentes com turma elegível
        UNION
coordenadores dos cursos elegíveis
        UNION
membros ativos do NDE
```

A existência de turma vigente é obrigatória somente para a população docente. **Coordenadores e membros ativos do NDE não dependem de turma/disciplina vigente para serem cadastrados.**

## Coordenadores

Origem: `LY_COORDENACAO`, relacionada a `LY_CURSO` e `LY_DOCENTE`.

São considerados os cursos pertencentes às faculdades configuradas em `qstione/config/filtros.py`.

Um coordenador deve ser incluído mesmo quando não possui qualquer registro em `LY_TURMA_DOCENTE` no período vigente.

O `IMP-006` não cria vínculo artificial de curso; ele apenas garante o cadastro do usuário. O vínculo e o papel `C` são tratados no `IMP-007`.

## NDE

Origem dos membros: `imp_nde_membros`.

Somente registros ativos são considerados, com status normalizado para `S`:

```sql
UPPER(LTRIM(RTRIM(CAST(status AS NVARCHAR(10))))) = 'S'
```

O e-mail `emailMembro` é normalizado e utilizado para localizar o cadastro correspondente em `LY_DOCENTE.mailbox`.

O NDE também não depende de turma vigente. O usuário é cadastrado no `IMP-006`; o papel `A` e os vínculos de curso são determinados no `IMP-007`.

## Deduplicação

O identificador do usuário é o `NUM_FUNC`. Um mesmo usuário pode aparecer nas três fontes, mas deve resultar em um único cadastro no `IMP-006`.

A transformação consolida os dados cadastrais sem gerar registros duplicados por curso.

## Campos

```text
matriculaUsuario
codigoUsuario
emailUsuario
nomeUsuario
```

O `codigoUsuario` é derivado do e-mail conforme as funções compartilhadas do projeto.

## Relação com o IMP-007

A responsabilidade é separada:

```text
IMP-006 = existência/cadastro do usuário
IMP-007 = vínculo usuário × curso × papel
```

Essa separação resolve especificamente o caso de coordenadores sem turma e NDE sem turma.

## Filtros vigentes

```python
ANO_VIGENTE = 2026
PERIODOS_VIGENTES = ['2']
FACULDADES_INCLUIDAS = ['001', '007']
SITUACAO_TURMA_VALIDA = 'aberta'
```

Os filtros de ano/período/situação aplicam-se à população de docentes por turma. Coordenadores e NDE seguem suas próprias fontes de elegibilidade.

## Validação realizada

A carga `2026.2` foi validada com sucesso. Dois coordenadores que anteriormente provocavam erro de usuário não cadastrado — `aline.botelho@foa.org.br` e `samantha.nobre@foa.org.br` — passaram a ser encontrados no `IMP-006` e o `IMP-007` seguinte foi concluído com zero erros.

## Critérios de aceite

- todo docente de turma elegível é considerado;
- todo coordenador de curso elegível é considerado, mesmo sem turma;
- todo membro NDE ativo é considerado, mesmo sem turma;
- dados NDE são resolvidos por `mailbox` em `LY_DOCENTE`;
- um `NUM_FUNC` produz um único cadastro;
- o `IMP-006` não inventa vínculos de curso;
- o `IMP-007` pode processar todos os usuários necessários sem erro de usuário não cadastrado.
