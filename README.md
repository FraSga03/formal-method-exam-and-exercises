# Volvo IT Process Mining

Process mining and temporal-logic verification over the BPI Challenge 2013 event
logs (Volvo IT Belgium, VINST incident and problem management), built with Gradio
and pm4py.

## Overview

The dashboard discovers process models from the logs, measures how well each
model matches the recorded behaviour, verifies temporal properties over every
case, and reports where the time goes. This folder is self-contained: copy it
anywhere and it runs on its own.

### Key features

- **Process discovery**: Alpha, Heuristics and Inductive miner, compared side by side
- **Conformance checking**: fitness, precision, generalisation and simplicity
- **Temporal verification**: eight shipped properties, or a formula you type,
  evaluated over finite traces with counterexamples
- **Performance analysis**: waiting times, case durations, variants, transition heatmap
- **Assistant**: questions answered from the measured figures of the loaded log,
  with OpenAI, Gemini or a local Ollama model

## Installation

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and Graphviz
(`sudo apt install graphviz`; pm4py shells out to `dot` to render Petri nets).

```bash
uv sync --all-extras
uv run python scripts/fetch_data.py   # downloads the three logs into data/raw/
uv run pytest                         # 267 tests
uv run python -m volvo.main           # http://127.0.0.1:7860
```

API keys are optional and can be passed as flags rather than written to disk:

```bash
uv run python -m volvo.main --openai-api-key sk-...   # or --gemini-api-key, --ollama-base-url
```

## Usage

1. **Data**: pick a log and an activity labelling.
2. **Preprocessing**: filter by activity, time range or case length, drop
   duplicates, relabel. Reload from the Data tab to undo.
3. **Discovery** and **Conformance**: choose a miner, read the Petri net and the
   four metrics.
4. **LTL**: run a shipped property or type your own; violating cases come back as
   counterexamples.
5. **Analytics**, **Anomalies**, **Prediction**: health score, waiting times,
   outliers, Markov successor probabilities.
6. **Report** and **Assistant**: generate the analysis as Markdown, or ask about
   the loaded log in natural language.

## Project structure

```
VolvoProcessMining/
├── volvo/
│   ├── domain.py          # log schemas and activity-label derivation
│   ├── logs/              # attribute-preserving loading, filters
│   ├── mining/            # discovery, conformance, performance
│   ├── verification/      # temporal-logic encoding and property library
│   ├── analysis/          # composite score, anomalies, Markov model
│   ├── ai/                # LLM providers and the grounding fact block
│   ├── ui/                # Gradio layout, callbacks, figures
│   ├── reporting/         # Markdown report generation
│   └── main.py            # command-line entry point
├── scripts/               # fetch data; regenerate results, figures, tables, PDFs
├── exercises/             # NuSMV, FSM and statechart coursework
└── docs/
    ├── report/documentation.pdf
    ├── presentation/presentation.pdf
    └── results/           # measured results for the write-up
```

## Dataset

Three logs, all loading to their published counts. BPI 2013 has no activity
column: the label is derived from Status + Sub Status, and the choice materially
changes the discovered model.

| Log | Cases | Events | Activities |
|---|---|---|---|
| Incidents | 7,554 | 65,533 | 13 |
| Open problems | 819 | 2,351 | 5 |
| Closed problems | 1,487 | 6,660 | 7 |

## Exercises

Three independent coursework exercises under `exercises/`, each with its own
README: `nusmv/` (symbolic model checking of two puzzles and Peterson's mutual
exclusion), `fsm/` (a state machine driving an LLM), and `itemis/` (a smart
kitchen statechart).

## Deliverables

`docs/report/documentation.pdf` and `docs/presentation/presentation.pdf`. Every
table and figure in both is generated from the analysis code, so the documents
cannot drift from the results. Rebuild them with
`uv run python scripts/build_all.py`, which needs a LaTeX toolchain
(`sudo apt install texlive-latex-recommended texlive-fonts-recommended latexmk`).

## Author

**Francesco Sgaramella**
University of Bari "Aldo Moro"
