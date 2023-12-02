from django import forms
from app.models import Booking, Profile

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'date', 'moving_time', 'current_address', 'destination_address',
            'property_type', 'bedrooms', 'services',
            'crew_size', 'vehicle_size', 'emergency_contact_name',
            'emergency_contact_phone_number', 'relationship_to_user',
            'instructions', 'accept_terms', 'special_items',
        ]

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'bio', 'address']