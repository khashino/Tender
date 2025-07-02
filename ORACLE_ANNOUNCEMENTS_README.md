# Oracle Announcements and News System

This system allows your Django application to read announcements and news data directly from Oracle database tables, similar to how your login and notification system works.

## Setup Instructions

### 1. Create Oracle Database Tables

Run the SQL script `oracle_tables_announcements_news.sql` in your Oracle database:

```bash
sqlplus your_username/your_password@your_connection_string @oracle_tables_announcements_news.sql
```

Or execute the SQL statements manually in Oracle SQL Developer or similar tool.

### 2. Tables Created

The script creates two main tables:

- **KRN_ANNOUNCEMENTS**: Stores announcements (اعلانات)
- **KRN_LATEST_NEWS**: Stores news items (آخرین اخبار)

Both tables include:
- Auto-incrementing primary key
- Title and content fields
- Created/updated timestamps
- Active status flag
- Optional group_id for filtering by user groups

### 3. Test the Setup

Use the Django management command to test the functionality:

```bash
# Test basic functionality
python manage.py test_oracle_announcements

# Test with a specific group ID
python manage.py test_oracle_announcements --group-id 1

# Create sample data and test
python manage.py test_oracle_announcements --create-sample
```

### 4. How It Works

The system works similarly to your existing Oracle authentication and notification system:

1. **Oracle Functions**: Located in `app2/oracle_utils.py`
   - `get_oracle_announcements(group_id=None, limit=5)`
   - `get_oracle_latest_news(group_id=None, limit=5)`
   - `get_oracle_announcement_count(group_id=None)`
   - `get_oracle_news_count(group_id=None)`
   - `create_oracle_announcement(title, content, group_id=None)`
   - `create_oracle_news(title, content, image_url=None, group_id=None)`

2. **Views Updated**: 
   - `home` view now reads from Oracle instead of Django models
   - `news_announcements` view also uses Oracle data
   - Both views handle Oracle user group filtering

3. **Template Compatibility**: The data is converted to match the existing template structure, so your templates don't need changes.

## Features

### Group-Based Filtering
- If a user is an Oracle user, announcements and news are filtered by their group_id
- Items with `GROUP_ID = NULL` are visible to all users
- Items with specific `GROUP_ID` are only visible to users in that group

### Error Handling
- If Oracle queries fail, the system falls back to empty lists
- Error messages are shown to authenticated users
- Logs errors for debugging

### Performance Optimizations
- Database indexes on frequently queried columns
- Configurable limits for queries
- Connection pooling through Django's database connections

## Usage Examples

### Adding Data via Oracle
```sql
-- Add a general announcement (visible to all)
INSERT INTO KRN_ANNOUNCEMENTS (TITLE, CONTENT, GROUP_ID) 
VALUES ('سیستم به روزرسانی شد', 'سیستم با ویژگی‌های جدید به روزرسانی شده است.', NULL);

-- Add a group-specific announcement
INSERT INTO KRN_ANNOUNCEMENTS (TITLE, CONTENT, GROUP_ID) 
VALUES ('اعلان ویژه گروه 1', 'این اعلان فقط برای کاربران گروه 1 قابل مشاهده است.', 1);

-- Add news with image
INSERT INTO KRN_LATEST_NEWS (TITLE, CONTENT, IMAGE_URL, GROUP_ID) 
VALUES ('خبر جدید', 'محتوای خبر...', '/static/images/news.jpg', NULL);
```

### Adding Data via Django
```python
from app2.oracle_utils import create_oracle_announcement, create_oracle_news

# Create announcement
announcement = create_oracle_announcement(
    title='اعلان جدید',
    content='متن اعلان...',
    group_id=1  # Optional
)

# Create news
news = create_oracle_news(
    title='خبر جدید',
    content='متن خبر...',
    image_url='/static/images/news.jpg',  # Optional
    group_id=None  # Visible to all
)
```

## Database Schema

### KRN_ANNOUNCEMENTS Table
```sql
ANNOUNCEMENT_ID  NUMBER (Primary Key, Auto-increment)
TITLE           VARCHAR2(200) NOT NULL
CONTENT         CLOB NOT NULL  
CREATED_AT      DATE DEFAULT SYSDATE
UPDATED_AT      DATE DEFAULT SYSDATE
IS_ACTIVE       NUMBER(1) DEFAULT 1
GROUP_ID        NUMBER (Optional)
```

### KRN_LATEST_NEWS Table
```sql
NEWS_ID         NUMBER (Primary Key, Auto-increment)
TITLE           VARCHAR2(200) NOT NULL
CONTENT         CLOB NOT NULL
IMAGE_URL       VARCHAR2(500) (Optional)
CREATED_AT      DATE DEFAULT SYSDATE
UPDATED_AT      DATE DEFAULT SYSDATE
IS_ACTIVE       NUMBER(1) DEFAULT 1
GROUP_ID        NUMBER (Optional)
```

## Migration from Django Models

If you have existing data in Django models, you can migrate it to Oracle:

```python
# Example migration script
from app2.models import Announcement, LatestNews
from app2.oracle_utils import create_oracle_announcement, create_oracle_news

# Migrate announcements
for ann in Announcement.objects.filter(is_active=True):
    create_oracle_announcement(
        title=ann.title,
        content=ann.content,
        group_id=None  # Set appropriate group_id if needed
    )

# Migrate news
for news in LatestNews.objects.filter(is_active=True):
    create_oracle_news(
        title=news.title,
        content=news.content,
        image_url=news.image.url if news.image else None,
        group_id=None
    )
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify Oracle connection settings in Django settings
2. **Permission Errors**: Ensure Oracle user has CREATE TABLE, INSERT, SELECT permissions
3. **Data Not Showing**: Check IS_ACTIVE flag and GROUP_ID filtering
4. **Encoding Issues**: Ensure Oracle database supports Unicode/UTF-8

### Debugging

Enable logging to see detailed Oracle query information:

```python
import logging
logging.getLogger('app2.oracle_utils').setLevel(logging.DEBUG)
```

### Testing Connection

```bash
python manage.py test_oracle
python manage.py test_oracle_announcements
```

## Benefits of Oracle Integration

1. **Centralized Data**: All data in one Oracle database
2. **Better Performance**: Direct database queries without Django ORM overhead
3. **Group-Based Access**: Fine-grained control over who sees what
4. **Scalability**: Oracle handles large datasets efficiently
5. **Consistency**: Same pattern as your existing Oracle authentication system 