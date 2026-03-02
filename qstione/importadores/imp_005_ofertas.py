"""
qstione/importadores/imp_005_ofertas.py
Importador para tabela imp_005_ofertas
Adaptado para SQL Server com alinhamento ao código de disciplina do imp_002
"""

from core.database import get_db_connection
from qstione.config.filtros import (
    ANO_VIGENTE,
    PERIODOS_VIGENTES,
    FACULDADES_INCLUIDAS,
    AREAS_CONHECIMENTO_INCLUIDAS,
    SITUACAO_TURMA_VALIDA,
    SEMESTRE_OFERTA_FIXO
)
from qstione.core.transformacoes import (
    gerar_codigo_oferta,
    gerar_codigo_tipo_oferta,
    mapear_turno,
    valor_fixo_2026_2,
    valor_fixo_vazio,
    truncar_texto
)
from qstione.core.validacoes import (
    validar_codigo_disciplina,
    validar_nome_disciplina,
    validar_codigo_curso
)


class ImportadorOfertas:

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # Funções auxiliares para verificação de existência de tabelas/índices
    # -------------------------------------------------------------------------
    def _tabela_existe(self, nome_tabela: str) -> bool:
        try:
            with get_db_connection(db_path='qstione.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
                """, (nome_tabela,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar existência da tabela: {e}")
            return False

    def _indice_existe(self, nome_indice: str) -> bool:
        try:
            with get_db_connection(db_path='qstione.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM sys.indexes WHERE name = ?", (nome_indice,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar índice: {e}")
            return False

    def _criar_tabela(self):
        if self._tabela_existe('imp_005_ofertas'):
            try:
                with get_db_connection(db_path='qstione.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'imp_005_ofertas'
                          AND COLUMN_NAME IN ('data_criacao', 'data_atualizacao')
                    """)
                    colunas = [row[0] for row in cursor.fetchall()]
                    if 'data_criacao' in colunas and 'data_atualizacao' in colunas:
                        print("✅ Tabela imp_005_ofertas já existe com estrutura correta.")
                        return
                    else:
                        print("⚠️  Colunas ausentes. Recriando tabela...")
                        cursor.execute("DROP TABLE imp_005_ofertas")
                        conn.commit()
            except Exception as e:
                print(f"⚠️  Erro ao verificar colunas: {e}. Recriando tabela...")
                with get_db_connection(db_path='qstione.db') as conn:
                    conn.execute("DROP TABLE IF EXISTS imp_005_ofertas")
                    conn.commit()

        print("🆕 Criando tabela imp_005_ofertas...")
        create_sql = """
            CREATE TABLE imp_005_ofertas (
                codigoOferta NVARCHAR(30) NOT NULL,
                nomeOferta NVARCHAR(100) NOT NULL,
                codigoDisciplina NVARCHAR(30) NOT NULL,
                semestreOferta NVARCHAR(6) NOT NULL,
                codigoTipoOferta NVARCHAR(3) NOT NULL,
                codigoOfertaOrigem NVARCHAR(30) NULL,
                turno NVARCHAR(1) NULL,
                codigoIdentificacaoAVA NVARCHAR(100) NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoOferta)
            )
        """
        try:
            with get_db_connection(db_path='qstione.db') as conn:
                conn.execute(create_sql)
                conn.commit()
            print("✅ Tabela criada.")
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return

        indices = [
            ('idx_ofertas_disciplina', "CREATE INDEX idx_ofertas_disciplina ON imp_005_ofertas(codigoDisciplina)"),
            ('idx_ofertas_tipo', "CREATE INDEX idx_ofertas_tipo ON imp_005_ofertas(codigoTipoOferta)")
        ]
        for nome_idx, sql_idx in indices:
            if not self._indice_existe(nome_idx):
                try:
                    with get_db_connection(db_path='qstione.db') as conn:
                        conn.execute(sql_idx)
                        conn.commit()
                    print(f"✅ Índice {nome_idx} criado.")
                except Exception as e:
                    print(f"⚠️ Índice {nome_idx} não pôde ser criado: {e}")
            else:
                print(f"✅ Índice {nome_idx} já existe.")

    # -------------------------------------------------------------------------
    # Funções para obter metadados das tabelas do Lyceum (INFORMATION_SCHEMA)
    # -------------------------------------------------------------------------
    def _coluna_existe(self, tabela: str, coluna: str) -> bool:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
                """, (tabela, coluna))
                return cursor.fetchone() is not None
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Obter mapeamento disciplina -> codigoDisciplina da tabela imp_002_disciplina
    # -------------------------------------------------------------------------
    def _obter_codigos_disciplina(self):
        """
        Consulta a tabela imp_002_disciplina no banco Qstione e retorna um dicionário
        com disciplina original -> codigoDisciplina (o código padronizado).
        Considera que cada disciplina tem um único registro (após agregação).
        """
        codigos = {}
        try:
            with get_db_connection(db_path='qstione.db') as conn:
                cursor = conn.cursor()
                # A tabela imp_002_disciplina tem colunas: codigoDisciplina, nomeDisciplina, codigoCurso, periodo
                # Precisamos relacionar o código original da disciplina (que não está armazenado).
                # Uma alternativa é extrair a parte antes do '-' do codigoDisciplina, assumindo que o código original é o prefixo.
                # Exemplo: "12345-ADM" -> disciplina original "12345". Isso é frágil, mas talvez funcione.
                # Outra opção: modificar o imp_002 para também armazenar o código original em uma coluna, mas isso exige alteração.
                # Por enquanto, vamos usar uma abordagem de extração, mas é melhor se tivermos uma coluna separada.
                cursor.execute("""
                    SELECT codigoDisciplina FROM imp_002_disciplina
                """)
                for row in cursor.fetchall():
                    codigo_completo = row[0]
                    # Extrai a parte antes do primeiro '-'
                    if '-' in codigo_completo:
                        original = codigo_completo.split('-')[0]
                        codigos[original] = codigo_completo
                    else:
                        # Se não tiver '-', assume que é o próprio código
                        codigos[codigo_completo] = codigo_completo
        except Exception as e:
            print(f"  ⚠️  Erro ao consultar imp_002_disciplina: {e}")
        return codigos

    # -------------------------------------------------------------------------
    # Obter dados do Lyceum com filtros centralizados
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()

            tem_curso_na_turma = self._coluna_existe('LY_TURMA', 'curso')
            tem_curso_na_disciplina = self._coluna_existe('LY_DISCIPLINA', 'curso')

            areas_validas = [a for a in AREAS_CONHECIMENTO_INCLUIDAS if a is not None]
            placeholders_areas = ','.join(['?'] * len(areas_validas))

            if tem_curso_na_turma:
                query = f"""
                    SELECT
                        t.disciplina,
                        t.turma,
                        t.ano,
                        t.semestre,
                        t.turno,
                        d.nome_compl,
                        t.curso as codigo_curso,
                        c.nome as nome_curso,
                        d.area_conhecimento
                    FROM LY_TURMA t
                    INNER JOIN LY_DISCIPLINA d
                        ON d.disciplina = t.disciplina
                    INNER JOIN LY_CURSO c
                        ON c.curso = t.curso
                    WHERE t.ano = ?
                      AND t.semestre IN ({','.join(['?'] * len(PERIODOS_VIGENTES))})
                      AND t.sit_turma = ?
                      AND d.faculdade IN ({','.join(['?'] * len(FACULDADES_INCLUIDAS))})
                      AND (d.area_conhecimento IN ({placeholders_areas})
                           OR d.area_conhecimento IS NULL)
                    ORDER BY t.disciplina, t.turma
                """
                params = [ANO_VIGENTE] + PERIODOS_VIGENTES + [SITUACAO_TURMA_VALIDA] + FACULDADES_INCLUIDAS + areas_validas

            elif tem_curso_na_disciplina:
                query = f"""
                    SELECT
                        t.disciplina,
                        t.turma,
                        t.ano,
                        t.semestre,
                        t.turno,
                        d.nome_compl,
                        d.curso as codigo_curso,
                        c.nome as nome_curso,
                        d.area_conhecimento
                    FROM LY_TURMA t
                    INNER JOIN LY_DISCIPLINA d
                        ON d.disciplina = t.disciplina
                    INNER JOIN LY_CURSO c
                        ON c.curso = d.curso
                    WHERE t.ano = ?
                      AND t.semestre IN ({','.join(['?'] * len(PERIODOS_VIGENTES))})
                      AND t.sit_turma = ?
                      AND d.faculdade IN ({','.join(['?'] * len(FACULDADES_INCLUIDAS))})
                      AND (d.area_conhecimento IN ({placeholders_areas})
                           OR d.area_conhecimento IS NULL)
                    ORDER BY t.disciplina, t.turma
                """
                params = [ANO_VIGENTE] + PERIODOS_VIGENTES + [SITUACAO_TURMA_VALIDA] + FACULDADES_INCLUIDAS + areas_validas

            else:
                query = f"""
                    SELECT
                        t.disciplina,
                        t.turma,
                        t.ano,
                        t.semestre,
                        t.turno,
                        d.nome_compl,
                        g.curso as codigo_curso,
                        c.nome as nome_curso,
                        d.area_conhecimento
                    FROM LY_TURMA t
                    INNER JOIN LY_DISCIPLINA d
                        ON d.disciplina = t.disciplina
                    INNER JOIN LY_GRADE g
                        ON g.disciplina = t.disciplina
                    INNER JOIN LY_CURSO c
                        ON c.curso = g.curso
                    WHERE t.ano = ?
                      AND t.semestre IN ({','.join(['?'] * len(PERIODOS_VIGENTES))})
                      AND t.sit_turma = ?
                      AND d.faculdade IN ({','.join(['?'] * len(FACULDADES_INCLUIDAS))})
                      AND (d.area_conhecimento IN ({placeholders_areas})
                           OR d.area_conhecimento IS NULL)
                    GROUP BY t.disciplina, t.turma, t.ano, t.semestre, t.turno,
                             d.nome_compl, g.curso, c.nome, d.area_conhecimento
                    ORDER BY t.disciplina, t.turma
                """
                params = [ANO_VIGENTE] + PERIODOS_VIGENTES + [SITUACAO_TURMA_VALIDA] + FACULDADES_INCLUIDAS + areas_validas

            cursor.execute(query, params)
            return cursor.fetchall()

    # -------------------------------------------------------------------------
    # Obter turmas regulares (T0) com filtros centralizados
    # -------------------------------------------------------------------------
    def obter_turmas_regulares(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            tem_curso_na_turma = self._coluna_existe('LY_TURMA', 'curso')

            if tem_curso_na_turma:
                query = f"""
                    SELECT
                        t.disciplina,
                        t.turma,
                        t.ano,
                        t.semestre,
                        c.nome as nome_curso,
                        t.curso as codigo_curso
                    FROM LY_TURMA t
                    INNER JOIN LY_DISCIPLINA d
                        ON d.disciplina = t.disciplina
                    INNER JOIN LY_CURSO c
                        ON c.curso = t.curso
                    WHERE t.ano = ?
                      AND t.semestre IN ({','.join(['?'] * len(PERIODOS_VIGENTES))})
                      AND t.sit_turma = ?
                      AND t.turma LIKE 'T0%'
                      AND d.faculdade IN ({','.join(['?'] * len(FACULDADES_INCLUIDAS))})
                """
                params = [ANO_VIGENTE] + PERIODOS_VIGENTES + [SITUACAO_TURMA_VALIDA] + FACULDADES_INCLUIDAS
            else:
                query = f"""
                    SELECT
                        t.disciplina,
                        t.turma,
                        t.ano,
                        t.semestre,
                        c.nome as nome_curso,
                        g.curso as codigo_curso
                    FROM LY_TURMA t
                    INNER JOIN LY_DISCIPLINA d
                        ON d.disciplina = t.disciplina
                    INNER JOIN LY_GRADE g
                        ON g.disciplina = t.disciplina
                    INNER JOIN LY_CURSO c
                        ON c.curso = g.curso
                    WHERE t.ano = ?
                      AND t.semestre IN ({','.join(['?'] * len(PERIODOS_VIGENTES))})
                      AND t.sit_turma = ?
                      AND t.turma LIKE 'T0%'
                      AND d.faculdade IN ({','.join(['?'] * len(FACULDADES_INCLUIDAS))})
                    GROUP BY t.disciplina, t.turma, t.ano, t.semestre, c.nome, g.curso
                """
                params = [ANO_VIGENTE] + PERIODOS_VIGENTES + [SITUACAO_TURMA_VALIDA] + FACULDADES_INCLUIDAS

            cursor.execute(query, params)
            turmas_regulares = {}
            for row in cursor.fetchall():
                disciplina, turma, ano, semestre, nome_curso, codigo_curso = row
                key = (disciplina, ano, semestre, codigo_curso)
                if key not in turmas_regulares:
                    turmas_regulares[key] = []
                turmas_regulares[key].append(turma)
            return turmas_regulares

    # -------------------------------------------------------------------------
    # Obter curso para disciplina (fallback)
    # -------------------------------------------------------------------------
    def obter_curso_para_disciplina(self, disciplina):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT TOP 1
                        g.curso,
                        c.nome
                    FROM LY_GRADE g
                    INNER JOIN LY_CURSO c ON c.curso = g.curso
                    WHERE g.disciplina = ?
                """
                cursor.execute(query, (disciplina,))
                row = cursor.fetchone()
                if row:
                    return row[0], row[1]
                return None, None
        except Exception as e:
            print(f"Erro ao obter curso para disciplina {disciplina}: {e}")
            return None, None

    # -------------------------------------------------------------------------
    # Transformar dados (usando mapeamento de disciplinas do imp_002)
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        # Obter mapeamento disciplina -> codigoDisciplina padronizado
        mapa_codigos = self._obter_codigos_disciplina()
        if not mapa_codigos:
            print("  ⚠️  Nenhum código de disciplina encontrado no imp_002. As ofertas serão geradas com base no curso da turma, mas podem haver divergências.")

        turmas_regulares = self.obter_turmas_regulares()
        dados_transformados = []

        for registro in dados_lyceum:
            if len(registro) == 9:
                disciplina, turma, ano, semestre, turno, nome_compl, codigo_curso, nome_curso, area_conhecimento = registro
            elif len(registro) == 7:
                disciplina, turma, ano, semestre, turno, nome_compl, area_conhecimento = registro
                codigo_curso, nome_curso = self.obter_curso_para_disciplina(disciplina)
            else:
                print(f"  ⚠️  Formato de registro inválido: {registro}")
                continue

            # Validações
            if not validar_codigo_disciplina(disciplina):
                print(f"  ⚠️  Código da disciplina inválido: {disciplina}")
                continue

            nome_disciplina = validar_nome_disciplina(nome_compl)
            if nome_disciplina is None:
                nome_disciplina = truncar_texto(nome_compl, 100)
                if not nome_disciplina:
                    print(f"  ⚠️  Nome da disciplina inválido após truncagem: {nome_compl}")
                    continue
                print(f"  ⚠️  Nome da disciplina truncado: {nome_disciplina}")

            # Determinar o código da disciplina padronizado
            if disciplina in mapa_codigos:
                codigo_disciplina_padrao = mapa_codigos[disciplina]
            else:
                # Fallback: gerar com base no curso da turma
                print(f"  ⚠️  Disciplina {disciplina} não encontrada no imp_002. Gerando código com curso {codigo_curso}.")
                from qstione.core.transformacoes import gerar_codigo_disciplina_curso
                codigo_disciplina_padrao = gerar_codigo_disciplina_curso(disciplina, nome_curso, codigo_curso)
                codigo_disciplina_padrao = truncar_texto(codigo_disciplina_padrao, 30)

            # Gerar código da oferta
            codigo_oferta = gerar_codigo_oferta(disciplina, turma, ano, semestre)
            semestre_oferta = valor_fixo_2026_2(None)
            codigo_tipo_oferta = gerar_codigo_tipo_oferta(turma)
            turno_oferta = mapear_turno(turno)
            codigo_ava = valor_fixo_vazio(None)

            # Código de origem para REC/REP
            codigo_oferta_origem = ''
            if codigo_tipo_oferta in ['REC', 'REP']:
                key = (disciplina, ano, semestre, codigo_curso)
                if key in turmas_regulares and turmas_regulares[key]:
                    turma_regular = turmas_regulares[key][0]
                    codigo_oferta_origem = gerar_codigo_oferta(disciplina, turma_regular, ano, semestre)

            dados_transformados.append({
                'codigoOferta': truncar_texto(codigo_oferta, 30),
                'nomeOferta': truncar_texto(turma, 100),
                'codigoDisciplina': codigo_disciplina_padrao,
                'semestreOferta': truncar_texto(semestre_oferta, 6),
                'codigoTipoOferta': truncar_texto(codigo_tipo_oferta, 3),
                'codigoOfertaOrigem': truncar_texto(codigo_oferta_origem, 30),
                'turno': truncar_texto(turno_oferta, 1),
                'codigoIdentificacaoAVA': truncar_texto(codigo_ava, 100)
            })

        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        merge_sql = """
            MERGE INTO imp_005_ofertas AS target
            USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?)) AS source
                (codigoOferta, nomeOferta, codigoDisciplina, semestreOferta,
                 codigoTipoOferta, codigoOfertaOrigem, turno, codigoIdentificacaoAVA)
            ON target.codigoOferta = source.codigoOferta
            WHEN MATCHED THEN
                UPDATE SET
                    nomeOferta = source.nomeOferta,
                    codigoDisciplina = source.codigoDisciplina,
                    semestreOferta = source.semestreOferta,
                    codigoTipoOferta = source.codigoTipoOferta,
                    codigoOfertaOrigem = source.codigoOfertaOrigem,
                    turno = source.turno,
                    codigoIdentificacaoAVA = source.codigoIdentificacaoAVA,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoOferta, nomeOferta, codigoDisciplina, semestreOferta,
                        codigoTipoOferta, codigoOfertaOrigem, turno, codigoIdentificacaoAVA,
                        data_criacao, data_atualizacao)
                VALUES (source.codigoOferta, source.nomeOferta, source.codigoDisciplina,
                        source.semestreOferta, source.codigoTipoOferta, source.codigoOfertaOrigem,
                        source.turno, source.codigoIdentificacaoAVA, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(db_path='qstione.db') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("SELECT 1 FROM imp_005_ofertas WHERE codigoOferta = ?", (reg['codigoOferta'],))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['codigoOferta'],
                        reg['nomeOferta'],
                        reg['codigoDisciplina'],
                        reg['semestreOferta'],
                        reg['codigoTipoOferta'],
                        reg['codigoOfertaOrigem'] or None,
                        reg['turno'] or None,
                        reg['codigoIdentificacaoAVA'] or None
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗  Erro ao importar {reg['codigoOferta']}: {e}")

            conn.commit()

        return {
            'total_inseridos': total_inseridos,
            'total_atualizados': total_atualizados,
            'total_erros': total_erros,
            'total_processados': len(dados_transformados)
        }

    # -------------------------------------------------------------------------
    # Execução principal
    # -------------------------------------------------------------------------
    def executar_importacao(self):
        print("=" * 70)
        print("IMPORTAÇÃO: imp_005_ofertas")
        print("=" * 70)

        # 1. Obter dados do Lyceum
        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum: {len(dados_lyceum)}")

        # 2. Transformar dados
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum)
        print(f"✅ Registros válidos para importação: {len(dados_transformados)}")

        # 3. Importar para Qstione
        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)

        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")

        return dados_transformados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorOfertas()
    importador.executar_importacao()