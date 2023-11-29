from django import forms
from app.models import Booking
class BookingForm(forms.ModelForm):
    class Meta:
        model= Booking
        fields=['date', 'address', 'destination', 'property', 'vehicle']
