from django.db import models
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class User(models.Model):
    firstname=models.CharField(max_length=100)
    lastname=models.CharField(max_length=100)
    email=models.EmailField()
    username=models.CharField(max_length=50)
    password=models.CharField(max_length=20)

    def __str__(self):
        return self.firstname+" "+self.lastname

class Booking(models.Model):
    date = models.DateField()
    moving_time = models.TimeField()
    current_address = models.CharField(max_length=100)
    destination_address = models.CharField(max_length=100)
    property_type = models.CharField(max_length=50)
    bedrooms = models.IntegerField()
    services = models.CharField(max_length=20)
    crew_size = models.IntegerField()
    vehicle_size = models.CharField(max_length=20)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone_number = models.CharField(max_length=20)
    relationship_to_user = models.CharField(max_length=50)
    instructions = models.TextField()
    accept_terms = models.BooleanField()
    special_items = models.BooleanField()

    def __str__(self):
        return str(self.date)



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    bio = models.TextField()
    address = models.TextField()

    def __str__(self):
        return f"{self.user.username}'s Profile"