import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from app2.models import App2User, Company
from shared_models.models import Tender

def generate_test_data():
    # Sample company names and domains
    company_names = [
        'پارس انرژی',
        'صنعت گستر ایرانیان',
        'توسعه فناوری آریا',
        'پیشگامان صنعت',
        'مهندسی نوآوران',
        'فن آوران پیشرو',
        'صنایع پترو پارس',
        'ساختمان سازان آینده',
        'تجهیزات صنعتی البرز',
        'مهندسی راه و ساختمان',
    ]
    
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    
    # Sample tender titles and descriptions
    tender_titles = [
        'تامین تجهیزات نیروگاهی',
        'احداث ساختمان اداری',
        'خرید قطعات یدکی',
        'نصب و راه اندازی سیستم تهویه',
        'تامین مواد اولیه پتروشیمی',
        'ساخت مخازن ذخیره سازی',
        'تعمیر و نگهداری تاسیسات',
        'تامین تجهیزات آزمایشگاهی',
        'اجرای پروژه فیبر نوری',
        'خرید تجهیزات IT',
    ]
    
    tender_descriptions = [
        'پروژه تامین و نصب تجهیزات نیروگاهی شامل توربین و ژنراتور',
        'ساخت ساختمان اداری 10 طبقه با زیربنای 5000 متر مربع',
        'تامین قطعات یدکی برای ماشین آلات صنعتی',
        'نصب و راه اندازی سیستم تهویه مطبوع صنعتی',
        'تامین مواد اولیه پتروشیمی برای خط تولید',
        'طراحی و ساخت مخازن ذخیره سازی مواد شیمیایی',
        'قرارداد سالیانه تعمیر و نگهداری تاسیسات صنعتی',
        'خرید و نصب تجهیزات آزمایشگاهی پیشرفته',
        'اجرای پروژه فیبر نوری در سطح شهر',
        'تامین تجهیزات IT و زیرساخت شبکه',
    ]
    
    print("Generating test data...")
    
    # Create App2Users and Companies
    for i in range(10):
        # Create App2User
        username = f'company_user_{i+1}'
        email = f'user{i+1}@{random.choice(domains)}'
        password = make_password('Test@123')  # All users will have password: Test@123
        
        user = App2User.objects.create(
            username=username,
            email=email,
            password=password,
            is_active=True
        )
        
        # Create Company
        company_name = company_names[i]
        registration_number = f'REG{random.randint(1000, 9999)}'
        economic_code = f'ECO{random.randint(10000, 99999)}'
        national_id = f'NAT{random.randint(1000000, 9999999)}'
        phone = f'021{random.randint(10000000, 99999999)}'
        
        Company.objects.create(
            user=user,
            name=company_name,
            registration_number=registration_number,
            economic_code=economic_code,
            national_id=national_id,
            phone=phone,
            address=f'تهران، خیابان {random.randint(1, 20)}، پلاک {random.randint(1, 100)}',
            website=f'http://www.{company_name.replace(" ", "")}.com',
            description=f'شرکت {company_name} فعال در زمینه صنعت و تجارت',
            is_verified=random.choice([True, False])
        )
        
        print(f"Created company: {company_name}")
    
    # Create Tenders
    now = datetime.now()
    
    for i in range(10):
        # Random dates
        published_date = now - timedelta(days=random.randint(1, 30))
        closing_date = published_date + timedelta(days=random.randint(15, 45))
        
        # Random status based on dates
        if closing_date < now:
            status = random.choice(['closed', 'awarded', 'cancelled'])
        else:
            status = random.choice(['draft', 'published'])
        
        # Random value between 1,000,000,000 and 10,000,000,000 Rials
        estimated_value = Decimal(random.randint(1000, 10000)) * 1000000
        
        tender = Tender.objects.create(
            title=tender_titles[i],
            description=tender_descriptions[i],
            reference_number=f'TDR-{published_date.strftime("%Y%m%d")}-{random.randint(100, 999)}',
            published_date=published_date,
            closing_date=closing_date,
            status=status,
            estimated_value=estimated_value,
            currency='IRR'  # Iranian Rial
        )
        
        print(f"Created tender: {tender.title}")

if __name__ == '__main__':
    generate_test_data() 