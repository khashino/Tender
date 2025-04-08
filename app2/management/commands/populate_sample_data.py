from django.core.management.base import BaseCommand
from app2.models import App2User, Announcement, LatestNews, Message, Notification
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populates the database with sample data for Announcement, LatestNews, Message, and Notification models'

    def handle(self, *args, **kwargs):
        # Get or create a test user
        test_user, created = App2User.objects.get_or_create(
            username='test2',
            defaults={
                'email': 'test@test.com',
                'password': 'Bonyan@123'
            }
        )

        # Create sample announcements
        announcements = [
            {
                'title': 'به روزرسانی سیستم',
                'content': 'سیستم در تاریخ 1403/01/15 به روزرسانی خواهد شد.'
            },
            {
                'title': 'تعطیلی نوروز',
                'content': 'سیستم در تعطیلات نوروز 1403 از تاریخ 1 تا 13 فروردین تعطیل خواهد بود.'
            },
            {
                'title': 'تغییرات جدید',
                'content': 'امکانات جدید به سیستم اضافه شده است.'
            }
        ]

        for announcement in announcements:
            Announcement.objects.create(
                title=announcement['title'],
                content=announcement['content']
            )

        # Create sample latest news
        news_items = [
            {
                'title': 'افتتاح پروژه جدید',
                'content': 'پروژه جدید در منطقه صنعتی شهرک صنعتی به بهره‌برداری رسید.',
                'image': None
            },
            {
                'title': 'همایش سالانه',
                'content': 'همایش سالانه شرکت‌ها در تاریخ 1403/02/01 برگزار خواهد شد.',
                'image': None
            },
            {
                'title': 'جایزه بهترین شرکت',
                'content': 'شرکت برتر سال 1402 معرفی شد.',
                'image': None
            }
        ]

        for news in news_items:
            LatestNews.objects.create(
                title=news['title'],
                content=news['content'],
                image=news['image']
            )

        # Create sample messages
        messages = [
            {
                'subject': 'خوش آمدید',
                'content': 'به سیستم خوش آمدید. لطفاً اطلاعات خود را تکمیل کنید.'
            },
            {
                'subject': 'تایید حساب کاربری',
                'content': 'حساب کاربری شما با موفقیت تایید شد.'
            },
            {
                'subject': 'یادآوری',
                'content': 'لطفاً اسناد خود را به روزرسانی کنید.'
            }
        ]

        for message in messages:
            Message.objects.create(
                receiver=test_user,
                subject=message['subject'],
                content=message['content']
            )

        # Create sample notifications
        notification_types = ['info', 'warning', 'success', 'error']
        notifications = [
            {
                'title': 'اطلاعیه عمومی',
                'message': 'سیستم در حال به روزرسانی است.',
                'notification_type': 'info'
            },
            {
                'title': 'هشدار امنیتی',
                'message': 'لطفاً رمز عبور خود را تغییر دهید.',
                'notification_type': 'warning'
            },
            {
                'title': 'موفقیت',
                'message': 'عملیات با موفقیت انجام شد.',
                'notification_type': 'success'
            },
            {
                'title': 'خطا در سیستم',
                'message': 'مشکلی در سیستم رخ داده است.',
                'notification_type': 'error'
            }
        ]

        for notification in notifications:
            Notification.objects.create(
                title=notification['title'],
                message=notification['message'],
                notification_type=notification['notification_type']
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated sample data')) 