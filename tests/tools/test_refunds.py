"""Unit tests for every calculate_refund rule in the cancellation policy."""

from datetime import datetime
from pathlib import Path

import pytest

from tools.refunds import calculate_refund


def test_full_rental_refund_at_least_48_hours_before_start(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """48 hours or more before the start: 100% of the rental price."""
    result = calculate_refund("CW-1001", now, bookings_path, policies_dir)

    assert "Rental refund: 40.00 EUR (100% of 40.00 EUR)." in result
    assert "Total refund: 90.00 EUR." in result


def test_half_rental_refund_between_24_and_48_hours(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """Less than 48 hours but at least 24: 50% of the rental price."""
    result = calculate_refund("CW-1002", now, bookings_path, policies_dir)

    assert "Rental refund: 40.00 EUR (50% of 80.00 EUR)." in result
    assert "Deposit refund: 300.00 EUR." in result
    assert "Total refund: 340.00 EUR." in result


def test_no_rental_refund_under_24_hours(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """Less than 24 hours before the start: 0% of the rental price."""
    result = calculate_refund("CW-1003", now, bookings_path, policies_dir)

    assert "Rental refund: 0.00 EUR (0% of 12.00 EUR)." in result
    assert "Deposit refund: 50.00 EUR." in result
    assert "Total refund: 50.00 EUR." in result


def test_refund_boundary_at_exactly_48_hours(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """Exactly 48 hours before the start still qualifies for 100%."""
    result = calculate_refund("CW-1007", now, bookings_path, policies_dir)

    assert "Rental refund: 36.00 EUR (100% of 36.00 EUR)." in result
    assert "Total refund: 186.00 EUR." in result


def test_refund_boundary_at_exactly_24_hours(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """Exactly 24 hours before the start still qualifies for 50%."""
    result = calculate_refund("CW-1010", now, bookings_path, policies_dir)

    assert "Rental refund: 20.00 EUR (50% of 40.00 EUR)." in result
    assert "Total refund: 170.00 EUR." in result


def test_booking_fee_is_never_refunded(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """The booking fee stays with the shop on every cancellation."""
    result = calculate_refund("CW-1001", now, bookings_path, policies_dir)

    assert "Booking fee refund: 0.00 EUR (the 2.00 EUR fee is not refunded)." in result
    assert "Total refund: 90.00 EUR." in result


def test_deposit_is_refunded_in_full(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """A cancelled confirmed booking returns the whole deposit."""
    result = calculate_refund("CW-1001", now, bookings_path, policies_dir)

    assert "Deposit refund: 50.00 EUR." in result
    assert "Total refund: 90.00 EUR." in result


@pytest.mark.parametrize(
    ("booking_id", "status"),
    [
        ("CW-1008", "in_progress"),
        ("CW-1006", "completed"),
        ("CW-1005", "cancelled"),
    ],
)
def test_non_cancellable_status_refunds_nothing(
    booking_id: str,
    status: str,
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """Bookings that are not confirmed cannot be cancelled and refund nothing."""
    result = calculate_refund(booking_id, now, bookings_path, policies_dir)

    assert f"cannot be cancelled because its status is {status}" in result
    assert "Nothing is refunded." in result
    assert "Total refund: 0.00 EUR." in result


def test_unknown_booking_is_not_found(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """A missing booking id returns a not-found result."""
    result = calculate_refund("CW-9999", now, bookings_path, policies_dir)

    assert result == "Booking CW-9999 was not found."


def test_voucher_refund_is_not_cash(
    now: datetime,
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """A voucher payment is refunded as a new voucher, not as money."""
    result = calculate_refund("CW-1004", now, bookings_path, policies_dir)

    assert "Total refund: 73.00 EUR." in result
    assert "new voucher for 73.00 EUR, not cash" in result


def test_refund_uses_the_fixed_shop_clock_by_default(
    bookings_path: Path,
    policies_dir: Path,
) -> None:
    """Omitting the clock still cancels at 2026-06-10 09:00 Europe/Warsaw."""
    result = calculate_refund("CW-1002", bookings_path=bookings_path, policies_dir=policies_dir)

    assert "2026-06-10T09:00:00+02:00" in result
    assert "Total refund: 340.00 EUR." in result


def test_refund_reports_corrupt_bookings(tmp_path: Path, now: datetime, policies_dir: Path) -> None:
    """Corrupt bookings JSON returns an error string."""
    path = tmp_path / "bookings.json"
    path.write_text("{", encoding="utf-8")

    result = calculate_refund("CW-1001", now, path, policies_dir)

    assert result.startswith("Could not read bookings:")


def test_refund_reports_a_missing_policy_file(
    tmp_path: Path,
    now: datetime,
    bookings_path: Path,
) -> None:
    """A missing cancellation policy returns an error string."""
    result = calculate_refund("CW-1001", now, bookings_path, tmp_path)

    assert result.startswith("Could not read policies:")
