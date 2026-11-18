"""Small asynchronous client for the Puzzary API."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientResponseError, ClientSession


class PuzzaryError(Exception):
    """Base Puzzary client error."""


class PuzzaryAuthenticationError(PuzzaryError):
    """The supplied API token was not accepted."""


class PuzzaryConnectionError(PuzzaryError):
    """The Puzzary server could not be reached."""


class PuzzaryApiError(PuzzaryError):
    """The Puzzary API rejected a request."""


class PuzzaryApiClient:
    """Access Puzzary without introducing a third-party dependency."""

    def __init__(self, base_url: str, api_token: str, session: ClientSession) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._session = session

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        allow_not_found: bool = False,
        binary: bool = False,
    ) -> Any:
        try:
            async with self._session.request(
                method,
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self._api_token}"},
                json=json,
                timeout=45,
            ) as response:
                if allow_not_found and response.status == 404:
                    return None
                if response.status == 401:
                    detail = await _response_detail(response)
                    raise PuzzaryAuthenticationError(detail or "API token was not accepted")
                if response.status >= 400:
                    detail = await _response_detail(response)
                    raise PuzzaryApiError(detail or f"Puzzary returned HTTP {response.status}")
                return await response.read() if binary else await response.json()
        except PuzzaryError:
            raise
        except (ClientError, TimeoutError, OSError) as exc:
            raise PuzzaryConnectionError(str(exc)) from exc

    async def async_account_stats(self) -> dict[str, Any]:
        return await self._request("GET", "/api/account/stats")

    async def async_latest_puzzle(self) -> dict[str, Any] | None:
        return await self._request("GET", "/api/puzzles/latest?printable=true", allow_not_found=True)

    async def async_puzzle_image(self, puzzle_id: str) -> bytes:
        return await self._request("GET", f"/api/puzzles/{puzzle_id}/print.png", binary=True)

    async def async_puzzles(
        self,
        *,
        availability: str = "active",
        status: str = "any",
        puzzle_type: str | None = None,
    ) -> dict[str, Any]:
        params: list[tuple[str, str]] = [
            ("availability", availability),
            ("status", status),
            ("printable", "true"),
            ("limit", "200"),
            ("sort", "created_desc"),
        ]
        if puzzle_type:
            params.append(("type", puzzle_type))
        return await self._request("GET", f"/api/puzzles?{urlencode(params)}")

    async def async_generate_puzzle(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/puzzles/generate", json=payload)

    async def async_puzzle_action(self, puzzle_id: str, action: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/puzzles/{puzzle_id}/{action}")


async def _response_detail(response) -> str:
    try:
        payload = await response.json()
    except (ClientError, ValueError, ClientResponseError):
        return await response.text()
    detail = payload.get("detail") if isinstance(payload, dict) else None
    return str(detail) if detail else ""
