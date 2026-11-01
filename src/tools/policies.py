"""Find the parts of data/policies that answer a customer question."""

from pathlib import Path


def search_policies(query: str, policies_dir: Path | None = None) -> str:
    """Return policy excerpts relevant to `query`, or an error string."""
    raise NotImplementedError
