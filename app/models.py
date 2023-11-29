from django.db import models

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
    date=models.CharField(max_length=100)
    address=models.CharField(max_length=100)
    destination=models.CharField(max_length=30)
    property=models.CharField(max_length=50)
    vehicle=models.CharField(max_length=20)

    def __str__(self):
        return self.date