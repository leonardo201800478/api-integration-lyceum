"""
Importador para tabela imp_009_professores_ofertas

Exporta a relação entre ofertas de disciplinas (turmas) e professores (e-mail).
Gera o código da oferta da mesma forma que o importador imp_005_ofertas.

Campos:
    - codigoOferta:   CHAR(30) – código da oferta (disciplina_turma_anoSemestre)
    - emailProfessor: CHAR(100) – e-mail do docente (minúsculas)

Filtros aplicados (idênticos ao imp_005_ofertas):
    - LY_TURMA: ano = 2026, semestre IN ('21','22','2'), sit_turma = 'aberta'
    - LY_DISCIPLINA: faculdade IN ('001','002','004')
    - Áreas de conhecimento: obrigatórias, optativas, pesquisa curricularizada ou NULL
    - LY_DOCENTE: ativo = 'S' e e-mail válido
"""

import sqlite3
from qstione.core.transformacoes import (
    gerar_codigo_oferta,
    converter_minusculas,
    truncar_texto
)
from qstione.core.validacoes import validar_email


class ImportadorProfessoresOfertas:
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione

    def obter_dados_lyceum(self):
        """
        Obtém do banco Lyceum os pares (disciplina, turma, ano, semestre, email)
        respeitando os filtros e garantindo DISTINCT para evitar duplicatas.
        """
        cursor = self.con_lyceum.cursor()

        query = """
            SELECT DISTINCT
                t.disciplina,
                t.turma,
                t.ano,
                t.semestre,
                d.email
            FROM LY_TURMA t
            INNER JOIN LY_DISCIPLINA dsc
                ON dsc.disciplina = t.disciplina
            INNER JOIN LY_TURMA_DOCENTE td
                ON td.disciplina = t.disciplina
                AND td.turma = t.turma
                AND td.ano = t.ano
                AND td.periodo = t.semestre
            INNER JOIN LY_DOCENTE d
                ON d.num_func = td.num_func
            WHERE t.ano = 2026
              AND t.semestre IN ('21', '22', '2')
              AND t.sit_turma = 'aberta'
              AND dsc.faculdade IN ('001', '002', '004')
              AND (dsc.area_conhecimento IN (
                      'Obrigatória',
                      'Disciplinas Obrigatórias',
                      'Optativa',
                      'Pesquisa Curricularizada'
                  ) OR dsc.area_conhecimento IS NULL)
              AND d.ativo = 'S'
              AND d.email IS NOT NULL
              AND d.email != ''
            ORDER BY t.disciplina, t.turma, d.email
        """

        cursor.execute(query)
        return cursor.fetchall()

    def transformar_dados(self, dados_lyceum):
        """
        Transforma cada registro bruto do Lyceum no formato esperado pelo Qstione.
        - Gera codigoOferta com a função gerar_codigo_oferta()
        - Converte e-mail para minúsculas
        - Valida o e-mail; registros inválidos são ignorados com aviso
        """
        dados_transformados = []

        for disciplina, turma, ano, semestre, email in dados_lyceum:
            # --- Validação do e-mail (campo obrigatório) ---
            if not validar_email(email):
                print(f"  ⚠️  E-mail inválido para oferta {disciplina}_{turma}_{ano}{semestre}: {email}")
                continue

            # --- Geração do código da oferta (igual ao imp_005) ---
            codigo_oferta = gerar_codigo_oferta(disciplina, turma, ano, semestre)
            codigo_oferta = truncar_texto(codigo_oferta, 30)

            # --- E-mail normalizado ---
            email_final = converter_minusculas(email)
            email_final = truncar_texto(email_final, 100)

            dados_transformados.append({
                'codigoOferta': codigo_oferta,
                'emailProfessor': email_final
            })

        return dados_transformados

    def importar_para_qstione(self, dados_transformados):
        """
        Cria/atualiza a tabela imp_009_professores_ofertas e insere os dados.
        Utiliza UPSERT (INSERT OR UPDATE) com chave primária composta.
        """
        cursor = self.con_qstione.cursor()

        # --- Criação da tabela (se não existir) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_009_professores_ofertas (
                codigoOferta CHAR(30) NOT NULL,
                emailProfessor CHAR(100) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (codigoOferta, emailProfessor)
            )
        ''')

        # --- Índices para consultas futuras ---
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_professores_ofertas_email
            ON imp_009_professores_ofertas(emailProfessor)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_professores_ofertas_codigo
            ON imp_009_professores_ofertas(codigoOferta)
        ''')

        # --- SQL de UPSERT (padrão do projeto) ---
        sql_upsert = '''
            INSERT INTO imp_009_professores_ofertas
            (codigoOferta, emailProfessor, data_atualizacao)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(codigoOferta, emailProfessor) DO UPDATE SET
                data_atualizacao = CURRENT_TIMESTAMP
        '''

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        for registro in dados_transformados:
            try:
                # Verifica se o par já existe (apenas para estatística)
                cursor.execute(
                    """SELECT 1 FROM imp_009_professores_ofertas
                       WHERE codigoOferta = ?
                         AND emailProfessor = ?""",
                    (registro['codigoOferta'], registro['emailProfessor'])
                )
                existe = cursor.fetchone()

                # Executa o UPSERT
                cursor.execute(sql_upsert, (
                    registro['codigoOferta'],
                    registro['emailProfessor']
                ))

                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1

            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗ Erro ao importar {registro['codigoOferta']} - {registro['emailProfessor']}: {e}")

        self.con_qstione.commit()

        return {
            'total_inseridos': total_inseridos,
            'total_atualizados': total_atualizados,
            'total_erros': total_erros,
            'total_processados': len(dados_transformados)
        }

    def executar_importacao(self):
        """
        Executa o fluxo completo de importação para imp_009_professores_ofertas.
        """
        print("=" * 70)
        print("IMPORTAÇÃO: imp_009_professores_ofertas")
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