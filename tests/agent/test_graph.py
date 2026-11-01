"""Offline agent-loop test. A fake model stands in for the provider."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_fake_model_answer_uses_the_tool_result() -> None:
    """The final answer contains the tool result and does not call a provider."""


@pytest.mark.skip(reason="skeleton")
def test_graph_runs_without_an_api_key() -> None:
    """The loop test needs no network and no API key."""
