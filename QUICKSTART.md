# Quick Start Guide - Local Access

Follow these steps to run the Test Bank Platform locally on your machine.

## Step 1: Activate Virtual Environment

```bash
cd /Users/mohammedalhajri/Test_Bank
source venv/bin/activate
```

## Step 2: Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt
```

## Step 3: Set Up Environment Variables

Create a `.env` file in the project root (`/Users/mohammedalhajri/Test_Bank/.env`) with the following content:

```env
# Django Settings
SECRET_KEY=django-insecure-change-this-in-production-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DB_NAME=testbank_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Stripe Configuration (for testing, use test keys)
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email Configuration (for password reset - console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Note:** 
- Replace `your_postgres_password` with your actual PostgreSQL password
- For Stripe, you can use test keys from https://dashboard.stripe.com/test/apikeys
- For local development, you can leave Stripe keys empty if you just want to test the UI

## Step 4: Create PostgreSQL Database

Make sure PostgreSQL is installed and running, then create the database:

```bash
createdb testbank_db
```

Or using psql:
```bash
psql -U postgres
CREATE DATABASE testbank_db;
\q
```

## Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Step 6: Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user (username, email, password).

## Step 7: Set Up Tailwind CSS

```bash
# Install Tailwind dependencies
python manage.py tailwind install

# Build Tailwind CSS (one-time build)
python manage.py tailwind build
```

## Step 8: Start the Development Server

Open **TWO terminal windows**:

### Terminal 1 - Tailwind Watcher (for CSS auto-rebuild during development)
```bash
cd /Users/mohammedalhajri/Test_Bank
source venv/bin/activate
python manage.py tailwind start
```

### Terminal 2 - Django Server
```bash
cd /Users/mohammedalhajri/Test_Bank
source venv/bin/activate
python manage.py runserver
```

## Step 9: Access the Application

Open your web browser and navigate to:

- **Main Application**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## Quick Test

1. **Register a new user**: http://127.0.0.1:8000/accounts/register/
2. **Login**: http://127.0.0.1:8000/accounts/login/
3. **Browse categories**: http://127.0.0.1:8000/categories/
4. **View dashboard**: http://127.0.0.1:8000/accounts/dashboard/

## Creating Test Data

To test the application, you need to create some test data via the admin panel:

1. Go to http://127.0.0.1:8000/admin/
2. Login with your superuser credentials
3. Create a **Category** (e.g., "School Level", "College Level", "Professional")
4. Create a **Test Bank** in that category
5. Add **Questions** to the test bank
6. Add **Answer Options** to each question (mark correct answers)

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running: `pg_isready` or `brew services start postgresql` (on macOS)
- Check database credentials in `.env` file
- Verify database exists: `psql -l | grep testbank_db`

### Migration Errors
- Make sure all apps are in `INSTALLED_APPS` in `settings.py`
- Try: `python manage.py makemigrations accounts catalog payments practice`
- Then: `python manage.py migrate`

### Tailwind CSS Not Loading
- Run: `python manage.py tailwind install`
- Run: `python manage.py tailwind build`
- Check that `theme` app is in `INSTALLED_APPS`

### Port Already in Use
- If port 8000 is busy, use a different port:
  ```bash
  python manage.py runserver 8001
  ```
- Then access at: http://127.0.0.1:8001/

### Static Files Not Found
- For development, Django serves static files automatically when `DEBUG=True`
- If issues persist, run: `python manage.py collectstatic`

## Stopping the Servers

- Press `Ctrl+C` in both terminal windows to stop the servers
- Deactivate virtual environment: `deactivate`

## Next Steps

- Read `README.md` for detailed documentation
- Check `SETUP.md` for additional setup information
- Explore the admin panel to create test banks and questions
- Test the purchase flow (requires Stripe test keys)

