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
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        # Convert Django-style %s placeholders to Oracle :1, :2, etc.
        if params:
            # Replace %s with :1, :2, etc.
            for i, param in enumerate(params, 1):
                query = query.replace('%s', f':{i}', 1)
        
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
            row_dict = _convert_oracle_row_to_dict(columns, row)
            result_list.append(row_dict)
        
        logger.info(f"Query executed successfully. Returned {len(result_list)} rows.")
        return result_list
        
    except Exception as e:
        logger.error(f"Error executing Oracle query: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Parameters: {params}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


def test_oracle_connection():
    """Test Oracle database connection"""
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.fetchone()
        cursor.close()
        connection.close()
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
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute(insert_query, params)
            
            # Commit the transaction
            cursor.execute("COMMIT")
            
            # Get the newly created user by username
            select_query = """
            SELECT a.ADDRESS, a.CREATED_DATE, a.DASHBOARD_TYPE, a.FAMILY,
                   a.GROUP_ID, a.IS_ACTIVE, a.NAME, a.PASSWORD,
                   a.PHONE_NUMBER, a.USER_ID, a.USER_NAME, a.VENDOR_ID
              FROM KRN_USER_DETAIL a
             WHERE UPPER(a.USER_NAME) = UPPER(:1)
               AND a.IS_ACTIVE = 1
             ORDER BY a.USER_ID DESC
            """
            
            cursor.execute(select_query, [user_data.get('user_name')])
            results = cursor.fetchall()
            
            if results:
                # Get column names
                columns = [col[0] for col in cursor.description]
                user_data = dict(zip(columns, results[0]))
                return user_data  # Return the first (newest) record
        finally:
            cursor.close()
            connection.close()
            
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
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = "SELECT COUNT(*) as count FROM KRN_USER_DETAIL WHERE UPPER(user_name) = UPPER(:1)"
        cursor.execute(query, [username])
        result = cursor.fetchone()
        
        return result and result[0] > 0
    except Exception as e:
        logger.error(f"Error checking username existence: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close() 

def get_oracle_connection():
    """
    Create and return an Oracle database connection using oracledb
    """
    try:
        # Get Oracle database settings from Django settings
        oracle_config = settings.DATABASES.get('oracle', {})
        
        # Extract connection parameters
        dsn = oracle_config.get('NAME', '192.168.0.191:1522/FREEPDB1')
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

def get_oracle_user_messages(user_id, limit=5):
    """
    Get messages for a user from KRN_USER_MESSAGE table
    
    Args:
        user_id (int): User ID to get messages for
        limit (int): Maximum number of messages to return
        
    Returns:
        list: List of message dictionaries
    """
    if not user_id:
        return []
        
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT MESSAGE_ID,
               USER_ID,
               MESSAGE_TEXT,
               SENT_DATE,
               IS_READ,
               TYPE,
               ICON
          FROM KRN_USER_MESSAGE
         WHERE USER_ID = :1
         ORDER BY SENT_DATE DESC
         FETCH FIRST :2 ROWS ONLY
        """
        
        cursor.execute(query, [user_id, limit])
        results = cursor.fetchall()
        
        messages = []
        if results:
            columns = [desc[0] for desc in cursor.description]
            for row in results:
                message_dict = _convert_oracle_row_to_dict(columns, row)
                messages.append(message_dict)
        
        return messages
        
    except Exception as e:
        logger.error(f"Error retrieving messages for user {user_id}: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_user_message_count(user_id, unread_only=True):
    """
    Get count of messages for a user from KRN_USER_MESSAGE table
    
    Args:
        user_id (int): User ID to count messages for
        unread_only (bool): If True, count only unread messages
        
    Returns:
        int: Number of messages
    """
    if not user_id:
        return 0
        
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if unread_only:
            query = """
            SELECT COUNT(*) as message_count
              FROM KRN_USER_MESSAGE
             WHERE USER_ID = :1 AND IS_READ = 0
            """
        else:
            query = """
            SELECT COUNT(*) as message_count
              FROM KRN_USER_MESSAGE
             WHERE USER_ID = :1
            """
        
        cursor.execute(query, [user_id])
        result = cursor.fetchone()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error counting messages for user {user_id}: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_notifications(group_id=None, limit=5):
    """
    Get notifications from KRN_USER_NOTIF table
    
    Args:
        group_id (int): Optional group ID to filter notifications
        limit (int): Maximum number of notifications to return
        
    Returns:
        list: List of notification dictionaries
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if group_id:
            query = """
            SELECT NOTIF_ID,
                   GROUP_ID,
                   NOTIF_TEXT,
                   NOTIF_DATE,
                   ICON,
                   TYPE
              FROM KRN_USER_NOTIF
             WHERE GROUP_ID = :1
             ORDER BY NOTIF_DATE DESC
             FETCH FIRST :2 ROWS ONLY
            """
            cursor.execute(query, [group_id, limit])
        else:
            # Get all notifications if no group specified
            query = """
            SELECT NOTIF_ID,
                   GROUP_ID,
                   NOTIF_TEXT,
                   NOTIF_DATE,
                   ICON,
                   TYPE
              FROM KRN_USER_NOTIF
             ORDER BY NOTIF_DATE DESC
             FETCH FIRST :1 ROWS ONLY
            """
            cursor.execute(query, [limit])
        
        results = cursor.fetchall()
        
        notifications = []
        if results:
            columns = [desc[0] for desc in cursor.description]
            for row in results:
                notif_dict = _convert_oracle_row_to_dict(columns, row)
                notifications.append(notif_dict)
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_notification_count(group_id=None):
    """
    Get count of notifications from KRN_USER_NOTIF table
    
    Args:
        group_id (int): Optional group ID to filter notifications
        
    Returns:
        int: Number of notifications
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if group_id:
            query = """
            SELECT COUNT(*) as notif_count
              FROM KRN_USER_NOTIF
             WHERE GROUP_ID = :1
            """
            cursor.execute(query, [group_id])
        else:
            query = """
            SELECT COUNT(*) as notif_count
              FROM KRN_USER_NOTIF
            """
            cursor.execute(query)
        
        result = cursor.fetchone()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error counting notifications: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def mark_oracle_message_as_read(message_id, user_id):
    """
    Mark a message as read in KRN_USER_MESSAGE table
    
    Args:
        message_id (int): Message ID to mark as read
        user_id (int): User ID (for security check)
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        update_query = """
        UPDATE KRN_USER_MESSAGE 
        SET IS_READ = 1
        WHERE MESSAGE_ID = :1 AND USER_ID = :2
        """
        
        cursor.execute(update_query, [message_id, user_id])
        connection.commit()
        
        logger.info(f"Message {message_id} marked as read for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error marking message as read: {str(e)}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_oracle_message(user_id, message_text, message_type=None):
    """
    Create a new message in KRN_USER_MESSAGE table
    
    Args:
        user_id (int): User ID to send message to
        message_text (str): Message content
        message_type (str): Optional message type
        
    Returns:
        dict: Created message data if successful, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO KRN_USER_MESSAGE 
        (USER_ID, MESSAGE_TEXT, TYPE, IS_READ)
        VALUES (:1, :2, :3, 0)
        RETURNING MESSAGE_ID INTO :4
        """
        
        # Create output variable for RETURNING clause
        message_id_var = cursor.var(int)
        
        cursor.execute(insert_query, [
            user_id,
            message_text,
            message_type,
            message_id_var
        ])
        connection.commit()
        
        # Get the generated MESSAGE_ID
        generated_message_id = message_id_var.getvalue()[0]
        
        result = {
            'MESSAGE_ID': generated_message_id,
            'USER_ID': user_id,
            'MESSAGE_TEXT': message_text,
            'TYPE': message_type,
            'IS_READ': 0
        }
        
        logger.info(f"Message created successfully with ID {generated_message_id} for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_announcements(group_id=None, limit=5):
    """
    Get announcements from KRN_ANNOUNCEMENTS table
    
    Args:
        group_id (int): Optional group ID to filter announcements
        limit (int): Maximum number of announcements to return
        
    Returns:
        list: List of announcement dictionaries
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if group_id:
            query = """
            SELECT ANNOUNCEMENT_ID,
                   TITLE,
                   CONTENT,
                   CREATED_AT,
                   UPDATED_AT,
                   IS_ACTIVE,
                   GROUP_ID
              FROM KRN_ANNOUNCEMENTS
             WHERE IS_ACTIVE = 1
               AND (GROUP_ID = :1 OR GROUP_ID IS NULL)
             ORDER BY CREATED_AT DESC
             FETCH FIRST :2 ROWS ONLY
            """
            cursor.execute(query, [group_id, limit])
        else:
            # Get all announcements if no group specified
            query = """
            SELECT ANNOUNCEMENT_ID,
                   TITLE,
                   CONTENT,
                   CREATED_AT,
                   UPDATED_AT,
                   IS_ACTIVE,
                   GROUP_ID
              FROM KRN_ANNOUNCEMENTS
             WHERE IS_ACTIVE = 1
             ORDER BY CREATED_AT DESC
             FETCH FIRST :1 ROWS ONLY
            """
            cursor.execute(query, [limit])
        
        results = cursor.fetchall()
        
        announcements = []
        if results:
            columns = [desc[0] for desc in cursor.description]
            for row in results:
                announcement_dict = _convert_oracle_row_to_dict(columns, row)
                announcements.append(announcement_dict)
        
        return announcements
        
    except Exception as e:
        logger.error(f"Error retrieving announcements: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_latest_news(group_id=None, limit=5):
    """
    Get latest news from KRN_LATEST_NEWS table
    
    Args:
        group_id (int): Optional group ID to filter news
        limit (int): Maximum number of news items to return
        
    Returns:
        list: List of news dictionaries
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if group_id:
            query = """
            SELECT NEWS_ID,
                   TITLE,
                   CONTENT,
                   IMAGE_URL,
                   CREATED_AT,
                   UPDATED_AT,
                   IS_ACTIVE,
                   GROUP_ID
              FROM KRN_LATEST_NEWS
             WHERE IS_ACTIVE = 1
               AND (GROUP_ID = :1 OR GROUP_ID IS NULL)
             ORDER BY CREATED_AT DESC
             FETCH FIRST :2 ROWS ONLY
            """
            cursor.execute(query, [group_id, limit])
        else:
            # Get all news if no group specified
            query = """
            SELECT NEWS_ID,
                   TITLE,
                   CONTENT,
                   IMAGE_URL,
                   CREATED_AT,
                   UPDATED_AT,
                   IS_ACTIVE,
                   GROUP_ID
              FROM KRN_LATEST_NEWS
             WHERE IS_ACTIVE = 1
             ORDER BY CREATED_AT DESC
             FETCH FIRST :1 ROWS ONLY
            """
            cursor.execute(query, [limit])
        
        results = cursor.fetchall()
        
        news_list = []
        if results:
            columns = [desc[0] for desc in cursor.description]
            for row in results:
                news_dict = _convert_oracle_row_to_dict(columns, row)
                news_list.append(news_dict)
        
        return news_list
        
    except Exception as e:
        logger.error(f"Error retrieving latest news: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_announcement_count(group_id=None):
    """
    Get count of active announcements from KRN_ANNOUNCEMENTS table
    
    Args:
        group_id (int): Optional group ID to filter announcements
        
    Returns:
        int: Number of active announcements
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if group_id:
            query = """
            SELECT COUNT(*) as announcement_count
              FROM KRN_ANNOUNCEMENTS
             WHERE IS_ACTIVE = 1
               AND (GROUP_ID = :1 OR GROUP_ID IS NULL)
            """
            cursor.execute(query, [group_id])
        else:
            query = """
            SELECT COUNT(*) as announcement_count
              FROM KRN_ANNOUNCEMENTS
             WHERE IS_ACTIVE = 1
            """
            cursor.execute(query)
        
        result = cursor.fetchone()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error counting announcements: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_news_count(group_id=None):
    """
    Get count of active news from KRN_LATEST_NEWS table
    
    Args:
        group_id (int): Optional group ID to filter news
        
    Returns:
        int: Number of active news items
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if group_id:
            query = """
            SELECT COUNT(*) as news_count
              FROM KRN_LATEST_NEWS
             WHERE IS_ACTIVE = 1
               AND (GROUP_ID = :1 OR GROUP_ID IS NULL)
            """
            cursor.execute(query, [group_id])
        else:
            query = """
            SELECT COUNT(*) as news_count
              FROM KRN_LATEST_NEWS
             WHERE IS_ACTIVE = 1
            """
            cursor.execute(query)
        
        result = cursor.fetchone()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error counting news: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_oracle_announcement(title, content, group_id=None):
    """
    Create a new announcement in KRN_ANNOUNCEMENTS table
    
    Args:
        title (str): Announcement title
        content (str): Announcement content
        group_id (int): Optional group ID to restrict access
        
    Returns:
        dict: Created announcement data if successful, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO KRN_ANNOUNCEMENTS 
        (TITLE, CONTENT, GROUP_ID)
        VALUES (:1, :2, :3)
        RETURNING ANNOUNCEMENT_ID INTO :4
        """
        
        # Create output variable for RETURNING clause
        announcement_id_var = cursor.var(int)
        
        cursor.execute(insert_query, [
            title,
            content,
            group_id,
            announcement_id_var
        ])
        connection.commit()
        
        # Get the generated ANNOUNCEMENT_ID
        generated_id = announcement_id_var.getvalue()[0]
        
        result = {
            'ANNOUNCEMENT_ID': generated_id,
            'TITLE': title,
            'CONTENT': content,
            'GROUP_ID': group_id,
            'IS_ACTIVE': 1
        }
        
        logger.info(f"Announcement created successfully with ID {generated_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating announcement: {str(e)}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_oracle_news(title, content, image_url=None, group_id=None):
    """
    Create a new news item in KRN_LATEST_NEWS table
    
    Args:
        title (str): News title
        content (str): News content
        image_url (str): Optional image URL/path
        group_id (int): Optional group ID to restrict access
        
    Returns:
        dict: Created news data if successful, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO KRN_LATEST_NEWS 
        (TITLE, CONTENT, IMAGE_URL, GROUP_ID)
        VALUES (:1, :2, :3, :4)
        RETURNING NEWS_ID INTO :5
        """
        
        # Create output variable for RETURNING clause
        news_id_var = cursor.var(int)
        
        cursor.execute(insert_query, [
            title,
            content,
            image_url,
            group_id,
            news_id_var
        ])
        connection.commit()
        
        # Get the generated NEWS_ID
        generated_id = news_id_var.getvalue()[0]
        
        result = {
            'NEWS_ID': generated_id,
            'TITLE': title,
            'CONTENT': content,
            'IMAGE_URL': image_url,
            'GROUP_ID': group_id,
            'IS_ACTIVE': 1
        }
        
        logger.info(f"News created successfully with ID {generated_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating news: {str(e)}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def _convert_oracle_row_to_dict(columns, row):
    """
    Helper function to convert Oracle row data to dictionary,
    handling CLOB fields properly by reading them while connection is active
    
    Args:
        columns: List of column names
        row: Row data from Oracle cursor
        
    Returns:
        dict: Dictionary with column names as keys and converted values
    """
    result_dict = {}
    for i, value in enumerate(row):
        column_name = columns[i]
        # Convert CLOB fields to strings while connection is active
        if hasattr(value, 'read'):  # This is a CLOB
            try:
                result_dict[column_name] = value.read()
            except Exception as e:
                logger.warning(f"Error reading CLOB for column {column_name}: {str(e)}")
                result_dict[column_name] = str(value) if value is not None else None
        else:
            result_dict[column_name] = value
    return result_dict

def get_oracle_open_tenders(limit=20):
    """
    Get open tender applications from KRNR_TENDER table
    
    Args:
        limit (int): Maximum number of tenders to return
        
    Returns:
        list: List of open tender dictionaries
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT TENDER_ID,
               TENDER_TITLE,
               TENDER_DESCRIPTION,
               CATEGORY_ID,
               START_DATE,
               END_DATE,
               SUBMISSION_DEADLINE,
               BUDGET_AMOUNT,
               CURRENCY,
               STATUS,
               CREATED_BY_USER_ID,
               CREATED_DATE
          FROM KRNR_TENDER
         WHERE UPPER(STATUS) = 'OPEN'
         ORDER BY CREATED_DATE DESC
         FETCH FIRST :1 ROWS ONLY
        """
        
        cursor.execute(query, [limit])
        results = cursor.fetchall()
        
        tenders = []
        if results:
            columns = [desc[0] for desc in cursor.description]
            for row in results:
                tender_dict = _convert_oracle_row_to_dict(columns, row)
                tenders.append(tender_dict)
        
        return tenders
        
    except Exception as e:
        logger.error(f"Error retrieving open tenders: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_tender_by_id(tender_id):
    """
    Get a specific tender by ID from KRNR_TENDER table
    
    Args:
        tender_id (int): Tender ID to retrieve
        
    Returns:
        dict: Tender data if found, None otherwise
    """
    if not tender_id:
        return None
        
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT TENDER_ID,
               TENDER_TITLE,
               TENDER_DESCRIPTION,
               CATEGORY_ID,
               START_DATE,
               END_DATE,
               SUBMISSION_DEADLINE,
               BUDGET_AMOUNT,
               CURRENCY,
               STATUS,
               CREATED_BY_USER_ID,
               CREATED_DATE
          FROM KRNR_TENDER
         WHERE TENDER_ID = :1
        """
        
        cursor.execute(query, [tender_id])
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            tender_dict = _convert_oracle_row_to_dict(columns, result)
            return tender_dict
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error retrieving tender {tender_id}: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_oracle_open_tenders_count():
    """
    Get count of open tenders from KRNR_TENDER table
    
    Returns:
        int: Number of open tenders
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT COUNT(*) as tender_count
          FROM KRNR_TENDER
         WHERE UPPER(STATUS) = 'OPEN'
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error counting open tenders: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_tender_application(tender_id, vendor_id, submission_notes=None):
    """
    Create a new tender application in KRNR_TENDER_APPLICATION table
    
    Args:
        tender_id (int): ID of the tender to apply for
        vendor_id (int): ID of the vendor/company applying
        submission_notes (str): Optional notes/comments for the application
        
    Returns:
        dict: Created application data if successful, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        # Check if application already exists
        check_query = """
        SELECT COUNT(*) as count
          FROM KRNR_TENDER_APPLICATION
         WHERE TENDER_ID = :1 AND VENDOR_ID = :2
        """
        
        cursor.execute(check_query, [tender_id, vendor_id])
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            # Application already exists
            logger.warning(f"Tender application already exists for tender_id={tender_id}, vendor_id={vendor_id}")
            return None
        
        # Create new application
        insert_query = """
        INSERT INTO KRNR_TENDER_APPLICATION 
        (TENDER_ID, VENDOR_ID, SUBMISSION_NOTES)
        VALUES (:1, :2, :3)
        RETURNING APPLICATION_ID INTO :4
        """
        
        # Create output variable for RETURNING clause
        application_id_var = cursor.var(int)
        
        cursor.execute(insert_query, [
            tender_id,
            vendor_id,
            submission_notes,
            application_id_var
        ])
        connection.commit()
        
        # Get the generated APPLICATION_ID
        generated_id = application_id_var.getvalue()[0]
        
        result = {
            'APPLICATION_ID': generated_id,
            'TENDER_ID': tender_id,
            'VENDOR_ID': vendor_id,
            'SUBMISSION_NOTES': submission_notes,
            'APPLICATION_STATUS': 'Submitted'
        }
        
        logger.info(f"Tender application created successfully with ID {generated_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating tender application: {str(e)}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_vendor_tender_applications(vendor_id, limit=20):
    """
    Get tender applications for a specific vendor from KRNR_TENDER_APPLICATION table
    
    Args:
        vendor_id (int): Vendor ID to get applications for
        limit (int): Maximum number of applications to return
        
    Returns:
        list: List of application dictionaries with tender details
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT ta.APPLICATION_ID,
               ta.TENDER_ID,
               ta.VENDOR_ID,
               ta.SUBMISSION_DATE,
               ta.APPLICATION_STATUS,
               ta.SUBMISSION_NOTES,
               t.TENDER_TITLE,
               t.TENDER_DESCRIPTION,
               t.START_DATE,
               t.END_DATE,
               t.SUBMISSION_DEADLINE,
               t.BUDGET_AMOUNT,
               t.CURRENCY,
               t.STATUS as TENDER_STATUS
          FROM KRNR_TENDER_APPLICATION ta
          JOIN KRNR_TENDER t ON ta.TENDER_ID = t.TENDER_ID
         WHERE ta.VENDOR_ID = :1
         ORDER BY ta.SUBMISSION_DATE DESC
         FETCH FIRST :2 ROWS ONLY
        """
        
        cursor.execute(query, [vendor_id, limit])
        results = cursor.fetchall()
        
        applications = []
        if results:
            columns = [desc[0] for desc in cursor.description]
            for row in results:
                application_dict = _convert_oracle_row_to_dict(columns, row)
                applications.append(application_dict)
        
        return applications
        
    except Exception as e:
        logger.error(f"Error retrieving applications for vendor {vendor_id}: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def check_tender_application_exists(tender_id, vendor_id):
    """
    Check if a tender application already exists for a specific tender and vendor
    
    Args:
        tender_id (int): Tender ID
        vendor_id (int): Vendor ID
        
    Returns:
        bool: True if application exists, False otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT COUNT(*) as count
          FROM KRNR_TENDER_APPLICATION
         WHERE TENDER_ID = :1 AND VENDOR_ID = :2
        """
        
        cursor.execute(query, [tender_id, vendor_id])
        result = cursor.fetchone()
        
        return result and result[0] > 0
        
    except Exception as e:
        logger.error(f"Error checking tender application existence: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_tender_application_status(application_id, new_status, notes=None):
    """
    Update the status of a tender application
    
    Args:
        application_id (int): Application ID to update
        new_status (str): New application status
        notes (str): Optional additional notes
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if notes:
            update_query = """
            UPDATE KRNR_TENDER_APPLICATION 
            SET APPLICATION_STATUS = :1,
                SUBMISSION_NOTES = :2
            WHERE APPLICATION_ID = :3
            """
            cursor.execute(update_query, [new_status, notes, application_id])
        else:
            update_query = """
            UPDATE KRNR_TENDER_APPLICATION 
            SET APPLICATION_STATUS = :1
            WHERE APPLICATION_ID = :2
            """
            cursor.execute(update_query, [new_status, application_id])
        
        connection.commit()
        
        logger.info(f"Updated application {application_id} status to {new_status}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating application status: {str(e)}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_tender_application_by_id(application_id):
    """
    Get a specific tender application by ID
    
    Args:
        application_id (int): Application ID
        
    Returns:
        dict: Application data if found, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT ta.APPLICATION_ID,
               ta.TENDER_ID,
               ta.VENDOR_ID,
               ta.SUBMISSION_DATE,
               ta.APPLICATION_STATUS,
               ta.SUBMISSION_NOTES,
               t.TENDER_TITLE,
               t.TENDER_DESCRIPTION,
               t.START_DATE,
               t.END_DATE,
               t.SUBMISSION_DEADLINE,
               t.BUDGET_AMOUNT,
               t.CURRENCY,
               t.STATUS as TENDER_STATUS,
               v.VENDOR_NAME
          FROM KRNR_TENDER_APPLICATION ta
          JOIN KRNR_TENDER t ON ta.TENDER_ID = t.TENDER_ID
          JOIN KRNR_VENDOR v ON ta.VENDOR_ID = v.VENDOR_ID
         WHERE ta.APPLICATION_ID = :1
        """
        
        cursor.execute(query, [application_id])
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            application_dict = _convert_oracle_row_to_dict(columns, result)
            return application_dict
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error retrieving application {application_id}: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close() 