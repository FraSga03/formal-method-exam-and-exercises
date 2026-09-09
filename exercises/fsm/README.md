# Movie review FSM

A finite state machine driving an LLM agent that based on response carries on the execution of the fsm.

## Running

```bash
uv sync --extra exercises
uv run python main.py --api-key sk-...
```

The key can also come from `OPENAI_API_KEY` in the environment or in `.env` at the
project root; `--api-key` wins over both. `--model` picks the OpenAI model.

Type `quit` or `exit`, or press Ctrl-C, to end the conversation.

Reviews are stored in `reviews.json`.

## States

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

## Layout

| File | Role |
|---|---|
| `models.py` | `Movie`, `Review`, `ManageAction` — the structured responses, with their constraints |
| `storage.py` | JSON persistence for reviews |
| `states.py` | The machine and its state handlers |
| `main.py` | Client setup and the conversation loop |
