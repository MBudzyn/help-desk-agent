"""Score agent answers against the question file and write the results."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypedDict

from langchain_google_genai.chat_models import GoogleRateLimitError

from agent.graph import AgentReply, reply
from config import ROOT

QUESTIONS_PATH = ROOT / "eval" / "questions.json"
RESULTS_PATH = ROOT / "eval" / "results.md"
STAFF_EMAIL = "help@citywheels.example"
QUESTION_GAP_SECONDS = 10
RATE_LIMIT_WAIT_SECONDS = 65
RATE_LIMIT_ATTEMPTS = 4
_EURO_AMOUNT = re.compile(
    r"(?:€|\bEUR\b)\s*\d|\d+(?:[.,]\d+)?\s*(?:€|\bEUR\b)",
    re.IGNORECASE,
)


class Question(TypedDict):
    """One evaluation question and the outcome the answer must meet."""

    id: str
    question: str
    expect_tool: str | None
    expect_contains: list[str]
    expect_refusal: bool


class ScoredAnswer(TypedDict):
    """One question after it has been checked."""

    id: str
    passed: bool
    reasons: list[str]
    tools: tuple[str, ...]
    text: str


def load_questions(path: Path) -> list[Question]:
    """Read the question file. Broken JSON or a bad shape raises."""
    loaded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        raise ValueError("questions file must be a list")
    return [_question(item) for item in loaded]


def score_question(question: Question, text: str, tools: Sequence[str]) -> list[str]:
    """Return the reasons an answer failed. An empty list means it passed."""
    reasons: list[str] = []
    expected_tool = question["expect_tool"]
    if expected_tool is not None and expected_tool not in tools:
        reasons.append(f"missing tool: {expected_tool}")
    folded = text.casefold()
    for fragment in question["expect_contains"]:
        if fragment.casefold() not in folded:
            reasons.append(f"missing text: {fragment}")
    if question["expect_refusal"]:
        if STAFF_EMAIL.casefold() not in folded:
            reasons.append("missing staff contact")
        if _EURO_AMOUNT.search(text) is not None:
            reasons.append("invented amount")
    return reasons


def run(
    questions: Sequence[Question],
    ask: Callable[[str], AgentReply],
    results_path: Path,
) -> str:
    """Score every question, write the results file, and return that text."""
    scored: list[ScoredAnswer] = []
    for question in questions:
        result = ask(question["question"])
        reasons = score_question(question, result.text, result.tools)
        scored.append(
            {
                "id": question["id"],
                "passed": reasons == [],
                "reasons": reasons,
                "tools": result.tools,
                "text": result.text,
            }
        )
    text = render_results(scored)
    results_path.write_text(text, encoding="utf-8")
    return text


def render_results(scored: Sequence[ScoredAnswer]) -> str:
    """Format the pass count and one section per question."""
    passed = sum(1 for item in scored if item["passed"])
    lines = [
        "# Evaluation results",
        "",
        f"{passed} of {len(scored)} passed.",
        "",
    ]
    for item in scored:
        label = "passed" if item["passed"] else "failed"
        lines.append(f"## {item['id']} — {label}")
        lines.append("")
        for reason in item["reasons"]:
            lines.append(f"- {reason}")
        if item["reasons"]:
            lines.append("")
        tool_names = ", ".join(item["tools"]) if item["tools"] else "none"
        lines.append(f"Tools: {tool_names}")
        lines.append("")
        body = item["text"].strip()
        lines.append(body if body != "" else "(empty answer)")
        lines.append("")
    return "\n".join(lines)


def ask_within_quota(
    question: str,
    ask: Callable[[str], AgentReply],
    pause: Callable[[float], None],
    *,
    gap: float = QUESTION_GAP_SECONDS,
    wait: float = RATE_LIMIT_WAIT_SECONDS,
    attempts: int = RATE_LIMIT_ATTEMPTS,
) -> AgentReply:
    """Call the model, wait out a free-tier 429, then leave a gap before the next question."""
    for attempt in range(attempts):
        try:
            result = ask(question)
        except GoogleRateLimitError:
            if attempt == attempts - 1:
                raise
            print(
                f"Free-tier limit reached. Waiting {wait:.0f} seconds before the next try.",
                flush=True,
            )
            pause(wait)
            continue
        pause(gap)
        return result
    raise RuntimeError("rate limit retries exhausted")


def main() -> None:
    """Score the question file with the real model and overwrite the results."""
    try:
        _require_model_env()
        questions = load_questions(QUESTIONS_PATH)

        def ask(question: str) -> AgentReply:
            print(f"Asking: {question}", flush=True)
            return ask_within_quota(question, reply, time.sleep)

        run(questions, ask, RESULTS_PATH)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Could not read questions: {error}", file=sys.stderr)
        raise SystemExit(1) from error


def _require_model_env() -> None:
    key = os.environ.get("GOOGLE_API_KEY", "")
    name = os.environ.get("MODEL_NAME", "")
    if key == "" or name == "":
        raise RuntimeError("GOOGLE_API_KEY and MODEL_NAME must be set")


def _question(item: object) -> Question:
    if not isinstance(item, dict):
        raise ValueError("each question must be an object")
    question_id = _text_field(item, "id")
    question = _text_field(item, "question")
    expect_tool = item.get("expect_tool")
    if expect_tool is not None and not isinstance(expect_tool, str):
        raise ValueError(f"{question_id}: expect_tool must be a string or null")
    contains = item.get("expect_contains")
    if not isinstance(contains, list):
        raise ValueError(f"{question_id}: expect_contains must be a list of strings")
    fragments: list[str] = []
    for fragment in contains:
        if not isinstance(fragment, str):
            raise ValueError(f"{question_id}: expect_contains must be a list of strings")
        fragments.append(fragment)
    refusal = item.get("expect_refusal")
    if not isinstance(refusal, bool):
        raise ValueError(f"{question_id}: expect_refusal must be true or false")
    return {
        "id": question_id,
        "question": question,
        "expect_tool": expect_tool,
        "expect_contains": fragments,
        "expect_refusal": refusal,
    }


def _text_field(item: dict[str, object], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{field} must be a non-empty string")
    return value
