import json

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect
from requests.auth import HTTPBasicAuth
from django.contrib.auth.hashers import check_password

from app.credentials import MpesaAccessToken, LipanaMpesaPpassword
from app.forms import BookingForm
from app.models import User, Booking
from app.models import Profile
from app.forms import ProfileForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required



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

# def register(request):
#     if request.method =="POST":
#         user = User(firstname=request.POST['firstname'],lastname=request.POST['lastname'],
#                        email=request.POST['email'],username=request.POST['username'],
#                        password=request.POST['password'],
#                        )
#         user.save()
#         return redirect('/login')
#     else:
#         return render(request,'login.html')
#
# # def login(request):
# #     return render(request, 'login.html')
#
#
# def login(request):
#     if request.method == "POST":
#         if User.objects.filter(username=request.POST['username'],
#                                  password=request.POST['password']).exists():
#             user= User.objects.get(username=request.POST['username'],
#                                        password=request.POST['password'])
#
#             return render (request, 'home.html', {'user':user})
#         else:
#             return render (request,'login.html')
#     else:
#         return render(request, 'login.html')



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

            return render (request, 'home.html', {'user':user})
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




@login_required
def view_profile(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'view_profile.html', {'profile': profile})

@login_required
def update_profile(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('view_profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'update_profile.html', {'form': form})

def pay(request):
    return render(request, 'pay.html')

def token(request):
    consumer_key = 'CAm9VK3ekASR4iLvDg2rw21gi1MaDDya'
    consumer_secret = 'YCNz4uSsZ0evsAqm'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    r = requests.get(api_URL, auth=HTTPBasicAuth(
        consumer_key, consumer_secret))
    mpesa_access_token = json.loads(r.text)
    validated_mpesa_access_token = mpesa_access_token["access_token"]

    return render(request, 'token.html', {"token":validated_mpesa_access_token})
def pay(request):
    return render(request, 'pay.html')

def stk(request):
    if request.method =="POST":
        phone = request.POST['phone']
        amount = request.POST['amount']
        access_token = MpesaAccessToken.validated_mpesa_access_token
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": "Bearer %s" % access_token}
        request = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": LipanaMpesaPpassword.decode_password,
            "Timestamp": LipanaMpesaPpassword.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            "PhoneNumber": phone,
            "CallBackURL": "https://sandbox.safaricom.co.ke/mpesa/",
            "AccountReference": "Ras Collection",
            "TransactionDesc": "Web Development Charges"
        }
        response = requests.post(api_url, json=request, headers=headers)
        return HttpResponse("Success")
