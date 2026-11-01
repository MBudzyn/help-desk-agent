"""Runtime settings: data paths, model env vars, and the fixed CityWheels clock."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")
CURRENT_TIME = datetime(2026, 6, 10, 9, 0, tzinfo=WARSAW)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
POLICIES_DIR = DATA_DIR / "policies"
BOOKINGS_PATH = DATA_DIR / "bookings.json"
