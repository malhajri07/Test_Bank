# Test Bank Platform

A comprehensive Django web application for managing and practicing test banks across different educational and professional levels.

## Features

- **User Authentication**: Registration, login, logout, and password reset
- **Test Bank Catalog**: Browse test banks by category (School, College, Professional)
- **Purchase System**: Stripe integration for purchasing test bank access
- **Practice Sessions**: Take practice tests with multiple question types (MCQ single, MCQ multi, True/False)
- **Results & Review**: View detailed results with explanations
- **User Dashboard**: Track purchased test banks and practice history
- **RTL Support**: Full support for Arabic and English with RTL/LTR layout switching
- **Responsive Design**: Modern, clean UI using Tailwind CSS

## Tech Stack

- **Backend**: Django 4.2+
- **Database**: PostgreSQL
- **Frontend**: Django Templates with Tailwind CSS
- **Payment**: Stripe Checkout
- **Testing**: pytest-django

## Project Structure

```
testbank_platform/
├── accounts/          # Authentication and user profiles
├── catalog/           # Categories, test banks, questions
├── payments/          # Purchase and Stripe integration
├── practice/          # User test sessions and results
├── templates/         # HTML templates
├── static/            # Static files (CSS, JS, images)
└── testbank_platform/ # Project settings
```

## Installation

### Option 1: Docker (Recommended)

See [DOCKER.md](DOCKER.md) for complete Docker setup instructions.

**Quick Start:**
```bash
# Copy environment file
cp env.example .env

# Edit .env with your settings

# Start with Docker Compose
docker-compose up --build
```

### Option 2: Local Development

### Prerequisites

- Python 3.9+
- PostgreSQL
- Node.js and npm (for Tailwind CSS)

### Setup Steps

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd Test_Bank
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Database Configuration
   DB_NAME=testbank_db
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_HOST=localhost
   DB_PORT=5432
   
   # Stripe Configuration
   STRIPE_PUBLIC_KEY=pk_test_your_key
   STRIPE_SECRET_KEY=sk_test_your_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
   ```

5. **Create PostgreSQL database**:
   ```bash
   createdb testbank_db
   ```

6. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

8. **Set up Tailwind CSS**:
   ```bash
   # Install Tailwind dependencies
   python manage.py tailwind install
   
   # Build Tailwind CSS (for production)
   python manage.py tailwind build
   
   # OR start Tailwind watcher (for development - auto-rebuilds on changes)
   python manage.py tailwind start
   ```
   
   Note: The theme app structure is already created. If you encounter issues, you may need to run migrations first:
   ```bash
   python manage.py migrate
   ```

## Running the Application

### Development Server

1. **Start Tailwind watcher** (in one terminal):
   ```bash
   python manage.py tailwind start
   ```

2. **Start Django development server** (in another terminal):
   ```bash
   python manage.py runserver
   ```

3. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Running Tests

Run tests using pytest:
```bash
pytest
```

Or using Django's test runner:
```bash
python manage.py test
```

## Key Commands

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Tailwind CSS Operations
```bash
# Install Tailwind (first time)
python manage.py tailwind install

# Build Tailwind CSS
python manage.py tailwind build

# Start Tailwind watcher (development)
python manage.py tailwind start
```

### Static Files
```bash
# Collect static files (production)
python manage.py collectstatic
```

## Configuration

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe Dashboard
3. Set up a webhook endpoint pointing to: `https://yourdomain.com/payments/webhook/stripe/`
4. Add webhook secret to `.env` file

### RTL/LTR Language Support

The application supports both English (LTR) and Arabic (RTL). Users can set their preferred language in their profile, which will:
- Switch the layout direction (LTR/RTL)
- Load appropriate fonts (Cairo for Arabic)
- Translate UI elements

## Usage Guide

### For Administrators

1. **Create Categories**: Go to Admin → Categories → Add Category
2. **Create Test Banks**: Go to Admin → Test Banks → Add Test Bank
3. **Add Questions**: Go to Admin → Questions → Add Question (with Answer Options)

### For Users

1. **Register**: Create an account at `/accounts/register/`
2. **Browse**: View test banks by category at `/categories/`
3. **Purchase**: Click "Buy Now" on any test bank detail page
4. **Practice**: Start practicing from your dashboard or test bank detail page
5. **Review**: View results and explanations after completing a practice session

## Security Considerations

- **Payment Webhooks**: Always verify Stripe webhook signatures (implemented in `payments/stripe_integration.py`)
- **Access Control**: Users can only practice test banks they've purchased
- **CSRF Protection**: All forms include CSRF tokens
- **Environment Variables**: Never commit `.env` file to version control

## Production Deployment

Before deploying to production:

1. Set `DEBUG=False` in settings
2. Configure `ALLOWED_HOSTS` properly
3. Set up proper database (PostgreSQL)
4. Configure static files serving (e.g., WhiteNoise or CDN)
5. Set up SSL/HTTPS
6. Configure email backend for password resets
7. Set up proper logging
8. Use environment variables for all secrets

## Code Comments

This project includes extensive code comments:
- **Docstrings**: All models, views, and important functions have docstrings
- **Inline Comments**: Complex logic and business rules are explained
- **Template Comments**: HTML templates include comments for major sections

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, please refer to the Django documentation or create an issue in the project repository.

