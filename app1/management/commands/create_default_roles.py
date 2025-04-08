from django.core.management.base import BaseCommand
from app1.models import Role

class Command(BaseCommand):
    help = 'Creates default roles with their permissions'

    def handle(self, *args, **options):
        # Get all role choices from the Role model
        role_choices = dict(Role.ROLE_CHOICES)
        
        # Create roles that don't exist yet
        for role_code, role_name in role_choices.items():
            role, created = Role.objects.get_or_create(
                name=role_code,
                defaults={
                    'description': f'نقش {role_name} در سیستم'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role_name}'))
                # Assign default permissions
                role.assign_default_permissions()
            else:
                self.stdout.write(self.style.WARNING(f'Role already exists: {role_name}'))
                
        self.stdout.write(self.style.SUCCESS('Successfully created/updated all default roles')) 