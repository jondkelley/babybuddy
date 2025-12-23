#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
until nc -z db 5432; do
  echo "Database port not yet available..."
  sleep 1
done
echo "Database port is open, waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to actually be ready to accept connections
until python manage.py migrate --check 2>/dev/null; do
  echo "PostgreSQL is starting up, waiting..."
  sleep 2
done
echo "Database is ready!"

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
exec gunicorn babybuddy.wsgi:application --bind 0.0.0.0:8000 --workers 3
