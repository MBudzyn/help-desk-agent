"""Run the agent on eval/questions.json and write eval/results.md."""

QUESTION_FIELDS = (
    "id",
    "question",
    "expect_tool",
    "expect_contains",
    "expect_refusal",
)


def main() -> None:
    """Score each question and overwrite eval/results.md with the run."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
