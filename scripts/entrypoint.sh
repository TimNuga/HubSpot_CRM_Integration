#!/usr/bin/env bash
set -e

# Wait for the DB to become available...
echo "Waiting for DB to be ready..."
/app/scripts/wait-for.sh "$DB_HOST" "$DB_PORT"

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

if [ "$RUN_TESTS" = "1" ]; then
  echo "Running pytest..."
  pytest --maxfail=1 --disable-warnings -q
  exit $?
else
  echo "Starting Gunicorn..."
  gunicorn "app.main:create_app()" --bind 0.0.0.0:5001 --workers 4
fi
