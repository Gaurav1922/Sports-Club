from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create admin if it doesn't exist"

    def handle(self, *args, **kwargs):
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "Admin@123")
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        mobile = os.getenv("ADMIN_MOBILE", "9999999999")

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS("Admin already exists"))
            return

        User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
            mobile_number=mobile,
        )

        self.stdout.write(self.style.SUCCESS("Admin created successfully"))
