"""Unit tests for get_booking."""

from pathlib import Path

import pytest

from tools.bookings import get_booking

CW_1001 = """\
Booking CW-1001
status: confirmed
bike_type: city
bikes: 1
start: 2026-06-13T10:00:00+02:00
end: 2026-06-15T10:00:00+02:00
add_ons: none
rental_price_eur: 40.00
booking_fee_eur: 2.00
deposit_eur: 50.00
paid_with: card
"""


def test_get_booking_returns_a_known_booking(bookings_path: Path) -> None:
    """A booking that exists is returned with the values stored in the file."""
    assert get_booking("CW-1001", bookings_path) == CW_1001


@pytest.mark.parametrize("booking_id", ["CW-9999", "cw-1001"])
def test_get_booking_reports_an_unknown_id(bookings_path: Path, booking_id: str) -> None:
    """An unknown booking id is a not-found result, not a crash."""
    assert get_booking(booking_id, bookings_path) == f"Booking {booking_id} was not found."


def test_get_booking_reports_corrupt_json(tmp_path: Path) -> None:
    """Corrupt bookings JSON returns an error string."""
    path = tmp_path / "bookings.json"
    path.write_text("{", encoding="utf-8")

    result = get_booking("CW-1001", path)

    assert result.startswith("Could not read bookings:")


def test_get_booking_reports_a_missing_file(tmp_path: Path) -> None:
    """A missing bookings file returns an error string."""
    result = get_booking("CW-1001", tmp_path / "missing.json")

    assert result.startswith("Could not read bookings:")
