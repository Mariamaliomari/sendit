from django.shortcuts import render, redirect

from app.form import BookingForm
from app.models import User, Booking

# Create your views here.
def home(request):
    return render(request, 'home.html')
def about(request):
    return render(request, 'about.html')
def services(request):
    return render(request, 'services.html')
def transporters(request):
    return render(request, 'transporters.html')
def dashbord(request):
    return render(request, 'dashbord.html')

def register(request):
    if request.method =="POST":
        user= User(firstname=request.POST['firstname'],lastname=request.POST['lastname'],
                       email=request.POST['email'],username=request.POST['username'],
                       password=request.POST['password'],
                       )
        user.save()
        return redirect('/')
    else:
        return render(request,'register.html')

def login(request):
    return render(request, 'login.html')


def index(request):
    if request.method == "POST":
        if User.objects.filter(username=request.POST['username'],
                                 password=request.POST['password']).exists():
            user= User.objects.get(username=request.POST['username'],
                                       password=request.POST['password'])

            return render (request, 'home.html', {'member':user})
        else:
            return render (request,'login.html')
    else:
        return render(request, 'login.html')
def startbook(request):
    if request.method=="POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            return  redirect("/")
    else:
        form=BookingForm()
        return render(request,'startbook.html', {'form':form})

def mybookings(request):
    bookings = Booking.objects.all()
    return render(request, 'mybookings.html', {'bookings':bookings})