#!/bin/bash
set -e

echo "Starting Advanced Duplicate Scanner..."

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis is ready!"

# Run database migrations if needed
echo "Checking database migrations..."
# python -m alembic upgrade head || echo "No migrations to run"

# Start the application
echo "Starting FastAPI server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000