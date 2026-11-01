"""Unit tests for get_booking."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_get_booking_returns_a_known_booking() -> None:
    """A booking that exists is returned from data/bookings.json."""


@pytest.mark.skip(reason="skeleton")
def test_get_booking_reports_an_unknown_id() -> None:
    """An unknown booking id is a not-found result, not a crash."""


@pytest.mark.skip(reason="skeleton")
def test_get_booking_reports_corrupt_json() -> None:
    """Corrupt bookings JSON returns an error string."""
