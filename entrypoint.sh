#!/bin/sh

# This script is the entrypoint for the 'web' container.
# It runs essential setup commands before starting the main application.

# Wait for the database to be ready (optional but good practice)
# echo "Waiting for postgres..."
# while ! nc -z db 5432; do
#   sleep 0.1
# done
# echo "PostgreSQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# The "exec" command is important. It replaces the shell process with the command
# that was passed to the container. This ensures that signals (like stopping the container)
# are passed correctly to the Gunicorn process.
exec "$@"
