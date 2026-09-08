from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Movie(BaseModel):
    movieId: str = Field(pattern=r"^tt\d{7,8}$")
    name: str = Field(min_length=1)
    year: int = Field(ge=1888, le=2100)


class Review(BaseModel):
    movieId: str = Field(pattern=r"^tt\d{7,8}$")
    movieName: str = Field(min_length=1)
    rate: int = Field(ge=1, le=5)
    review: str

    @field_validator("review")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("review text is empty")
        return stripped


class ManageAction(BaseModel):
    """Fields are optional for a delete."""

    action: Literal["edit", "delete"]
    rate: int | None = Field(default=None, ge=1, le=5)
    review: str | None = None
