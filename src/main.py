"""CLI entrypoint. One customer question in, one answer out."""

import sys

from agent.graph import answer

USAGE = (
    "Ask one CityWheels question, for example: "
    'python -m main "What time do you open on Saturday?"'
)


def main() -> None:
    """Print the agent's answer for one command-line question."""
    question = " ".join(sys.argv[1:]).strip()
    if question == "":
        print(USAGE)
        return
    try:
        print(answer(question))
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
