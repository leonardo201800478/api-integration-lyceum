# Documentação — aluno-sync

Esta pasta concentra a documentação funcional e técnica do projeto `aluno-sync`, com foco na integração **Lyceum → Qstione** e nas regras necessárias para manutenção segura da carga.

## Documentos normativos

### [QSTIONE_CARGA_COMPLETA.md](QSTIONE_CARGA_COMPLETA.md)

Documento principal da integração. Contém:

- arquitetura e responsabilidades;
- princípio de fonte de verdade;
- camada intermediária `imp_XXX_*`;
- contrato HTTP POST da API Qstione;
- filtros letivos vigentes;
- ordem das etapas;
- regra de turma compartilhada e código técnico `999`;
- responsabilidades dos principais importadores;
- regras de usuários, NDE e papéis;
- execução, validação e critérios de aceite;
- status da carga ativa e escopo reservado para inativação.

### [IMP_007_USUARIOS_CURSOS.md](IMP_007_USUARIOS_CURSOS.md)

Documento específico do IMP-007, detalhando:

- vínculo usuário × curso;
- papel global por usuário;
- hierarquia `C > A > P`;
- papel administrativo `G`;
- tratamento de membros NDE;
- propagação do papel efetivo;
- tratamento do curso técnico `999`;
- critérios de aceite.

## Estado atual da implementação

### Carga ativa — FINALIZADA

A carga ativa via POST para a API Qstione foi validada para `2026.2`, com execução completa sem erros nas etapas testadas.

Resultado de referência:

| Etapa | Resultado |
|---|---:|
| IMP-007 | 535 registros / 0 erros |
| IMP-010 | 4.893 relações aluno/curso / 0 erros |
| IMP-011 | 19.290 registros / 0 erros |
| IMP-013 | 11 registros / 0 erros |
| Carga completa | concluída com sucesso |

### Inativação — PENDENTE / PRÓXIMA FASE

A inativação de usuários, docentes, NDE e alunos não faz parte da carga ativa finalizada. Será especificada e implementada posteriormente, após definição do comportamento da API Qstione para inativação e realização de testes controlados.

## Regras de manutenção

Toda alteração funcional relevante deve atualizar a documentação correspondente. Em especial:

- filtros de ano/período;
- faculdades incluídas;
- situação de turma;
- mapeamento/de-para de cursos;
- regras de turma compartilhada;
- população de usuários;
- hierarquia de papéis;
- NDE;
- relacionamentos aluno/curso;
- relacionamentos usuário/curso/papel;
- professor/oferta;
- contrato da API;
- ordem das etapas.

## Separação das regras

A documentação deve distinguir:

1. **Especificação Qstione** — exigências do contrato externo.
2. **Lyceum** — comportamento e dados da origem acadêmica.
3. **Integração** — transformações necessárias para compatibilizar origem e destino.
4. **Decisão técnica** — implementação adotada pelo projeto.

Essa separação evita transformar uma decisão de implementação em uma regra acadêmica.

## Princípios para a próxima fase

A futura inativação deverá ser tratada separadamente da carga ativa e deverá:

- identificar primeiro os registros que perderam elegibilidade;
- evitar exclusão física quando a API oferecer mecanismo de inativação;
- validar o contrato da API antes de alterar o código;
- executar testes controlados;
- registrar auditoria da alteração;
- somente então integrar a rotina ao processo automático.
