import pytest
from pydantic import ValidationError

from models import Movie, Review


def test_movie_accepts_an_imdb_id():
    movie = Movie(movieId="tt0111161", name="The Shawshank Redemption", year=1994)
    assert movie.movieId == "tt0111161"


def test_movie_rejects_a_bare_number_as_id():
    with pytest.raises(ValidationError):
        Movie(movieId="111161", name="The Shawshank Redemption", year=1994)


def test_movie_rejects_a_year_before_cinema():
    with pytest.raises(ValidationError):
        Movie(movieId="tt0111161", name="The Shawshank Redemption", year=1600)


def test_review_accepts_a_rate_in_range():
    review = Review(movieId="tt0111161", movieName="Shawshank", rate=5, review="Great.")
    assert review.rate == 5


@pytest.mark.parametrize("rate", [0, 6, -1])
def test_review_rejects_a_rate_out_of_range(rate):
    with pytest.raises(ValidationError):
        Review(movieId="tt0111161", movieName="Shawshank", rate=rate, review="Great.")


def test_review_rejects_blank_text():
    with pytest.raises(ValidationError):
        Review(movieId="tt0111161", movieName="Shawshank", rate=4, review="   ")


def test_review_strips_surrounding_whitespace():
    review = Review(movieId="tt0111161", movieName="Shawshank", rate=4, review="  Good.  ")
    assert review.review == "Good."
