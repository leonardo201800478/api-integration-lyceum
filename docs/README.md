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

### [SYNC_LYCEUM_V2.md](SYNC_LYCEUM_V2.md)

Documento da nova arquitetura de sincronização Lyceum. Contém:

- separação entre coleta Lyceum e carga Qstione;
- estrutura `sync_v2/`;
- catálogo de endpoints cobertos;
- adaptador de compatibilidade;
- runner controlado;
- estratégia de migração endpoint por endpoint;
- objetivos de paginação, checkpoint, incrementalidade, retry e métricas;
- critérios de segurança para não interferir na carga Qstione.

### [IMP_006_USUARIOS.md](IMP_006_USUARIOS.md)

Documenta a população de usuários do IMP-006, incluindo docentes, coordenadores e NDE.

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

### Carga Qstione — FINALIZADA

A carga ativa via POST para a API Qstione foi validada para `2026.2`, com execução completa sem erros nas etapas testadas.

### Sincronização Lyceum V2 — EM CONSTRUÇÃO

A V2 foi criada em paralelo à implementação existente. Nesta primeira fase, os endpoints V2 usam adaptadores para a implementação atual. Isso permite testar uma nova superfície sem alterar o comportamento já validado.

A V2 **ainda não deve ser considerada substituta da sincronização legada**.

## Regras de manutenção

Toda alteração funcional relevante deve atualizar a documentação correspondente.

A sincronização Lyceum V2 deve ser migrada **endpoint por endpoint**, sempre comparando os resultados com a implementação atual antes de qualquer substituição.

Não devem ser introduzidas simultaneamente mudanças na sincronização Lyceum e nos importadores Qstione. Isso mantém o diagnóstico isolado e reduz o risco operacional.

## Separação das regras

A documentação deve distinguir:

1. **Especificação Qstione** — exigências do contrato externo.
2. **Lyceum** — comportamento e dados da origem acadêmica.
3. **Integração** — transformações necessárias para compatibilizar origem e destino.
4. **Decisão técnica** — implementação adotada pelo projeto.

## Inativação

A inativação de usuários, docentes, NDE e alunos permanece fora do escopo da carga ativa. Será especificada posteriormente, após definição e testes do mecanismo apropriado da API Qstione.
