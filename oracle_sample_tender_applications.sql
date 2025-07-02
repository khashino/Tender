-- Sample data for NAK.KRNR_TENDER_APPLICATION table
-- This script creates sample tender applications for testing

-- Insert sample vendor if not exists
INSERT INTO NAK.KRNR_VENDOR (VENDOR_ID, VENDOR_NAME, REGISTRATION_NUMBER, EMAIL, PHONE_NUMBER, ADDRESS)
SELECT 1, 'شرکت نمونه فناوری', '123456789', 'sample@company.com', '02112345678', 'تهران، خیابان ولیعصر'
FROM dual
WHERE NOT EXISTS (SELECT 1 FROM NAK.KRNR_VENDOR WHERE VENDOR_ID = 1);

-- Insert sample tender applications
-- Application 1: Submitted
INSERT INTO NAK.KRNR_TENDER_APPLICATION (
    APPLICATION_ID,
    TENDER_ID,
    VENDOR_ID,
    APPLICATION_STATUS,
    SUBMISSION_DATE,
    SUBMISSION_NOTES,
    CREATED_DATE
) VALUES (
    1,
    1, -- IT Infrastructure tender
    1, -- Sample vendor
    'Submitted',
    SYSDATE - 2,
    'ما آماده اجرای این پروژه فناوری اطلاعات هستیم. تیم متخصص ما با سابقه 10 سال کار در این زمینه قادر به انجام موفقیت‌آمیز این پروژه می‌باشد.',
    SYSDATE - 2
);

-- Application 2: Under Review
INSERT INTO NAK.KRNR_TENDER_APPLICATION (
    APPLICATION_ID,
    TENDER_ID,
    VENDOR_ID,
    APPLICATION_STATUS,
    SUBMISSION_DATE,
    SUBMISSION_NOTES,
    CREATED_DATE
) VALUES (
    2,
    2, -- Construction Project tender
    1, -- Sample vendor
    'Under Review',
    SYSDATE - 5,
    'شرکت ما با بیش از 15 سال تجربه در حوزه ساختمان، آماده اجرای این پروژه ساختمانی است. نمونه کارهای قبلی ما در پورتفولیو موجود است.',
    SYSDATE - 5
);

-- Application 3: Approved
INSERT INTO NAK.KRNR_TENDER_APPLICATION (
    APPLICATION_ID,
    TENDER_ID,
    VENDOR_ID,
    APPLICATION_STATUS,
    SUBMISSION_DATE,
    SUBMISSION_NOTES,
    CREATED_DATE
) VALUES (
    3,
    6, -- Office Supplies tender
    1, -- Sample vendor
    'Approved',
    SYSDATE - 10,
    'ما تامین‌کننده مواد اداری با کیفیت بالا هستیم. قیمت‌های رقابتی و تحویل سریع از مزایای ما است.',
    SYSDATE - 10
);

-- Application 4: Rejected
INSERT INTO NAK.KRNR_TENDER_APPLICATION (
    APPLICATION_ID,
    TENDER_ID,
    VENDOR_ID,
    APPLICATION_STATUS,
    SUBMISSION_DATE,
    SUBMISSION_NOTES,
    CREATED_DATE
) VALUES (
    4,
    4, -- Catering Services tender
    1, -- Sample vendor
    'Rejected',
    SYSDATE - 15,
    'شرکت تغذیه ما با استانداردهای بهداشتی بالا آماده ارائه خدمات پذیرایی است.',
    SYSDATE - 15
);

-- Commit the changes
COMMIT;

-- Display the inserted records
SELECT 
    ta.APPLICATION_ID,
    ta.TENDER_ID,
    t.TITLE as TENDER_TITLE,
    ta.APPLICATION_STATUS,
    ta.SUBMISSION_DATE,
    ta.SUBMISSION_NOTES
FROM NAK.KRNR_TENDER_APPLICATION ta
JOIN NAK.KRNR_TENDER t ON ta.TENDER_ID = t.TENDER_ID
WHERE ta.VENDOR_ID = 1
ORDER BY ta.SUBMISSION_DATE DESC; 