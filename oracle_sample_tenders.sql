-- Sample Tender Data for KRNR_TENDER Table
-- Insert test data for open tenders

-- Sample Tender 1: IT Infrastructure
INSERT INTO KRNR_TENDER (
    TENDER_TITLE,
    TENDER_DESCRIPTION,
    CATEGORY_ID,
    START_DATE,
    END_DATE,
    SUBMISSION_DEADLINE,
    BUDGET_AMOUNT,
    CURRENCY,
    STATUS,
    CREATED_BY_USER_ID
) VALUES (
    'تامین تجهیزات شبکه و زیرساخت IT',
    'مناقصه عمومی برای تامین تجهیزات شبکه شامل سوئیچ، روتر، سرور و تجهیزات امنیتی جهت ارتقاء زیرساخت فناوری اطلاعات شرکت. پیمانکار باید دارای گواهینامه‌های معتبر و تجربه حداقل 5 سال در این زمینه باشد.',
    1,
    TIMESTAMP '2025-01-01 08:00:00',
    TIMESTAMP '2025-03-15 18:00:00',
    TIMESTAMP '2025-02-15 15:00:00',
    5000000000,
    'ریال',
    'Open',
    1
);

-- Sample Tender 2: Construction Project
INSERT INTO KRNR_TENDER (
    TENDER_TITLE,
    TENDER_DESCRIPTION,
    CATEGORY_ID,
    START_DATE,
    END_DATE,
    SUBMISSION_DEADLINE,
    BUDGET_AMOUNT,
    CURRENCY,
    STATUS,
    CREATED_BY_USER_ID
) VALUES (
    'احداث ساختمان اداری مجتمع تجاری',
    'مناقصه احداث ساختمان اداری 10 طبقه با مساحت 5000 متر مربع شامل طراحی، ساخت و تحویل کامل پروژه. پیمانکار باید دارای رتبه بندی مناسب از سازمان برنامه و بودجه و تجربه اجرای پروژه‌های مشابه باشد.',
    2,
    TIMESTAMP '2025-01-10 09:00:00',
    TIMESTAMP '2025-07-30 17:00:00',
    TIMESTAMP '2025-02-20 16:00:00',
    15000000000,
    'ریال',
    'Open',
    1
);

-- Sample Tender 3: Transportation Services
INSERT INTO KRNR_TENDER (
    TENDER_TITLE,
    TENDER_DESCRIPTION,
    CATEGORY_ID,
    START_DATE,
    END_DATE,
    SUBMISSION_DEADLINE,
    BUDGET_AMOUNT,
    CURRENCY,
    STATUS,
    CREATED_BY_USER_ID
) VALUES (
    'خدمات حمل و نقل پرسنل',
    'مناقصه ارائه خدمات حمل و نقل پرسنل شرکت برای مدت یک سال شامل تامین اتوبوس، راننده، سوخت و نگهداری. مسیرهای مختلف شهری و ساعات کاری متنوع. ناوگان باید حداکثر 3 سال قدمت داشته باشد.',
    3,
    TIMESTAMP '2025-01-05 08:30:00',
    TIMESTAMP '2025-12-31 18:00:00',
    TIMESTAMP '2025-02-05 14:00:00',
    2000000000,
    'ریال',
    'Open',
    1
);

-- Sample Tender 4: Catering Services
INSERT INTO KRNR_TENDER (
    TENDER_TITLE,
    TENDER_DESCRIPTION,
    CATEGORY_ID,
    START_DATE,
    END_DATE,
    SUBMISSION_DEADLINE,
    BUDGET_AMOUNT,
    CURRENCY,
    STATUS,
    CREATED_BY_USER_ID
) VALUES (
    'تامین غذای پرسنل و مهمانان',
    'مناقصه تامین غذای پرسنل شرکت برای مدت یک سال شامل صبحانه، ناهار و عصرانه. متقاضی باید دارای مجوزهای بهداشتی معتبر و تجربه کافی در خدمات تغذیه سازمانی باشد. تعداد پرسنل حدود 500 نفر.',
    4,
    TIMESTAMP '2025-01-12 09:00:00',
    TIMESTAMP '2025-12-31 18:00:00',
    TIMESTAMP '2025-02-10 15:30:00',
    3000000000,
    'ریال',
    'Open',
    1
);

-- Sample Tender 5: Security Services
INSERT INTO KRNR_TENDER (
    TENDER_TITLE,
    TENDER_DESCRIPTION,
    CATEGORY_ID,
    START_DATE,
    END_DATE,
    SUBMISSION_DEADLINE,
    BUDGET_AMOUNT,
    CURRENCY,
    STATUS,
    CREATED_BY_USER_ID
) VALUES (
    'خدمات نگهبانی و حفاظت فیزیکی',
    'مناقصه ارائه خدمات نگهبانی و حفاظت فیزیکی مجموعه‌های شرکت به صورت 24 ساعته. شامل نگهبانان مسلح و غیرمسلح، سیستم کنترل تردد و گزارش‌دهی منظم. متقاضی باید دارای مجوز از وزارت کشور باشد.',
    5,
    TIMESTAMP '2025-01-08 10:00:00',
    TIMESTAMP '2025-12-31 23:59:59',
    TIMESTAMP '2025-02-08 16:00:00',
    4000000000,
    'ریال',
    'Open',
    1
);

-- Sample Tender 6: Office Supplies
INSERT INTO KRNR_TENDER (
    TENDER_TITLE,
    TENDER_DESCRIPTION,
    CATEGORY_ID,
    START_DATE,
    END_DATE,
    SUBMISSION_DEADLINE,
    BUDGET_AMOUNT,
    CURRENCY,
    STATUS,
    CREATED_BY_USER_ID
) VALUES (
    'تامین لوازم اداری و ملزومات',
    'مناقصه تامین لوازم اداری، کاغذ، لوازم التحریر، کارتریج چاپگر و سایر ملزومات اداری برای مدت یک سال. تحویل باید به صورت ماهانه و بر اساس درخواست انجام شود. کیفیت کالا باید مطابق استانداردهای تعیین شده باشد.',
    6,
    TIMESTAMP '2025-01-15 08:00:00',
    TIMESTAMP '2025-12-31 18:00:00',
    TIMESTAMP '2025-02-25 17:00:00',
    800000000,
    'ریال',
    'Open',
    1
);

-- Commit the changes
COMMIT;

-- Display inserted records
SELECT 
    TENDER_ID,
    TENDER_TITLE,
    STATUS,
    BUDGET_AMOUNT,
    CURRENCY,
    SUBMISSION_DEADLINE
FROM KRNR_TENDER 
WHERE STATUS = 'Open'
ORDER BY CREATED_DATE DESC; 