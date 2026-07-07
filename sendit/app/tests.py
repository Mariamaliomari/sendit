from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Booking, MovingCompany, Profile


class RegistrationAndLoginTests(TestCase):
    def test_register_creates_hashed_password_and_profile(self):
        response = self.client.post(reverse("register"), {
            "first_name": "Jane",
            "last_name": "Doe",
            "username": "janedoe",
            "email": "jane@example.com",
            "phone_number": "0712345678",
            "role": Profile.Role.CLIENT,
            "password1": "S3curePass!123",
            "password2": "S3curePass!123",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="janedoe")
        # Password must be hashed, never stored in plain text.
        self.assertNotEqual(user.password, "S3curePass!123")
        self.assertTrue(user.check_password("S3curePass!123"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_login_actually_authenticates(self):
        user = User.objects.create_user(username="bob", password="TestPass!123")
        Profile.objects.create(user=user, role=Profile.Role.CLIENT)
        response = self.client.post(reverse("login"), {"username": "bob", "password": "TestPass!123"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


class BookingFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="client1", password="pass12345")
        Profile.objects.create(user=self.user, role=Profile.Role.CLIENT)
        self.company = MovingCompany.objects.create(name="Test Movers", base_price=3000)

    def test_quote_calculation_returns_positive_price(self):
        from app.pricing import calculate_quote
        price = calculate_quote(self.company, bedrooms=2, crew_size=3, services="full")
        self.assertGreater(price, 0)

    def test_only_owner_can_view_booking(self):
        booking = Booking.objects.create(
            client=self.user, date="2026-08-01", moving_time="09:00",
            current_address="A", destination_address="B",
        )
        other = User.objects.create_user(username="other", password="pass12345")
        Profile.objects.create(user=other, role=Profile.Role.CLIENT)
        self.client.login(username="other", password="pass12345")
        response = self.client.get(reverse("booking_detail", args=[booking.pk]))
        self.assertRedirects(response, reverse("mybookings"))
