"""
Django management command to test Oracle database connectivity
"""

from django.core.management.base import BaseCommand
from django.db import connections
from app2.oracle_utils import test_oracle_connection, execute_oracle_query


class Command(BaseCommand):
    help = 'Test Oracle database connection and execute sample queries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            help='Custom SELECT query to execute'
        )

    def handle(self, *args, **options):
        self.stdout.write('Testing Oracle database connection...')
        
        try:
            # Test basic connection
            success, message = test_oracle_connection()
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Oracle database connection successful! {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Oracle database connection failed! {message}')
                )
                return
            
            # Execute sample queries
            self.stdout.write('\nExecuting sample queries...')
            
            # Query 1: Get current user
            try:
                result = execute_oracle_query("SELECT USER FROM DUAL")
                self.stdout.write(f"Current user: {result[0]['USER']}")
            except Exception as e:
                self.stdout.write(f"Error getting current user: {str(e)}")
            
            # Query 2: Get current date
            try:
                result = execute_oracle_query("SELECT SYSDATE FROM DUAL")
                self.stdout.write(f"Current date: {result[0]['SYSDATE']}")
            except Exception as e:
                self.stdout.write(f"Error getting current date: {str(e)}")
            
            # Query 3: Count tables
            try:
                result = execute_oracle_query("SELECT COUNT(*) as TABLE_COUNT FROM USER_TABLES")
                self.stdout.write(f"Number of tables: {result[0]['TABLE_COUNT']}")
            except Exception as e:
                self.stdout.write(f"Error counting tables: {str(e)}")
            
            # Execute custom query if provided
            if options['query']:
                self.stdout.write(f'\nExecuting custom query: {options["query"]}')
                try:
                    results = execute_oracle_query(options['query'])
                    self.stdout.write(f"Query returned {len(results)} rows:")
                    
                    # Display first 5 results
                    for i, row in enumerate(results[:5]):
                        self.stdout.write(f"Row {i+1}: {row}")
                    
                    if len(results) > 5:
                        self.stdout.write(f"... and {len(results) - 5} more rows")
                        
                except Exception as e:
                    self.stdout.write(f"Error executing custom query: {str(e)}")
            
            self.stdout.write(
                self.style.SUCCESS('\n✓ Oracle database test completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Oracle database test failed: {str(e)}')
            ) 