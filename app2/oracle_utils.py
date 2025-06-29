"""
Oracle Database Utilities for App2
Provides functions to execute SELECT queries on Oracle database
"""

import logging
from django.db import connections
from django.conf import settings
from typing import List, Dict, Any, Optional
from django.db.utils import DatabaseError

logger = logging.getLogger(__name__)

class OracleQueryExecutor:
    """Utility class for executing Oracle database queries."""
    
    def __init__(self, database_alias: str = 'oracle'):
        """
        Initialize Oracle query executor.
        
        Args:
            database_alias: The database alias defined in Django settings
        """
        self.database_alias = database_alias
    
    def execute_select_query(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query on Oracle database.
        
        Args:
            query: SQL SELECT query string
            params: Optional list of parameters for the query
            
        Returns:
            List of dictionaries representing the query results
            
        Raises:
            Exception: If query execution fails
        """
        try:
            connection = connections[self.database_alias]
            
            with connection.cursor() as cursor:
                logger.info(f"Executing Oracle query: {query}")
                if params:
                    logger.info(f"Query parameters: {params}")
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [col[0] for col in cursor.description]
                
                # Fetch all results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                result_list = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    result_list.append(row_dict)
                
                logger.info(f"Query executed successfully. Returned {len(result_list)} rows.")
                return result_list
                
        except Exception as e:
            logger.error(f"Error executing Oracle query: {str(e)}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Parameters: {params}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the Oracle database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            connection = connections[self.database_alias]
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                logger.info("Oracle database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Oracle database connection test failed: {str(e)}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries containing column information
        """
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            DATA_LENGTH,
            DATA_PRECISION,
            DATA_SCALE,
            NULLABLE,
            DATA_DEFAULT
        FROM USER_TAB_COLUMNS 
        WHERE TABLE_NAME = UPPER(%s)
        ORDER BY COLUMN_ID
        """
        
        return self.execute_select_query(query, [table_name])
    
    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables accessible to the current user.
        
        Returns:
            List of table names
        """
        query = "SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME"
        results = self.execute_select_query(query)
        return [row['TABLE_NAME'] for row in results]


# Convenience functions for easy access
def execute_oracle_query(query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query on Oracle database.
    
    Args:
        query: SQL SELECT query string
        params: Optional list of parameters for the query
        
    Returns:
        List of dictionaries representing the query results
    """
    executor = OracleQueryExecutor()
    return executor.execute_select_query(query, params)


def test_oracle_connection():
    """Test Oracle database connection"""
    try:
        connection = connections['oracle']
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
        return True, "Connection successful"
    except Exception as e:
        error_msg = f"Connection failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_oracle_tables() -> List[str]:
    """
    Get list of all Oracle tables accessible to the current user.
    
    Returns:
        List of table names
    """
    executor = OracleQueryExecutor()
    return executor.get_all_tables()


def get_oracle_table_info(table_name: str) -> List[Dict[str, Any]]:
    """
    Get column information for a specific Oracle table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of dictionaries containing column information
    """
    executor = OracleQueryExecutor()
    return executor.get_table_info(table_name) 