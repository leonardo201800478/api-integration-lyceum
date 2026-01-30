"""
Importador para tabela imp_002_disciplina
"""

import sqlite3
from qstione.core.transformacoes import (
    converter_inteiro,
    gerar_codigo_disciplina_curso
)
from qstione.core.validacoes import (
    validar_codigo_disciplina,
    validar_nome_disciplina,
    validar_codigo_curso,
    validar_periodo
)

class ImportadorDisciplinas:
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione
    
    def obter_dados_lyceum(self):
        """
        Obtém dados do banco Lyceum para a tabela imp_002_disciplina
        """
        cursor = self.con_lyceum.cursor()
        
        query = """
            SELECT
                g.disciplina,
                d.nome_compl,
                g.curso,
                c.nome as nome_curso,
                g.serie_ideal
            FROM LY_GRADE g
            INNER JOIN LY_DISCIPLINA d
                ON d.disciplina = g.disciplina
            INNER JOIN LY_CURSO c
                ON c.curso = g.curso
            WHERE c.ativo = 'S'
              AND c.faculdade IN ('001', '002', '004')
            ORDER BY g.curso, g.serie_ideal, g.disciplina
        """
        
        cursor.execute(query)
        return cursor.fetchall()
    
    def transformar_dados(self, dados_lyceum):
        """
        Transforma dados do Lyceum para o formato Qstione
        """
        dados_transformados = []
        
        for registro in dados_lyceum:
            disciplina, nome_compl, curso, nome_curso, serie_ideal = registro
            
            # Validar campos obrigatórios usando as funções de validação
            if not validar_codigo_disciplina(disciplina):
                print(f"  ⚠️  Código da disciplina inválido: {disciplina}")
                continue
                
            nome_disciplina = validar_nome_disciplina(nome_compl)
            if nome_disciplina is None:
                print(f"  ⚠️  Nome da disciplina inválido: {nome_compl}")
                continue
                
            if not validar_codigo_curso(curso):
                print(f"  ⚠️  Código do curso inválido: {curso} para a disciplina {disciplina}")
                continue
                
            if not validar_periodo(serie_ideal):
                print(f"  ⚠️  Período inválido: {serie_ideal} para a disciplina {disciplina}")
                continue
            
            # Aplicar transformações
            periodo = converter_inteiro(serie_ideal)

            # Regra de negócio: período 0 vira 1
            if periodo == 0:
                periodo = 1

            # Gerar código da disciplina formatado
            codigo_disciplina_final = gerar_codigo_disciplina_curso(
                disciplina, 
                nome_curso, 
                curso
            )

            dados_transformados.append({
                'codigoDisciplina': codigo_disciplina_final,
                'nomeDisciplina': nome_disciplina,
                'codigoCurso': str(curso)[:30],
                'periodo': periodo
            })
        
        return dados_transformados
    
    def importar_para_qstione(self, dados_transformados):
        """
        Importa dados para o banco Qstione
        """
        cursor = self.con_qstione.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_002_disciplina (
                codigoDisciplina CHAR(30) NOT NULL,
                nomeDisciplina CHAR(100) NOT NULL,
                codigoCurso CHAR(30) NOT NULL,
                periodo INTEGER NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (codigoDisciplina, codigoCurso, periodo)
            )
        ''')
        
        # Criar índice para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_disciplinas_curso 
            ON imp_002_disciplina(codigoCurso)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_disciplinas_nome 
            ON imp_002_disciplina(nomeDisciplina)
        ''')
        
        # SQL para UPSERT (INSERT OR UPDATE) - chave primária composta
        sql_upsert = '''
            INSERT INTO imp_002_disciplina 
            (codigoDisciplina, nomeDisciplina, codigoCurso, periodo, data_atualizacao)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(codigoDisciplina, codigoCurso, periodo) DO UPDATE SET
                nomeDisciplina = excluded.nomeDisciplina,
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
                    """SELECT codigoDisciplina, codigoCurso, periodo 
                       FROM imp_002_disciplina 
                       WHERE codigoDisciplina = ? 
                         AND codigoCurso = ? 
                         AND periodo = ?""",
                    (registro['codigoDisciplina'], 
                     registro['codigoCurso'], 
                     registro['periodo'])
                )
                
                existe = cursor.fetchone()
                
                # Executar UPSERT
                cursor.execute(sql_upsert, (
                    registro['codigoDisciplina'],
                    registro['nomeDisciplina'],
                    registro['codigoCurso'],
                    registro['periodo']
                ))
                
                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1
                    
            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗  Erro ao importar {registro['codigoDisciplina']} - {registro['codigoCurso']} - {registro['periodo']}: {e}")
        
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
        print("IMPORTAÇÃO: imp_002_disciplina")
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