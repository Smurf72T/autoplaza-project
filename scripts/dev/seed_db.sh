#!/bin/bash

echo "Seeding database..."

python manage.py migrate
python manage.py loaddata fixtures/*.json

echo "Database seeded successfully!"