import pytest
from pydantic import ValidationError

from models import ManageAction, Movie, Review
from states import apply_manage_action, format_reviews
import storage


def a_review(rate=5, text="Great."):
    return Review(movieId="tt0111161", movieName="Shawshank", rate=rate, review=text)


def a_movie():
    return Movie(movieId="tt0111161", name="Shawshank", year=1994)


def test_no_reviews_says_so_and_names_the_film():
    out = format_reviews("Shawshank", 1994, [])
    assert "no reviews" in out.lower()
    assert "Shawshank" in out
    assert "1994" in out


def test_a_review_shows_its_rate_and_text():
    out = format_reviews("Shawshank", 1994, [a_review(rate=4, text="Solid.")])
    assert "4" in out
    assert "Solid." in out


def test_every_review_is_listed():
    out = format_reviews("Shawshank", 1994, [a_review(text="One."), a_review(text="Two.")])
    assert "One." in out
    assert "Two." in out


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DEFAULT_PATH", tmp_path / "reviews.json")


def test_delete_removes_the_stored_review():
    storage.upsert_review(a_review())
    message = apply_manage_action(a_movie(), ManageAction(action="delete"))
    assert storage.load_reviews() == []
    assert "deleted" in message.lower()


def test_delete_says_so_when_there_is_nothing_to_delete():
    message = apply_manage_action(a_movie(), ManageAction(action="delete"))
    assert "no review" in message.lower()


def test_edit_replaces_the_stored_review():
    storage.upsert_review(a_review(rate=1, text="Bad."))
    apply_manage_action(a_movie(), ManageAction(action="edit", rate=5, review="Changed my mind."))
    stored = storage.load_reviews()
    assert len(stored) == 1
    assert stored[0].rate == 5
    assert stored[0].review == "Changed my mind."


def test_edit_without_a_rate_keeps_the_old_one():
    storage.upsert_review(a_review(rate=3, text="Fine."))
    apply_manage_action(a_movie(), ManageAction(action="edit", review="Better than I said."))
    stored = storage.load_reviews()
    assert stored[0].rate == 3
    assert stored[0].review == "Better than I said."


def test_edit_of_an_unreviewed_film_is_refused():
    message = apply_manage_action(a_movie(), ManageAction(action="edit", rate=4, review="Good."))
    assert storage.load_reviews() == []
    assert "no review" in message.lower()


def test_edit_with_an_empty_review_is_rejected_not_silently_kept():
    storage.upsert_review(a_review(rate=3, text="Fine."))
    with pytest.raises(ValidationError):
        apply_manage_action(a_movie(), ManageAction(action="edit", review=""))
    stored = storage.load_reviews()
    assert stored[0].review == "Fine."
