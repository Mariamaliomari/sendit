from django.contrib import admin

from app.models import Booking, InventoryItem, Message, MoveTask, MovingCompany, Payment, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "phone_number"]
    list_filter = ["role"]
    search_fields = ["user__username", "user__email", "phone_number"]


@admin.register(MovingCompany)
class MovingCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "rating", "is_verified", "base_price", "years_in_business"]
    list_filter = ["is_verified"]
    search_fields = ["name"]


class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 0


class MoveTaskInline(admin.TabularInline):
    model = MoveTask
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "client", "company", "driver", "date", "status", "price"]
    list_filter = ["status", "property_type"]
    search_fields = ["client__username", "current_address", "destination_address"]
    inlines = [InventoryItemInline, MoveTaskInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "booking", "phone_number", "amount", "status", "created_at"]
    list_filter = ["status"]


admin.site.register(Message)
