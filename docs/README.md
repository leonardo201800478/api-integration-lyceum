# Documentação do projeto

Esta pasta concentra a documentação funcional e técnica das integrações do `aluno-sync`.

## Documentos

### [QSTIONE_CARGA_COMPLETA.md](QSTIONE_CARGA_COMPLETA.md)

Documento principal da integração Lyceum → Qstione. Registra:

- objetivo da integração;
- arquitetura e responsabilidades;
- ordem das etapas IMP;
- contrato de comunicação com a API Qstione;
- filtros letivos;
- regras de transformação;
- regra oficial de turma compartilhada (`999` / `Turma Compartilhada`);
- responsabilidades dos importadores;
- execução e diagnóstico;
- critérios de aceite;
- orientações para manutenção futura.

### [IMP_007_USUARIOS_CURSOS.md](IMP_007_USUARIOS_CURSOS.md)

Documento específico da regra de usuários x cursos do IMP-007. Registra explicitamente:

- diferença entre vínculo de curso e papel do usuário;
- hierarquia global `C > A > P`;
- papel máximo único por usuário;
- propagação do papel máximo para todos os cursos do usuário;
- comportamento de coordenadores que também lecionam em outros cursos;
- comportamento de avaliadores NDE que também possuem vínculos docentes;
- regra do código técnico `999` para turmas compartilhadas;
- critérios de aceite do IMP-007.

## Regra de documentação

Toda alteração funcional relevante deve atualizar a documentação correspondente.

Em especial, qualquer mudança em:

- código de curso;
- mapeamento/de-para;
- filtro de período;
- situação de turma;
- regra de turma compartilhada;
- relacionamento aluno/curso;
- relacionamento usuário/curso/papel;
- hierarquia de papéis;
- relacionamento professor/oferta;
- contrato da API;
- ordem de carga;

deve ser registrada neste conjunto documental.

## Fonte da regra

A documentação deve distinguir claramente:

1. **regra da especificação Qstione** — exigência do contrato externo;
2. **regra do Lyceum** — comportamento da origem acadêmica;
3. **regra de integração** — transformação necessária para compatibilizar origem e destino;
4. **decisão técnica** — implementação utilizada pelo projeto.

Essa separação evita que uma solução técnica seja confundida com uma regra acadêmica de origem.
