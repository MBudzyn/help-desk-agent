"""CLI tests. A stand-in answer keeps these off the network."""

from __future__ import annotations

import sys

import pytest

import main


def test_cli_prints_the_agent_answer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """One question is passed to the agent and its text is printed."""
    seen: list[str] = []

    def fake_answer(question: str) -> str:
        seen.append(question)
        return "Total refund: 340.00 EUR."

    monkeypatch.setattr(main, "answer", fake_answer)
    monkeypatch.setattr(sys, "argv", ["main", "Cancel", "booking", "CW-1002."])

    main.main()

    assert seen == ["Cancel booking CW-1002."]
    assert capsys.readouterr().out == "Total refund: 340.00 EUR.\n"


def test_cli_without_a_question_does_not_call_the_agent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty command prints how to ask and leaves the model alone."""

    def forbidden(question: str) -> str:
        raise AssertionError("agent was called")

    monkeypatch.setattr(main, "answer", forbidden)
    monkeypatch.setattr(sys, "argv", ["main"])

    main.main()

    assert "python -m main" in capsys.readouterr().out


def test_cli_reports_a_missing_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing key or model name stops before the provider is called."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.setattr(sys, "argv", ["main", "What time do you open on Saturday?"])

    with pytest.raises(SystemExit) as caught:
        main.main()

    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert "GOOGLE_API_KEY" in error
    assert "MODEL_NAME" in error
