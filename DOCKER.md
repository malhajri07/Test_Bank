# Docker Setup Guide for Exam Stellar

This guide explains how to run the Exam Stellar Django application using Docker and Docker Compose.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/malhajri07/Test_Bank.git
cd Test_Bank
```

### 2. Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and update the following:
- `SECRET_KEY` - Generate a new secret key
- `DB_PASSWORD` - Set a secure database password
- `STRIPE_*` - Add your Stripe keys (if using payments)

### 3. Build and Run with Docker Compose

**Development mode:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

**Production mode:**
```bash
docker-compose up --build
```

The application will be available at:
- **Web**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/
- **Nginx** (production): http://localhost:80

### 4. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Or set `CREATE_SUPERUSER=true` in `.env` for automatic superuser creation (development only).

## Docker Commands

### Start Services

```bash
# Start all services
docker-compose up -d

# Start with logs
docker-compose up

# Start specific services
docker-compose up db web
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

### Execute Commands

```bash
# Django shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run tests
docker-compose exec web pytest

# Run load tests
docker-compose exec web python manage.py run_load_test --scenario=normal --users=10
```

### Database Access

```bash
# PostgreSQL shell
docker-compose exec db psql -U postgres -d testbank_db

# Backup database
docker-compose exec db pg_dump -U postgres testbank_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres testbank_db < backup.sql
```

## Development Workflow

### With Tailwind CSS Watcher

```bash
# Start all services including Tailwind watcher
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up
```

### Hot Reload

The development setup includes volume mounts for hot reload:
- Code changes are reflected immediately
- Static files are served from volumes
- Database persists in named volumes

### Running Tests

```bash
# Run all tests
docker-compose exec web pytest

# Run specific test file
docker-compose exec web pytest stress_tests/benchmarks/

# Run with coverage
docker-compose exec web pytest --cov=.
```

## Production Deployment

### Build Production Image

```bash
docker build -t exam-stellar:latest .
```

### Run with Production Compose

```bash
# Update .env with production settings
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Start with Nginx
docker-compose --profile production up -d
```

### Environment Variables for Production

Ensure these are set in `.env`:
- `DEBUG=False`
- `SECRET_KEY` - Strong, random secret key
- `ALLOWED_HOSTS` - Your domain name
- `DB_PASSWORD` - Strong database password
- `STRIPE_*` - Production Stripe keys

### Static Files

Static files are collected automatically on container start. For Nginx:
- Static files: `/usr/share/nginx/html/static/`
- Media files: `/usr/share/nginx/html/media/`

## Docker Compose Services

### `db` - PostgreSQL Database
- Image: `postgres:15-alpine`
- Port: `5432`
- Volume: `postgres_data`
- Health check enabled

### `web` - Django Application
- Built from `Dockerfile`
- Port: `8000`
- Volumes: code, staticfiles, media
- Depends on: `db`

### `nginx` - Web Server (Production)
- Image: `nginx:alpine`
- Port: `80`
- Serves static files and reverse proxies to Django
- Only runs with `--profile production`

### `tailwind` - Tailwind CSS Watcher (Development)
- Built from `Dockerfile.dev`
- Watches for CSS changes
- Only runs with `--profile dev`

## Volumes

- `postgres_data` - PostgreSQL database files
- `static_volume` - Collected static files
- `media_volume` - User-uploaded media files

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec web python manage.py dbshell
```

### Permission Issues

If you encounter permission issues with volumes:

```bash
# Fix ownership
sudo chown -R $USER:$USER .
```

### Port Already in Use

If port 8000 or 5432 is already in use:

```bash
# Change ports in .env
WEB_PORT=8001
DB_PORT=5433
```

### Rebuild After Changes

```bash
# Rebuild without cache
docker-compose build --no-cache

# Rebuild specific service
docker-compose build --no-cache web
```

### Clear Everything

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean up Docker system
docker system prune -a
```

## Health Checks

The application includes health checks:
- Database: `pg_isready` check
- Web: HTTP check on `/`
- Container health status: `docker-compose ps`

## Security Notes

1. **Never commit `.env` file** - It contains sensitive information
2. **Use strong passwords** in production
3. **Set `DEBUG=False`** in production
4. **Use HTTPS** in production (configure SSL in Nginx)
5. **Regular backups** of the database volume
6. **Keep images updated** - Regularly rebuild with latest base images

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

