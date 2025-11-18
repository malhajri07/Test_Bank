#!/bin/bash
# Docker entrypoint script for Django application

set -e

echo "Starting Exam Stellar application..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
if command -v pg_isready > /dev/null 2>&1; then
    while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up - executing commands"
else
    # Fallback: simple sleep if pg_isready not available
    echo "Waiting 5 seconds for PostgreSQL to initialize..."
    sleep 5
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (for development)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF
fi

# Execute the command passed to docker run
exec "$@"

