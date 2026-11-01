# Solution

## Setup

### What you need

Install Docker with Compose v2. On Windows or macOS that is Docker Desktop. You do not install Python, pip, or the libraries yourself. The image installs them.

From the repository root, tests run with no key. The agent and the evaluation need a local `.env`, which git does not track:

```bash
cp .env.example .env
```

On Windows PowerShell use `Copy-Item .env.example .env`. Then set the two values, with no quotes:

```text
GOOGLE_API_KEY=your key from Google AI Studio
MODEL_NAME=gemini-3.5-flash-lite
```

Both the `agent` and `eval` services read that file. A missing value stops the process with a message before it calls Gemini.

### Why Docker

The project runs in Docker so the same build works on a Windows machine and in GitHub Actions. The image is Python 3.12. Tests do not depend on a virtual environment installed on the host, and the host clock is never the shop clock.

One image, `citywheels-help-desk:local`, serves the agent, the tests, and the evaluation. Only the `agent` service builds it. `test` and `eval` reuse the tag. Building all three services at once used to fail, because they tried to publish the same tag in parallel.

### Commands

```bash
docker compose build
docker compose run --rm agent "I want to cancel booking CW-1002. How much will I get back?"
docker compose run --rm test
docker compose run --rm eval
```

Run the commands from the repository root. The same lines work in PowerShell when the question is in double quotes. The first `docker compose build` downloads the Python image and the libraries, so it takes a few minutes. Later builds are shorter. A change under `src/` needs a new build, because the Dockerfile copies the source before it installs the package. Paths passed to `pytest` inside the container use forward slashes, for example `tests/tools/test_policies.py`.

`test` runs `pytest` with no network and no API key. `agent` and `eval` both read `GOOGLE_API_KEY` and `MODEL_NAME` from `.env`.

The evaluation calls the free tier, which allows 15 requests a minute for this model. The script waits 10 seconds between questions and, on HTTP 429, waits 65 seconds and tries the same question again. A full run takes a few minutes. It overwrites `eval/results.md`.

### Continuous checks

GitHub Actions runs `docker compose build` and `docker compose run --rm -T test` on every push and pull request. The workflow is `.github/workflows/tests.yml`. It does not call the model and does not need the API key.

### Layout

```text
src/main.py                 command-line entrypoint
src/config.py               data paths and the fixed shop clock
src/agent/graph.py          the tool-calling loop
src/agent/prompts.py        instructions for the model
src/agent/tools.py          wrappers the model is allowed to call
src/agent/evaluate.py       scores a run and writes eval/results.md
src/tools/                  booking lookup, policy search, refund math
data/policies/              shop rules
data/bookings.json          example bookings
tests/                      offline pytest suite
eval/questions.json         questions and expected outcomes
eval/run_eval.py            live evaluation entrypoint
eval/results.md             last evaluation run
```

## How I wrote the code

Each slice started from `main` on a short-lived branch and was merged back before the next one. A slice was one tool, the agent loop, the CLI, or the evaluation.

The usual shape was two commits. The first adds tests that fail because the behaviour is not there yet. The second makes those tests pass. Messages are in English and say why the change exists. Refund tests name the 24-hour and 48-hour boundaries, the kept booking fee, vouchers, card refunds, and the statuses that cannot be cancelled. The loop tests name the fixed clock and the cutoff.

`pytest` never calls Gemini. Tool tests use the files in `data/` and, for broken input, `tmp_path`. The loop test injects a scripted model. The evaluation scorer is tested the same way. The live model is only the `eval` service.

The order was a hello-world CLI, then one shared image, then `get_booking`, `search_policies`, and `calculate_refund`, then one tool-calling loop, then the real CLI, then the 12-question evaluation, then this document and the GitHub Actions workflow.

## Model and provider

The provider is Google Gemini through the LangChain Google GenAI chat model. LangGraph runs the loop. The model name is `gemini-3.5-flash-lite`, set in `.env` as `MODEL_NAME`.

I tried `gemini-2.5-flash` first. The API told new users that model is gone. `gemini-3.8-flash` then returned 503 because of demand. Listing the models this key can call, and sending one short prompt to a few Flash-Lite names, showed that `gemini-3.5-flash-lite` answers in a few seconds. It is a free-tier model, which is enough for a help desk that only has to pick a tool and quote the result. The client is created with `max_retries=0`, so a rate-limit error reaches the evaluation script instead of being retried in a tight loop.

## How the agent works

There is one model. It is offered three tools and it decides, on each turn, whether to call one of them or to answer in text. The code does not walk the tools in a fixed order.

`src/main.py` reads one question from the command line and prints the final text. A missing `GOOGLE_API_KEY` or `MODEL_NAME` exits with a message before any provider client is built. An empty command prints a usage line and does not call the model.

`answer()` in `src/agent/graph.py` compiles a LangGraph graph. The agent node calls the model. If the reply names a tool, a tool node runs that tool and the result comes back as a message. This repeats until the model sends plain text. The customer message always starts with `Current time: 2026-06-10 09:00 Europe/Warsaw`. That clock is `CURRENT_TIME` in `src/config.py`. Nothing in the tools or the graph reads the system clock.

After four tool results without a final answer, the graph stops calling the model and tells the customer to contact `help@citywheels.example`. The instructions in `src/agent/prompts.py` say to answer only from tool results, to leave refund arithmetic to `calculate_refund`, to quote a full opening range when the policy gives one, and to include the staff email whenever the customer is sent to the staff. Bad-weather amounts are left to the staff.

## Tools

The tools in `src/tools/` are plain Python. They do not call a model.

`get_booking` loads `data/bookings.json` with `Decimal` for money and returns one booking, or `Booking {id} was not found.` An unreadable file or bad JSON returns an error string. The process does not crash.

`search_policies` splits the Markdown files on `##` headings and scores sections by the words in the question. It returns at most three sections. A short alias list treats hire and rent, bicycle and bike, ebike and electric, and child and kid as the same word, so "hire a bicycle" still finds the rental prices. No match returns the staff contact. One unreadable policy file fails the whole search.

`calculate_refund` checks that `cancellations.md` can be read, then applies the bands in code. At least 48 hours before the start refunds 100% of the rental price, at least 24 hours and under 48 hours refunds 50%, and under 24 hours refunds none. The booking fee is never refunded. The deposit is refunded in full only when the status is `confirmed`. `in_progress`, `completed`, and `cancelled` refund nothing, including the deposit. A card refund goes back to the same card within five working days. A voucher refund is a new voucher, not cash. The thresholds are `timedelta` values, not numbers parsed out of the Markdown. Bad weather is not an amount in this function.

At the fixed clock the checked amounts are CW-1002 at 33 hours, 340.00 EUR back to the card, and CW-1004, a voucher, 73.00 EUR as a new voucher. CW-1005 is already cancelled, so the refund is 0.00 EUR.

## Evaluation results

`eval/questions.json` has 12 questions: shop facts, one missing booking, three refunds, and three refusals. The scorer in `src/agent/evaluate.py` checks the tool name on the tool messages, requires each expected fragment in the answer, and treats a refusal as passed only when `help@citywheels.example` is present and the answer contains no euro amount.

The first live run scored 10 of 12.

Saturday hours called `search_policies` and said the shop opens at 08:00 in April to October. It never said 20:00, so the required fragment `08:00–20:00` was missing. Bad weather called the policy tool and told the customer to contact the staff, but it did not include the email address.

I added two lines to the prompt: quote the whole opening range, and include the staff email whenever the customer is sent to the staff. The second run, which is the committed `eval/results.md`, was again 10 of 12. The failures moved.

Saturday now says "from 08:00 to 20:00". That is the right range. The checker still wants the policy's own spelling, `08:00–20:00`, with an en dash. The answer failed on punctuation.

Bad weather no longer called `search_policies`. The prompt already says that the staff decide those refunds, so the model answered from the instructions, included the email, and invented no amount. The customer got the right decision. The checker failed it because the expected tool was missing. The prompt change fixed the missing email and removed the reason to open the document.

I stopped there. Another run would spend the free-tier quota to chase a dash and a tool the model no longer needs. The task asks for an honest score and an explanation.

## Judges and richer tools

I first wanted several bots. One would answer, and a reviser would check that the sentence was grounded in the tool text and was not a hallucination. A second model can disagree with the tool and can also invent a refund, and this assignment asks for one tool-calling loop whose money is computed in Python. The reviser stayed an idea. The checks that shipped are deterministic: unit tests, a scripted model in the loop test, and the evaluation scorer.

The useful judge is still code, run after the loop on a live answer. If `calculate_refund` ran, every euro amount in the final sentence has to appear in that tool message. If `get_booking` ran, the booking id in the sentence has to be the id the tool returned. When the check fails, the customer gets the staff contact and the tool text, and the model is not asked to repair the number. A second model, if I added one later, would only see the tool messages and would not be allowed to change an amount.

The same thinking produced a small tool change that did ship. `search_policies` would miss "can my 14 year old hire a bicycle" if it only looked for "rent" and "bike". The alias groups cover hire/rent, bicycle/bike, ebike/electric, and child/kid. I would not add a general thesaurus. The next tool I would add is narrower than another synonym list: `opening_hours` would take the fixed clock, pick April–October or November–March, and return one sentence that already contains `08:00–20:00` or the winter hours. The model would quote that sentence instead of rewriting the dash.

## AI coding assistants

I used Cursor while building this. It drafted tests, the tool functions, the LangGraph loop, and the evaluation scorer. I kept the commits and the branches, and I ran the suite in Docker after each slice.

Two of its outputs were wrong, and the runs showed it.

It told me to set `MODEL_NAME=gemini-2.5-flash`. One real question returned 404: that model is no longer available to new users. The replacement it switched to, `gemini-3.8-flash`, then returned 503 under load. I listed the models on the key and tried a short prompt against Flash-Lite names. `gemini-3.5-flash-lite` answered. The model in `.env` is the one that answered, not the first name suggested.

The prompt edit it wrote for the first evaluation also caused the second failure above. Telling the model, in the instructions, that bad weather is a staff decision made the following run skip `search_policies`. I saw that in `eval/results.md`: the answer was right, and the tool list was empty. The Saturday check has the same shape. The answer contained both times, and it still failed because the model wrote "to" instead of the en dash in `08:00–20:00`.

## Limitations

The agent has no memory. A follow-up such as "and what if I cancel tomorrow?" is a new question, and "tomorrow" is not applied to the fixed clock.

The free tier caps this model at 15 requests a minute. One shop question is often two model calls, so a batch of 12 questions has to sleep. A hung connection has no timeout of its own. The evaluation wait covers HTTP 429. A silent socket still has to be stopped from outside.

The policy search is lexical. Wording outside the small alias list can miss a section, and the model can quote the winter hours next to the summer hours because the tool returns the whole section. The opening-hours tool described above is the direct fix.

The evaluation can reject a correct paraphrase. Saturday is the example. It can also reject a correct staff referral when the model does not call the tool the question file expected.

Refund percentages live in Python. If `cancellations.md` changed the bands and the code was not updated, the tool would still use 48 hours and 24 hours. The file is only checked to be readable.

## What I would do next

I would add the deterministic judge from the section above, then `opening_hours`, and only then try a second model as a reviser that may not change amounts. I would also give the Gemini client a request timeout so a quiet connection fails in seconds.

A second evaluation column for another model, using the same question file, would make a comparison the score and the failure notes rather than a general impression.
