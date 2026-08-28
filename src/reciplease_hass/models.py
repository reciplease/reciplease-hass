"""Data models returned by the Reciplease client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class HouseSelf:
    """The house/role a given API key resolves to."""

    house_id: str
    house_name: str | None
    role: str


@dataclass(frozen=True)
class PantrySummary:
    """Aggregate counts derived from the house's pantry list."""

    total_items: int
    expired_items: int


@dataclass(frozen=True)
class PlannedMeal:
    """A single planned meal."""

    id: str
    name: str
    date: date
    recipe_name: str | None


@dataclass(frozen=True)
class PlannedMealsSummary:
    """Upcoming planned meals, nearest first."""

    upcoming_count: int
    next_meal: PlannedMeal | None
