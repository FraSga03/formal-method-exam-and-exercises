import json
from pathlib import Path

from pydantic import ValidationError

from models import Review

DEFAULT_PATH = Path(__file__).parent / "reviews.json"


def _resolve(path: Path | None) -> Path:
    return DEFAULT_PATH if path is None else path


def load_reviews(path: Path | None = None) -> list[Review]:
    """Stored reviews, skipping any entry that no longer validates."""
    target = _resolve(path)
    if not target.exists():
        return []
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []

    reviews = []
    for entry in raw:
        try:
            reviews.append(Review.model_validate(entry))
        except ValidationError:
            continue
    return reviews


def save_reviews(reviews: list[Review], path: Path | None = None) -> None:
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps([r.model_dump() for r in reviews], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def reviews_for(movie_id: str, path: Path | None = None) -> list[Review]:
    return [r for r in load_reviews(path) if r.movieId == movie_id]


def upsert_review(review: Review, path: Path | None = None) -> None:
    """One review per film: a second review of the same film replaces the first."""
    reviews = [r for r in load_reviews(path) if r.movieId != review.movieId]
    reviews.append(review)
    save_reviews(reviews, path)


def delete_review(movie_id: str, path: Path | None = None) -> bool:
    reviews = load_reviews(path)
    remaining = [r for r in reviews if r.movieId != movie_id]
    if len(remaining) == len(reviews):
        return False
    save_reviews(remaining, path)
    return True
