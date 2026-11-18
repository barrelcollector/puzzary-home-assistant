"""UI configuration flow for Puzzary."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PuzzaryApiClient, PuzzaryAuthenticationError, PuzzaryConnectionError, PuzzaryError
from .const import CONF_API_TOKEN, CONF_BASE_URL, DOMAIN


class PuzzaryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a Puzzary server and API token."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip().rstrip("/")
            token = user_input[CONF_API_TOKEN].strip()
            parsed = urlparse(base_url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors["base"] = "invalid_url"
            else:
                client = PuzzaryApiClient(base_url, token, async_get_clientsession(self.hass))
                try:
                    stats = await client.async_account_stats()
                except PuzzaryAuthenticationError:
                    errors["base"] = "invalid_auth"
                except PuzzaryConnectionError:
                    errors["base"] = "cannot_connect"
                except PuzzaryError:
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(f"{base_url}|{stats['user_id']}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Puzzary ({parsed.hostname})",
                        data={CONF_BASE_URL: base_url, CONF_API_TOKEN: token},
                    )

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=(user_input or {}).get(CONF_BASE_URL, "http://")): str,
            vol.Required(CONF_API_TOKEN): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
