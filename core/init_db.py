from core.db import DatabaseManager

def initialize_database():
    """
    Initialize the database by creating necessary extensions and tables.
    """
    with open('core/init_db.sql', 'r') as file:
        sql_script = file.read()

    with DatabaseManager.get_connection(autocommit=True) as (conn, cursor):
        cursor.execute(sql_script)
