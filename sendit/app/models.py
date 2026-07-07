from django.conf import settings
from django.db import models

# All models reference Django's built-in, secure auth.User via
# settings.AUTH_USER_MODEL. There is no custom User model here — the
# original project accidentally shadowed Django's real User class, which
# broke authentication and stored passwords in plain text. That mistake
# is intentionally not repeated.


class Profile(models.Model):
    """Extra information + role attached to every account."""

    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        DRIVER = "driver", "Driver"
        ADMIN = "admin", "Admin"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_role_display()})"

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_driver(self):
        return self.role == self.Role.DRIVER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN


class MovingCompany(models.Model):
    """A mover that clients can discover, compare, and book."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="companies/", blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=3000)
    price_per_bedroom = models.DecimalField(max_digits=10, decimal_places=2, default=1500)
    price_per_crew_member = models.DecimalField(max_digits=10, decimal_places=2, default=800)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5)
    years_in_business = models.PositiveIntegerField(default=1)
    is_verified = models.BooleanField(default=True, help_text="Verified / trustworthy badge")
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name_plural = "Moving companies"
        ordering = ["-rating", "name"]

    def __str__(self):
        return self.name

    def estimate_price(self, bedrooms, crew_size):
        return self.base_price + (self.price_per_bedroom * bedrooms) + (self.price_per_crew_member * crew_size)


class Booking(models.Model):
    """A move request created by a client — the core booking record."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft - awaiting quote"
        QUOTED = "quoted", "Quote ready"
        CONFIRMED = "confirmed", "Confirmed"
        IN_PROGRESS = "in_progress", "Move in progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    PROPERTY_TYPES = [
        ("apartment", "Apartment"),
        ("house", "House"),
        ("office", "Office"),
        ("studio", "Studio"),
    ]

    SERVICE_CHOICES = [
        ("full", "Full-service move"),
        ("loading_only", "Loading & unloading only"),
        ("packing_only", "Packing only"),
        ("transport_only", "Transport only"),
    ]

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    company = models.ForeignKey(
        MovingCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings"
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_bookings",
        limit_choices_to={"profile__role": "driver"},
    )

    date = models.DateField()
    moving_time = models.TimeField()
    current_address = models.CharField(max_length=200)
    destination_address = models.CharField(max_length=200)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES, default="apartment")
    bedrooms = models.PositiveIntegerField(default=1)
    services = models.CharField(max_length=30, choices=SERVICE_CHOICES, default="full")
    crew_size = models.PositiveIntegerField(default=2)
    vehicle_size = models.CharField(max_length=20, default="medium")
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone_number = models.CharField(max_length=20, blank=True)
    relationship_to_user = models.CharField(max_length=50, blank=True)
    instructions = models.TextField(blank=True)
    accept_terms = models.BooleanField(default=False)
    special_items = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.pk} — {self.client} on {self.date}"


class MoveTask(models.Model):
    """A single to-do item on a client's moving-day timeline/checklist."""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=150)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "created_at"]

    def __str__(self):
        return self.title


class InventoryItem(models.Model):
    """A single belonging catalogued for a move."""

    CATEGORY_CHOICES = [
        ("living_room", "Living Room"),
        ("bedroom", "Bedroom"),
        ("kitchen", "Kitchen"),
        ("bathroom", "Bathroom"),
        ("office", "Office"),
        ("garage", "Garage/Storage"),
        ("other", "Other"),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="inventory_items")
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    quantity = models.PositiveIntegerField(default=1)
    is_fragile = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} x{self.quantity}"


class Message(models.Model):
    """A simple in-app note between a client and their mover/driver for a booking."""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} on booking #{self.booking_id}"


class Payment(models.Model):
    """An M-Pesa STK Push payment attempt tied to a booking."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    raw_callback = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.pk} for booking #{self.booking_id} ({self.status})"
