from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser
from app2.oracle_utils import execute_oracle_query, get_vendor_by_id, get_oracle_connection
import logging

logger = logging.getLogger(__name__)


class OracleUserPK:
    """Mock primary key field for OracleUser"""
    def value_to_string(self, value):
        return str(value)


class OracleUserMeta:
    """Mock _meta class for OracleUser to make it compatible with Django's auth system"""
    
    def __init__(self):
        self.pk = OracleUserPK()


class OracleVendor:
    """Represents a vendor/company from KRNR_VENDOR table"""
    
    def __init__(self, vendor_data):
        if vendor_data:
            self.vendor_id = vendor_data.get('VENDOR_ID')
            self.name = vendor_data.get('VENDOR_NAME')
            self.registration_number = vendor_data.get('REGISTRATION_NUMBER')
            self.address = vendor_data.get('ADDRESS')
            self.email = vendor_data.get('EMAIL')
            self.phone = vendor_data.get('PHONE_NUMBER')
        else:
            # Default values when no vendor data is available
            self.vendor_id = None
            self.name = None
            self.registration_number = None
            self.address = None
            self.email = None
            self.phone = None
    
    def __str__(self):
        return self.name or f"Vendor {self.vendor_id}"


class OracleUser:
    """Custom user class for Oracle database authentication"""
    
    def __init__(self, user_data):
        self.user_data = user_data
        self._is_authenticated = True
        self.is_active = bool(user_data.get('IS_ACTIVE', 0))
        self.is_anonymous = False
        self.is_superuser = False
        self.is_staff = False
        
        # User properties from Oracle table
        self.user_id = user_data.get('USER_ID')
        self.username = user_data.get('USER_NAME')
        self.name = user_data.get('NAME')
        self.family = user_data.get('FAMILY')
        self.phone_number = user_data.get('PHONE_NUMBER')
        self.address = user_data.get('ADDRESS')
        self.vendor_id = user_data.get('VENDOR_ID')
        self.group_id = user_data.get('GROUP_ID')
        self.dashboard_type = user_data.get('DASHBOARD_TYPE')
        self.created_date = user_data.get('CREATED_DATE')
        
        # Cache for vendor/company data
        self._company = None
        self._company_loaded = False
        
        # USER_ID is the primary key from Oracle - ensure it's properly handled
        # Since USER_ID is GENERATED ALWAYS AS IDENTITY, it should always be a valid integer
        if self.user_id is not None:
            try:
                # Ensure it's an integer (Oracle NUMBER type)
                self.pk = int(self.user_id)
                self.id = self.pk  # Django expects both pk and id
            except (ValueError, TypeError):
                # If conversion fails, there's a data issue
                raise ValueError(f"Invalid USER_ID primary key: {self.user_id}")
        else:
            raise ValueError("USER_ID cannot be None - it's the primary key")
            
        self.first_name = self.name or ''
        self.last_name = self.family or ''
        self.email = ''  # Not available in Oracle table
        
        # Add _meta attribute for Django auth compatibility
        self._meta = OracleUserMeta()
        
        # Add _state attribute for Django compatibility
        self._state = type('obj', (object,), {'adding': False, 'db': None})()
    
    @property
    def company(self):
        """Get the vendor/company associated with this user"""
        if not self._company_loaded:
            if self.vendor_id:
                try:
                    vendor_data = get_vendor_by_id(self.vendor_id)
                    self._company = OracleVendor(vendor_data)
                except Exception as e:
                    logger.error(f"Error loading vendor data for user {self.user_id}: {str(e)}")
                    self._company = OracleVendor(None)
            else:
                self._company = OracleVendor(None)
            self._company_loaded = True
        return self._company
    
    @property
    def is_authenticated(self):
        """Always return True for authenticated users"""
        return self._is_authenticated
    
    def __str__(self):
        # Return username only to avoid session serialization issues
        return str(self.username) if self.username else f"User_{self.pk}"
    
    def __repr__(self):
        return f"<OracleUser: {self.username} (ID: {self.user_id})>"
    
    def get_full_name(self):
        return f"{self.name} {self.family}".strip()
    
    def get_short_name(self):
        return self.name or self.username
    
    def has_perm(self, perm, obj=None):
        return False  # No permission system for now
    
    def has_module_perms(self, app_label):
        return False  # No permission system for now
    
    def save(self, *args, **kwargs):
        """Mock save method for Django compatibility"""
        pass
    
    def delete(self, *args, **kwargs):
        """Mock delete method for Django compatibility"""
        pass
    
    def get_username(self):
        """Return the username for this user"""
        return self.username
    
    def serializable_value(self, field_name):
        """Return serializable value for session storage"""
        if field_name == 'pk' or field_name == 'id':
            return int(self.pk)  # Always return as integer
        return getattr(self, field_name, None)
    
    def _get_pk_val(self):
        """Return the primary key value - required for Django compatibility"""
        return int(self.pk)  # Always return as integer
    
    def __int__(self):
        """Return integer representation of the user (the primary key)"""
        return int(self.pk)
    
    def natural_key(self):
        """Return natural key for the user"""
        return (self.username,)
    
    # Additional methods for Django compatibility
    def get_session_auth_hash(self):
        """Return a hash for session invalidation"""
        return str(self.pk)
    
    def get_deferred_fields(self):
        """Return empty set for Django compatibility"""
        return set()
    
    def refresh_from_db(self, using=None, fields=None):
        """Mock method for Django compatibility"""
        pass


class OracleAuthBackend(BaseBackend):
    """Authentication backend using Oracle KRN_USER_DETAIL table"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        
        try:
            # Use direct oracledb connection instead of Django's database connections
            connection = get_oracle_connection()
            cursor = connection.cursor()
            
            # Query Oracle database for user authentication
            query = """
            SELECT a.ADDRESS,
                   a.CREATED_DATE,
                   a.DASHBOARD_TYPE,
                   a.FAMILY,
                   a.GROUP_ID,
                   a.IS_ACTIVE,
                   a.NAME,
                   a.PASSWORD,
                   a.PHONE_NUMBER,
                   a.USER_ID,
                   a.USER_NAME,
                   a.VENDOR_ID
              FROM KRN_USER_DETAIL a
             WHERE dashboard_type = 'Public' 
               AND is_active = 1
               AND UPPER(user_name) = UPPER(:1) 
               AND password = :2
            """
            
            cursor.execute(query, [username, password])
            results = cursor.fetchall()
            
            if results:
                # Get column names
                columns = [col[0] for col in cursor.description]
                user_data = dict(zip(columns, results[0]))
                
                logger.info(f"Oracle authentication successful for user: {username}")
                return OracleUser(user_data)
            else:
                logger.warning(f"Oracle authentication failed for user: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Oracle authentication error: {str(e)}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    
    def get_user(self, user_id):
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid user_id format: {user_id}")
                return None
            
            # Use direct oracledb connection instead of Django's database connections
            connection = get_oracle_connection()
            cursor = connection.cursor()
            
            # Get user by USER_ID from Oracle
            query = """
            SELECT a.ADDRESS,
                   a.CREATED_DATE,
                   a.DASHBOARD_TYPE,
                   a.FAMILY,
                   a.GROUP_ID,
                   a.IS_ACTIVE,
                   a.NAME,
                   a.PASSWORD,
                   a.PHONE_NUMBER,
                   a.USER_ID,
                   a.USER_NAME,
                   a.VENDOR_ID
              FROM KRN_USER_DETAIL a
             WHERE user_id = :1 
               AND dashboard_type = 'Public' 
               AND is_active = 1
            """
            
            cursor.execute(query, [user_id])
            results = cursor.fetchall()
            
            if results:
                # Get column names
                columns = [col[0] for col in cursor.description]
                user_data = dict(zip(columns, results[0]))
                return OracleUser(user_data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting Oracle user by ID {user_id}: {str(e)}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()


# Keep the old backend for backward compatibility
class App2AuthBackend(BaseBackend):
    """Legacy authentication backend - now redirects to Oracle"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Redirect to Oracle authentication
        oracle_backend = OracleAuthBackend()
        return oracle_backend.authenticate(request, username, password, **kwargs)
    
    def get_user(self, user_id):
        # Redirect to Oracle user retrieval
        oracle_backend = OracleAuthBackend()
        return oracle_backend.get_user(user_id) 