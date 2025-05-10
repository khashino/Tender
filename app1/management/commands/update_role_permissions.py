from django.core.management.base import BaseCommand
from app1.models import Role
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Updates permissions for all roles'

    def handle(self, *args, **options):
        # Get all roles
        roles = Role.objects.all()
        
        # Get all ViewFlow permissions
        viewflow_permissions = Permission.objects.filter(
            content_type__app_label='viewflow'
        )
        
        # Update permissions for each role
        for role in roles:
            self.stdout.write(f'Updating permissions for role: {role.name}')
            
            # Clear existing permissions
            role.permissions.clear()
            
            # Get permissions for this role
            permission_codenames = role.ROLE_PERMISSIONS.get(role.name, [])
            
            # Get all permissions
            permissions = Permission.objects.filter(codename__in=permission_codenames)
            
            # Add ViewFlow permissions
            permissions = permissions | viewflow_permissions
            
            # Assign permissions to the role
            role.permissions.add(*permissions)
            
            # Add is_staff and is_superuser to users with this role
            for user_role in role.user_roles.all():
                user = user_role.user
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(f'Updated user {user.username} to staff and superuser')
            
            self.stdout.write(self.style.SUCCESS(f'Successfully updated permissions for role: {role.name}')) 