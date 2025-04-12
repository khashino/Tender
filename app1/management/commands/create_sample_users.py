from django.core.management.base import BaseCommand
from app1.models import App1User, Role, UserRole
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates sample users for each role in the app1 application'

    def handle(self, *args, **options):
        # Dictionary mapping role codes to sample user details
        sample_users = {
            'purchase_expert': {'username': 'purchase_expert', 'email': 'purchase@example.com', 'password': 'Bonyan@123', 'first_name': 'Purchase', 'last_name': 'Expert'},
            'team_leader': {'username': 'team_leader', 'email': 'teamlead@example.com', 'password': 'Bonyan@123', 'first_name': 'Team', 'last_name': 'Leader'},
            'supply_chain_manager': {'username': 'supply_manager', 'email': 'supply@example.com', 'password': 'Bonyan@123', 'first_name': 'Supply', 'last_name': 'Manager'},
            'technical_evaluator': {'username': 'tech_eval', 'email': 'techeval@example.com', 'password': 'Bonyan@123', 'first_name': 'Technical', 'last_name': 'Evaluator'},
            'financial_deputy': {'username': 'fin_deputy', 'email': 'findeputy@example.com', 'password': 'Bonyan@123', 'first_name': 'Financial', 'last_name': 'Deputy'},
            'financial_manager': {'username': 'fin_manager', 'email': 'finmanager@example.com', 'password': 'Bonyan@123', 'first_name': 'Financial', 'last_name': 'Manager'},
            'commercial_team_evaluator': {'username': 'commercial_eval', 'email': 'commercial@example.com', 'password': 'Bonyan@123', 'first_name': 'Commercial', 'last_name': 'Evaluator'},
            'financial_team_evaluator': {'username': 'financial_eval', 'email': 'fineval@example.com', 'password': 'Bonyan@123', 'first_name': 'Financial', 'last_name': 'Evaluator'},
            'transaction_commission': {'username': 'transaction_comm', 'email': 'transcomm@example.com', 'password': 'Bonyan@123', 'first_name': 'Transaction', 'last_name': 'Commission'},
            'ceo': {'username': 'ceo_user', 'email': 'ceo@example.com', 'password': 'Bonyan@123', 'first_name': 'CEO', 'last_name': 'User'},
        }
        
        # Get or create each role
        with transaction.atomic():
            for role_code, user_data in sample_users.items():
                self.stdout.write(f"Processing role: {role_code}")
                
                # Get or create the role
                role, role_created = Role.objects.get_or_create(
                    name=role_code,
                    defaults={'description': f'Role for {role_code}'}
                )
                
                if role_created:
                    self.stdout.write(f"Created role: {role}")
                    # Assign default permissions
                    role.assign_default_permissions()
                else:
                    self.stdout.write(f"Using existing role: {role}")
                
                # Check if user already exists
                if App1User.objects.filter(username=user_data['username']).exists():
                    user = App1User.objects.get(username=user_data['username'])
                    self.stdout.write(f"User {user.username} already exists.")
                    # Update password for existing user
                    user.set_password(user_data['password'])
                    user.save()
                    self.stdout.write(f"Updated password for user: {user.username}")
                else:
                    # Create the user
                    user = App1User.objects.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name']
                    )
                    self.stdout.write(f"Created user: {user.username}")
                
                # Assign role to user
                user_role, created = UserRole.objects.get_or_create(
                    user=user,
                    role=role
                )
                
                if created:
                    self.stdout.write(f"Assigned role {role} to user {user.username}")
                else:
                    self.stdout.write(f"User {user.username} already has role {role}")
            
            self.stdout.write(self.style.SUCCESS('Successfully created sample users for all roles')) 