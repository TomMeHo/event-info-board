#!/bin/bash
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Load fixtures (only inserts, no duplicates due to primary key)
echo "Loading fixtures..."
python manage.py loaddata rank

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 eventBoard.wsgi:application
