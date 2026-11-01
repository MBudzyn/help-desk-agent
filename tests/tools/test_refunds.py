"""Unit tests for every calculate_refund rule in the cancellation policy."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_full_rental_refund_at_least_48_hours_before_start() -> None:
    """48 hours or more before the start: 100% of the rental price."""


@pytest.mark.skip(reason="skeleton")
def test_half_rental_refund_between_24_and_48_hours() -> None:
    """Less than 48 hours but at least 24: 50% of the rental price."""


@pytest.mark.skip(reason="skeleton")
def test_no_rental_refund_under_24_hours() -> None:
    """Less than 24 hours before the start: 0% of the rental price."""


@pytest.mark.skip(reason="skeleton")
def test_refund_boundary_at_exactly_48_hours() -> None:
    """Exactly 48 hours before the start still qualifies for 100%."""


@pytest.mark.skip(reason="skeleton")
def test_refund_boundary_at_exactly_24_hours() -> None:
    """Exactly 24 hours before the start still qualifies for 50%."""


@pytest.mark.skip(reason="skeleton")
def test_booking_fee_is_never_refunded() -> None:
    """The booking fee stays with the shop on every cancellation."""


@pytest.mark.skip(reason="skeleton")
def test_deposit_is_refunded_in_full() -> None:
    """A cancelled confirmed booking returns the whole deposit."""


@pytest.mark.skip(reason="skeleton")
@pytest.mark.parametrize("status", ["in_progress", "completed", "cancelled"])
def test_non_cancellable_status_refunds_nothing(status: str) -> None:
    """Bookings that are not confirmed cannot be cancelled and refund nothing."""


@pytest.mark.skip(reason="skeleton")
def test_unknown_booking_is_not_found() -> None:
    """A missing booking id returns a not-found result."""


@pytest.mark.skip(reason="skeleton")
def test_voucher_refund_is_not_cash() -> None:
    """A voucher payment is refunded as a new voucher, not as money."""
