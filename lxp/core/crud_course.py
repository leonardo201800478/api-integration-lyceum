# lxp/core/crud_course.py
"""
Operações de banco para a tabela lxp_course (SQL Server).
Funções para criar tabela, inserir, atualizar e buscar cursos.
"""
import pyodbc
from core.database_sqlserver import get_sqlserver_connection
from core.logger import logger

def criar_tabela_course(conn=None):
    """
    Cria a tabela lxp_course no banco lxp, caso não exista.
    Pode receber uma conexão existente ou criar uma nova.
    """
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='lxp_course' AND xtype='U')
    CREATE TABLE lxp_course (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(150) NOT NULL,
        externalId NVARCHAR(50) NOT NULL UNIQUE,
        isActive BIT NOT NULL,
        externalTeachingModalityId NVARCHAR(50) NOT NULL,
        externalEducationLevelId NVARCHAR(50) NOT NULL,
        courseTypeId NVARCHAR(15) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    """
    fechar_conexao = False
    if conn is None:
        conn = get_sqlserver_connection('lxp')
        fechar_conexao = True
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info("Tabela lxp_course verificada/criada com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao criar/verificar tabela lxp_course: {e}")
        raise
    finally:
        if fechar_conexao:
            conn.close()

def upsert_course(conn, curso_data):
    """
    Insere ou atualiza um curso na tabela lxp_course.
    curso_data: dicionário com as chaves: name, externalId, isActive,
                externalTeachingModalityId, externalEducationLevelId, courseTypeId.
    isActive deve ser booleano (True/False).
    """
    upsert_sql = """
    MERGE lxp_course AS target
    USING (SELECT ? AS externalId) AS source
    ON target.externalId = source.externalId
    WHEN MATCHED THEN
        UPDATE SET
            name = ?,
            isActive = ?,
            externalTeachingModalityId = ?,
            externalEducationLevelId = ?,
            courseTypeId = ?,
            updated_at = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (name, externalId, isActive, externalTeachingModalityId,
                externalEducationLevelId, courseTypeId)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    params = (
        curso_data['externalId'],                 # source ON
        curso_data['name'],
        curso_data['isActive'],
        curso_data['externalTeachingModalityId'],
        curso_data['externalEducationLevelId'],
        curso_data['courseTypeId'],
        curso_data['name'],                       # INSERT
        curso_data['externalId'],
        curso_data['isActive'],
        curso_data['externalTeachingModalityId'],
        curso_data['externalEducationLevelId'],
        curso_data['courseTypeId']
    )
    cursor = conn.cursor()
    cursor.execute(upsert_sql, params)
    conn.commit()
    logger.info(f"Upsert concluído para curso externalId={curso_data['externalId']}")

def listar_cursos(conn=None):
    """Retorna todos os cursos ativos (opcional)"""
    if conn is None:
        conn = get_sqlserver_connection('lxp')
        fechar = True
    else:
        fechar = False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lxp_course WHERE isActive = 1")
        rows = cursor.fetchall()
        return rows
    finally:
        if fechar:
            conn.close()