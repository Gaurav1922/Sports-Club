from django.test import override_settings
from rest_framework.test import APITestCase

from .models import User


@override_settings(ADMIN_PASSCODE='TestAdminPass123')
class AdminLoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            mobile_number='9000000000',
            password='AdminPass123',
            is_staff=True,
            is_active=True,
        )

    def test_admin_login_with_passcode(self):
        response = self.client.post(
            '/api/auth/admin-login/',
            {'mobile_number': '9000000000', 'passcode': 'TestAdminPass123'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_admin_login_with_invalid_passcode(self):
        response = self.client.post(
            '/api/auth/admin-login/',
            {'mobile_number': '9000000000', 'passcode': 'wrong-passcode'},
            format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_admin_login_with_password(self):
        response = self.client.post(
            '/api/auth/admin-login/',
            {'mobile_number': '9000000000', 'password': 'AdminPass123'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
