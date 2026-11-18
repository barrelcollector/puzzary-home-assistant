"""Puzzary integration setup and administrative actions."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PuzzaryApiClient, PuzzaryError
from .const import (
    CONF_API_TOKEN,
    CONF_BASE_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_ARCHIVE_PUZZLE,
    SERVICE_GENERATE_PUZZLE,
    SERVICE_PUBLISH_PUZZLE,
    SERVICE_REFRESH,
    SERVICE_UNARCHIVE_PUZZLE,
)
from .coordinator import PuzzaryCoordinator
from .media_source import PuzzaryMediaView

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_PUZZLE_ID = "puzzle_id"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register actions even before a config entry is loaded."""

    hass.http.register_view(PuzzaryMediaView())

    async def async_handle_service(call: ServiceCall) -> ServiceResponse | None:
        coordinator = _coordinator_for_call(hass, call)
        client = coordinator.client
        try:
            if call.service == SERVICE_REFRESH:
                await coordinator.async_request_refresh()
                return {"refreshed": True} if call.return_response else None
            if call.service == SERVICE_GENERATE_PUZZLE:
                payload: dict[str, Any] = {
                    "puzzle_type": call.data["puzzle_type"],
                    "theme": call.data.get("theme", "general"),
                    "difficulty": call.data.get("difficulty", "easy"),
                    "word_bank_slugs": call.data.get("word_bank_slugs", []),
                    "seed": call.data.get("seed") or None,
                    "completion_message": call.data.get("completion_message", ""),
                    "visibility": call.data.get("visibility", "public"),
                    "generation_options": call.data.get("generation_options", {}),
                }
                result = await client.async_generate_puzzle(payload)
            else:
                action = {
                    SERVICE_PUBLISH_PUZZLE: "publish",
                    SERVICE_ARCHIVE_PUZZLE: "archive",
                    SERVICE_UNARCHIVE_PUZZLE: "unarchive",
                }[call.service]
                result = await client.async_puzzle_action(call.data[ATTR_PUZZLE_ID], action)
            await coordinator.async_request_refresh()
            return result if call.return_response else None
        except PuzzaryError as exc:
            raise HomeAssistantError(str(exc)) from exc

    base_schema = {vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string}
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        async_handle_service,
        schema=vol.Schema(base_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_PUZZLE,
        async_handle_service,
        schema=vol.Schema({
            **base_schema,
            vol.Required("puzzle_type"): cv.string,
            vol.Optional("theme", default="general"): cv.string,
            vol.Optional("difficulty", default="easy"): cv.string,
            vol.Optional("word_bank_slugs", default=[]): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional("seed", default=""): cv.string,
            vol.Optional("completion_message", default=""): cv.string,
            vol.Optional("visibility", default="public"): vol.In(("public", "unlisted")),
            vol.Optional("generation_options", default={}): dict,
        }),
        supports_response=SupportsResponse.OPTIONAL,
    )
    puzzle_action_schema = vol.Schema({**base_schema, vol.Required(ATTR_PUZZLE_ID): cv.string})
    for service in (SERVICE_PUBLISH_PUZZLE, SERVICE_ARCHIVE_PUZZLE, SERVICE_UNARCHIVE_PUZZLE):
        hass.services.async_register(
            DOMAIN,
            service,
            async_handle_service,
            schema=puzzle_action_schema,
            supports_response=SupportsResponse.OPTIONAL,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Puzzary server account."""
    client = PuzzaryApiClient(
        entry.data[CONF_BASE_URL],
        entry.data[CONF_API_TOKEN],
        async_get_clientsession(hass),
    )
    coordinator = PuzzaryCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Puzzary config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _coordinator_for_call(hass: HomeAssistant, call: ServiceCall) -> PuzzaryCoordinator:
    entry = hass.config_entries.async_get_entry(call.data[ATTR_CONFIG_ENTRY_ID])
    if entry is None or entry.domain != DOMAIN or not isinstance(getattr(entry, "runtime_data", None), PuzzaryCoordinator):
        raise ServiceValidationError("Select a loaded Puzzary configuration entry")
    return entry.runtime_data
