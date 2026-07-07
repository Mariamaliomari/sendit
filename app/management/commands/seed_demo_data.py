from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from app.models import MovingCompany, Profile


class Command(BaseCommand):
    help = "Creates demo moving companies and one demo user per role (client/driver/admin) for local testing."

    def handle(self, *args, **options):
        companies = [
            dict(name="Swift Movers Kenya", description="Fast, insured moves across Nairobi.",
                 base_price=3000, price_per_bedroom=1500, price_per_crew_member=800,
                 rating=4.8, years_in_business=6, is_verified=True, phone_number="0700111222"),
            dict(name="CarefulHands Relocation", description="Specialists in fragile and office moves.",
                 base_price=3500, price_per_bedroom=1700, price_per_crew_member=900,
                 rating=4.6, years_in_business=4, is_verified=True, phone_number="0700333444"),
            dict(name="Budget Move Co", description="Affordable moves for students and small flats.",
                 base_price=2000, price_per_bedroom=1000, price_per_crew_member=600,
                 rating=4.1, years_in_business=2, is_verified=False, phone_number="0700555666"),
        ]
        for data in companies:
            MovingCompany.objects.get_or_create(name=data["name"], defaults=data)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(companies)} moving companies."))

        demo_users = [
            ("demo_client", Profile.Role.CLIENT),
            ("demo_driver", Profile.Role.DRIVER),
            ("demo_admin", Profile.Role.ADMIN),
        ]
        for username, role in demo_users:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password="Demo1234!", email=f"{username}@example.com")
                if role == Profile.Role.ADMIN:
                    user.is_staff = True
                    user.save()
                Profile.objects.create(user=user, role=role)
                self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}' / password 'Demo1234!' (role: {role})"))
            else:
                self.stdout.write(f"User '{username}' already exists, skipping.")
