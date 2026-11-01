"""Look up one booking in data/bookings.json."""

from pathlib import Path


def get_booking(booking_id: str, bookings_path: Path | None = None) -> str:
    """Return one booking as text, a not-found message, or an error string."""
    raise NotImplementedError
