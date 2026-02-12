"""
Importador para tabela imp_008_usuarios_disciplinas

Exporta a relação entre disciplinas e docentes (email) para o Qstione.
Gera o código da disciplina concatenado com as iniciais do curso,
seguindo a mesma regra do importador imp_002_disciplina.

Campos:
    - codigoDisciplina: CHAR(30)  – código da disciplina + '-' + iniciais do curso
    - emailUsuario:      CHAR(100) – e-mail do docente (minúsculas)

Filtros aplicados:
    - LY_TURMA_DOCENTE: ano = 2026, periodo = '21'
    - LY_DISCIPLINA:    faculdade IN ('001', '002')
    - LY_DOCENTE:       ativo = 'S'
    - Apenas docentes com e‑mail válido (validar_email)
"""

import sqlite3
from qstione.core.transformacoes import (
    gerar_codigo_disciplina_curso,
    converter_minusculas,
    truncar_texto
)
from qstione.core.validacoes import validar_email


class ImportadorUsuariosDisciplinas:
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione

    def obter_dados_lyceum(self):
        """
        Obtém do banco Lyceum os pares (disciplina, email) únicos,
        respeitando os filtros de ano, período, faculdade e docente ativo.
        """
        cursor = self.con_lyceum.cursor()

        # A consulta garante DISTINCT para evitar duplicatas
        query = """
            SELECT DISTINCT
                td.disciplina,
                d.email,
                g.curso AS codigo_curso,
                c.nome   AS nome_curso
            FROM LY_TURMA_DOCENTE td
            INNER JOIN LY_DISCIPLINA dsc
                ON dsc.disciplina = td.disciplina
            INNER JOIN LY_DOCENTE d
                ON d.num_func = td.num_func
            INNER JOIN LY_GRADE g
                ON g.disciplina = td.disciplina
            INNER JOIN LY_CURSO c
                ON c.curso = g.curso
            WHERE td.ano = 2026
              AND td.periodo = '21'
              AND dsc.faculdade IN ('001', '002')
              AND d.ativo = 'S'
            ORDER BY td.disciplina, d.email
        """

        cursor.execute(query)
        return cursor.fetchall()

    def transformar_dados(self, dados_lyceum):
        """
        Transforma cada registro bruto do Lyceum no formato esperado pelo Qstione.
        - Gera codigoDisciplina com a função gerar_codigo_disciplina_curso
        - Converte e‑mail para minúsculas
        - Valida o e‑mail; registros inválidos são ignorados com aviso
        """
        dados_transformados = []

        for disciplina, email, codigo_curso, nome_curso in dados_lyceum:
            # --- Validação do e-mail (campo obrigatório) ---
            if not validar_email(email):
                print(f"  ⚠️  E-mail inválido para disciplina {disciplina}: {email}")
                continue

            # --- Transformações ---
            # 1. Geração do código da disciplina (igual ao imp_002)
            codigo_disciplina_final = gerar_codigo_disciplina_curso(
                disciplina,
                nome_curso,
                codigo_curso
            )

            # 2. E-mail em minúsculas e truncado (segurança)
            email_final = converter_minusculas(email)
            email_final = truncar_texto(email_final, 100)

            # 3. Truncar código da disciplina para 30 caracteres
            codigo_disciplina_final = truncar_texto(codigo_disciplina_final, 30)

            dados_transformados.append({
                'codigoDisciplina': codigo_disciplina_final,
                'emailUsuario': email_final
            })

        return dados_transformados

    def importar_para_qstione(self, dados_transformados):
        """
        Cria/atualiza a tabela imp_008_usuarios_disciplinas e insere os dados.
        Utiliza UPSERT (INSERT OR UPDATE) com chave primária composta.
        """
        cursor = self.con_qstione.cursor()

        # --- Criação da tabela (se não existir) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_008_usuarios_disciplinas (
                codigoDisciplina CHAR(30) NOT NULL,
                emailUsuario CHAR(100) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (codigoDisciplina, emailUsuario)
            )
        ''')

        # --- Índices para consultas futuras ---
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_disciplinas_email
            ON imp_008_usuarios_disciplinas(emailUsuario)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_disciplinas_codigo
            ON imp_008_usuarios_disciplinas(codigoDisciplina)
        ''')

        # --- SQL de UPSERT (padrão do projeto) ---
        sql_upsert = '''
            INSERT INTO imp_008_usuarios_disciplinas
            (codigoDisciplina, emailUsuario, data_atualizacao)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(codigoDisciplina, emailUsuario) DO UPDATE SET
                data_atualizacao = CURRENT_TIMESTAMP
        '''

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        for registro in dados_transformados:
            try:
                # Verifica se o par já existe (apenas para estatística)
                cursor.execute(
                    """SELECT 1 FROM imp_008_usuarios_disciplinas
                       WHERE codigoDisciplina = ?
                         AND emailUsuario = ?""",
                    (registro['codigoDisciplina'], registro['emailUsuario'])
                )
                existe = cursor.fetchone()

                # Executa o UPSERT
                cursor.execute(sql_upsert, (
                    registro['codigoDisciplina'],
                    registro['emailUsuario']
                ))

                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1

            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗ Erro ao importar {registro['codigoDisciplina']} - {registro['emailUsuario']}: {e}")

        self.con_qstione.commit()

        return {
            'total_inseridos': total_inseridos,
            'total_atualizados': total_atualizados,
            'total_erros': total_erros,
            'total_processados': len(dados_transformados)
        }

    def executar_importacao(self):
        """
        Executa o fluxo completo de importação para imp_008_usuarios_disciplinas.
        """
        print("=" * 70)
        print("IMPORTAÇÃO: imp_008_usuarios_disciplinas")
        print("=" * 70)

        # 1. Obtém dados brutos do Lyceum
        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum (após DISTINCT): {len(dados_lyceum)}")

        # 2. Transforma e valida os dados
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum)
        print(f"✅ Registros válidos para importação: {len(dados_transformados)}")

        # 3. Importa para o banco Qstione
        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)

        # 4. Exibe relatório final
        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")

        return dados_transformados