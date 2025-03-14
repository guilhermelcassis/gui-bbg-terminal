#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Upgrading pip..."
pip install --upgrade pip

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Applying database migrations..."
python manage.py migrate

echo "Checking deployment readiness..."
python manage.py check --deploy

echo "Build completed successfully!" 