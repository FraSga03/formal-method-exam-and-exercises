# Movie Review FSM

A finite state machine driving an LLM dialogue agent with structured JSON outputs.

## Running

```bash
uv sync --extra exercises
uv run python main.py --api-key sk-...
```

The API key can also be set via `OPENAI_API_KEY` or a `.env` file. Choose an alternative model with `--model`. Type `quit` or press Ctrl+C to exit. Saved reviews are stored in `reviews.json`.

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> START

    START --> SELECT_MOVIE_TO_REVIEW
    SELECT_MOVIE_TO_REVIEW --> REVIEW
    SELECT_MOVIE_TO_REVIEW --> SELECT_MOVIE_TO_REVIEW
    REVIEW --> REVIEW
    REVIEW --> SELECT_MOVIE_TO_REVIEW
    REVIEW --> START

    START --> SELECT_MOVIE_PAST_REVIEW
    SELECT_MOVIE_PAST_REVIEW --> SHOW_REVIEWS
    SELECT_MOVIE_PAST_REVIEW --> SELECT_MOVIE_PAST_REVIEW
    SHOW_REVIEWS --> SELECT_MOVIE_PAST_REVIEW
    SHOW_REVIEWS --> START

    START --> SELECT_MOVIE_TO_MANAGE
    SELECT_MOVIE_TO_MANAGE --> MANAGE_REVIEW
    SELECT_MOVIE_TO_MANAGE --> SELECT_MOVIE_TO_MANAGE
    SELECT_MOVIE_TO_MANAGE --> START
    MANAGE_REVIEW --> MANAGE_REVIEW
    MANAGE_REVIEW --> SELECT_MOVIE_TO_MANAGE
    MANAGE_REVIEW --> START

    START --> START
    START --> END
    SELECT_MOVIE_TO_REVIEW --> END
    REVIEW --> END
    SELECT_MOVIE_PAST_REVIEW --> END
    SHOW_REVIEWS --> END
    SELECT_MOVIE_TO_MANAGE --> END
    MANAGE_REVIEW --> END

    END --> [*]
```

## Structure

- `models.py`: Pydantic models (`Movie`, `Review`, `ManageAction`) constraining LLM responses.
- `states.py`: Finite state machine transitions and conversational state handlers.
- `storage.py`: Review persistence in `reviews.json`.
- `main.py`: Interactive CLI runner and client configuration.
