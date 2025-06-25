#!/bin/bash
set -e

echo "🚀 Starting EnvelopeBudget application..."

# Wait for database if using PostgreSQL
if [ "$DATABASE_ENGINE" = "postgresql" ]; then
  echo "⏳ Waiting for PostgreSQL..."
  while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
    sleep 0.1
  done
  echo "✅ PostgreSQL started"
fi

# Run migrations
echo "🚀 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if specified
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "👤 Creating superuser..."
  python manage.py shell <<END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
END
fi

# Compress static files
echo "📦 Compressing static files..."
python manage.py compress --force

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Test nginx configuration
echo "🔧 Testing Nginx configuration..."
nginx -t

# Start nginx in background
echo "🚀 Starting Nginx..."
nginx

# Start Gunicorn
echo "🦄 Starting Gunicorn..."
exec gunicorn budgetapp.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile -
