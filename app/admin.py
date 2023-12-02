from django.contrib import admin
from app.models import User,Booking
from django.contrib import admin
from app.models import Profile

# Register your models here.
admin.site.register(User)
admin.site.register(Booking)




@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'email', 'phone_number', 'bio', 'address']
    search_fields = ['user__username', 'user__email', 'first_name', 'last_name']
