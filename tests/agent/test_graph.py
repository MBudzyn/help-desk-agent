"""Offline agent-loop tests. A scripted model stands in for the provider."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from agent.graph import answer
from agent.prompts import SYSTEM_PROMPT


class ScriptedModel:
    """Returns prepared replies and records every prompt it is shown."""

    def __init__(self, replies: list[Any]) -> None:
        self._replies = list(replies)
        self.seen: list[list[Any]] = []
        self.tools: list[Any] = []

    def bind_tools(self, tools: list[Any]) -> ScriptedModel:
        self.tools = tools
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.seen.append(list(messages))
        reply = self._replies.pop(0)
        result = reply(messages) if callable(reply) else reply
        if not isinstance(result, AIMessage):
            raise TypeError("scripted reply must be an AIMessage")
        return result


def _tool_call(name: str, args: dict[str, str], call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


def _quote_last_tool(messages: list[Any]) -> AIMessage:
    tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
    return AIMessage(content=str(tool_messages[-1].content))


def test_fake_model_answer_uses_the_refund_tool_result() -> None:
    """The final answer contains the refund tool result and does not call a provider."""
    model = ScriptedModel(
        [
            _tool_call("calculate_refund", {"booking_id": "CW-1002"}, "call-1"),
            _quote_last_tool,
        ]
    )

    text = answer("I want to cancel booking CW-1002. How much will I get back?", model=model)

    assert model.seen
    assert any(isinstance(message, ToolMessage) for message in model.seen[1])
    assert "Total refund: 340.00 EUR." in text


def test_graph_runs_without_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loop test needs no network and no API key."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)

    def forbidden() -> None:
        raise AssertionError("real model was constructed")

    monkeypatch.setattr("agent.graph._real_model", forbidden)
    model = ScriptedModel(
        [
            _tool_call("get_booking", {"booking_id": "CW-1001"}, "call-1"),
            _quote_last_tool,
        ]
    )

    text = answer("What is booking CW-1001?", model=model)

    assert "Booking CW-1001" in text
    assert "status: confirmed" in text


def test_unknown_booking_reaches_the_customer() -> None:
    """A missing booking id is quoted from the tool instead of being invented."""
    model = ScriptedModel(
        [
            _tool_call("get_booking", {"booking_id": "CW-9999"}, "call-1"),
            _quote_last_tool,
        ]
    )

    text = answer("Look up booking CW-9999.", model=model)

    assert text == "Booking CW-9999 was not found."


def test_policy_excerpt_reaches_the_customer() -> None:
    """A shop question quotes the policy section the tool returned."""
    model = ScriptedModel(
        [
            _tool_call("search_policies", {"query": "What time do you open on Saturday?"}, "call-1"),
            _quote_last_tool,
        ]
    )

    text = answer("What time do you open on Saturday?", model=model)

    assert "When are you open?" in text
    assert "Saturday" in text


def test_booking_lookup_can_be_followed_by_a_refund() -> None:
    """The loop can run two tools before the final answer."""
    def second_or_final(messages: list[Any]) -> AIMessage:
        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        if len(tool_messages) == 1:
            return _tool_call("calculate_refund", {"booking_id": "CW-1002"}, "call-2")
        return _quote_last_tool(messages)

    model = ScriptedModel(
        [
            _tool_call("get_booking", {"booking_id": "CW-1002"}, "call-1"),
            second_or_final,
            second_or_final,
        ]
    )

    text = answer("Cancel booking CW-1002.", model=model)

    assert "Booking CW-1002" in str(model.seen[1])
    assert "Total refund: 340.00 EUR." in text


def test_model_receives_the_shop_rules_and_fixed_clock() -> None:
    """Every turn shows the instructions and the shop clock, not the system time."""
    model = ScriptedModel([AIMessage(content="Please contact the staff at help@citywheels.example.")])

    text = answer("What is the capital of Australia?", model=model)

    first_turn = model.seen[0]
    assert isinstance(first_turn[0], SystemMessage)
    assert first_turn[0].content == SYSTEM_PROMPT
    assert isinstance(first_turn[1], HumanMessage)
    assert "Current time: 2026-06-10 09:00 Europe/Warsaw" in str(first_turn[1].content)
    assert text == "Please contact the staff at help@citywheels.example."


def test_graph_binds_the_three_shop_tools() -> None:
    """The model is offered only the three CityWheels tools."""
    model = ScriptedModel([AIMessage(content="ok")])

    answer("Hello", model=model)

    assert {tool.name for tool in model.tools} == {
        "search_policies",
        "get_booking",
        "calculate_refund",
    }


def test_tool_loop_stops_and_sends_the_customer_to_staff() -> None:
    """A model that never stops calling tools is cut off with the staff contact."""
    model = ScriptedModel(
        [_tool_call("calculate_refund", {"booking_id": "CW-1002"}, f"call-{index}") for index in range(1, 8)]
    )

    text = answer("Keep calculating the refund.", model=model)

    assert len(model.seen) == 4
    assert "help@citywheels.example" in text
    assert "could not finish" in text
    assert "340.00 EUR" not in text
