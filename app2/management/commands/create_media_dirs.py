from django.core.management.base import BaseCommand
import os
from django.conf import settings
import stat
import sys

class Command(BaseCommand):
    help = 'Creates media directories for app2'

    def handle(self, *args, **options):
        try:
            # Get media root path
            media_root = os.path.abspath(settings.MEDIA_ROOT)
            
            if not media_root:
                self.stderr.write(self.style.ERROR('MEDIA_ROOT is not set in settings.py'))
                sys.exit(1)
            
            # Create base media directory
            self.stdout.write(f'Creating media directory at: {media_root}')
            os.makedirs(media_root, exist_ok=True)
            
            # Create app2 directory structure
            app2_dir = os.path.join(media_root, 'app2')
            self.stdout.write(f'Creating app2 directory at: {app2_dir}')
            os.makedirs(app2_dir, exist_ok=True)
            
            # Create subdirectories for logos and documents
            logos_dir = os.path.join(app2_dir, 'logos')
            documents_dir = os.path.join(app2_dir, 'documents')
            self.stdout.write(f'Creating logos directory at: {logos_dir}')
            self.stdout.write(f'Creating documents directory at: {documents_dir}')
            os.makedirs(logos_dir, exist_ok=True)
            os.makedirs(documents_dir, exist_ok=True)
            
            # Set permissions for the directories (only on Unix-like systems)
            if os.name != 'nt':  # Not Windows
                for root, dirs, files in os.walk(media_root):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
                    for f in files:
                        os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            
            self.stdout.write(self.style.SUCCESS('Successfully created media directories'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error creating directories: {str(e)}'))
            sys.exit(1) 