# qstione/importadores/imp_nde.py
import os
import sys
import pandas as pd

# Adiciona a raiz do projeto (ALUNO-SYNC) ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.database import get_db_connection
from qstione.core.transformacoes import truncar_texto
from qstione.core.validacoes import validar_codigo_curso, validar_nome_curso


class ImportadorNDE:
    def __init__(self, caminho_excel="qstione/nde/nde.xlsx"):
        self.caminho_excel = caminho_excel

    # -------------------- Helpers para tabelas/índices --------------------
    def _tabela_existe(self, nome_tabela: str) -> bool:
        try:
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
                """, (nome_tabela,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar tabela {nome_tabela}: {e}")
            return False

    def _indice_existe(self, nome_indice: str, nome_tabela: str = None) -> bool:
        try:
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                if nome_tabela:
                    cursor.execute(
                        "SELECT 1 FROM sys.indexes WHERE name = ? AND object_id = OBJECT_ID(?)",
                        (nome_indice, nome_tabela)
                    )
                else:
                    cursor.execute("SELECT 1 FROM sys.indexes WHERE name = ?", (nome_indice,))
                return cursor.fetchone() is not None
        except Exception:
            return False

    # -------------------- Criação das tabelas --------------------
    def _criar_tabelas(self):
        if not self._tabela_existe('imp_nde_cursos'):
            print("🆕 Criando tabela imp_nde_cursos...")
            create_cursos = """
                CREATE TABLE imp_nde_cursos (
                    codigoCurso NVARCHAR(30) NOT NULL,
                    nomeCurso NVARCHAR(64) NOT NULL,
                    coordenador NVARCHAR(100) NOT NULL,
                    emailCoordenador NVARCHAR(100) NULL,
                    data_criacao DATETIME2 DEFAULT GETDATE(),
                    data_atualizacao DATETIME2 DEFAULT GETDATE(),
                    PRIMARY KEY (codigoCurso)
                )
            """
            with get_db_connection(database_name='qstione') as conn:
                conn.execute(create_cursos)
                conn.commit()
            print("✅ Tabela imp_nde_cursos criada.")
        else:
            print("✅ Tabela imp_nde_cursos já existe.")

        if not self._tabela_existe('imp_nde_membros'):
            print("🆕 Criando tabela imp_nde_membros...")
            create_membros = """
                CREATE TABLE imp_nde_membros (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    codigoCurso NVARCHAR(30) NOT NULL,
                    nomeMembro NVARCHAR(100) NOT NULL,
                    emailMembro NVARCHAR(100) NULL,
                    data_criacao DATETIME2 DEFAULT GETDATE(),
                    data_atualizacao DATETIME2 DEFAULT GETDATE(),
                    CONSTRAINT fk_membros_cursos FOREIGN KEY (codigoCurso)
                        REFERENCES imp_nde_cursos(codigoCurso)
                        ON DELETE CASCADE
                )
            """
            with get_db_connection(database_name='qstione') as conn:
                conn.execute(create_membros)
                conn.commit()
            print("✅ Tabela imp_nde_membros criada.")
        else:
            print("✅ Tabela imp_nde_membros já existe.")

        # Índices
        if not self._indice_existe('idx_nde_cursos_nome', 'imp_nde_cursos'):
            with get_db_connection(database_name='qstione') as conn:
                conn.execute("CREATE INDEX idx_nde_cursos_nome ON imp_nde_cursos(nomeCurso)")
                conn.commit()
            print("✅ Índice idx_nde_cursos_nome criado.")

        if not self._indice_existe('idx_nde_membros_curso', 'imp_nde_membros'):
            with get_db_connection(database_name='qstione') as conn:
                conn.execute("CREATE INDEX idx_nde_membros_curso ON imp_nde_membros(codigoCurso)")
                conn.commit()
            print("✅ Índice idx_nde_membros_curso criado.")

    # -------------------- Leitura do Excel --------------------
    def obter_dados_excel(self):
        if not os.path.exists(self.caminho_excel):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho_excel}")

        df = pd.read_excel(self.caminho_excel, sheet_name='Planilha1', dtype=str)
        df = df.where(pd.notnull(df), None)
        df.columns = ['codigoCurso', 'nomeCurso', 'Coordenador', 'emailCoordenador',
                      'nomeMembro', 'emailMembro']
        return df

    # -------------------- Transformação --------------------
    def transformar_dados(self, df):
        # Função auxiliar para limpar valores
        def limpar_texto(valor):
            if pd.isna(valor) or valor is None:
                return None
            return str(valor).strip()

        # 1. Agrupar cursos únicos
        cursos_unicos = {}
        membros_brutos = []  # lista temporária com chave = nome_curso (ou código)

        for _, row in df.iterrows():
            codigo = limpar_texto(row['codigoCurso'])
            nome = limpar_texto(row['nomeCurso'])
            if not nome:
                continue

            coord_nome = limpar_texto(row['Coordenador'])
            coord_email = limpar_texto(row['emailCoordenador'])
            membro_nome = limpar_texto(row['nomeMembro'])
            membro_email = limpar_texto(row['emailMembro'])

            # Chave: se tem código, usa código; senão usa nome
            chave = codigo if codigo else nome

            # Inicializa curso se não existir
            if chave not in cursos_unicos:
                cursos_unicos[chave] = {
                    'codigoCurso': codigo,
                    'nomeCurso': nome,
                    'coordenador': coord_nome or '',
                    'emailCoordenador': coord_email
                }
            else:
                # Atualiza coordenador se ainda não tiver
                if coord_nome and not cursos_unicos[chave]['coordenador']:
                    cursos_unicos[chave]['coordenador'] = coord_nome
                if coord_email and not cursos_unicos[chave]['emailCoordenador']:
                    cursos_unicos[chave]['emailCoordenador'] = coord_email

            # Coleta membro (se houver)
            if membro_nome:
                membros_brutos.append({
                    'chave_curso': chave,
                    'nomeMembro': truncar_texto(membro_nome, 100),
                    'emailMembro': truncar_texto(membro_email, 100) if membro_email else None
                })

        # 2. Gerar códigos para cursos que não têm
        used_codes = set()
        for chave, curso in cursos_unicos.items():
            if curso['codigoCurso']:
                codigo = curso['codigoCurso']
                # Garantir unicidade (caso raro)
                if codigo in used_codes:
                    i = 1
                    while f"{codigo}_{i}" in used_codes:
                        i += 1
                    codigo = f"{codigo}_{i}"
                used_codes.add(codigo)
                curso['codigoCurso'] = codigo
            else:
                # Gerar a partir do nome
                nome = curso['nomeCurso']
                if not nome:
                    continue
                # Pega as iniciais (3 primeiras letras de cada palavra)
                iniciais = ''.join([p[0] for p in nome.split() if p])[:3].upper()
                if not iniciais:
                    iniciais = 'XXX'
                base = iniciais
                if base not in used_codes:
                    codigo = base
                else:
                    i = 1
                    while f"{base}{i:02d}" in used_codes:
                        i += 1
                    codigo = f"{base}{i:02d}"
                used_codes.add(codigo)
                curso['codigoCurso'] = codigo

        # 3. Mapear chave -> código final
        chave_para_codigo = {}
        for chave, curso in cursos_unicos.items():
            chave_para_codigo[chave] = curso['codigoCurso']

        # 4. Converter membros_brutos para usar código do curso
        membros_final = []
        for m in membros_brutos:
            codigo_curso = chave_para_codigo.get(m['chave_curso'])
            if not codigo_curso:
                continue
            membros_final.append({
                'codigoCurso': codigo_curso,
                'nomeMembro': m['nomeMembro'],
                'emailMembro': m['emailMembro']
            })

        # 5. Remover membros duplicados
        membros_unicos = []
        seen = set()
        for m in membros_final:
            chave = (m['codigoCurso'], m['nomeMembro'], m['emailMembro'])
            if chave not in seen:
                seen.add(chave)
                membros_unicos.append(m)

        # 6. Cursos finais (validação e truncamento)
        cursos_final = []
        for curso in cursos_unicos.values():
            codigo = curso['codigoCurso']
            nome = truncar_texto(curso['nomeCurso'], 64)
            coord = truncar_texto(curso['coordenador'], 100) if curso['coordenador'] else ''
            email_coord = truncar_texto(curso['emailCoordenador'], 100) if curso['emailCoordenador'] else None

            if not validar_codigo_curso(codigo):
                print(f"  ⚠️  Código inválido: {codigo} (nome: {nome})")
                continue
            if not validar_nome_curso(nome):
                print(f"  ⚠️  Nome inválido: {nome}")
                continue

            cursos_final.append({
                'codigoCurso': codigo,
                'nomeCurso': nome,
                'coordenador': coord,
                'emailCoordenador': email_coord
            })

        return cursos_final, membros_unicos

    # -------------------- Importação para o Qstione --------------------
    def importar_para_qstione(self, cursos_data, membros_data):
        self._criar_tabelas()

        merge_cursos = """
            MERGE INTO imp_nde_cursos AS target
            USING (VALUES (?, ?, ?, ?)) AS source (codigoCurso, nomeCurso, coordenador, emailCoordenador)
            ON target.codigoCurso = source.codigoCurso
            WHEN MATCHED THEN
                UPDATE SET
                    nomeCurso = source.nomeCurso,
                    coordenador = source.coordenador,
                    emailCoordenador = source.emailCoordenador,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoCurso, nomeCurso, coordenador, emailCoordenador, data_criacao, data_atualizacao)
                VALUES (source.codigoCurso, source.nomeCurso, source.coordenador, source.emailCoordenador, GETDATE(), GETDATE());
        """

        merge_membros = """
            MERGE INTO imp_nde_membros AS target
            USING (VALUES (?, ?, ?)) AS source (codigoCurso, nomeMembro, emailMembro)
            ON target.codigoCurso = source.codigoCurso
               AND target.nomeMembro = source.nomeMembro
               AND (target.emailMembro = source.emailMembro OR (target.emailMembro IS NULL AND source.emailMembro IS NULL))
            WHEN MATCHED THEN
                UPDATE SET
                    emailMembro = source.emailMembro,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoCurso, nomeMembro, emailMembro, data_criacao, data_atualizacao)
                VALUES (source.codigoCurso, source.nomeMembro, source.emailMembro, GETDATE(), GETDATE());
        """

        total_inseridos_cursos = 0
        total_atualizados_cursos = 0
        total_inseridos_membros = 0
        total_atualizados_membros = 0
        total_erros = 0

        with get_db_connection(database_name='qstione') as conn:
            cursor = conn.cursor()

            # ----- CURSOS -----
            for curso in cursos_data:
                try:
                    cursor.execute("SELECT codigoCurso FROM imp_nde_cursos WHERE codigoCurso = ?", (curso['codigoCurso'],))
                    existe = cursor.fetchone() is not None
                    cursor.execute(merge_cursos, (
                        curso['codigoCurso'],
                        curso['nomeCurso'],
                        curso['coordenador'],
                        curso['emailCoordenador']
                    ))
                    if existe:
                        total_atualizados_cursos += 1
                    else:
                        total_inseridos_cursos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗  Erro ao importar curso {curso['codigoCurso']}: {e}")

            conn.commit()

            # ----- MEMBROS (apenas se o curso existir) -----
            cursos_existentes = set()
            cursor.execute("SELECT codigoCurso FROM imp_nde_cursos")
            for row in cursor.fetchall():
                cursos_existentes.add(row[0])

            for membro in membros_data:
                if membro['codigoCurso'] not in cursos_existentes:
                    print(f"  ⚠️  Curso {membro['codigoCurso']} não encontrado. Membro ignorado: {membro['nomeMembro']}")
                    continue

                try:
                    cursor.execute("""
                        SELECT id FROM imp_nde_membros
                        WHERE codigoCurso = ? AND nomeMembro = ? AND (emailMembro = ? OR (emailMembro IS NULL AND ? IS NULL))
                    """, (membro['codigoCurso'], membro['nomeMembro'], membro['emailMembro'], membro['emailMembro']))
                    existe = cursor.fetchone() is not None
                    cursor.execute(merge_membros, (
                        membro['codigoCurso'],
                        membro['nomeMembro'],
                        membro['emailMembro']
                    ))
                    if existe:
                        total_atualizados_membros += 1
                    else:
                        total_inseridos_membros += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗  Erro ao importar membro {membro['nomeMembro']} do curso {membro['codigoCurso']}: {e}")

            conn.commit()

        return {
            'total_inseridos_cursos': total_inseridos_cursos,
            'total_atualizados_cursos': total_atualizados_cursos,
            'total_inseridos_membros': total_inseridos_membros,
            'total_atualizados_membros': total_atualizados_membros,
            'total_erros': total_erros,
            'total_cursos': len(cursos_data),
            'total_membros': len(membros_data)
        }

    # -------------------- Execução --------------------
    def executar_importacao(self):
        print("=" * 70)
        print("IMPORTAÇÃO: imp_nde")
        print("=" * 70)

        try:
            df = self.obter_dados_excel()
            print(f"📊 Registros lidos do Excel: {len(df)}")
        except Exception as e:
            print(f"❌ Erro ao ler o arquivo Excel: {e}")
            return

        print("🔄 Transformando dados...")
        cursos_data, membros_data = self.transformar_dados(df)
        print(f"✅ Cursos identificados: {len(cursos_data)}")
        print(f"✅ Membros identificados (após remoção de duplicatas): {len(membros_data)}")

        print("💾 Importando para Qstione...")
        resultado = self.importar_para_qstione(cursos_data, membros_data)

        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  Cursos:")
        print(f"    ✓ Inseridos: {resultado['total_inseridos_cursos']}")
        print(f"    ↻ Atualizados: {resultado['total_atualizados_cursos']}")
        print(f"  Membros:")
        print(f"    ✓ Inseridos: {resultado['total_inseridos_membros']}")
        print(f"    ↻ Atualizados: {resultado['total_atualizados_membros']}")
        print(f"  ✗ Erros totais: {resultado['total_erros']}")
        print(f"  📋 Total de cursos processados: {resultado['total_cursos']}")
        print(f"  📋 Total de membros processados: {resultado['total_membros']}")

        return cursos_data, membros_data


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorNDE()
    importador.executar_importacao()