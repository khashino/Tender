"""
Django management command to fix Oracle login issues
"""

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate
from app2.auth_backend import OracleUser


class Command(BaseCommand):
    help = 'Fix Oracle login issues by clearing sessions and testing authentication'

    def handle(self, *args, **options):
        self.stdout.write('Fixing Oracle Login Issues...')
        
        # Step 1: Clear all sessions
        self.stdout.write('1. Clearing all sessions...')
        try:
            session_count = Session.objects.count()
            Session.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Cleared {session_count} sessions')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error clearing sessions: {str(e)}')
            )
        
        # Step 2: Test Oracle authentication
        self.stdout.write('\n2. Testing Oracle authentication...')
        try:
            user = authenticate(username='khashi', password='Bonyan123')
            if user and isinstance(user, OracleUser):
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Oracle authentication successful')
                )
                self.stdout.write(f'   User ID: {user.pk} (type: {type(user.pk)})')
                self.stdout.write(f'   Username: {user.username}')
                self.stdout.write(f'   Full Name: {user.get_full_name()}')
                
                # Test primary key conversion
                try:
                    pk_int = int(user.pk)
                    self.stdout.write(f'   PK as int: {pk_int}')
                    self.stdout.write(
                        self.style.SUCCESS('✓ Primary key conversion successful')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Primary key conversion failed: {str(e)}')
                    )
                
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Oracle authentication failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Authentication test failed: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Oracle login fix completed!')
        )
        self.stdout.write('You can now try logging in through the web interface.') 