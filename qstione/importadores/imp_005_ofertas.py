"""
Importador para tabela imp_005_ofertas
"""

import sqlite3
from qstione.core.transformacoes import (
    gerar_codigo_oferta,
    gerar_codigo_disciplina_curso,
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
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione
    
    def obter_dados_lyceum(self):
        """
        Obtém dados do banco Lyceum para a tabela imp_005_ofertas
        """
        cursor = self.con_lyceum.cursor()
        
        # Primeiro, vamos descobrir a estrutura das tabelas
        try:
            # Verificar se LY_TURMA tem a coluna 'curso'
            cursor.execute("PRAGMA table_info(LY_TURMA)")
            colunas_turma = [col[1] for col in cursor.fetchall()]
            tem_curso_na_turma = 'curso' in colunas_turma
            
            print(f"🔍 LY_TURMA tem coluna 'curso'? {tem_curso_na_turma}")
            
            # Verificar se LY_DISCIPLINA tem a coluna 'curso'
            cursor.execute("PRAGMA table_info(LY_DISCIPLINA)")
            colunas_disciplina = [col[1] for col in cursor.fetchall()]
            tem_curso_na_disciplina = 'curso' in colunas_disciplina
            
            print(f"🔍 LY_DISCIPLINA tem coluna 'curso'? {tem_curso_na_disciplina}")
            
            if tem_curso_na_turma:
                # Se LY_TURMA tem a coluna curso, usamos ela
                query = """
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
                    WHERE t.ano = 2026
                      AND t.semestre IN ('21', '22', '2')
                      AND t.sit_turma = 'aberta'
                      AND d.faculdade IN ('001', '002', '004')
                      AND (d.area_conhecimento IN ('Obrigatória', 'Disciplinas Obrigatórias', 'Optativa', 'Pesquisa Curricularizada') 
                           OR d.area_conhecimento IS NULL)
                    ORDER BY t.disciplina, t.turma
                """
            elif tem_curso_na_disciplina:
                # Se LY_DISCIPLINA tem a coluna curso, usamos ela
                query = """
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
                    WHERE t.ano = 2026
                      AND t.semestre IN ('21', '22', '2')
                      AND t.sit_turma = 'aberta'
                      AND d.faculdade IN ('001', '002', '004')
                      AND (d.area_conhecimento IN ('Obrigatória', 'Disciplinas Obrigatórias', 'Optativa', 'Pesquisa Curricularizada') 
                           OR d.area_conhecimento IS NULL)
                    ORDER BY t.disciplina, t.turma
                """
            else:
                # Se nenhuma tem, tentamos usar LY_GRADE para fazer a relação
                query = """
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
                    WHERE t.ano = 2026
                      AND t.semestre IN ('21', '22', '2')
                      AND t.sit_turma = 'aberta'
                      AND d.faculdade IN ('001', '002', '004')
                      AND (d.area_conhecimento IN ('Obrigatória', 'Disciplinas Obrigatórias', 'Optativa', 'Pesquisa Curricularizada') 
                           OR d.area_conhecimento IS NULL)
                    GROUP BY t.disciplina, t.turma, t.ano, t.semestre
                    ORDER BY t.disciplina, t.turma
                """
            
            cursor.execute(query)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"Erro ao verificar estrutura das tabelas: {e}")
            # Fallback para uma consulta mais simples
            query = """
                SELECT
                    t.disciplina,
                    t.turma,
                    t.ano,
                    t.semestre,
                    t.turno,
                    d.nome_compl,
                    d.area_conhecimento
                FROM LY_TURMA t
                INNER JOIN LY_DISCIPLINA d
                    ON d.disciplina = t.disciplina
                WHERE t.ano = 2026
                  AND t.semestre IN ('21', '22', '2')
                  AND t.sit_turma = 'aberta'
                  AND d.faculdade IN ('001', '002', '004')
                  AND (d.area_conhecimento IN ('Obrigatória', 'Disciplinas Obrigatórias', 'Optativa', 'Pesquisa Curricularizada') 
                       OR d.area_conhecimento IS NULL)
                ORDER BY t.disciplina, t.turma
            """
            cursor.execute(query)
            return cursor.fetchall()
    
    def obter_turmas_regulares(self):
        """
        Obtém todas as turmas regulares (T0) para auxiliar na geração do codigoOfertaOrigem
        """
        cursor = self.con_lyceum.cursor()
        
        try:
            # Verificar se LY_TURMA tem a coluna 'curso'
            cursor.execute("PRAGMA table_info(LY_TURMA)")
            colunas_turma = [col[1] for col in cursor.fetchall()]
            tem_curso_na_turma = 'curso' in colunas_turma
            
            if tem_curso_na_turma:
                query = """
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
                    WHERE t.ano = 2026
                      AND t.semestre IN ('21', '22', '2')
                      AND t.sit_turma = 'aberta'
                      AND t.turma LIKE 'T0%'
                      AND d.faculdade IN ('001', '002', '004')
                """
            else:
                # Usar LY_GRADE para obter o curso
                query = """
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
                    WHERE t.ano = 2026
                      AND t.semestre IN ('21', '22', '2')
                      AND t.sit_turma = 'aberta'
                      AND t.turma LIKE 'T0%'
                      AND d.faculdade IN ('001', '002', '004')
                    GROUP BY t.disciplina, t.turma, t.ano, t.semestre
                """
            
            cursor.execute(query)
            turmas_regulares = {}
            
            for row in cursor.fetchall():
                disciplina, turma, ano, semestre, nome_curso, codigo_curso = row
                key = (disciplina, ano, semestre, codigo_curso)
                if key not in turmas_regulares:
                    turmas_regulares[key] = []
                turmas_regulares[key].append(turma)
            
            return turmas_regulares
            
        except Exception as e:
            print(f"Erro ao obter turmas regulares: {e}")
            return {}
    
    def transformar_dados(self, dados_lyceum):
        """
        Transforma dados do Lyceum para o formato Qstione
        """
        dados_transformados = []
        
        # Primeiro, coletar todas as turmas regulares (T0) para cada disciplina
        turmas_regulares = self.obter_turmas_regulares()
        
        for registro in dados_lyceum:
            # O registro pode ter diferentes números de elementos dependendo da consulta usada
            if len(registro) == 9:
                # Consulta completa com curso
                disciplina, turma, ano, semestre, turno, nome_compl, codigo_curso, nome_curso, area_conhecimento = registro
            elif len(registro) == 7:
                # Consulta sem curso (fallback)
                disciplina, turma, ano, semestre, turno, nome_compl, area_conhecimento = registro
                # Precisamos obter o curso de outra forma
                codigo_curso, nome_curso = self.obter_curso_para_disciplina(disciplina)
            else:
                print(f"  ⚠️  Formato de registro inválido: {registro}")
                continue
            
            # Validar campos obrigatórios
            if not validar_codigo_disciplina(disciplina):
                print(f"  ⚠️  Código da disciplina inválido: {disciplina}")
                continue
                
            nome_disciplina = validar_nome_disciplina(nome_compl)
            if nome_disciplina is None:
                print(f"  ⚠️  Nome da disciplina inválido: {nome_compl}")
                continue
            
            # Verificar se temos informações do curso
            if not codigo_curso or not nome_curso:
                print(f"  ⚠️  Não foi possível obter informações do curso para a disciplina: {disciplina}")
                continue
            
            if not validar_codigo_curso(codigo_curso):
                print(f"  ⚠️  Código do curso inválido: {codigo_curso} para a disciplina {disciplina}")
                continue
            
            # Aplicar transformações
            codigo_oferta = gerar_codigo_oferta(disciplina, turma, ano, semestre)
            codigo_disciplina = gerar_codigo_disciplina_curso(disciplina, nome_curso, codigo_curso)
            semestre_oferta = valor_fixo_2026_2(None)
            codigo_tipo_oferta = gerar_codigo_tipo_oferta(turma)
            turno_oferta = mapear_turno(turno)
            codigo_ava = valor_fixo_vazio(None)
            
            # Gerar código da oferta de origem (para REC e REP)
            codigo_oferta_origem = ''
            if codigo_tipo_oferta in ['REC', 'REP']:
                # Buscar turma regular correspondente
                key = (disciplina, ano, semestre, codigo_curso)
                if key in turmas_regulares and turmas_regulares[key]:
                    # Gerar o código da oferta de origem usando a turma regular
                    turma_regular = turmas_regulares[key][0]
                    codigo_oferta_origem = gerar_codigo_oferta(
                        disciplina, turma_regular, ano, semestre
                    )
            
            dados_transformados.append({
                'codigoOferta': truncar_texto(codigo_oferta, 30),
                'nomeOferta': truncar_texto(turma, 100),
                'codigoDisciplina': truncar_texto(codigo_disciplina, 30),
                'semestreOferta': truncar_texto(semestre_oferta, 6),
                'codigoTipoOferta': truncar_texto(codigo_tipo_oferta, 3),
                'codigoOfertaOrigem': truncar_texto(codigo_oferta_origem, 30),
                'turno': truncar_texto(turno_oferta, 1),
                'codigoIdentificacaoAVA': truncar_texto(codigo_ava, 100)
            })
        
        return dados_transformados
    
    def obter_curso_para_disciplina(self, disciplina):
        """
        Obtém o curso associado a uma disciplina usando LY_GRADE
        """
        try:
            cursor = self.con_lyceum.cursor()
            
            query = """
                SELECT 
                    g.curso,
                    c.nome
                FROM LY_GRADE g
                INNER JOIN LY_CURSO c ON c.curso = g.curso
                WHERE g.disciplina = ?
                LIMIT 1
            """
            
            cursor.execute(query, (disciplina,))
            resultado = cursor.fetchone()
            
            if resultado:
                return resultado[0], resultado[1]
            
            return None, None
            
        except Exception as e:
            print(f"Erro ao obter curso para disciplina {disciplina}: {e}")
            return None, None
    
    def importar_para_qstione(self, dados_transformados):
        """
        Importa dados para o banco Qstione
        """
        cursor = self.con_qstione.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_005_ofertas (
                codigoOferta CHAR(30) NOT NULL,
                nomeOferta CHAR(100) NOT NULL,
                codigoDisciplina CHAR(30) NOT NULL,
                semestreOferta CHAR(6) NOT NULL,
                codigoTipoOferta CHAR(3) NOT NULL,
                codigoOfertaOrigem CHAR(30),
                turno CHAR(1),
                codigoIdentificacaoAVA CHAR(100),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (codigoOferta)
            )
        ''')
        
        # Criar índice para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ofertas_disciplina 
            ON imp_005_ofertas(codigoDisciplina)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ofertas_tipo 
            ON imp_005_ofertas(codigoTipoOferta)
        ''')
        
        # SQL para UPSERT (INSERT OR UPDATE)
        sql_upsert = '''
            INSERT INTO imp_005_ofertas 
            (codigoOferta, nomeOferta, codigoDisciplina, semestreOferta, 
             codigoTipoOferta, codigoOfertaOrigem, turno, codigoIdentificacaoAVA, 
             data_atualizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(codigoOferta) DO UPDATE SET
                nomeOferta = excluded.nomeOferta,
                codigoDisciplina = excluded.codigoDisciplina,
                semestreOferta = excluded.semestreOferta,
                codigoTipoOferta = excluded.codigoTipoOferta,
                codigoOfertaOrigem = excluded.codigoOfertaOrigem,
                turno = excluded.turno,
                codigoIdentificacaoAVA = excluded.codigoIdentificacaoAVA,
                data_atualizacao = CURRENT_TIMESTAMP
        '''
        
        # Importar/Atualizar dados
        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0
        
        for registro in dados_transformados:
            try:
                # Verificar se já existe
                cursor.execute(
                    "SELECT codigoOferta FROM imp_005_ofertas WHERE codigoOferta = ?",
                    (registro['codigoOferta'],)
                )
                
                existe = cursor.fetchone()
                
                # Executar UPSERT
                cursor.execute(sql_upsert, (
                    registro['codigoOferta'],
                    registro['nomeOferta'],
                    registro['codigoDisciplina'],
                    registro['semestreOferta'],
                    registro['codigoTipoOferta'],
                    registro['codigoOfertaOrigem'] or None,
                    registro['turno'] or None,
                    registro['codigoIdentificacaoAVA'] or None
                ))
                
                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1
                    
            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗  Erro ao importar {registro['codigoOferta']}: {e}")
        
        self.con_qstione.commit()
        
        return {
            'total_inseridos': total_inseridos,
            'total_atualizados': total_atualizados,
            'total_erros': total_erros,
            'total_processados': len(dados_transformados)
        }
    
    def executar_importacao(self):
        """
        Executa todo o processo de importação
        """
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