"""Tests for ReciplaseClient.

Home Assistant pins an exact aiohttp version, and aiohttp-mocking libraries tend to lag behind
new aiohttp releases, so rather than depend on one of those (and risk it breaking whenever HA
bumps its pin), these tests fake just the two aiohttp surfaces the client actually touches:
`ClientSession.request()` as an async context manager, and the response object it yields.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

import pytest
from aiohttp import ClientConnectionError

from reciplease_hass import InvalidAuth, ReciplaseClient, ReciplaseConnectionError

BASE_URL = "https://reciplease.example.com"
API_KEY = "rcpl_testkey1234567890"


class FakeResponse:
    """A minimal stand-in for aiohttp.ClientResponse."""

    def __init__(self, status: int, payload: Any) -> None:
        self.status = status
        self._payload = payload

    async def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


class FakeSession:
    """A minimal stand-in for aiohttp.ClientSession that plays back queued responses."""

    def __init__(self, responses: Sequence[FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append((method, url))
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_client(*responses: FakeResponse | Exception) -> tuple[ReciplaseClient, FakeSession]:
    session = FakeSession(responses)
    return ReciplaseClient(session, BASE_URL, API_KEY), session


async def test_async_get_self_resolves_house_and_role() -> None:
    client, _ = make_client(
        FakeResponse(200, {"houseId": "house-1", "houseName": "Test House", "role": "READ_ONLY"})
    )

    result = await client.async_get_self()

    assert result.house_id == "house-1"
    assert result.house_name == "Test House"
    assert result.role == "READ_ONLY"


async def test_async_get_self_raises_invalid_auth_on_401() -> None:
    client, _ = make_client(FakeResponse(401, None))

    with pytest.raises(InvalidAuth):
        await client.async_get_self()


async def test_house_scoped_call_before_self_raises() -> None:
    client, _ = make_client()

    with pytest.raises(RuntimeError):
        await client.async_get_pantry_summary()


async def test_async_get_pantry_summary_counts_items() -> None:
    client, session = make_client(
        FakeResponse(200, {"houseId": "house-1", "houseName": "Test House", "role": "READ_ONLY"}),
        FakeResponse(200, [{"uuid": "item-1"}, {"uuid": "item-2"}]),
        FakeResponse(200, [{"uuid": "item-2"}]),
    )
    await client.async_get_self()

    summary = await client.async_get_pantry_summary()

    assert summary.total_items == 2
    assert summary.expired_items == 1
    assert session.requests[1] == ("GET", f"{BASE_URL}/api/pantry")
    assert session.requests[2] == ("GET", f"{BASE_URL}/api/pantry/expired")


async def test_async_get_planned_meals_summary_finds_the_nearest_meal() -> None:
    client, _ = make_client(
        FakeResponse(200, {"houseId": "house-1", "houseName": "Test House", "role": "READ_ONLY"}),
        FakeResponse(
            200,
            [
                {"plannedMealId": "meal-2", "name": "Tacos", "date": "2026-02-01", "recipe": None},
                {"plannedMealId": "meal-1", "name": "Pasta", "date": "2026-01-15", "recipe": {"id": "r-1", "name": "Spaghetti"}},
            ],
        ),
    )
    await client.async_get_self()

    summary = await client.async_get_planned_meals_summary()

    assert summary.upcoming_count == 2
    assert summary.next_meal is not None
    assert summary.next_meal.id == "meal-1"
    assert summary.next_meal.name == "Pasta"
    assert summary.next_meal.recipe_name == "Spaghetti"


async def test_async_get_planned_meals_summary_with_no_upcoming_meals() -> None:
    client, _ = make_client(
        FakeResponse(200, {"houseId": "house-1", "houseName": "Test House", "role": "READ_ONLY"}),
        FakeResponse(200, []),
    )
    await client.async_get_self()

    summary = await client.async_get_planned_meals_summary()

    assert summary.upcoming_count == 0
    assert summary.next_meal is None


async def test_connection_error_is_wrapped() -> None:
    client, _ = make_client(ClientConnectionError("boom"))

    with pytest.raises(ReciplaseConnectionError):
        await client.async_get_self()
