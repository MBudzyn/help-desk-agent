"""Look up one booking in data/bookings.json."""

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from config import BOOKINGS_PATH

_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class Booking:
    """One booking, with amounts in cents and the timestamps stored in the file."""

    id: str
    status: str
    bike_type: str
    bikes: int
    start: datetime
    end: datetime
    add_ons: tuple[str, ...]
    rental_price_eur: Decimal
    booking_fee_eur: Decimal
    deposit_eur: Decimal
    paid_with: str


def get_booking(booking_id: str, bookings_path: Path | None = None) -> str:
    """Return one booking as text, a not-found message, or an error string."""
    path = BOOKINGS_PATH if bookings_path is None else bookings_path
    try:
        bookings = load_bookings(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f"Could not read bookings: {exc}"
    booking = bookings.get(booking_id)
    if booking is None:
        return f"Booking {booking_id} was not found."
    return _format_booking(booking)


def load_bookings(path: Path) -> dict[str, Booking]:
    """Read bookings from JSON. Callers turn I/O and parse errors into text."""
    raw = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(raw, list):
        raise ValueError("bookings file must contain a list")
    bookings: dict[str, Booking] = {}
    for item in raw:
        booking = _parse_booking(item)
        if booking.id in bookings:
            raise ValueError(f"duplicate booking id {booking.id}")
        bookings[booking.id] = booking
    return bookings


def _parse_booking(item: Any) -> Booking:
    if not isinstance(item, dict):
        raise ValueError("booking must be an object")
    try:
        return Booking(
            id=_text(item, "id"),
            status=_text(item, "status"),
            bike_type=_text(item, "bike_type"),
            bikes=_bikes(item["bikes"]),
            start=datetime.fromisoformat(_text(item, "start")),
            end=datetime.fromisoformat(_text(item, "end")),
            add_ons=_add_ons(item["add_ons"]),
            rental_price_eur=_money(item["rental_price_eur"]),
            booking_fee_eur=_money(item["booking_fee_eur"]),
            deposit_eur=_money(item["deposit_eur"]),
            paid_with=_text(item, "paid_with"),
        )
    except KeyError as exc:
        raise ValueError(f"booking is missing {exc.args[0]}") from exc


def _format_booking(booking: Booking) -> str:
    add_ons = ", ".join(booking.add_ons) if booking.add_ons else "none"
    lines = (
        f"Booking {booking.id}",
        f"status: {booking.status}",
        f"bike_type: {booking.bike_type}",
        f"bikes: {booking.bikes}",
        f"start: {booking.start.isoformat()}",
        f"end: {booking.end.isoformat()}",
        f"add_ons: {add_ons}",
        f"rental_price_eur: {booking.rental_price_eur:.2f}",
        f"booking_fee_eur: {booking.booking_fee_eur:.2f}",
        f"deposit_eur: {booking.deposit_eur:.2f}",
        f"paid_with: {booking.paid_with}",
    )
    return "\n".join(lines) + "\n"


def _text(item: dict[str, Any], key: str) -> str:
    value = item[key]
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _bikes(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("bikes must be an integer")
    return value


def _add_ons(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(name, str) for name in value):
        raise ValueError("add_ons must be a list of strings")
    return tuple(value)


def _money(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int)):
        raise ValueError("amount must be a number")
    return Decimal(value).quantize(_CENTS)
