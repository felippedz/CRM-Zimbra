import os
import pyodbc

SERVER = os.getenv('SQL_SERVER', 'localhost,1433')
DATABASE = os.getenv('SQL_DATABASE', 'zimbra_crm')
DRIVER = os.getenv('ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')

CONNECTION_STRING = (
    f'DRIVER={{{DRIVER}}};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    'UID=sa;'
    'PWD=Zimbra2026*;'
    'TrustServerCertificate=yes;'
)


def get_db_connection():
    conn = pyodbc.connect(CONNECTION_STRING)
    conn.autocommit = False
    return conn


def _row_to_dict(cursor, row):
    if row is None:
        return None

    columns = [col[0] for col in cursor.description]

    return dict(zip(columns, row))


def fetchone(query, params=None):

    conn = get_db_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(query, params or ())

        row = cursor.fetchone()

        return _row_to_dict(cursor, row)

    finally:

        conn.close()


def fetchall(query, params=None):

    conn = get_db_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(query, params or ())

        rows = cursor.fetchall()

        return [_row_to_dict(cursor, row) for row in rows]

    finally:

        conn.close()


def execute(query, params=None):

    conn = get_db_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(query, params or ())

        conn.commit()

        return cursor.rowcount

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()
