#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser only if it doesn't exist yet. Password comes from
# DJANGO_SUPERUSER_PASSWORD (Render env var) - never hardcoded, and
# this does NOT touch the password of an admin that already exists,
# so changing it via the UI sticks across future deploys.
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if password and not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@sportsclub.com',
        password=password,
        mobile_number='9000000000',
        is_mobile_verified=True
    )
    print('Superuser created successfully')
elif not password:
    print('DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation')
else:
    print('Superuser already exists - leaving password untouched')
"