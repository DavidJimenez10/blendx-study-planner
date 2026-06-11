#!/bin/sh
set -e

echo "Applying database migrations..."
uv run alembic upgrade head

echo "Seeding database..."
uv run python -m app.seed

echo "Starting FastAPI server..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
