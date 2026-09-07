# Volvo IT Process Mining

Process mining and LTL verification over the BPI Challenge 2013 event logs
(Volvo IT Belgium, VINST incident and problem management).

Formal Methods project, University of Bari. This folder is self-contained: copy
it anywhere and it runs on its own.

## Setup

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and Graphviz
(`sudo apt install graphviz` — pm4py shells out to `dot` to render Petri nets).

```bash
uv sync --extra dev
uv run python scripts/fetch_data.py   # downloads the three logs into data/raw/
uv run pytest volvo/tests -v
```

## Dashboard

```bash
uv run python -m volvo.main
```

Then open http://127.0.0.1:7860.

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
