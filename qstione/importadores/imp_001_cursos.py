"""
Importador para tabela imp_001_cursos
"""

import sqlite3
from qstione.core.transformacoes import (
    converter_inteiro,
    valor_fixo_4000000001,
    truncar_texto
)
from qstione.core.validacoes import (
    validar_codigo_curso,
    validar_nome_curso,
    validar_quant_periodos
)

class ImportadorCursos:
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione
    
    def obter_dados_lyceum(self):
        """
        Obtém dados do banco Lyceum para a tabela imp_001_cursos
        """
        cursor = self.con_lyceum.cursor()
        
        query = """
            SELECT
                c.curso,
                c.nome,
                cr.prazo_ideal
            FROM LY_CURSO c
            INNER JOIN (
                SELECT
                    curso,
                    MAX(curriculo) AS curriculo
                FROM LY_CURRICULO
                GROUP BY curso
            ) mc
                ON mc.curso = c.curso
            INNER JOIN LY_CURRICULO cr
                ON cr.curso = mc.curso
               AND cr.curriculo = mc.curriculo
            WHERE c.ativo = 'S'
              AND c.faculdade IN ('001', '002', '004')
        """
        
        cursor.execute(query)
        return cursor.fetchall()
    
    def transformar_dados(self, dados_lyceum):
        """
        Transforma dados do Lyceum para o formato Qstione
        """
        dados_transformados = []
        
        for registro in dados_lyceum:
            curso, nome, prazo_ideal = registro
            
            # Validar campos obrigatórios usando as funções de validação
            if not validar_codigo_curso(curso):
                print(f"  ⚠️  Código do curso inválido: {curso}")
                continue
                
            if not validar_nome_curso(nome):
                print(f"  ⚠️  Nome do curso inválido: {nome}")
                continue
                
            if not validar_quant_periodos(prazo_ideal):
                print(f"  ⚠️  Quantidade de períodos inválida: {prazo_ideal} para o curso {curso}")
                continue
            
            # Aplicar transformações
            quant_periodos = converter_inteiro(prazo_ideal)
            nome_curso = truncar_texto(nome, 64)
            codigo_unidade = valor_fixo_4000000001(None)
            
            dados_transformados.append({
                'codigoCurso': str(curso)[:30],
                'nomeCurso': nome_curso,
                'quantPeriodos': quant_periodos,
                'codigoUnidadeOrganizacional': codigo_unidade
            })
        
        return dados_transformados
    
    def importar_para_qstione(self, dados_transformados):
        """
        Importa dados para o banco Qstione
        """
        cursor = self.con_qstione.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_001_cursos (
                codigoCurso CHAR(30) NOT NULL,
                nomeCurso CHAR(64) NOT NULL,
                quantPeriodos INTEGER NOT NULL,
                codigoUnidadeOrganizacional CHAR(30) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (codigoCurso)
            )
        ''')
        
        # Criar índice para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cursos_nome 
            ON imp_001_cursos(nomeCurso)
        ''')
        
        # SQL para UPSERT (INSERT OR UPDATE)
        sql_upsert = '''
            INSERT INTO imp_001_cursos 
            (codigoCurso, nomeCurso, quantPeriodos, codigoUnidadeOrganizacional, data_atualizacao)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(codigoCurso) DO UPDATE SET
                nomeCurso = excluded.nomeCurso,
                quantPeriodos = excluded.quantPeriodos,
                codigoUnidadeOrganizacional = excluded.codigoUnidadeOrganizacional,
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
                    "SELECT codigoCurso FROM imp_001_cursos WHERE codigoCurso = ?",
                    (registro['codigoCurso'],)
                )
                
                existe = cursor.fetchone()
                
                # Executar UPSERT
                cursor.execute(sql_upsert, (
                    registro['codigoCurso'],
                    registro['nomeCurso'],
                    registro['quantPeriodos'],
                    registro['codigoUnidadeOrganizacional']
                ))
                
                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1
                    
            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗  Erro ao importar {registro['codigoCurso']}: {e}")
        
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
        print("IMPORTAÇÃO: imp_001_cursos")
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