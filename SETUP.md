# Quick Setup Guide

## Initial Setup Checklist

1. ✅ Create virtual environment and install dependencies
2. ✅ Set up `.env` file with database and Stripe credentials
3. ✅ Create PostgreSQL database
4. ✅ Run migrations: `python manage.py makemigrations && python manage.py migrate`
5. ✅ Create superuser: `python manage.py createsuperuser`
6. ✅ Set up Tailwind: `python manage.py tailwind install`
7. ✅ Build Tailwind: `python manage.py tailwind build` (or use `tailwind start` for development)

## Running the Application

### Terminal 1 - Tailwind Watcher (Development)
```bash
source venv/bin/activate
python manage.py tailwind start
```

### Terminal 2 - Django Server
```bash
source venv/bin/activate
python manage.py runserver
```

## Creating Test Data

After setting up, you can create test data via Django admin:

1. Login to admin: http://127.0.0.1:8000/admin/
2. Create a Category (e.g., "School Level")
3. Create a TestBank in that category
4. Add Questions to the TestBank
5. Add AnswerOptions to each Question (mark correct answers)

## Testing Stripe Integration

For testing Stripe payments:

1. Use Stripe test mode keys in `.env`
2. Use test card numbers from Stripe documentation:
   - Success: 4242 4242 4242 4242
   - Decline: 4000 0000 0000 0002
3. Set up webhook endpoint in Stripe Dashboard pointing to:
   `http://your-domain.com/payments/webhook/stripe/`
4. Use Stripe CLI for local webhook testing:
   ```bash
   stripe listen --forward-to localhost:8000/payments/webhook/stripe/
   ```

## Common Issues

### Database Connection Error
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists: `createdb testbank_db`

### Tailwind CSS Not Loading
- Run `python manage.py tailwind install`
- Run `python manage.py tailwind build`
- Check that `theme` app is in `INSTALLED_APPS`

### Migration Errors
- Ensure all apps are in `INSTALLED_APPS` in `settings.py`
- Run `python manage.py makemigrations` for each app if needed
- Check for custom user model migration conflicts

### Static Files Not Found
- Run `python manage.py collectstatic` (production)
- Ensure `STATIC_URL` and `STATIC_ROOT` are configured
- Check `DEBUG=True` for development static file serving

