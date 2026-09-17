# Volvo IT Process Mining (BPI Challenge 2013)

Process mining and trace-by-trace temporal logic verification over the Volvo IT Belgium incident and problem management logs (VINST), built with Python, pm4py, flloat, and Gradio.

## What is in this repository

The project provides an end-to-end pipeline and interactive web interface to analyze the BPI Challenge 2013 dataset:
- Automated discovery of Petri nets using Alpha, Heuristics, and Inductive miners.
- Conformance checking across token-based and alignment-based replay (fitness, precision, generalization, simplicity).
- Formal verification of finite-trace Linear Temporal Logic ($\text{LTL}_f$) properties over all traces, identifying counterexamples and points of failure.
- Performance and bottleneck analysis (waiting times, case durations, variant Pareto distributions, transition heatmaps).
- Automated generation of camera-ready LaTeX reports and presentations with exact empirical figures.

## Quickstart

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and Graphviz (`sudo apt install graphviz`).

```bash
# Setup environment and dependencies
uv sync --all-extras

# Download raw logs into data/raw/
uv run python scripts/fetch_data.py

# Run the test suite
uv run pytest

# Launch the Gradio dashboard
uv run python -m volvo.main
```

The web dashboard opens at `http://127.0.0.1:7860`.

Optional LLM grounding features can be enabled with API keys passed on the command line:
```bash
uv run python -m volvo.main --openai-api-key sk-...
# or --gemini-api-key <key>, --ollama-base-url http://localhost:11434
```

## Dataset

The BPI Challenge 2013 dataset contains three event logs from Volvo IT's VINST ticketing system. The raw files lack a single dedicated activity column; activity labels are derived from `Status` and `Sub Status` columns (`status` mode for 4 broad lifecycle stages, or `status_substatus` for 13 fine-grained operational steps).

| Log | Cases | Events | Activities (`status_substatus`) |
|---|---|---|---|
| Incidents | 7,554 | 65,533 | 13 |
| Open problems | 819 | 2,351 | 5 |
| Closed problems | 1,487 | 6,660 | 7 |

## Project Structure

```
VolvoProcessMining/
├── volvo/
│   ├── domain.py          # Schemas and activity-label definitions
│   ├── logs/              # Ingestion, attribute preservation, filtering
│   ├── mining/            # Discovery (Alpha/Heuristics/Inductive), replay, metrics
│   ├── verification/      # LTL_f encoding, property library, flloat verifier
│   ├── analysis/          # Health scores, anomaly detection, Markov transitions
│   ├── ai/                # Optional LLM grounding against measured metrics
│   ├── ui/                # Gradio layout, callbacks, and visualization
│   ├── reporting/         # Markdown export routines
│   └── main.py            # CLI entry point
├── scripts/               # Data fetching, pipeline orchestration, table/PDF compilation
├── exercises/             # Independent coursework (NuSMV, FSM, itemis statecharts)
└── docs/
    ├── report/documentation.pdf     # Full academic report (LaTeX)
    ├── presentation/presentation.pdf # Beamer presentation slides
    └── tables/                      # Generated LaTeX tables pinned to code
```

## Reproducing Results and Compiling Documents

To regenerate all figures, empirical LaTeX tables, markdown summaries, and compile both the report and presentation PDFs:

```bash
uv run python scripts/build_all.py
```

Compiling the LaTeX documents requires `latexmk` and standard TeX Live packages:
```bash
sudo apt install texlive-latex-recommended texlive-fonts-recommended latexmk
```

## Independent Exercises

Coursework modules in `exercises/` have dedicated documentation:
- `exercises/nusmv/`: Symbolic model checking with NuSMV (river crossing, Königsberg bridges, and Peterson's mutual exclusion algorithm).
- `exercises/fsm/`: Deterministic finite state machine orchestrating structured LLM dialogue.
- `exercises/itemis/`: Concurrent, event-driven smart kitchen statechart in itemis CREATE.

## Author

Francesco Sgaramella
