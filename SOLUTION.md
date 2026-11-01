# Solution

## How to install and run

The agent, the tests, and the evaluation run in Docker.

```bash
docker compose run --rm agent "I want to cancel booking CW-1002. How much will I get back?"
docker compose run --rm test
docker compose run --rm eval
```

`test` runs `pytest` with no network and no API key. `eval` reads `GOOGLE_API_KEY` and `MODEL_NAME` from `.env`. Copy `.env.example` to `.env` and fill in the values before that run.

## Model and provider

Not chosen yet.

## How the agent works

Not written yet. The intended loop is: the model picks a tool, `src/tools/` runs it, and the tool result goes back to the model until it answers.

## Evaluation results

No evaluation has been run yet.

## AI coding assistants

Not written yet.

## Limitations

Not written yet.

## What I would do next

Not written yet.
