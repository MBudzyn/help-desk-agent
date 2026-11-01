"""Shared fixtures. The clock and data files stay fixed for every test."""

from datetime import datetime
from pathlib import Path

import pytest

from config import BOOKINGS_PATH, CURRENT_TIME, POLICIES_DIR


@pytest.fixture
def now() -> datetime:
    return CURRENT_TIME


@pytest.fixture
def bookings_path() -> Path:
    return BOOKINGS_PATH


@pytest.fixture
def policies_dir() -> Path:
    return POLICIES_DIR
