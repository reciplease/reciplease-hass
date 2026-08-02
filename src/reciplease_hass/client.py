"""Async client for the Reciplease API."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .exceptions import InvalidAuth, ReciplaseConnectionError
from .models import HouseSelf, InventorySummary, PlannedMeal, PlannedMealsSummary

HOUSE_HEADER = "X-RCPLS-House-Id"
UPCOMING_MEALS_WINDOW = timedelta(days=14)


class ReciplaseClient:
    """Talks to a Reciplease house service-account API key."""

    def __init__(self, session: ClientSession, base_url: str, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._house_id: str | None = None

    async def async_get_self(self) -> HouseSelf:
        """Resolve the house/role this API key authenticates as.

        Must be called (and its house_id cached) before any other house-scoped
        call, since the raw key alone doesn't reveal which house it belongs to.
        """
        data = await self._request("GET", "/api/houses/api-keys/self", house_scoped=False)
        self._house_id = data["houseId"]
        return HouseSelf(
            house_id=data["houseId"],
            house_name=data.get("houseName"),
            role=data["role"],
        )

    async def async_get_inventory_summary(self) -> InventorySummary:
        """Fetch inventory counts for the house."""
        items = await self._request("GET", "/api/inventory", params={"excludeFullyConsumed": "true"})
        expired = await self._request("GET", "/api/inventory/expired")
        return InventorySummary(total_items=len(items), expired_items=len(expired))

    async def async_get_planned_meals_summary(self) -> PlannedMealsSummary:
        """Fetch upcoming planned meals for the house."""
        today = datetime.now().astimezone().date()
        params = {
            "start": today.isoformat(),
            "end": (today + UPCOMING_MEALS_WINDOW).isoformat(),
        }
        meals = await self._request("GET", "/api/planned-meals", params=params)
        meals.sort(key=lambda meal: meal["date"])
        next_meal = None
        if meals:
            first = meals[0]
            next_meal = PlannedMeal(
                id=first["plannedMealId"],
                name=first["name"],
                date=date.fromisoformat(first["date"]),
                recipe_name=first["recipe"]["name"] if first.get("recipe") else None,
            )
        return PlannedMealsSummary(upcoming_count=len(meals), next_meal=next_meal)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        house_scoped: bool = True,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        if house_scoped:
            headers[HOUSE_HEADER] = self._require_house_id()
        try:
            async with self._session.request(
                method, f"{self._base_url}{path}", headers=headers, params=params
            ) as response:
                if response.status in (401, 403):
                    raise InvalidAuth(f"{method} {path} returned {response.status}")
                response.raise_for_status()
                return await response.json()
        except ClientResponseError as err:
            raise ReciplaseConnectionError(str(err)) from err
        except ClientError as err:
            raise ReciplaseConnectionError(str(err)) from err

    def _require_house_id(self) -> str:
        if self._house_id is None:
            raise RuntimeError("async_get_self() must be called before any house-scoped request")
        return self._house_id
