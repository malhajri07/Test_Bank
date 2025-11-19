# Dockerfile for Exam Stellar Django Application
# Multi-stage build for optimized production image

# Stage 1: Build stage
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm for Tailwind CSS
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy theme static source and build Tailwind CSS
COPY theme/static_src/ theme/static_src/
WORKDIR /app/theme/static_src
RUN npm install && npm run build

# Stage 2: Production stage
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/django/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create django user
RUN useradd -m -u 1000 django && \
    mkdir -p /app /app/staticfiles /app/media && \
    chown -R django:django /app

# Copy Python dependencies from builder
COPY --from=builder --chown=django:django /root/.local /home/django/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=django:django . .

# Copy built Tailwind CSS from builder
COPY --from=builder --chown=django:django /app/theme/static/css/dist/ theme/static/css/dist/

# Copy entrypoint script
COPY --chown=django:django docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Switch to django user
USER django

# Expose port (Cloud Run uses PORT env var, defaults to 8080)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/ || exit 1

# Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
# Use PORT environment variable (Cloud Run sets this to 8080)
# Default to 8080 if PORT is not set
CMD gunicorn testbank_platform.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 3 --timeout 120

