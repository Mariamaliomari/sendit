from django.urls import path

from app import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("transporters/", views.transporters, name="transporters"),

    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("bookings/new/", views.start_booking, name="startbook"),
    path("bookings/", views.my_bookings, name="mybookings"),
    path("bookings/<int:booking_id>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:booking_id>/quote/", views.get_quote, name="get_quote"),
    path("bookings/<int:booking_id>/pay/", views.pay, name="pay"),

    path("bookings/<int:booking_id>/inventory/", views.inventory, name="inventory"),
    path(
        "bookings/<int:booking_id>/inventory/<int:item_id>/delete/",
        views.delete_inventory_item,
        name="delete_inventory_item",
    ),

    path("bookings/<int:booking_id>/timeline/", views.timeline, name="timeline"),
    path("bookings/<int:booking_id>/timeline/<int:task_id>/toggle/", views.toggle_task, name="toggle_task"),

    path("profile/", views.view_profile, name="view_profile"),
    path("profile/update/", views.update_profile, name="update_profile"),

    path("payments/callback/", views.mpesa_callback, name="mpesa_callback"),
    path("payments/<int:payment_id>/status/", views.payment_status, name="payment_status"),
]
