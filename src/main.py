"""CLI entrypoint. One customer question in, one answer out."""

import sys


def main() -> None:
    """Print a placeholder greeting until the agent loop is wired up."""
    question = " ".join(sys.argv[1:]).strip()
    if question:
        print(f"Hello from CityWheels. You asked: {question}")
        return
    print("Hello from CityWheels.")


if __name__ == "__main__":
    main()
