# build.sh
#!/usr/bin/env bash
# Exit on error
set -o errexit

# Create directories
mkdir -p logs
mkdir -p media/qr_codes

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create sample data (optional - remove in production)
python manage.py create_sample_data

# Create superuser if it doesn't exist
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        phone_number='+919999999999',
        username='admin',
        password='admin123'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

echo "Build completed successfully!"
