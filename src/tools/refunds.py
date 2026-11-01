"""Refund amounts from the cancellation policy. The model never does this math."""

import json
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from config import BOOKINGS_PATH, CURRENT_TIME, POLICIES_DIR
from tools.bookings import Booking, load_bookings

_CENTS = Decimal("0.01")
_FULL_RATE = Decimal("1")
_HALF_RATE = Decimal("0.5")
_FULL_NOTICE = timedelta(hours=48)
_HALF_NOTICE = timedelta(hours=24)


def calculate_refund(
    booking_id: str,
    now: datetime | None = None,
    bookings_path: Path | None = None,
    policies_dir: Path | None = None,
) -> str:
    """Return the refund for cancelling `booking_id` at `now`, or an error string."""
    moment = CURRENT_TIME if now is None else now
    bookings = BOOKINGS_PATH if bookings_path is None else bookings_path
    policies = POLICIES_DIR if policies_dir is None else policies_dir
    try:
        _read_cancellation_policy(policies)
    except (OSError, UnicodeError) as exc:
        return f"Could not read policies: {exc}"
    try:
        loaded = load_bookings(bookings)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f"Could not read bookings: {exc}"
    booking = loaded.get(booking_id)
    if booking is None:
        return f"Booking {booking_id} was not found."
    if booking.status != "confirmed":
        return _cannot_cancel(booking)
    return _confirmed_refund(booking, moment)


def _read_cancellation_policy(policies_dir: Path) -> None:
    """The amount is coded below. This only checks that the policy file can be read."""
    policy = policies_dir / "cancellations.md"
    if not policy.is_file():
        raise FileNotFoundError(f"cancellation policy not found: {policy}")
    policy.read_text(encoding="utf-8")


def _cannot_cancel(booking: Booking) -> str:
    return (
        f"Booking {booking.id} cannot be cancelled because its status is {booking.status}. "
        "Nothing is refunded.\n"
        "Total refund: 0.00 EUR."
    )


def _confirmed_refund(booking: Booking, moment: datetime) -> str:
    rate = _rental_rate(booking.start, moment)
    rental_refund = (booking.rental_price_eur * rate).quantize(_CENTS, rounding=ROUND_HALF_UP)
    deposit_refund = booking.deposit_eur.quantize(_CENTS, rounding=ROUND_HALF_UP)
    total = (rental_refund + deposit_refund).quantize(_CENTS, rounding=ROUND_HALF_UP)
    percent = (rate * Decimal(100)).quantize(Decimal("1"))
    hours = (booking.start - moment).total_seconds() / 3600
    lines = (
        f"Booking {booking.id} can be cancelled.",
        f"Cancelled at {moment.isoformat()}, {hours:g} hours before the start.",
        (
            f"Rental refund: {rental_refund:.2f} EUR "
            f"({percent:.0f}% of {booking.rental_price_eur:.2f} EUR)."
        ),
        (
            "Booking fee refund: 0.00 EUR "
            f"(the {booking.booking_fee_eur:.2f} EUR fee is not refunded)."
        ),
        f"Deposit refund: {deposit_refund:.2f} EUR.",
        f"Total refund: {total:.2f} EUR.",
        _payment_line(booking.paid_with, total),
    )
    return "\n".join(lines)


def _rental_rate(start: datetime, moment: datetime) -> Decimal:
    remaining = start - moment
    if remaining >= _FULL_NOTICE:
        return _FULL_RATE
    if remaining >= _HALF_NOTICE:
        return _HALF_RATE
    return Decimal(0)


def _payment_line(paid_with: str, total: Decimal) -> str:
    if paid_with == "voucher":
        return f"Paid with voucher: the refund is a new voucher for {total:.2f} EUR, not cash."
    return "Paid with card: the refund goes back to the same card within 5 working days."
