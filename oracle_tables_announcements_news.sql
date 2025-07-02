-- Oracle Database Tables for Announcements and News
-- Run these CREATE TABLE statements in your Oracle database

-- Table for Announcements (اعلانات)
CREATE TABLE KRN_ANNOUNCEMENTS (
    ANNOUNCEMENT_ID NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    TITLE VARCHAR2(200) NOT NULL,
    CONTENT CLOB NOT NULL,
    CREATED_AT DATE DEFAULT SYSDATE NOT NULL,
    UPDATED_AT DATE DEFAULT SYSDATE NOT NULL,
    IS_ACTIVE NUMBER(1) DEFAULT 1 CHECK (IS_ACTIVE IN (0, 1)),
    GROUP_ID NUMBER, -- Optional: to filter announcements by user group
    CONSTRAINT idx_announcements_active CHECK (IS_ACTIVE IN (0, 1))
);

-- Table for Latest News (آخرین اخبار)
CREATE TABLE KRN_LATEST_NEWS (
    NEWS_ID NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    TITLE VARCHAR2(200) NOT NULL,
    CONTENT CLOB NOT NULL,
    IMAGE_URL VARCHAR2(500), -- Store image path/URL as string
    CREATED_AT DATE DEFAULT SYSDATE NOT NULL,
    UPDATED_AT DATE DEFAULT SYSDATE NOT NULL,
    IS_ACTIVE NUMBER(1) DEFAULT 1 CHECK (IS_ACTIVE IN (0, 1)),
    GROUP_ID NUMBER, -- Optional: to filter news by user group
    CONSTRAINT idx_news_active CHECK (IS_ACTIVE IN (0, 1))
);

-- Create indexes for better performance
CREATE INDEX idx_announcements_created_at ON KRN_ANNOUNCEMENTS(CREATED_AT DESC);
CREATE INDEX idx_announcements_active ON KRN_ANNOUNCEMENTS(IS_ACTIVE);
CREATE INDEX idx_announcements_group ON KRN_ANNOUNCEMENTS(GROUP_ID);

CREATE INDEX idx_news_created_at ON KRN_LATEST_NEWS(CREATED_AT DESC);
CREATE INDEX idx_news_active ON KRN_LATEST_NEWS(IS_ACTIVE);
CREATE INDEX idx_news_group ON KRN_LATEST_NEWS(GROUP_ID);

-- Create triggers to automatically update UPDATED_AT column
CREATE OR REPLACE TRIGGER trg_announcements_updated_at
    BEFORE UPDATE ON KRN_ANNOUNCEMENTS
    FOR EACH ROW
BEGIN
    :NEW.UPDATED_AT := SYSDATE;
END;
/

CREATE OR REPLACE TRIGGER trg_news_updated_at
    BEFORE UPDATE ON KRN_LATEST_NEWS
    FOR EACH ROW
BEGIN
    :NEW.UPDATED_AT := SYSDATE;
END;
/

-- Insert sample data for testing
INSERT INTO KRN_ANNOUNCEMENTS (TITLE, CONTENT, GROUP_ID) VALUES 
('به روزرسانی سیستم', 'سیستم در تاریخ 1403/01/15 به روزرسانی خواهد شد. لطفاً آمادگی لازم را داشته باشید.', NULL);

INSERT INTO KRN_ANNOUNCEMENTS (TITLE, CONTENT, GROUP_ID) VALUES 
('تعطیلی نوروز', 'سیستم در تعطیلات نوروز 1403 از تاریخ 1 تا 13 فروردین تعطیل خواهد بود.', NULL);

INSERT INTO KRN_ANNOUNCEMENTS (TITLE, CONTENT, GROUP_ID) VALUES 
('امکانات جدید', 'امکانات جدید به سیستم اضافه شده است. جهت آشنایی با آنها راهنما را مطالعه کنید.', NULL);

INSERT INTO KRN_LATEST_NEWS (TITLE, CONTENT, IMAGE_URL, GROUP_ID) VALUES 
('راه‌اندازی پورتال جدید', 'پورتال جدید مناقصات با امکانات پیشرفته راه‌اندازی شد.', '/static/images/news/portal.jpg', NULL);

INSERT INTO KRN_LATEST_NEWS (TITLE, CONTENT, IMAGE_URL, GROUP_ID) VALUES 
('آموزش استفاده از سیستم', 'جلسات آموزشی استفاده از سیستم جدید برگزار خواهد شد.', '/static/images/news/training.jpg', NULL);

INSERT INTO KRN_LATEST_NEWS (TITLE, CONTENT, IMAGE_URL, GROUP_ID) VALUES 
('تغییرات قوانین', 'قوانین جدید مناقصات ابلاغ شده است. لطفاً آنها را مطالعه کنید.', '/static/images/news/rules.jpg', NULL);

-- Commit the changes
COMMIT;

-- Verify the data was inserted
SELECT 'Announcements Count: ' || COUNT(*) FROM KRN_ANNOUNCEMENTS;
SELECT 'News Count: ' || COUNT(*) FROM KRN_LATEST_NEWS; 