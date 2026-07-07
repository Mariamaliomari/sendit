"""
Deterministic, transparent quote calculation.

This is intentionally simple (no external rates API) so that quotes are
instant and reproducible, matching the "Get Your Price — instant
guaranteed price" objective. A company's price is its own base rate plus
per-bedroom and per-crew-member charges, with small adjustments for
optional services.
"""

from decimal import Decimal

SERVICE_MULTIPLIERS = {
    "full": Decimal("1.0"),
    "loading_only": Decimal("0.6"),
    "packing_only": Decimal("0.4"),
    "transport_only": Decimal("0.7"),
}


def calculate_quote(company, bedrooms, crew_size, services="full"):
    """Return a Decimal price quote for a given company and move details."""
    base = company.estimate_price(bedrooms=bedrooms, crew_size=crew_size)
    multiplier = SERVICE_MULTIPLIERS.get(services, Decimal("1.0"))
    return (base * multiplier).quantize(Decimal("1.00"))
