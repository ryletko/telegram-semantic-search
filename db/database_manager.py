"""
Database management module for handling connections and common database operations.
"""
import psycopg2
from psycopg2.extras import Json
from contextlib import contextmanager
from db.config import DB_CONFIG

class DatabaseManager:
    """
    Database manager class that handles database connections and provides common operations.
    """
    
    @staticmethod
    @contextmanager
    def get_connection(autocommit=False):
        """
        Context manager for database connections.
        
        Args:
            autocommit (bool): Whether to enable autocommit mode
            
        Yields:
            tuple: (connection, cursor) tuple
        """
        conn = None
        try:
            print(f"{DB_CONFIG}")
            conn = psycopg2.connect(**DB_CONFIG)
            print(f"Connected to {DB_CONFIG['database']} on {DB_CONFIG['host']}")
            conn.autocommit = autocommit
            cursor = conn.cursor()
            yield conn, cursor
        except Exception as e:
            if conn and not autocommit:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def execute_query(query, params=None, autocommit=False, fetch=None):
        """
        Execute a query and optionally return results.
        
        Args:
            query (str): SQL query to execute
            params (tuple/list): Parameters for the query
            autocommit (bool): Whether to enable autocommit mode
            fetch (str): One of 'one', 'all', or None to determine what to fetch
            
        Returns:
            The query results if fetch is specified, otherwise None
        """
        with DatabaseManager.get_connection(autocommit) as (conn, cursor):
            cursor.execute(query, params or ())
            
            if not fetch:
                if not autocommit:
                    conn.commit()
                return cursor.rowcount
            
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            else:
                raise ValueError("fetch must be 'one', 'all', or None")
                
            if not autocommit:
                conn.commit()
                
            return result
    
    @staticmethod
    def table_exists(table_name):
        """Check if a table exists in the database."""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """
        result = DatabaseManager.execute_query(query, (table_name,), fetch='one')
        return result[0] if result else False
    
    @staticmethod
    def column_exists(table_name, column_name):
        """Check if a column exists in a table."""
        if not DatabaseManager.table_exists(table_name):
            return False
            
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            )
        """
        result = DatabaseManager.execute_query(query, (table_name, column_name), fetch='one')
        return result[0] if result else False
    
    @staticmethod
    def insert_returning(table, data, returning='id'):
        """
        Insert data into a table and return a specific column.
        
        Args:
            table (str): Table name
            data (dict): Dictionary of column names and values
            returning (str): Column to return
            
        Returns:
            The value of the returning column
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING {returning}
        """
        
        result = DatabaseManager.execute_query(query, values, fetch='one')
        return result[0] if result else None
    
    @staticmethod
    def format_json_param(param):
        """Format a parameter as JSON for psycopg2."""
        return Json(param) 