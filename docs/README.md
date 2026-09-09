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

## Regra de documentação

Toda alteração funcional relevante deve atualizar a documentação correspondente.

Em especial, qualquer mudança em:

- código de curso;
- mapeamento/de-para;
- filtro de período;
- situação de turma;
- regra de turma compartilhada;
- relacionamento aluno/curso;
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
