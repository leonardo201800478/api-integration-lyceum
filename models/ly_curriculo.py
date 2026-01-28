#!/usr/bin/env python3
"""
Modelo para tabela LY_CURRICULOS - Tabela completa de currículos do Lyceum
"""
from core.database import execute_query, fetch_all, fetch_one, get_db_connection
from typing import List, Dict, Optional
import sqlite3

class LyCurriculoModel:
    """Modelo para tabela LY_CURRICULOS"""
    
    TABLE_NAME = "ly_curriculos"
    
    @classmethod
    def create_table(cls, db_name="dados_unifoa.db"):
        """Cria a tabela LY_CURRICULOS com todos os campos da API"""
        query = f'''
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Campos principais
            curriculo TEXT(30) NOT NULL,
            curso TEXT(30) NOT NULL,
            turno TEXT(10),
            prazo_ideal REAL,
            prazo_max REAL,
            ano_ini INTEGER,
            sem_ini INTEGER,
            regime TEXT(20),
            aulas_previstas REAL,
            creditos REAL,
            
            -- Informações de situação e datas
            situacao TEXT(20),
            stamp_atualizacao TEXT,
            dt_homolog TEXT,
            dt_extincao TEXT,
            
            -- Informações acadêmicas
            modalidade TEXT(50),
            servico TEXT(50),
            valor TEXT(50),
            codigo_secundario TEXT(50),
            nome_secundario TEXT(100),
            classificacao TEXT(50),
            habilinep TEXT(10),
            pesquisa TEXT(10),
            tese_dissertacao TEXT(10),
            tipo_prazo_concl TEXT(10),
            tipo_prazo_orien TEXT(10),
            prazo_conc_prev INTEGER,
            prazo_desig_orien INTEGER,
            prazo_max_adap INTEGER,
            unid_prazo_max_adap TEXT(10),
            retem_serie INTEGER,
            serie_max_orient INTEGER,
            ativ_compl_ch INTEGER,
            ativ_compl_creditos INTEGER,
            perc_ch_pres REAL,
            perc_ch_semi_pres REAL,
            perc_ch_nao_pres REAL,
            ver_ch_integracao TEXT(10),
            ver_cred_integracao TEXT(10),
            max_alunos INTEGER,
            min_alunos INTEGER,
            num_disc_atras_prog INTEGER,
            
            -- Informações de trancamento e cancelamento
            tranc_max INTEGER,
            tranc_cons_max INTEGER,
            tranc_max_discip INTEGER,
            canc_max_discip INTEGER,
            atlz_max_discip INTEGER,
            n_max_dias_tranc INTEGER,
            tranc_interv_data TEXT(10),
            tranca_primeiro_periodo TEXT(10),
            excecao_trancamento TEXT(100),
            permite_cancelamento TEXT(10),
            
            -- Informações de matrícula
            credmin_matr INTEGER,
            credmin_foragrade INTEGER,
            credmax_foragrade INTEGER,
            ratear_mens TEXT(10),
            ratear_desc TEXT(10),
            matr_obrig_todas_discip_serie TEXT(10),
            restringe_unid_fis TEXT(10),
            
            -- Observações e informações complementares
            obs TEXT,
            indice TEXT(10),
            colecao_livros TEXT(50),
            
            -- Campos de empresa/instituição
            emp_cnpj TEXT(20),
            emp_endereco TEXT(100),
            emp_end_num TEXT(10),
            emp_end_compl TEXT(50),
            emp_bairro TEXT(50),
            emp_cep TEXT(10),
            emp_municipio TEXT(50),
            emp_fone TEXT(20),
            emp_contato TEXT(50),
            
            -- Campos flag
            fl_field01 TEXT(10),
            fl_field02 TEXT(10),
            fl_field03 TEXT(10),
            fl_field04 TEXT(10),
            fl_field05 TEXT(10),
            fl_field06 TEXT(10),
            fl_field07 TEXT(10),
            fl_field08 TEXT(10),
            fl_field09 TEXT(10),
            fl_field10 TEXT(10),
            
            -- Metadados da importação
            data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(curriculo, curso)
        )
        '''
        
        execute_query(query, db_name=db_name)
        
        # Criar índices para melhor performance
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_curriculo ON {cls.TABLE_NAME}(curriculo)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_curso ON {cls.TABLE_NAME}(curso)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_turno ON {cls.TABLE_NAME}(turno)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_prazo_ideal ON {cls.TABLE_NAME}(prazo_ideal)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_prazo_max ON {cls.TABLE_NAME}(prazo_max)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_situacao ON {cls.TABLE_NAME}(situacao)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_curso_curriculo ON {cls.TABLE_NAME}(curso, curriculo)"
        ]
        
        for index_query in indexes:
            execute_query(index_query, db_name=db_name)
        
        print(f"✅ Tabela {cls.TABLE_NAME} criada/verificada")
    
    @classmethod
    def insert_curriculo(cls, curriculo_data: dict, db_name="dados_unifoa.db"):
        """Insere um novo currículo"""
        query = f'''
        INSERT OR REPLACE INTO {cls.TABLE_NAME} 
        (
            curriculo, curso, turno, prazo_ideal, prazo_max, ano_ini, sem_ini, regime,
            aulas_previstas, creditos, situacao, stamp_atualizacao, dt_homolog, dt_extincao,
            modalidade, servico, valor, codigo_secundario, nome_secundario, classificacao,
            habilinep, pesquisa, tese_dissertacao, tipo_prazo_concl, tipo_prazo_orien,
            prazo_conc_prev, prazo_desig_orien, prazo_max_adap, unid_prazo_max_adap,
            retem_serie, serie_max_orient, ativ_compl_ch, ativ_compl_creditos, perc_ch_pres,
            perc_ch_semi_pres, perc_ch_nao_pres, ver_ch_integracao, ver_cred_integracao,
            max_alunos, min_alunos, num_disc_atras_prog, tranc_max, tranc_cons_max,
            tranc_max_discip, canc_max_discip, atlz_max_discip, n_max_dias_tranc,
            tranc_interv_data, tranca_primeiro_periodo, excecao_trancamento,
            permite_cancelamento, credmin_matr, credmin_foragrade, credmax_foragrade,
            ratear_mens, ratear_desc, matr_obrig_todas_discip_serie, restringe_unid_fis,
            obs, emp_cnpj, emp_endereco, emp_end_num, emp_end_compl, emp_bairro,
            emp_cep, emp_municipio, emp_fone, emp_contato, indice, colecao_livros,
            fl_field01, fl_field02, fl_field03, fl_field04, fl_field05,
            fl_field06, fl_field07, fl_field08, fl_field09, fl_field10
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        '''
        
        params = (
            curriculo_data.get('curriculo'),
            curriculo_data.get('curso'),
            curriculo_data.get('turno'),
            curriculo_data.get('prazo_ideal'),
            curriculo_data.get('prazo_max'),
            curriculo_data.get('ano_ini'),
            curriculo_data.get('sem_ini'),
            curriculo_data.get('regime'),
            curriculo_data.get('aulas_previstas'),
            curriculo_data.get('creditos'),
            curriculo_data.get('situacao'),
            curriculo_data.get('stamp_atualizacao'),
            curriculo_data.get('dt_homolog'),
            curriculo_data.get('dt_extincao'),
            curriculo_data.get('modalidade'),
            curriculo_data.get('servico'),
            curriculo_data.get('valor'),
            curriculo_data.get('codigo_secundario'),
            curriculo_data.get('nome_secundario'),
            curriculo_data.get('classificacao'),
            curriculo_data.get('habilinep'),
            curriculo_data.get('pesquisa'),
            curriculo_data.get('tese_dissertacao'),
            curriculo_data.get('tipo_prazo_concl'),
            curriculo_data.get('tipo_prazo_orien'),
            curriculo_data.get('prazo_conc_prev'),
            curriculo_data.get('prazo_desig_orien'),
            curriculo_data.get('prazo_max_adap'),
            curriculo_data.get('unid_prazo_max_adap'),
            curriculo_data.get('retem_serie'),
            curriculo_data.get('serie_max_orient'),
            curriculo_data.get('ativ_compl_ch'),
            curriculo_data.get('ativ_compl_creditos'),
            curriculo_data.get('perc_ch_pres'),
            curriculo_data.get('perc_ch_semi_pres'),
            curriculo_data.get('perc_ch_nao_pres'),
            curriculo_data.get('ver_ch_integracao'),
            curriculo_data.get('ver_cred_integracao'),
            curriculo_data.get('max_alunos'),
            curriculo_data.get('min_alunos'),
            curriculo_data.get('num_disc_atras_prog'),
            curriculo_data.get('tranc_max'),
            curriculo_data.get('tranc_cons_max'),
            curriculo_data.get('tranc_max_discip'),
            curriculo_data.get('canc_max_discip'),
            curriculo_data.get('atlz_max_discip'),
            curriculo_data.get('n_max_dias_tranc'),
            curriculo_data.get('tranc_interv_data'),
            curriculo_data.get('tranca_primeiro_periodo'),
            curriculo_data.get('excecao_trancamento'),
            curriculo_data.get('permite_cancelamento'),
            curriculo_data.get('credmin_matr'),
            curriculo_data.get('credmin_foragrade'),
            curriculo_data.get('credmax_foragrade'),
            curriculo_data.get('ratear_mens'),
            curriculo_data.get('ratear_desc'),
            curriculo_data.get('matr_obrig_todas_discip_serie'),
            curriculo_data.get('restringe_unid_fis'),
            curriculo_data.get('obs'),
            curriculo_data.get('emp_cnpj'),
            curriculo_data.get('emp_endereco'),
            curriculo_data.get('emp_end_num'),
            curriculo_data.get('emp_end_compl'),
            curriculo_data.get('emp_bairro'),
            curriculo_data.get('emp_cep'),
            curriculo_data.get('emp_municipio'),
            curriculo_data.get('emp_fone'),
            curriculo_data.get('emp_contato'),
            curriculo_data.get('indice'),
            curriculo_data.get('colecao_livros'),
            curriculo_data.get('fl_field01'),
            curriculo_data.get('fl_field02'),
            curriculo_data.get('fl_field03'),
            curriculo_data.get('fl_field04'),
            curriculo_data.get('fl_field05'),
            curriculo_data.get('fl_field06'),
            curriculo_data.get('fl_field07'),
            curriculo_data.get('fl_field08'),
            curriculo_data.get('fl_field09'),
            curriculo_data.get('fl_field10')
        )
        
        execute_query(query, params, db_name=db_name)
    
    @classmethod
    def insert_batch(cls, curriculos: List[Dict], db_name="dados_unifoa.db"):
        """Insere múltiplos currículos de uma vez"""
        saved_count = 0
        
        with get_db_connection(db_name) as conn:
            cursor = conn.cursor()
            
            query = f'''
            INSERT OR REPLACE INTO {cls.TABLE_NAME} 
            (
                curriculo, curso, turno, prazo_ideal, prazo_max, ano_ini, sem_ini, regime,
                aulas_previstas, creditos, situacao, stamp_atualizacao, dt_homolog, dt_extincao,
                modalidade, servico, valor, codigo_secundario, nome_secundario, classificacao,
                habilinep, pesquisa, tese_dissertacao, tipo_prazo_concl, tipo_prazo_orien,
                prazo_conc_prev, prazo_desig_orien, prazo_max_adap, unid_prazo_max_adap,
                retem_serie, serie_max_orient, ativ_compl_ch, ativ_compl_creditos, perc_ch_pres,
                perc_ch_semi_pres, perc_ch_nao_pres, ver_ch_integracao, ver_cred_integracao,
                max_alunos, min_alunos, num_disc_atras_prog, tranc_max, tranc_cons_max,
                tranc_max_discip, canc_max_discip, atlz_max_discip, n_max_dias_tranc,
                tranc_interv_data, tranca_primeiro_periodo, excecao_trancamento,
                permite_cancelamento, credmin_matr, credmin_foragrade, credmax_foragrade,
                ratear_mens, ratear_desc, matr_obrig_todas_discip_serie, restringe_unid_fis,
                obs, emp_cnpj, emp_endereco, emp_end_num, emp_end_compl, emp_bairro,
                emp_cep, emp_municipio, emp_fone, emp_contato, indice, colecao_livros,
                fl_field01, fl_field02, fl_field03, fl_field04, fl_field05,
                fl_field06, fl_field07, fl_field08, fl_field09, fl_field10
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            '''
            
            for curriculo in curriculos:
                try:
                    params = (
                        curriculo.get('curriculo'),
                        curriculo.get('curso'),
                        curriculo.get('turno'),
                        curriculo.get('prazo_ideal'),
                        curriculo.get('prazo_max'),
                        curriculo.get('ano_ini'),
                        curriculo.get('sem_ini'),
                        curriculo.get('regime'),
                        curriculo.get('aulas_previstas'),
                        curriculo.get('creditos'),
                        curriculo.get('situacao'),
                        curriculo.get('stamp_atualizacao'),
                        curriculo.get('dt_homolog'),
                        curriculo.get('dt_extincao'),
                        curriculo.get('modalidade'),
                        curriculo.get('servico'),
                        curriculo.get('valor'),
                        curriculo.get('codigo_secundario'),
                        curriculo.get('nome_secundario'),
                        curriculo.get('classificacao'),
                        curriculo.get('habilinep'),
                        curriculo.get('pesquisa'),
                        curriculo.get('tese_dissertacao'),
                        curriculo.get('tipo_prazo_concl'),
                        curriculo.get('tipo_prazo_orien'),
                        curriculo.get('prazo_conc_prev'),
                        curriculo.get('prazo_desig_orien'),
                        curriculo.get('prazo_max_adap'),
                        curriculo.get('unid_prazo_max_adap'),
                        curriculo.get('retem_serie'),
                        curriculo.get('serie_max_orient'),
                        curriculo.get('ativ_compl_ch'),
                        curriculo.get('ativ_compl_creditos'),
                        curriculo.get('perc_ch_pres'),
                        curriculo.get('perc_ch_semi_pres'),
                        curriculo.get('perc_ch_nao_pres'),
                        curriculo.get('ver_ch_integracao'),
                        curriculo.get('ver_cred_integracao'),
                        curriculo.get('max_alunos'),
                        curriculo.get('min_alunos'),
                        curriculo.get('num_disc_atras_prog'),
                        curriculo.get('tranc_max'),
                        curriculo.get('tranc_cons_max'),
                        curriculo.get('tranc_max_discip'),
                        curriculo.get('canc_max_discip'),
                        curriculo.get('atlz_max_discip'),
                        curriculo.get('n_max_dias_tranc'),
                        curriculo.get('tranc_interv_data'),
                        curriculo.get('tranca_primeiro_periodo'),
                        curriculo.get('excecao_trancamento'),
                        curriculo.get('permite_cancelamento'),
                        curriculo.get('credmin_matr'),
                        curriculo.get('credmin_foragrade'),
                        curriculo.get('credmax_foragrade'),
                        curriculo.get('ratear_mens'),
                        curriculo.get('ratear_desc'),
                        curriculo.get('matr_obrig_todas_discip_serie'),
                        curriculo.get('restringe_unid_fis'),
                        curriculo.get('obs'),
                        curriculo.get('emp_cnpj'),
                        curriculo.get('emp_endereco'),
                        curriculo.get('emp_end_num'),
                        curriculo.get('emp_end_compl'),
                        curriculo.get('emp_bairro'),
                        curriculo.get('emp_cep'),
                        curriculo.get('emp_municipio'),
                        curriculo.get('emp_fone'),
                        curriculo.get('emp_contato'),
                        curriculo.get('indice'),
                        curriculo.get('colecao_livros'),
                        curriculo.get('fl_field01'),
                        curriculo.get('fl_field02'),
                        curriculo.get('fl_field03'),
                        curriculo.get('fl_field04'),
                        curriculo.get('fl_field05'),
                        curriculo.get('fl_field06'),
                        curriculo.get('fl_field07'),
                        curriculo.get('fl_field08'),
                        curriculo.get('fl_field09'),
                        curriculo.get('fl_field10')
                    )
                    
                    cursor.execute(query, params)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Erro ao salvar currículo {curriculo.get('curriculo')}: {e}")
            
            conn.commit()
        
        return saved_count
    
    @classmethod
    def get_summary(cls, db_name="dados_unifoa.db"):
        """Obtém resumo dos dados"""
        with get_db_connection(db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {cls.TABLE_NAME}")
            total = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(DISTINCT curso) FROM {cls.TABLE_NAME}")
            cursos_distintos = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(DISTINCT turno) FROM {cls.TABLE_NAME}")
            turnos_distintos = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(DISTINCT situacao) FROM {cls.TABLE_NAME}")
            situacoes_distintas = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT AVG(prazo_ideal) FROM {cls.TABLE_NAME} WHERE prazo_ideal IS NOT NULL")
            avg_prazo_ideal = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT AVG(prazo_max) FROM {cls.TABLE_NAME} WHERE prazo_max IS NOT NULL")
            avg_prazo_max = cursor.fetchone()[0]
            
            return {
                "total_curriculos": total,
                "cursos_distintos": cursos_distintos,
                "turnos_distintos": turnos_distintos,
                "situacoes_distintas": situacoes_distintas,
                "media_prazo_ideal": round(avg_prazo_ideal, 2) if avg_prazo_ideal else 0,
                "media_prazo_max": round(avg_prazo_max, 2) if avg_prazo_max else 0
            }
    
    @classmethod
    def get_curriculos_por_curso(cls, curso: str, db_name="dados_unifoa.db"):
        """Busca currículos por curso"""
        query = f'''
        SELECT curriculo, turno, prazo_ideal, prazo_max, ano_ini, sem_ini, regime,
               aulas_previstas, creditos, situacao, modalidade, servico
        FROM {cls.TABLE_NAME}
        WHERE curso = ?
        ORDER BY CAST(curriculo AS INTEGER) DESC
        '''
        
        return fetch_all(query, (curso,), db_name=db_name)
    
    @classmethod
    def get_maior_curriculo_por_curso(cls, curso: str, db_name="dados_unifoa.db"):
        """Busca o maior currículo (maior ID) por curso"""
        query = f'''
        SELECT curriculo, turno, prazo_ideal, prazo_max, ano_ini, sem_ini, regime,
               aulas_previstas, creditos, situacao, modalidade, servico
        FROM {cls.TABLE_NAME}
        WHERE curso = ?
        ORDER BY CAST(curriculo AS INTEGER) DESC
        LIMIT 1
        '''
        
        result = fetch_one(query, (curso,), db_name=db_name)
        
        if result:
            return {
                'curriculo': result[0],
                'turno': result[1],
                'prazo_ideal': result[2],
                'prazo_max': result[3],
                'ano_ini': result[4],
                'sem_ini': result[5],
                'regime': result[6],
                'aulas_previstas': result[7],
                'creditos': result[8],
                'situacao': result[9],
                'modalidade': result[10],
                'servico': result[11]
            }
        
        return None
    
    @classmethod
    def get_cursos_com_curriculos(cls, db_name="dados_unifoa.db"):
        """Retorna lista de cursos que têm currículos"""
        query = f'''
        SELECT DISTINCT curso
        FROM {cls.TABLE_NAME}
        ORDER BY curso
        '''
        
        results = fetch_all(query, db_name=db_name)
        return [row[0] for row in results]
    
    @classmethod
    def get_curriculos_recentes(cls, limit=10, db_name="dados_unifoa.db"):
        """Retorna currículos mais recentes"""
        query = f'''
        SELECT curriculo, curso, turno, prazo_ideal, prazo_max, situacao
        FROM {cls.TABLE_NAME}
        ORDER BY data_importacao DESC
        LIMIT ?
        '''
        
        return fetch_all(query, (limit,), db_name=db_name)
    
    @classmethod
    def limpar_tabela(cls, db_name="dados_unifoa.db"):
        """Limpa toda a tabela"""
        query = f"DELETE FROM {cls.TABLE_NAME}"
        cursor = execute_query(query, db_name=db_name)
        print(f"✅ {cursor.rowcount} currículos removidos")
        
        # Resetar o autoincrement
        execute_query(f"DELETE FROM sqlite_sequence WHERE name='{cls.TABLE_NAME}'", db_name=db_name)
        
        return cursor.rowcount