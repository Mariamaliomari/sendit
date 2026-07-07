import json
import logging

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app.forms import (
    BookingForm, InventoryItemForm, MessageForm, MoveTaskForm,
    ProfileForm, QuoteSelectionForm, RegisterForm, StyledAuthenticationForm,
)
from app.models import Booking, InventoryItem, MoveTask, MovingCompany, Payment, Profile
from app.mpesa import MpesaError, initiate_stk_push
from app.pricing import calculate_quote

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public marketing pages
# ---------------------------------------------------------------------------

def home(request):
    featured_companies = MovingCompany.objects.filter(is_verified=True)[:3]
    return render(request, "home.html", {"featured_companies": featured_companies})


def about(request):
    return render(request, "about.html")


def services(request):
    return render(request, "services.html")


def transporters(request):
    companies = MovingCompany.objects.all()
    return render(request, "transporters.html", {"companies": companies})


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Welcome to Sendit! Your account has been created.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url or "dashboard")
        messages.error(request, "Invalid username or password.")
    else:
        form = StyledAuthenticationForm()
    return render(request, "login.html", {"form": form})


@login_required
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


# ---------------------------------------------------------------------------
# Dashboard (role-aware)
# ---------------------------------------------------------------------------

def _get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


@login_required
def dashboard(request):
    profile = _get_or_create_profile(request.user)

    if profile.is_driver:
        bookings = Booking.objects.filter(driver=request.user)
    elif profile.is_admin_role:
        bookings = Booking.objects.all()
    else:
        bookings = Booking.objects.filter(client=request.user)

    context = {
        "profile": profile,
        "bookings": bookings[:5],
        "booking_count": bookings.count(),
        "companies_count": MovingCompany.objects.count(),
    }
    return render(request, "dashboard.html", context)


# ---------------------------------------------------------------------------
# Booking flow: 1) enter details -> 2) get price -> 3) book -> 4) track
# ---------------------------------------------------------------------------

@login_required
def start_booking(request):
    """Step 1: Enter your details."""
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.client = request.user
            booking.status = Booking.Status.DRAFT
            booking.save()
            return redirect("get_quote", booking_id=booking.pk)
    else:
        form = BookingForm()
    return render(request, "startbook.html", {"form": form})


@login_required
def get_quote(request, booking_id):
    """Step 2: Get your price — select one or two movers, see instant quotes."""
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)
    quotes = None

    if request.method == "POST":
        if "company_id" in request.POST:
            # Final choice made from the comparison list below.
            company = get_object_or_404(MovingCompany, pk=request.POST["company_id"])
            booking.company = company
            booking.price = calculate_quote(company, booking.bedrooms, booking.crew_size, booking.services)
            booking.status = Booking.Status.CONFIRMED
            booking.save()
            messages.success(request, f"Booking confirmed with {company.name}!")
            return redirect("booking_detail", booking_id=booking.pk)

        selection_form = QuoteSelectionForm(request.POST)
        if selection_form.is_valid():
            selected = selection_form.cleaned_data["companies"]
            quotes = [
                {
                    "company": company,
                    "price": calculate_quote(company, booking.bedrooms, booking.crew_size, booking.services),
                }
                for company in selected
            ]
            booking.status = Booking.Status.QUOTED
            booking.save()
    else:
        selection_form = QuoteSelectionForm()

    return render(
        request,
        "quote.html",
        {"booking": booking, "selection_form": selection_form if quotes is None else None, "quotes": quotes},
    )


@login_required
def my_bookings(request):
    """Step 4 (list view): Track your moves."""
    profile = _get_or_create_profile(request.user)
    if profile.is_driver:
        bookings = Booking.objects.filter(driver=request.user)
    elif profile.is_admin_role:
        bookings = Booking.objects.all()
    else:
        bookings = Booking.objects.filter(client=request.user)
    return render(request, "mybookings.html", {"bookings": bookings})


@login_required
def booking_detail(request, booking_id):
    """Step 4 (detail view): Track and communicate with your mover."""
    booking = get_object_or_404(Booking, pk=booking_id)
    profile = _get_or_create_profile(request.user)

    is_owner = booking.client_id == request.user.id
    is_assigned_driver = booking.driver_id == request.user.id
    if not (is_owner or is_assigned_driver or profile.is_admin_role):
        messages.error(request, "You don't have access to that booking.")
        return redirect("mybookings")

    if request.method == "POST" and "content" in request.POST:
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            msg = message_form.save(commit=False)
            msg.booking = booking
            msg.sender = request.user
            msg.save()
            return redirect("booking_detail", booking_id=booking.pk)
    else:
        message_form = MessageForm()

    # Drivers/admins can move the status forward (this is the "tracking" update).
    if request.method == "POST" and "status" in request.POST and (is_assigned_driver or profile.is_admin_role):
        new_status = request.POST["status"]
        if new_status in Booking.Status.values:
            booking.status = new_status
            booking.save()
            return redirect("booking_detail", booking_id=booking.pk)

    context = {
        "booking": booking,
        "message_form": message_form,
        "chat_messages": booking.messages.select_related("sender"),
        "can_update_status": is_assigned_driver or profile.is_admin_role,
        "status_choices": Booking.Status.choices,
        "latest_payment": booking.payments.order_by("-id").first(),
    }
    return render(request, "booking_detail.html", context)


# ---------------------------------------------------------------------------
# Inventory checklist (objective #3)
# ---------------------------------------------------------------------------

@login_required
def inventory(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)

    if request.method == "POST":
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.booking = booking
            item.save()
            return redirect("inventory", booking_id=booking.pk)
    else:
        form = InventoryItemForm()

    items = booking.inventory_items.all()
    return render(request, "inventory.html", {"booking": booking, "form": form, "items": items})


@login_required
@require_POST
def delete_inventory_item(request, booking_id, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id, booking_id=booking_id, booking__client=request.user)
    item.delete()
    return redirect("inventory", booking_id=booking_id)


# ---------------------------------------------------------------------------
# Moving-day timeline / planning checklist (objective #2)
# ---------------------------------------------------------------------------

@login_required
def timeline(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)

    if request.method == "POST":
        form = MoveTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.booking = booking
            task.save()
            return redirect("timeline", booking_id=booking.pk)
    else:
        form = MoveTaskForm()

    tasks = booking.tasks.all()
    return render(request, "timeline.html", {"booking": booking, "form": form, "tasks": tasks})


@login_required
@require_POST
def toggle_task(request, booking_id, task_id):
    task = get_object_or_404(MoveTask, pk=task_id, booking_id=booking_id, booking__client=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect("timeline", booking_id=booking_id)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@login_required
def view_profile(request):
    profile = _get_or_create_profile(request.user)
    return render(request, "view_profile.html", {"profile": profile})


@login_required
def update_profile(request):
    profile = _get_or_create_profile(request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("view_profile")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, "update_profile.html", {"form": form})


# ---------------------------------------------------------------------------
# M-Pesa payments
# ---------------------------------------------------------------------------

@login_required
def pay(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)

    if not booking.price:
        messages.error(request, "This booking doesn't have a price yet.")
        return redirect("booking_detail", booking_id=booking.pk)

    if request.method == "POST":
        phone_number = request.POST.get("phone_number", "").strip()
        if not phone_number:
            messages.error(request, "Please enter the M-Pesa phone number to pay with.")
        else:
            payment = Payment.objects.create(
                booking=booking, phone_number=phone_number, amount=booking.price
            )
            try:
                result = initiate_stk_push(
                    phone_number=phone_number,
                    amount=booking.price,
                    account_reference=f"Booking-{booking.pk}",
                )
                payment.checkout_request_id = result.get("CheckoutRequestID", "")
                payment.merchant_request_id = result.get("MerchantRequestID", "")
                payment.save()
                messages.success(request, "Check your phone to complete the M-Pesa payment.")
            except MpesaError as exc:
                payment.status = Payment.Status.FAILED
                payment.save()
                messages.error(request, f"Payment could not be started: {exc}")
            except Exception:
                logger.exception("M-Pesa STK push failed for booking %s", booking.pk)
                payment.status = Payment.Status.FAILED
                payment.save()
                messages.error(request, "Payment could not be started. Please try again shortly.")
            return redirect("booking_detail", booking_id=booking.pk)

    return render(request, "pay.html", {"booking": booking})


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Safaricom calls this URL asynchronously to confirm a payment result.
    It must stay CSRF-exempt (Safaricom's servers can't send a Django CSRF
    token) but does not trust any client-supplied identifiers beyond the
    CheckoutRequestID Safaricom itself issued us."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ResultDesc": "Invalid payload"}, status=400)

    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    if not checkout_request_id:
        return JsonResponse({"ResultDesc": "Missing CheckoutRequestID"}, status=400)

    try:
        payment = Payment.objects.get(checkout_request_id=checkout_request_id)
    except Payment.DoesNotExist:
        logger.warning("Received M-Pesa callback for unknown CheckoutRequestID %s", checkout_request_id)
        return JsonResponse({"ResultDesc": "Unknown payment"}, status=404)

    payment.raw_callback = payload
    if result_code == 0:
        payment.status = Payment.Status.SUCCESS
        items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        for item in items:
            if item.get("Name") == "MpesaReceiptNumber":
                payment.mpesa_receipt_number = item.get("Value", "")
    else:
        payment.status = Payment.Status.FAILED
    payment.save()

    return JsonResponse({"ResultDesc": "Received"})

@login_required
def payment_status(request, payment_id):
    """Polled by the booking detail page to check if the M-Pesa callback
    has arrived yet and updated the payment's status."""
    payment = get_object_or_404(Payment, pk=payment_id, booking__client=request.user)
    return JsonResponse({"status": payment.status})