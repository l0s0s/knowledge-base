#!/bin/bash

set -e

echo "Setting up Knowledge Base API..."

if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

echo "Building Docker containers..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for database to be ready..."
sleep 10

echo "Running migrations..."
docker-compose exec -T web python manage.py migrate --noinput

echo "Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "Setup complete!"
echo ""
echo "Access points:"
echo "  - API: http://localhost:8000/knowledge/"
echo "  - API Endpoint Docs: open any endpoint in browser (e.g., /knowledge/)"
echo "  - Admin: http://localhost:8000/admin/"
echo ""
echo "To create a superuser, run:"
echo "  docker-compose exec web python manage.py createsuperuser"
echo ""
echo "To run tests:"
echo "  make test"
