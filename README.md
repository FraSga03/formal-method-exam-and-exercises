# Volvo IT Process Mining

Process mining analysis of the BPI Challenge 2013 event logs (Volvo IT Belgium, VINST incident and problem management system) using PM4Py, flloat, and Gradio.

---

## Documentation and Deliverables

The main project deliverables (academic report and presentation slides) are in the `docs/` folder:

- **Report (PDF)**: [`docs/report/documentation.pdf`](docs/report/documentation.pdf)
  - 7-page written report covering process discovery, conformance checking, performance bottlenecks, and temporal verification.
  - LaTeX source: [`docs/report/documentation.tex`](docs/report/documentation.tex)
- **Presentation (PDF)**: [`docs/presentation/presentation.pdf`](docs/presentation/presentation.pdf)
  - 20-slide presentation deck.
  - LaTeX Beamer source: [`docs/presentation/presentation.tex`](docs/presentation/presentation.tex)
- **Generated Tables & Figures**:
  - Raw tables: `docs/tables/`
  - Generated plots and Petri nets: `docs/figures/`
  - Markdown summary reports: `docs/results/`

---

## Coursework Exercises

The independent coursework exercises are located in the `exercises/` folder, each with its own code and dedicated `README.md`:

1. **Finite State Machine (`exercises/fsm/`)**
   - Deterministic state machine driving structured dialogue.
   - Documentation & CLI usage: [`exercises/fsm/README.md`](exercises/fsm/README.md)
   - Run with: `uv run python exercises/fsm/main.py`
2. **itemis CREATE Statechart (`exercises/itemis/`)**
   - Event-driven smart kitchen statechart with concurrent operating modes, timers, and safety guards.
   - Documentation & model specification: [`exercises/itemis/README.md`](exercises/itemis/README.md)
   - Model file: `exercises/itemis/smart_kitchen.sct`
3. **NuSMV Model Checking (`exercises/nusmv/`)**
   - Symbolic model checking specifications in NuSMV: river crossing puzzle, Königsberg bridges, and Peterson's mutual exclusion algorithm.
   - Documentation & verification instructions: [`exercises/nusmv/README.md`](exercises/nusmv/README.md)
   - Models: `exercises/nusmv/river_crossing.smv`, `exercises/nusmv/bridges.smv`, `exercises/nusmv/peterson.smv`

---

## Quick Start

Requirements: Python 3.12+, `uv`, and Graphviz (`sudo apt install graphviz`).

```bash
# Install dependencies
uv sync --all-extras

# Download the BPI Challenge 2013 logs into data/raw/
uv run python scripts/fetch_data.py

# Run the automated test suite (267 tests)
uv run pytest

# Launch the Gradio web dashboard
uv run python -m volvo.main
```

The web dashboard runs locally at `http://127.0.0.1:7860`.

To enable the optional LLM assistant panel:
```bash
uv run python -m volvo.main --openai-api-key sk-...
# or with Gemini / local Ollama:
# uv run python -m volvo.main --gemini-api-key <key>
# uv run python -m volvo.main --ollama-base-url http://localhost:11434
```

---

## Dataset

The BPI Challenge 2013 dataset includes three event logs from Volvo IT's VINST ticketing tool. Activities are derived from `Status` and `Sub Status` (either 4 broad statuses or 13 composite status+substatus values).

| Log | Cases | Events | Activities | File |
|---|---|---|---|---|
| Incidents | 7,554 | 65,533 | 13 | `data/raw/bpic2013_incidents.csv` |
| Open problems | 819 | 2,351 | 5 | `data/raw/BPI_Challenge_2013_open_problems.xes` |
| Closed problems | 1,487 | 6,660 | 7 | `data/raw/BPI_Challenge_2013_closed_problems.xes` |

---

## Rebuilding Results and Compiling PDFs

All figures, tables, and PDFs can be recompiled in one step:
```bash
uv run python scripts/build_all.py
```

This updates all tables in `docs/tables/`, renders Petri nets and performance charts in `docs/figures/`, and runs `latexmk` to generate both `documentation.pdf` and `presentation.pdf`.

Requirements for compiling LaTeX:
```bash
sudo apt install texlive-latex-recommended texlive-fonts-recommended latexmk
```

---

## Repository Structure

```
VolvoProcessMining/
├── volvo/                 # Core Python package (mining, LTLf verification, Gradio UI)
├── exercises/             # Independent course exercises
│   ├── fsm/               # State machine dialog exercise
│   ├── itemis/            # itemis CREATE statechart exercise
│   └── nusmv/             # NuSMV formal verification models
├── docs/                  # Deliverables
│   ├── report/            # LaTeX academic report (documentation.pdf / .tex)
│   ├── presentation/      # LaTeX Beamer slides (presentation.pdf / .tex)
│   ├── figures/           # Generated Petri nets and distribution plots
│   ├── tables/            # Generated LaTeX table inputs
│   └── results/           # Markdown summary reports per log
├── scripts/               # Utility and build scripts (fetch_data, build_all, etc.)
└── data/                  # Event log datasets (downloaded via fetch_data.py)
```

## Author

Francesco Sgaramella
