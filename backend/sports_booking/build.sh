#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if not exists
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@sportsclub.com',
        password='Admin@123',
        mobile_number='9000000000',
        is_mobile_verified=True
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
new_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if new_password:
    u = User.objects.filter(username='admin').first()
    if u:
        u.set_password(new_password)
        u.save()
        print('Admin password reset')
"