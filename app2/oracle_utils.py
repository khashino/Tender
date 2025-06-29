"""
Oracle Database Utilities for App2
Provides functions to execute SELECT queries on Oracle database
"""

import logging
from django.db import connections
from django.conf import settings
from typing import List, Dict, Any, Optional
from django.db.utils import DatabaseError
import oracledb

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


def create_oracle_user(user_data):
    """
    Create a new user in the Oracle KRN_USER_DETAIL table
    
    Args:
        user_data (dict): Dictionary containing user information
        
    Returns:
        dict: The created user data with USER_ID, or None if failed
    """
    try:
        # Insert query for KRN_USER_DETAIL table with RETURNING clause
        # USER_ID is auto-generated, so we don't include it in INSERT
        insert_query = """
        INSERT INTO KRN_USER_DETAIL (
            NAME, FAMILY, USER_NAME, PASSWORD, PHONE_NUMBER, 
            ADDRESS, GROUP_ID, DASHBOARD_TYPE, IS_ACTIVE, 
            CREATED_DATE, VENDOR_ID
        ) VALUES (
            %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, 
            SYSDATE, %s
        )
        """
        
        # Prepare parameters
        params = [
            user_data.get('name'),
            user_data.get('family'),
            user_data.get('user_name'),
            user_data.get('password'),
            user_data.get('phone_number'),
            user_data.get('address'),
            user_data.get('group_id', 1),  # Default to group 1
            'Public',  # Default dashboard type
            1,  # IS_ACTIVE = 1 (active)
            user_data.get('vendor_id')
        ]
        
        # Execute insert and get the new user
        with connections['oracle'].cursor() as cursor:
            cursor.execute(insert_query, params)
            
            # Commit the transaction
            cursor.execute("COMMIT")
            
            # Get the newly created user by username
            select_query = """
            SELECT a.ADDRESS, a.CREATED_DATE, a.DASHBOARD_TYPE, a.FAMILY,
                   a.GROUP_ID, a.IS_ACTIVE, a.NAME, a.PASSWORD,
                   a.PHONE_NUMBER, a.USER_ID, a.USER_NAME, a.VENDOR_ID
              FROM KRN_USER_DETAIL a
             WHERE UPPER(a.USER_NAME) = UPPER(%s)
               AND a.IS_ACTIVE = 1
             ORDER BY a.USER_ID DESC
            """
            
            result = execute_oracle_query(select_query, [user_data.get('user_name')])
            if result:
                return result[0]  # Return the first (newest) record
            
        return None
        
    except Exception as e:
        logger.error(f"Error creating Oracle user: {str(e)}")
        return None
        

def check_username_exists(username):
    """
    Check if a username already exists in the Oracle KRN_USER_DETAIL table
    
    Args:
        username (str): Username to check
        
    Returns:
        bool: True if username exists, False otherwise
    """
    try:
        query = "SELECT COUNT(*) as count FROM KRN_USER_DETAIL WHERE UPPER(user_name) = UPPER(%s)"
        result = execute_oracle_query(query, [username])
        return result and result[0]['COUNT'] > 0
    except Exception as e:
        logger.error(f"Error checking username existence: {str(e)}")
        return False 

def get_oracle_connection():
    """
    Create and return an Oracle database connection using oracledb
    """
    try:
        # Get Oracle database settings from Django settings
        oracle_config = settings.DATABASES.get('oracle', {})
        
        # Extract connection parameters
        dsn = oracle_config.get('NAME', '192.168.7.93:1522/FREEPDB1')
        user = oracle_config.get('USER', 'NAK')
        password = oracle_config.get('PASSWORD', '78007625645_Kh')
        
        # Create connection using oracledb
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        
        logger.info("Oracle database connection established successfully")
        return connection
        
    except Exception as e:
        logger.error(f"Failed to connect to Oracle database: {str(e)}")
        raise

def get_vendor_by_id(vendor_id):
    """
    Get vendor/company information by vendor_id from KRNR_VENDOR table
    
    Args:
        vendor_id (int): Vendor ID to look up
        
    Returns:
        dict: Vendor data if found, None otherwise
    """
    if not vendor_id:
        return None
        
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT VENDOR_ID,
               VENDOR_NAME,
               REGISTRATION_NUMBER,
               ADDRESS,
               EMAIL,
               PHONE_NUMBER
          FROM KRNR_VENDOR
         WHERE VENDOR_ID = :1
        """
        
        cursor.execute(query, [vendor_id])
        result = cursor.fetchone()
        
        if result:
            # Convert result to dictionary
            columns = [desc[0] for desc in cursor.description]
            vendor_dict = dict(zip(columns, result))
            return vendor_dict
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error retrieving vendor {vendor_id}: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_vendor(vendor_data):
    """
    Create a new vendor/company in the KRNR_VENDOR table
    
    Args:
        vendor_data (dict): Dictionary containing vendor information
        
    Returns:
        dict: Created vendor data if successful, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        # Prepare the insert query - VENDOR_ID is auto-generated by sequence
        # Using RETURNING clause to get the generated VENDOR_ID
        insert_query = """
        INSERT INTO KRNR_VENDOR 
        (VENDOR_NAME, REGISTRATION_NUMBER, ADDRESS, EMAIL, PHONE_NUMBER)
        VALUES (:1, :2, :3, :4, :5)
        RETURNING VENDOR_ID INTO :6
        """
        
        # Prepare parameters
        params = [
            vendor_data.get('vendor_name'),
            vendor_data.get('registration_number'),
            vendor_data.get('address'),
            vendor_data.get('email'),
            vendor_data.get('phone_number')
        ]
        
        # Create output variable for RETURNING clause
        vendor_id_var = cursor.var(int)
        params.append(vendor_id_var)
        
        # Execute the insert
        cursor.execute(insert_query, params)
        connection.commit()
        
        # Get the generated VENDOR_ID
        generated_vendor_id = vendor_id_var.getvalue()[0]
        
        # Create the result dictionary
        result = {
            'VENDOR_ID': generated_vendor_id,
            'VENDOR_NAME': vendor_data.get('vendor_name'),
            'REGISTRATION_NUMBER': vendor_data.get('registration_number'),
            'ADDRESS': vendor_data.get('address'),
            'EMAIL': vendor_data.get('email'),
            'PHONE_NUMBER': vendor_data.get('phone_number')
        }
        
        logger.info(f"Vendor created successfully with ID {generated_vendor_id}: {vendor_data.get('vendor_name')}")
        return result
            
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_user_vendor_id(user_id, vendor_id):
    """
    Update the vendor_id for a user in KRN_USER_DETAIL table
    
    Args:
        user_id (int): User ID to update
        vendor_id (int): Vendor ID to assign
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        update_query = """
        UPDATE KRN_USER_DETAIL 
        SET VENDOR_ID = :1
        WHERE USER_ID = :2
        """
        
        cursor.execute(update_query, [vendor_id, user_id])
        connection.commit()
        
        logger.info(f"Updated user {user_id} with vendor_id {vendor_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user vendor_id: {str(e)}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close() 