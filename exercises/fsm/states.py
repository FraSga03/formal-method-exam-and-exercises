from fsm_llm import LLMStateMachine

from models import ManageAction, Movie, Review
from storage import delete_review, reviews_for, upsert_review

SELECTED_MOVIE = "selected_movie"

IMDB_HINT = (
    " Use the IMDb id of the film for movieId, not its name."
    " Search for the name and year if you need to look it up."
)

fsm = LLMStateMachine(initial_state="START", end_state="END")


def format_reviews(movie_name: str, year: int, reviews: list[Review]) -> str:
    if not reviews:
        return f"There are no reviews for {movie_name} ({year})."

    lines = [f"Reviews for {movie_name} ({year}):"]
    lines += [f"\t{r.rate}/5 - {r.review}" for r in reviews]
    return "\n".join(lines)


@fsm.define_state(
    state_key="START",
    prompt_template=(
        "You are a movie review assistant. Ask the user whether they want to"
        " review a film, read past reviews, or change a review they already wrote."
    ),
    transitions={
        "SELECT_MOVIE_TO_REVIEW": "If the user wants to review a film",
        "SELECT_MOVIE_PAST_REVIEW": "If the user wants to read past reviews",
        "SELECT_MOVIE_TO_MANAGE": "If the user wants to change or delete a review they wrote",
        "END": "If the user wants to end the conversation",
        "START": "If you did not understand, ask again",
    },
)
async def start_state(fsm: LLMStateMachine, response: str, will_transition: bool) -> str:
    if will_transition and fsm.get_next_state() == "END":
        return "Goodbye!"
    return response


@fsm.define_state(
    state_key="SELECT_MOVIE_PAST_REVIEW",
    prompt_template=(
        "Ask which film the user wants to read reviews for. Go to SHOW_REVIEWS"
        " once you are sure of the film, otherwise ask them to clarify." + IMDB_HINT
    ),
    response_model=Movie,
    transitions={
        "SHOW_REVIEWS": "If you are sure which film it is",
        "END": "If the user wants to end the conversation",
        "SELECT_MOVIE_PAST_REVIEW": "If you are not sure which film it is",
    },
)
async def select_movie_past_review(fsm: LLMStateMachine, response: Movie, will_transition: bool):
    if not will_transition:
        return response

    next_state = fsm.get_next_state()
    if next_state == "SHOW_REVIEWS":
        listing = format_reviews(response.name, response.year, reviews_for(response.movieId))
        return listing + "\n\nAnother film, or back to the start?"
    if next_state == "END":
        return "Goodbye!"
    return response


@fsm.define_state(
    state_key="SHOW_REVIEWS",
    prompt_template="Ask whether the user wants reviews for another film or to go back to the start.",
    transitions={
        "SELECT_MOVIE_PAST_REVIEW": "If the user wants reviews for another film",
        "START": "If the user wants to go back to the start",
        "END": "If the user wants to end the conversation",
    },
)
async def show_reviews(fsm: LLMStateMachine, response: str, will_transition: bool) -> str:
    if will_transition and fsm.get_next_state() == "END":
        return "Goodbye!"
    return response


@fsm.define_state(
    state_key="SELECT_MOVIE_TO_REVIEW",
    prompt_template=(
        "Ask which film the user wants to review. Go to REVIEW once you are sure"
        " of the film, otherwise ask them to clarify." + IMDB_HINT
    ),
    response_model=Movie,
    transitions={
        "REVIEW": "If you are sure which film it is",
        "END": "If the user wants to end the conversation",
        "SELECT_MOVIE_TO_REVIEW": "If you are not sure which film it is",
    },
)
async def select_movie_to_review(fsm: LLMStateMachine, response: Movie, will_transition: bool):
    if not will_transition:
        return response

    next_state = fsm.get_next_state()
    if next_state == "REVIEW":
        fsm.set_context_data(SELECTED_MOVIE, response)
        return f"Let's review {response.name} ({response.year}). What did you think, and what do you rate it out of 5?"
    if next_state == "END":
        return "Goodbye!"
    return response


@fsm.define_state(
    state_key="REVIEW",
    prompt_template=(
        "The user is reviewing {selected_movie.name} ({selected_movie.year})."
        " Collect their review text and a rate from 1 to 5. Go back to START once"
        " you have both; stay here if something is missing." + IMDB_HINT
    ),
    response_model=Review,
    transitions={
        "START": "If the review text and the rate are both present",
        "SELECT_MOVIE_TO_REVIEW": "If the user wants to review a different film",
        "REVIEW": "If the review text or the rate is missing",
        "END": "If the user wants to end the conversation",
    },
)
async def review_state(fsm: LLMStateMachine, response: Review, will_transition: bool):
    if not will_transition:
        return response

    next_state = fsm.get_next_state()
    if next_state == "START":
        upsert_review(response)
        return "Saved. Review another film, read past reviews, or change one?"
    if next_state == "SELECT_MOVIE_TO_REVIEW":
        return "Sure. Which film?"
    if next_state == "REVIEW":
        return "I still need both the review and a rate from 1 to 5."
    return "Goodbye!"


@fsm.define_state(
    state_key="END",
    prompt_template="Say goodbye.",
)
async def end_state(fsm: LLMStateMachine, response: str, will_transition: bool) -> str:
    return "Goodbye!"


def apply_manage_action(movie: Movie, action: ManageAction) -> str:
    existing = reviews_for(movie.movieId)
    if not existing:
        return f"There is no review of {movie.name} ({movie.year}) to change."

    if action.action == "delete":
        delete_review(movie.movieId)
        return f"Deleted your review of {movie.name} ({movie.year})."

    current = existing[0]
    upsert_review(
        Review(
            movieId=movie.movieId,
            movieName=movie.name,
            rate=action.rate if action.rate is not None else current.rate,
            review=action.review if action.review is not None else current.review,
        )
    )
    return f"Updated your review of {movie.name} ({movie.year})."


@fsm.define_state(
    state_key="SELECT_MOVIE_TO_MANAGE",
    prompt_template=(
        "Ask which film's review the user wants to change or delete. Go to"
        " MANAGE_REVIEW once you are sure of the film, otherwise ask them to"
        " clarify." + IMDB_HINT
    ),
    response_model=Movie,
    transitions={
        "MANAGE_REVIEW": "If you are sure which film it is",
        "START": "If the user wants to go back to the start",
        "END": "If the user wants to end the conversation",
        "SELECT_MOVIE_TO_MANAGE": "If you are not sure which film it is",
    },
)
async def select_movie_to_manage(fsm: LLMStateMachine, response: Movie, will_transition: bool):
    if not will_transition:
        return response

    next_state = fsm.get_next_state()
    if next_state == "MANAGE_REVIEW":
        fsm.set_context_data(SELECTED_MOVIE, response)
        listing = format_reviews(response.name, response.year, reviews_for(response.movieId))
        return listing + "\n\nDo you want to change it or delete it?"
    if next_state == "END":
        return "Goodbye!"
    return response


@fsm.define_state(
    state_key="MANAGE_REVIEW",
    prompt_template=(
        "The user is changing their review of {selected_movie.name}"
        " ({selected_movie.year}). Set action to delete if they want it removed,"
        " or to edit with the new rate and review text. Ask again if it is"
        " unclear which they mean."
    ),
    response_model=ManageAction,
    transitions={
        "START": "Once the review has been changed or deleted",
        "SELECT_MOVIE_TO_MANAGE": "If the user wants to change a different film's review",
        "MANAGE_REVIEW": "If it is unclear what to change, or the new review is incomplete",
        "END": "If the user wants to end the conversation",
    },
)
async def manage_review(fsm: LLMStateMachine, response: ManageAction, will_transition: bool):
    if not will_transition:
        return response

    next_state = fsm.get_next_state()
    if next_state == "START":
        movie = fsm.get_context_data(SELECTED_MOVIE)
        return apply_manage_action(movie, response) + "\n\nAnything else?"
    if next_state == "SELECT_MOVIE_TO_MANAGE":
        return "Sure. Which film?"
    if next_state == "MANAGE_REVIEW":
        return "Should I change the review or delete it?"
    return "Goodbye!"
