#!/bin/bash
set -e

echo "=== AutoService Pro — Production Deploy ==="

echo ">> Building containers..."
docker-compose -f docker-compose.prod.yml build

echo ">> Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo ">> Waiting for database..."
sleep 5

echo ">> Running migrations..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

echo ">> Collecting static files..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

echo ">> Loading initial data..."
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata initial_data || true
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata notification_templates || true

echo ""
echo "=== Deployed successfully! ==="
echo "    Web:   http://localhost"
echo "    Admin: http://localhost/admin/"
echo ""
echo "To create superuser:"
echo "    docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
