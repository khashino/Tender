"""
Django management command to test Oracle announcements and news functionality
"""

from django.core.management.base import BaseCommand
from app2.oracle_utils import (
    test_oracle_connection, 
    get_oracle_announcements, 
    get_oracle_latest_news,
    get_oracle_announcement_count,
    get_oracle_news_count,
    create_oracle_announcement,
    create_oracle_news
)


class Command(BaseCommand):
    help = 'Test Oracle announcements and news functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Create sample announcements and news data'
        )
        parser.add_argument(
            '--group-id',
            type=int,
            help='Test with specific group ID'
        )

    def handle(self, *args, **options):
        self.stdout.write('Testing Oracle announcements and news functionality...')
        
        # Test basic connection
        try:
            success, message = test_oracle_connection()
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Oracle database connection successful!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Oracle database connection failed! {message}')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Connection test error: {str(e)}')
            )
            return
        
        # Create sample data if requested
        if options['create_sample']:
            self.stdout.write('\nCreating sample data...')
            try:
                # Create sample announcement
                announcement = create_oracle_announcement(
                    title='تست اعلان از Django',
                    content='این یک اعلان تستی است که از طریق Django management command ایجاد شده است.',
                    group_id=options.get('group_id')
                )
                if announcement:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Sample announcement created with ID: {announcement["ANNOUNCEMENT_ID"]}')
                    )
                
                # Create sample news
                news = create_oracle_news(
                    title='تست خبر از Django',
                    content='این یک خبر تستی است که از طریق Django management command ایجاد شده است.',
                    image_url='/static/images/test.jpg',
                    group_id=options.get('group_id')
                )
                if news:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Sample news created with ID: {news["NEWS_ID"]}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating sample data: {str(e)}')
                )
        
        # Test retrieving data
        self.stdout.write('\nTesting data retrieval...')
        
        try:
            # Test announcements
            announcements = get_oracle_announcements(group_id=options.get('group_id'), limit=5)
            announcement_count = get_oracle_announcement_count(group_id=options.get('group_id'))
            
            self.stdout.write(f'Announcements found: {len(announcements)} (Total active: {announcement_count})')
            for i, ann in enumerate(announcements, 1):
                self.stdout.write(f'  {i}. {ann["TITLE"]} (ID: {ann["ANNOUNCEMENT_ID"]})')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error retrieving announcements: {str(e)}')
            )
        
        try:
            # Test news
            news_list = get_oracle_latest_news(group_id=options.get('group_id'), limit=5)
            news_count = get_oracle_news_count(group_id=options.get('group_id'))
            
            self.stdout.write(f'News found: {len(news_list)} (Total active: {news_count})')
            for i, news in enumerate(news_list, 1):
                self.stdout.write(f'  {i}. {news["TITLE"]} (ID: {news["NEWS_ID"]})')
                if news.get('IMAGE_URL'):
                    self.stdout.write(f'     Image: {news["IMAGE_URL"]}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error retrieving news: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nTesting completed successfully!')
        ) 