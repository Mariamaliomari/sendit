"""
M-Pesa Daraja (STK Push) helper functions.

Fixes applied vs. the original implementation:
- No network call happens at import time. The original code fetched an
  access token inside a class body, which ran the instant the module was
  imported — meaning the entire Django app could fail to start if
  Safaricom's API was slow, down, or the hardcoded key was invalid.
  Every function below is only called on demand, when a payment is
  actually being processed.
- All credentials come from Django settings (which reads them from
  environment variables) instead of being hardcoded in source.
- The confusing pattern of overwriting Django's `request` object with a
  plain dict has been removed; the payload is now a clearly-named
  `payload` variable.
"""

import base64
from datetime import datetime

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth


class MpesaError(Exception):
    """Raised when an M-Pesa API call fails or is misconfigured."""


def get_access_token():
    """Fetch a fresh OAuth access token from Safaricom. Call this lazily,
    only when you're about to make a payment request — never at import time.
    """
    if not settings.MPESA_CONSUMER_KEY or not settings.MPESA_CONSUMER_SECRET:
        raise MpesaError(
            "M-Pesa is not configured. Set MPESA_CONSUMER_KEY and "
            "MPESA_CONSUMER_SECRET in your .env file."
        )

    url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise MpesaError(f"Unexpected response from Safaricom: {data}")
    return token


def _build_password_and_timestamp():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode("utf-8")
    return password, timestamp


def initiate_stk_push(phone_number, amount, account_reference="Sendit Booking", description="Move payment"):
    """Trigger an STK push prompt on the customer's phone. Returns the
    parsed JSON response from Safaricom (includes CheckoutRequestID)."""
    if not settings.MPESA_PASSKEY:
        raise MpesaError("MPESA_PASSKEY is not configured in your .env file.")
    if not settings.MPESA_CALLBACK_URL:
        raise MpesaError("MPESA_CALLBACK_URL is not configured in your .env file.")

    token = get_access_token()
    password, timestamp = _build_password_and_timestamp()

    url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": description,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()
