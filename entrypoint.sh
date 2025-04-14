#!/bin/bash

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

echo "postgresql started"

python manage.py migrate

python manage.py runserver 0.0.0.0:8000
