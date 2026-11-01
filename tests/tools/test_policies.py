"""Unit tests for search_policies."""

from pathlib import Path

from tools.policies import search_policies

NO_MATCH = (
    "No policy section matches this question. "
    "Contact the staff at help@citywheels.example or +48 000 000 000."
)


def test_search_returns_saturday_opening_hours(policies_dir: Path) -> None:
    """A question about Saturday hours returns the opening-hours section."""
    result = search_policies("What time do you open on Saturday?", policies_dir)

    assert "When are you open?" in result
    assert "08:00–20:00" in result
    assert "Saturday" in result


def test_search_returns_the_e_bike_day_price(policies_dir: Path) -> None:
    """A day-price question returns the rental table, not a calculated total."""
    result = search_policies("How much is an e-bike for a whole day?", policies_dir)

    assert "Electric bike" in result
    assert "40 EUR" in result


def test_search_returns_the_electric_bike_age_limit(policies_dir: Path) -> None:
    """An age question returns the electric-bike age rule."""
    result = search_policies("Can my 14-year-old rent an e-bike?", policies_dir)

    assert "from 16 years old" in result


def test_search_matches_hire_and_bicycle_to_the_rental_prices(policies_dir: Path) -> None:
    """Shop synonyms still find the rental table."""
    result = search_policies("How much does it cost to hire a bicycle for a day?", policies_dir)

    assert "Bike rental" in result
    assert "Per day" in result


def test_search_matches_a_fourteen_year_old_hiring_an_e_bike(policies_dir: Path) -> None:
    """A reworded age question still returns the electric-bike age rule."""
    result = search_policies("Can my 14 year old hire an e-bike?", policies_dir)

    assert "from 16 years old" in result


def test_search_reports_when_nothing_matches(policies_dir: Path) -> None:
    """A question outside the shop rules tells the customer to contact the staff."""
    result = search_policies("What is the capital of Australia?", policies_dir)

    assert result == NO_MATCH


def test_search_reports_a_missing_policy_directory(tmp_path: Path) -> None:
    """A missing policies directory returns an error string."""
    result = search_policies("opening hours", tmp_path / "missing")

    assert result.startswith("Could not read policies:")


def test_search_reports_an_unreadable_policy_file(tmp_path: Path) -> None:
    """An unreadable policy file returns an error string and does not crash."""
    policies = tmp_path / "policies"
    policies.mkdir()
    (policies / "faq.md").symlink_to(tmp_path / "missing.md")

    result = search_policies("opening hours", policies)

    assert result.startswith("Could not read policies:")
