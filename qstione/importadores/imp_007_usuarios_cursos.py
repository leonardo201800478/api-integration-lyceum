"""
Importador para tabela imp_007_usuarios_cursos
"""

import sqlite3
from qstione.core.transformacoes import (
    converter_minusculas,
    determinar_papel_usuario
)
from qstione.core.validacoes import (
    validar_codigo_curso,
    validar_email,
    validar_papel_usuario
)

class ImportadorUsuariosCursos:
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione
    
    def obter_coordenadores(self):
        """
        Obtém a lista de coordenadores da tabela LY_COORDENACAO
        Retorna um dicionário onde a chave é (num_func, curso)
        """
        cursor = self.con_lyceum.cursor()
        
        query = """
            SELECT DISTINCT num_func, curso
            FROM LY_COORDENACAO
        """
        
        cursor.execute(query)
        coordenadores = {}
        
        for row in cursor.fetchall():
            num_func, curso = row
            chave = (str(num_func), str(curso))
            coordenadores[chave] = True
        
        print(f"📋 Coordenadores encontrados: {len(coordenadores)}")
        return coordenadores
    
    def obter_dados_lyceum(self):
        """
        Obtém dados do banco Lyceum para a tabela imp_007_usuarios_cursos
        Seguindo a lógica especificada
        """
        cursor = self.con_lyceum.cursor()
        
        # 1. Primeiro obter coordenadores
        coordenadores = self.obter_coordenadores()
        
        # 2. Obter dados principais
        query = """
            SELECT DISTINCT
                td.num_func,
                td.disciplina,
                d.email,
                g.curso
            FROM LY_TURMA_DOCENTE td
            -- Relacionar com LY_GRADE para obter o curso da disciplina
            INNER JOIN LY_GRADE g
                ON g.disciplina = td.disciplina
            -- Relacionar com LY_DOCENTE para obter o email
            INNER JOIN LY_DOCENTE d
                ON d.num_func = td.num_func
            WHERE td.ano = 2026
              AND td.periodo = '21'
              AND d.ativo = 'S'
            ORDER BY td.num_func, g.curso
        """
        
        cursor.execute(query)
        return cursor.fetchall(), coordenadores
    
    def transformar_dados(self, dados_lyceum, coordenadores):
        """
        Transforma dados do Lyceum para o formato Qstione
        """
        dados_transformados = []
        
        for registro in dados_lyceum:
            num_func, disciplina, email, curso = registro
            
            # Validar campos obrigatórios
            if not validar_codigo_curso(curso):
                print(f"  ⚠️  Código do curso inválido: {curso} para docente {num_func}")
                continue
                
            if not validar_email(email):
                print(f"  ⚠️  Email inválido: {email} para docente {num_func}")
                continue
            
            # Aplicar transformações
            email_final = converter_minusculas(email)
            
            # Determinar papel do usuário
            papel = determinar_papel_usuario(num_func, curso, coordenadores)
            
            if not validar_papel_usuario(papel):
                print(f"  ⚠️  Papel do usuário inválido: {papel} para docente {num_func}")
                continue
            
            dados_transformados.append({
                'codigoCurso': str(curso)[:30],
                'emailUsuario': email_final[:100],
                'papelUsuario': papel
            })
        
        return dados_transformados
    
    def importar_para_qstione(self, dados_transformados):
        """
        Importa dados para o banco Qstione
        """
        cursor = self.con_qstione.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_007_usuarios_cursos (
                codigoCurso CHAR(30) NOT NULL,
                emailUsuario CHAR(100) NOT NULL,
                papelUsuario CHAR(1) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (codigoCurso, emailUsuario)
            )
        ''')
        
        # Criar índice para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_cursos_email 
            ON imp_007_usuarios_cursos(emailUsuario)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_cursos_curso 
            ON imp_007_usuarios_cursos(codigoCurso)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_cursos_papel 
            ON imp_007_usuarios_cursos(papelUsuario)
        ''')
        
        # SQL para UPSERT (INSERT OR UPDATE) - chave primária composta
        sql_upsert = '''
            INSERT INTO imp_007_usuarios_cursos 
            (codigoCurso, emailUsuario, papelUsuario, data_atualizacao)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(codigoCurso, emailUsuario) DO UPDATE SET
                papelUsuario = excluded.papelUsuario,
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
                    """SELECT codigoCurso, emailUsuario 
                       FROM imp_007_usuarios_cursos 
                       WHERE codigoCurso = ? 
                         AND emailUsuario = ?""",
                    (registro['codigoCurso'], 
                     registro['emailUsuario'])
                )
                
                existe = cursor.fetchone()
                
                # Executar UPSERT
                cursor.execute(sql_upsert, (
                    registro['codigoCurso'],
                    registro['emailUsuario'],
                    registro['papelUsuario']
                ))
                
                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1
                    
            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗  Erro ao importar {registro['codigoCurso']} - {registro['emailUsuario']}: {e}")
        
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
        print("IMPORTAÇÃO: imp_007_usuarios_cursos")
        print("=" * 70)
        
        # 1. Obter dados do Lyceum
        print("📋 Obtendo dados do Lyceum...")
        dados_lyceum, coordenadores = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum: {len(dados_lyceum)}")
        
        # 2. Transformar dados
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum, coordenadores)
        print(f"✅ Registros válidos para importação: {len(dados_transformados)}")
        
        # 3. Importar para Qstione
        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)
        
        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")
        
        # Estatísticas de papéis
        coordenadores_count = sum(1 for reg in dados_transformados if reg['papelUsuario'] == 1)
        professores_count = sum(1 for reg in dados_transformados if reg['papelUsuario'] == 2)
        
        print(f"\n👥 DISTRIBUIÇÃO DE PAPÉIS:")
        print(f"  👑 Coordenadores (C): {coordenadores_count}")
        print(f"  👨‍🏫 Professores (P): {professores_count}")
        
        return dados_transformados