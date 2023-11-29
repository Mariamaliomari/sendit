
from django.urls import path
from app import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.register, name='register'),
    path('login/', views.login, name='login'),

    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('transporters/', views.transporters, name='transporters'),
    path('dashbord/', views.dashbord, name='dashbord'),
    path('addbooking/', views.startbook, name='startbook'),
    path('showbooking/', views.mybookings, name='mybookings'),

]