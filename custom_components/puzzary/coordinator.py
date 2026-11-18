"""Shared polling coordinator for Puzzary."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PuzzaryApiClient, PuzzaryAuthenticationError, PuzzaryError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PuzzaryCoordinator(DataUpdateCoordinator[dict]):
    """Poll the account and latest printable puzzle in one update cycle."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: PuzzaryApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            stats, latest = await asyncio.gather(
                self.client.async_account_stats(),
                self.client.async_latest_puzzle(),
            )
        except PuzzaryAuthenticationError as exc:
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except PuzzaryError as exc:
            raise UpdateFailed(str(exc)) from exc
        return {"stats": stats, "latest": latest}
