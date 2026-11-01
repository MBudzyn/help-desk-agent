"""Refund amounts from the cancellation policy. The model never does this math."""

from datetime import datetime
from pathlib import Path


def calculate_refund(
    booking_id: str,
    now: datetime | None = None,
    bookings_path: Path | None = None,
    policies_dir: Path | None = None,
) -> str:
    """Return the refund for cancelling `booking_id` at `now`, or an error string."""
    raise NotImplementedError
