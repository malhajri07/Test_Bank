# Database Access Guide

## Database Information

### Database Type
**PostgreSQL** (Postgres)

### Database Configuration
- **Database Name**: `testbank_db` (default, can be changed in `.env`)
- **Host**: `localhost`
- **Port**: `5432`
- **User**: Configured in `.env` file (default: `postgres` or your system username)

### CMS Tables in Database

All CMS content is stored in the following PostgreSQL tables:

1. **`cms_page`** - Stores all CMS pages (About, Terms, Privacy, etc.)
2. **`cms_announcement`** - Stores announcements/banners
3. **`cms_media`** - Stores uploaded media files (images, documents, etc.)
4. **`cms_contentblock`** - Stores reusable content blocks

## How to Access the Database

### Method 1: Django Admin (Easiest - Recommended)

**URL**: http://localhost:8000/admin/

1. Log in with your superuser credentials
2. Navigate to **CMS** section
3. Access:
   - **Pages** → `/admin/cms/page/`
   - **Announcements** → `/admin/cms/announcement/`
   - **Media** → `/admin/cms/media/`
   - **Content Blocks** → `/admin/cms/contentblock/`

**Advantages**:
- User-friendly interface
- Rich text editor for content
- File uploads
- No SQL knowledge needed

### Method 2: Django Shell (Python ORM)

Access database using Django's ORM (Object-Relational Mapping):

```bash
cd /Users/mohammedalhajri/Test_Bank
source venv/bin/activate
python manage.py shell
```

**Example Commands in Django Shell**:

```python
# Import CMS models
from cms.models import Page, Announcement, Media, ContentBlock

# Get all published pages
pages = Page.objects.filter(status='published')
for page in pages:
    print(f"{page.title} - {page.slug}")

# Get active announcements
from django.utils import timezone
now = timezone.now()
announcements = Announcement.objects.filter(
    is_active=True,
    start_date__lte=now,
    end_date__gte=now
)
for ann in announcements:
    print(f"{ann.title} - {ann.announcement_type}")

# Create a new page
new_page = Page.objects.create(
    title="Test Page",
    slug="test-page",
    content="<p>This is test content</p>",
    status="published"
)

# Update a page
page = Page.objects.get(slug='about-us')
page.content = "<p>Updated content</p>"
page.save()

# Delete a page
Page.objects.get(slug='test-page').delete()

# Get all media files
media = Media.objects.all()
for m in media:
    print(f"{m.title} - {m.file.url}")
```

### Method 3: Direct PostgreSQL Access (psql)

Connect directly to PostgreSQL using command line:

```bash
# Connect to PostgreSQL
psql -U your_username -d testbank_db

# Or if using default postgres user
psql -U postgres -d testbank_db
```

**Useful SQL Commands**:

```sql
-- List all tables
\dt

-- List CMS tables
\dt cms_*

-- View all pages
SELECT id, title, slug, status, created_at FROM cms_page;

-- View all announcements
SELECT id, title, announcement_type, is_active, show_on_homepage 
FROM cms_announcement;

-- View page content
SELECT title, content FROM cms_page WHERE slug = 'about-us';

-- Update a page
UPDATE cms_page 
SET content = '<p>New content</p>' 
WHERE slug = 'about-us';

-- Count records
SELECT COUNT(*) FROM cms_page;
SELECT COUNT(*) FROM cms_announcement;

-- Exit psql
\q
```

### Method 4: Django Database Shell

Django's database shell (direct SQL access):

```bash
python manage.py dbshell
```

This opens a PostgreSQL shell connected to your database. You can run SQL commands directly.

### Method 5: Database GUI Tools

Use graphical tools to access PostgreSQL:

**Popular Options**:
1. **pgAdmin** - Official PostgreSQL admin tool
   - Download: https://www.pgadmin.org/
   - Connect using: localhost:5432, database: testbank_db

2. **DBeaver** - Universal database tool
   - Download: https://dbeaver.io/
   - Supports PostgreSQL

3. **TablePlus** (Mac) - Modern database client
   - Download: https://tableplus.com/

4. **Postico** (Mac) - PostgreSQL client
   - Download: https://eggerapps.at/postico/

**Connection Details for GUI Tools**:
- **Host**: localhost
- **Port**: 5432
- **Database**: testbank_db
- **User**: (from your `.env` file)
- **Password**: (from your `.env` file)

## Database Schema for CMS Tables

### cms_page Table Structure
```sql
CREATE TABLE cms_page (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    content TEXT,
    meta_title VARCHAR(200),
    meta_description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    is_featured BOOLEAN DEFAULT FALSE,
    order INTEGER DEFAULT 0,
    author_id INTEGER REFERENCES accounts_customuser(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    published_at TIMESTAMP
);
```

### cms_announcement Table Structure
```sql
CREATE TABLE cms_announcement (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    announcement_type VARCHAR(20) DEFAULT 'info',
    is_active BOOLEAN DEFAULT TRUE,
    show_on_homepage BOOLEAN DEFAULT TRUE,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    link_url VARCHAR(200),
    link_text VARCHAR(100),
    author_id INTEGER REFERENCES accounts_customuser(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Quick Access Commands

### View Database Connection Info
```bash
python manage.py shell
```
Then:
```python
from django.conf import settings
print(settings.DATABASES['default'])
```

### Check Database Tables
```bash
python manage.py dbshell
```
Then:
```sql
\dt
```

### Export CMS Data
```bash
# Export all CMS pages
python manage.py dumpdata cms.Page > cms_pages.json

# Export all announcements
python manage.py dumpdata cms.Announcement > cms_announcements.json

# Export all CMS data
python manage.py dumpdata cms > cms_all.json
```

### Import CMS Data
```bash
python manage.py loaddata cms_all.json
```

## Important Notes

1. **All CMS content is stored in PostgreSQL** - Pages, announcements, media metadata, and content blocks
2. **Media files** are stored in the `media/` directory, but their metadata (title, description, etc.) is in the database
3. **Rich text content** is stored as HTML in the database
4. **Always backup** before making direct database changes
5. **Use Django Admin** for most operations - it's safer and includes validation

## Environment Variables

Your database connection is configured in `.env` file:

```env
DB_NAME=testbank_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

To check your current database settings:
```bash
python manage.py shell
```
```python
from django.conf import settings
db = settings.DATABASES['default']
print(f"Database: {db['NAME']}")
print(f"User: {db['USER']}")
print(f"Host: {db['HOST']}")
print(f"Port: {db['PORT']}")
```

