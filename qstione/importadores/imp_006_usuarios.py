"""
Importador para tabela imp_006_usuarios
"""

import sqlite3
from qstione.core.transformacoes import (
    extrair_usuario_email, 
    converter_minusculas,
    truncar_texto
)
from qstione.core.validacoes import validar_email, validar_matricula, validar_nome

class ImportadorUsuarios:
    def __init__(self, conexao_lyceum, conexao_qstione):
        self.con_lyceum = conexao_lyceum
        self.con_qstione = conexao_qstione
    
    def obter_dados_lyceum(self):
        """
        Obtém dados do banco Lyceum para a tabela imp_006_usuarios
        """
        cursor = self.con_lyceum.cursor()
        
        query = """
            SELECT 
                d.matricula,
                d.email,
                COALESCE(d.nome_social, d.nome_compl) as nome_completo,
                d.cpf
            FROM LY_DOCENTE d
            WHERE d.ativo = 'S'
            GROUP BY d.cpf
            ORDER BY d.matricula
        """
        
        cursor.execute(query)
        return cursor.fetchall()
    
    def transformar_dados(self, dados_lyceum):
        """
        Transforma dados do Lyceum para o formato Qstione
        """
        dados_transformados = []
        
        for registro in dados_lyceum:
            matricula, email, nome, cpf = registro
            
            # Validar campos obrigatórios usando as funções de validação
            if not validar_matricula(matricula):
                print(f"  ⚠️  Matrícula inválida: {matricula}")
                continue
                
            if not validar_email(email):
                print(f"  ⚠️  Email inválido: {email}")
                continue
                
            if not validar_nome(nome):
                print(f"  ⚠️  Nome inválido: {nome}")
                continue
            
            # Aplicar transformações
            email_final = converter_minusculas(email)
            codigo_usuario = extrair_usuario_email(email)
            nome_final = truncar_texto(nome, 64)
            
            dados_transformados.append({
                'matriculaUsuario': str(matricula)[:20],
                'codigoUsuario': codigo_usuario[:24] if codigo_usuario else None,
                'emailUsuario': email_final[:100],
                'nomeUsuario': nome_final
            })
        
        return dados_transformados
    
    def importar_para_qstione(self, dados_transformados):
        """
        Importa dados para o banco Qstione
        """
        cursor = self.con_qstione.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imp_006_usuarios (
                matriculaUsuario CHAR(20) NOT NULL,
                codigoUsuario CHAR(24),
                emailUsuario CHAR(100) NOT NULL,
                nomeUsuario CHAR(64) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (matriculaUsuario)
            )
        ''')
        
        # Criar índice para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_email 
            ON imp_006_usuarios(emailUsuario)
        ''')
        
        # SQL para UPSERT (INSERT OR UPDATE)
        sql_upsert = '''
            INSERT INTO imp_006_usuarios 
            (matriculaUsuario, codigoUsuario, emailUsuario, nomeUsuario, data_atualizacao)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(matriculaUsuario) DO UPDATE SET
                codigoUsuario = excluded.codigoUsuario,
                emailUsuario = excluded.emailUsuario,
                nomeUsuario = excluded.nomeUsuario,
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
                    "SELECT matriculaUsuario FROM imp_006_usuarios WHERE matriculaUsuario = ?",
                    (registro['matriculaUsuario'],)
                )
                
                existe = cursor.fetchone()
                
                # Executar UPSERT
                cursor.execute(sql_upsert, (
                    registro['matriculaUsuario'],
                    registro['codigoUsuario'],
                    registro['emailUsuario'],
                    registro['nomeUsuario']
                ))
                
                if existe:
                    total_atualizados += 1
                else:
                    total_inseridos += 1
                    
            except sqlite3.Error as e:
                total_erros += 1
                print(f"  ✗  Erro ao importar {registro['matriculaUsuario']}: {e}")
        
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
        print("IMPORTAÇÃO: imp_006_usuarios")
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