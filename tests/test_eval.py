"""Offline checks for the evaluation scorer. They never call a provider."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from langchain_google_genai.chat_models import GoogleRateLimitError

from agent.evaluate import (
    QUESTIONS_PATH,
    Question,
    ask_within_quota,
    load_questions,
    main,
    run,
    score_question,
)
from agent.graph import AgentReply


def _question(question_id: str) -> Question:
    questions = load_questions(QUESTIONS_PATH)
    return next(item for item in questions if item["id"] == question_id)


def test_question_file_has_the_required_mix() -> None:
    """The task asks for 10 questions, including two refunds and two refusals."""
    questions = load_questions(QUESTIONS_PATH)

    refunds = [item for item in questions if item["expect_tool"] == "calculate_refund"]
    refusals = [item for item in questions if item["expect_refusal"]]

    assert len(questions) >= 10
    assert len(refunds) >= 2
    assert len(refusals) >= 2


def test_score_passes_when_the_tool_and_text_match() -> None:
    """A quoted refund amount and the refund tool count as a pass."""
    question = _question("refund-cw-1002")

    reasons = score_question(
        question,
        "Total refund: 340.00 EUR.",
        ("calculate_refund",),
    )

    assert reasons == []


def test_score_fails_when_the_amount_is_missing() -> None:
    """The right tool with the wrong amount does not pass."""
    question = _question("refund-cw-1002")

    reasons = score_question(
        question,
        "Total refund: 10.00 EUR.",
        ("calculate_refund",),
    )

    assert "missing text: 340.00" in reasons


def test_score_fails_when_a_refusal_invents_an_amount() -> None:
    """A staff referral that also states a euro amount is a failed refusal."""
    question = _question("bad-weather")

    reasons = score_question(
        question,
        "You would get 40.00 EUR back. Contact help@citywheels.example.",
        ("search_policies",),
    )

    assert "invented amount" in reasons


def test_score_passes_a_refusal_that_sends_the_customer_to_staff() -> None:
    """A refusal needs the staff email and must not name a euro amount."""
    question = _question("capital-of-australia")

    reasons = score_question(
        question,
        "I cannot answer that. Please contact help@citywheels.example or +48 000 000 000.",
        (),
    )

    assert reasons == []


def test_run_writes_the_pass_count(tmp_path: Path) -> None:
    """The results file records how many questions passed."""
    questions = [_question("refund-cw-1002"), _question("refund-cw-1004")]

    def fake(question: str) -> AgentReply:
        if "CW-1002" in question:
            return AgentReply("Total refund: 340.00 EUR.", ("calculate_refund",))
        return AgentReply("Total refund: 1.00 EUR.", ("calculate_refund",))

    text = run(questions, fake, tmp_path / "results.md")

    assert "1 of 2 passed" in text
    assert "missing text: 73.00" in text


def test_quota_wait_retries_the_same_question() -> None:
    """A free-tier 429 waits and tries the question again instead of aborting the run."""
    waits: list[float] = []
    calls = 0

    def fake(question: str) -> AgentReply:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise GoogleRateLimitError("429")
        return AgentReply("Please contact help@citywheels.example.", ())

    result = ask_within_quota(
        "What is the capital of Australia?",
        fake,
        waits.append,
        gap=0,
        wait=65,
    )

    assert calls == 2
    assert waits == [65, 0]
    assert "help@citywheels.example" in result.text


def test_load_questions_rejects_broken_json(tmp_path: Path) -> None:
    """A corrupt question file raises, so the process can report it and exit."""
    path = tmp_path / "questions.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_questions(path)


def test_eval_reports_a_missing_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The live run stops before calling the provider when the key is absent."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)

    with pytest.raises(SystemExit) as caught:
        main()

    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert "GOOGLE_API_KEY" in error
    assert "MODEL_NAME" in error
