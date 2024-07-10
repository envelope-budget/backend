#!/bin/bash

# Exit on any error
set -e

# Run migrations
echo "🚀 Running database migrations..."
python manage.py migrate

# Create superuser if specified
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "👤 Creating superuser..."
  python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
END
fi

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start Nginx and Gunicorn
echo "🚀 Starting Nginx and Gunicorn..."
service nginx start
exec gunicorn --bind 0.0.0.0:8000 budgetapp.wsgi:application --workers 2 --log-level debug
