# Volvo IT Process Mining

Process mining and LTL verification over the BPI Challenge 2013 event logs
(Volvo IT Belgium, VINST incident and problem management).

Formal Methods project, University of Bari. This folder is self-contained: copy
it anywhere and it runs on its own.

## Setup

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and Graphviz
(`sudo apt install graphviz` — pm4py shells out to `dot` to render Petri nets).

```bash
uv sync --all-extras
uv run python scripts/fetch_data.py   # downloads the three logs into data/raw/
uv run pytest                         # 235 tests: the dashboard and the exercises
```

`uv sync` prunes whatever the named extras do not cover, so use `--all-extras`
unless you know you want a narrower environment: `dev` carries pytest, `ai` the
LLM providers the dashboard's analysis panels use, and `exercises` the state
machine under `exercises/fsm/`. Installing only some of them removes the rest and
the corresponding tests start failing.

## Dashboard

```bash
uv run python -m volvo.main
uv run python -m volvo.main --openai-api-key sk-...   # or --gemini-api-key, --ollama-base-url
uv run python -m volvo.main --host 0.0.0.0 --port 8080
```

Then open http://127.0.0.1:7860.

Keys are read from `.env` and the environment as before; the flags override both,
which is the way to run it without writing a key to disk.

## Scripts

```bash
uv run python scripts/run_baseline.py      # compare discovery algorithms
```

## Reports

```bash
uv run python scripts/run_report.py
```

Writes one report per log to `docs/results/`. An LLM narrative section is added
when a provider is available; everything else works without one.

Three providers are supported. Copy `.env.example` to `.env` and fill in whichever
you want; the dashboard lists the ones that are actually usable.

**Local (recommended)** — no key, no billing, works offline:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
uv sync --extra ai
```

The first call takes about a minute while the model loads into VRAM; after that
it answers in about a second.

**Hosted**, for machines that cannot run a local model — set `OPENAI_API_KEY`
(https://platform.openai.com/api-keys, billed per token) or `GEMINI_API_KEY`
(https://aistudio.google.com/apikey, free tier available).

When several are available the local one is chosen by default, so nothing is
billed unless you pick a hosted provider explicitly.

## Dataset

Three logs, all loading to their published counts — see `data/README.md`.
The activity label is derived from Status + Sub Status; BPI 2013 has no activity
column, and the choice of mode materially changes the discovered model.

| Log | Cases | Events | Activities |
|---|---|---|---|
| Incidents | 7,554 | 65,533 | 13 |
| Open problems | 819 | 2,351 | 5 |
| Closed problems | 1,487 | 6,660 | 7 |

## Exercises

Three formal-methods exercises live under `exercises/`, independent of the dashboard
and of each other. Each has its own README with the detail; below is how to run them.

### `exercises/nusmv/` — symbolic model checking

Three SMV models: two river-crossing and bridge-walking puzzles, solved by refuting a
reachability property and reading the counterexample as the solution, and Peterson's
mutual exclusion with safety, liveness under fairness, and a deliberately broken
variant.

Needs NuSMV, which is not packaged for Debian or Ubuntu — download the binary from
<https://nusmv.fbk.eu/downloads.html> and either put it on `PATH` or point `NUSMV` at it.

```bash
./exercises/nusmv/check.sh                    # all three models
./exercises/nusmv/check.sh peterson.smv       # one model
NUSMV=/opt/NuSMV-2.6.0-Linux/bin/NuSMV ./exercises/nusmv/check.sh
```

Expect 15 specifications and no `WARNING` line. Two of them print `is false` on
purpose: those are the refutations whose counterexample is the answer — the eleven
crossings of the river, and the walk over all eight bridges.
`exercises/nusmv/README.md` records the expected verdict for every specification, so a
disagreement means a broken model rather than a stale table.

### `exercises/fsm/` — a state machine driving an LLM

A movie review assistant: each state carries a prompt, its declared transitions and,
where it collects structured data, a response model. The model chooses the transition;
the code decides what it does.

```bash
uv run python exercises/fsm/main.py --api-key sk-...
uv run python exercises/fsm/main.py --api-key sk-... --model gpt-4o
uv run pytest exercises/fsm -v                # 33 tests, no API key needed
```

The key may also come from `OPENAI_API_KEY` in the environment or in `.env`;
`--api-key` beats both. Type `quit`, `exit` or Ctrl-C to end the conversation.
Reviews are kept in `exercises/fsm/reviews.json`, one per film, and survive between
runs. The state handlers need a live model and are not unit tested — the validation,
the persistence and the pure helpers are.

### `exercises/itemis/` — a statechart

`Statechart.ysc`, a smart kitchen modelled in itemis CREATE (YAKINDU Statechart Tools).
Nothing to run from this repository: open the folder as an Eclipse project in itemis
CREATE and use its built-in simulator. `exercises/itemis/README.md` describes the four
orthogonal regions and the events that drive them.

## Layout

| Path | Role |
|---|---|
| `volvo/domain.py` | Declared log schemas and activity-label derivation |
| `volvo/logs/` | Attribute-preserving loading into an `EventLogBundle` |
| `volvo/mining/` | Discovery, conformance, algorithm comparison |
| `volvo/config.py` | Paths and API keys — no domain knowledge |
| `docs/results/` | Measured results for the write-up |

pm4py is AGPL v3.

## Deliverables

`docs/report/report.pdf` and `docs/presentation/presentation.pdf`.

Every table and figure in both is generated from the analysis code — no measured
value is transcribed by hand, so the documents cannot drift from the results.

Rebuild everything from scratch:

```bash
uv run python scripts/build_all.py
```

That runs the baseline, verification, analytics and report scripts, regenerates
`docs/figures/` and `docs/tables/`, then builds both PDFs. It needs a LaTeX
toolchain:

```bash
sudo apt install texlive-latex-recommended texlive-fonts-recommended latexmk
```
