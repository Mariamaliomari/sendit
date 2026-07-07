import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MovingCompany",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="companies/")),
                ("base_price", models.DecimalField(decimal_places=2, default=3000, max_digits=10)),
                ("price_per_bedroom", models.DecimalField(decimal_places=2, default=1500, max_digits=10)),
                ("price_per_crew_member", models.DecimalField(decimal_places=2, default=800, max_digits=10)),
                ("rating", models.DecimalField(decimal_places=1, default=4.5, max_digits=2)),
                ("years_in_business", models.PositiveIntegerField(default=1)),
                ("is_verified", models.BooleanField(default=True, help_text="Verified / trustworthy badge")),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
            ],
            options={
                "verbose_name_plural": "Moving companies",
                "ordering": ["-rating", "name"],
            },
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("client", "Client"), ("driver", "Driver"), ("admin", "Admin")], default="client", max_length=10)),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("bio", models.TextField(blank=True)),
                ("address", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("moving_time", models.TimeField()),
                ("current_address", models.CharField(max_length=200)),
                ("destination_address", models.CharField(max_length=200)),
                ("property_type", models.CharField(choices=[("apartment", "Apartment"), ("house", "House"), ("office", "Office"), ("studio", "Studio")], default="apartment", max_length=50)),
                ("bedrooms", models.PositiveIntegerField(default=1)),
                ("services", models.CharField(choices=[("full", "Full-service move"), ("loading_only", "Loading & unloading only"), ("packing_only", "Packing only"), ("transport_only", "Transport only")], default="full", max_length=30)),
                ("crew_size", models.PositiveIntegerField(default=2)),
                ("vehicle_size", models.CharField(default="medium", max_length=20)),
                ("emergency_contact_name", models.CharField(blank=True, max_length=100)),
                ("emergency_contact_phone_number", models.CharField(blank=True, max_length=20)),
                ("relationship_to_user", models.CharField(blank=True, max_length=50)),
                ("instructions", models.TextField(blank=True)),
                ("accept_terms", models.BooleanField(default=False)),
                ("special_items", models.BooleanField(default=False)),
                ("status", models.CharField(choices=[("draft", "Draft - awaiting quote"), ("quoted", "Quote ready"), ("confirmed", "Confirmed"), ("in_progress", "Move in progress"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="draft", max_length=20)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookings", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bookings", to="app.movingcompany")),
                ("driver", models.ForeignKey(blank=True, limit_choices_to={"profile__role": "driver"}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_bookings", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="MoveTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("is_completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="app.booking")),
            ],
            options={
                "ordering": ["due_date", "created_at"],
            },
        ),
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("category", models.CharField(choices=[("living_room", "Living Room"), ("bedroom", "Bedroom"), ("kitchen", "Kitchen"), ("bathroom", "Bathroom"), ("office", "Office"), ("garage", "Garage/Storage"), ("other", "Other")], default="other", max_length=20)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("is_fragile", models.BooleanField(default=False)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inventory_items", to="app.booking")),
            ],
            options={
                "ordering": ["category", "name"],
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="app.booking")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone_number", models.CharField(max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("checkout_request_id", models.CharField(blank=True, max_length=100)),
                ("merchant_request_id", models.CharField(blank=True, max_length=100)),
                ("mpesa_receipt_number", models.CharField(blank=True, max_length=50)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed")], default="pending", max_length=10)),
                ("raw_callback", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="app.booking")),
            ],
        ),
    ]
