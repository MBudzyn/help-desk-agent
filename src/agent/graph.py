"""Build the tool-calling loop and turn one question into a final answer."""

from typing import Any


def build_graph() -> Any:
    """Compile the LangGraph agent with the three CityWheels tools."""
    raise NotImplementedError


def answer(question: str) -> str:
    """Run one question through the agent and return its final text."""
    raise NotImplementedError
