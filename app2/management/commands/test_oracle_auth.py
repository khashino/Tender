"""
Django management command to test Oracle authentication
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from app2.auth_backend import OracleUser
from app2.oracle_utils import execute_oracle_query


class Command(BaseCommand):
    help = 'Test Oracle authentication with KRN_USER_DETAIL table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to test authentication'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password to test authentication'
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all active public users'
        )

    def handle(self, *args, **options):
        self.stdout.write('Testing Oracle Authentication...')
        
        # List users if requested
        if options['list_users']:
            self.list_active_users()
            return
        
        # Test authentication if username and password provided
        if options['username'] and options['password']:
            self.test_authentication(options['username'], options['password'])
        else:
            self.stdout.write(
                self.style.WARNING('Please provide --username and --password to test authentication, or use --list-users to see available users')
            )
    
    def list_active_users(self):
        """List all active public users"""
        try:
            query = """
            SELECT a.USER_ID,
                   a.USER_NAME,
                   a.NAME,
                   a.FAMILY,
                   a.PHONE_NUMBER,
                   a.CREATED_DATE,
                   a.VENDOR_ID
              FROM KRN_USER_DETAIL a
             WHERE dashboard_type = 'Public' 
               AND is_active = 1
             ORDER BY a.USER_NAME
            """
            
            results = execute_oracle_query(query)
            
            if results:
                self.stdout.write(f'\nFound {len(results)} active public users:')
                self.stdout.write('-' * 80)
                
                for user in results:
                    full_name = f"{user.get('NAME', '')} {user.get('FAMILY', '')}".strip()
                    self.stdout.write(
                        f"ID: {user['USER_ID']:<5} | "
                        f"Username: {user['USER_NAME']:<15} | "
                        f"Name: {full_name:<25} | "
                        f"Phone: {user.get('PHONE_NUMBER', 'N/A'):<15} | "
                        f"Vendor: {user.get('VENDOR_ID', 'N/A')}"
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('No active public users found in KRN_USER_DETAIL table')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error listing users: {str(e)}')
            )
    
    def test_authentication(self, username, password):
        """Test authentication with given credentials"""
        try:
            self.stdout.write(f'\nTesting authentication for username: {username}')
            
            # Test using Django authenticate function
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if isinstance(user, OracleUser):
                    self.stdout.write(
                        self.style.SUCCESS('✓ Oracle authentication successful!')
                    )
                    
                    # Display user information
                    self.stdout.write('\nUser Information:')
                    self.stdout.write('-' * 40)
                    self.stdout.write(f"User ID: {user.user_id}")
                    self.stdout.write(f"Username: {user.username}")
                    self.stdout.write(f"Full Name: {user.get_full_name()}")
                    self.stdout.write(f"Phone: {user.phone_number or 'N/A'}")
                    self.stdout.write(f"Address: {user.address or 'N/A'}")
                    self.stdout.write(f"Vendor ID: {user.vendor_id or 'N/A'}")
                    self.stdout.write(f"Group ID: {user.group_id or 'N/A'}")
                    self.stdout.write(f"Dashboard Type: {user.dashboard_type}")
                    self.stdout.write(f"Created Date: {user.created_date}")
                    self.stdout.write(f"Is Active: {user.is_active}")
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Authentication successful (non-Oracle user)')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Authentication failed - Invalid username or password')
                )
                
                # Check if user exists but password is wrong
                check_query = """
                SELECT USER_NAME, IS_ACTIVE, DASHBOARD_TYPE
                  FROM KRN_USER_DETAIL
                 WHERE UPPER(user_name) = UPPER(%s)
                """
                
                check_results = execute_oracle_query(check_query, [username])
                
                if check_results:
                    user_info = check_results[0]
                    self.stdout.write(f"User '{username}' exists in database:")
                    self.stdout.write(f"  - Is Active: {user_info['IS_ACTIVE']}")
                    self.stdout.write(f"  - Dashboard Type: {user_info['DASHBOARD_TYPE']}")
                    
                    if user_info['IS_ACTIVE'] != 1:
                        self.stdout.write(
                            self.style.WARNING('  - User is not active!')
                        )
                    if user_info['DASHBOARD_TYPE'] != 'Public':
                        self.stdout.write(
                            self.style.WARNING('  - User dashboard type is not "Public"!')
                        )
                else:
                    self.stdout.write(f"User '{username}' not found in KRN_USER_DETAIL table")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing authentication: {str(e)}')
            ) 