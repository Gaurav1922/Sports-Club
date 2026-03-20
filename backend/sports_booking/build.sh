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

"""# Create sample data (optional - remove in production)
python manage.py create_sample_data
"""
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(username='admin', email='admin@sportsclub.com', password='Admin@123', mobile_number='9999999999', is_mobile_verified=True)
    print('Superuser created')
else:
    print('Admin already exists')


# echo "Build completed successfully!"
