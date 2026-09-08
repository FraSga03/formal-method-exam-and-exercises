import json

import pytest

from models import Review
import storage


@pytest.fixture
def path(tmp_path):
    return tmp_path / "reviews.json"


def a_review(movie_id="tt0111161", rate=5, text="Great."):
    return Review(movieId=movie_id, movieName="Shawshank", rate=rate, review=text)


def test_load_returns_empty_when_the_file_is_missing(path):
    assert storage.load_reviews(path) == []


def test_load_returns_empty_on_unreadable_json(path):
    path.write_text("{ not json", encoding="utf-8")
    assert storage.load_reviews(path) == []


def test_save_then_load_round_trips(path):
    storage.save_reviews([a_review()], path)
    loaded = storage.load_reviews(path)
    assert loaded == [a_review()]


def test_saved_file_is_a_json_list(path):
    storage.save_reviews([a_review()], path)
    assert json.loads(path.read_text(encoding="utf-8"))[0]["movieId"] == "tt0111161"


def test_upsert_appends_a_new_film(path):
    storage.upsert_review(a_review("tt0111161"), path)
    storage.upsert_review(a_review("tt0068646"), path)
    assert len(storage.load_reviews(path)) == 2


def test_upsert_replaces_the_review_of_the_same_film(path):
    storage.upsert_review(a_review(rate=1, text="Bad."), path)
    storage.upsert_review(a_review(rate=5, text="Changed my mind."), path)
    stored = storage.load_reviews(path)
    assert len(stored) == 1
    assert stored[0].rate == 5


def test_reviews_for_filters_by_film(path):
    storage.upsert_review(a_review("tt0111161"), path)
    storage.upsert_review(a_review("tt0068646"), path)
    assert [r.movieId for r in storage.reviews_for("tt0068646", path)] == ["tt0068646"]


def test_delete_removes_and_reports_true(path):
    storage.upsert_review(a_review(), path)
    assert storage.delete_review("tt0111161", path) is True
    assert storage.load_reviews(path) == []


def test_delete_reports_false_when_nothing_matches(path):
    assert storage.delete_review("tt0111161", path) is False


def test_a_corrupt_entry_does_not_lose_the_valid_ones(path):
    path.write_text(
        json.dumps([{"movieId": "nonsense"}, a_review().model_dump()]),
        encoding="utf-8",
    )
    assert [r.movieId for r in storage.load_reviews(path)] == ["tt0111161"]
