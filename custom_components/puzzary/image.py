"""Latest printable puzzle image."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import PuzzaryCoordinator
from .entity import PuzzaryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PuzzaryCoordinator = entry.runtime_data
    async_add_entities([PuzzaryLatestImage(hass, coordinator)])


class PuzzaryLatestImage(PuzzaryEntity, ImageEntity):
    """Image entity backed by the latest printable puzzle."""

    _attr_translation_key = "latest_puzzle"
    _attr_content_type = "image/png"

    def __init__(self, hass: HomeAssistant, coordinator: PuzzaryCoordinator) -> None:
        PuzzaryEntity.__init__(self, coordinator, "latest_puzzle_image")
        ImageEntity.__init__(self, hass)
        latest = coordinator.data.get("latest")
        self._puzzle_id = latest["id"] if latest else None
        self._image: bytes | None = None
        self._attr_image_last_updated: datetime | None = dt_util.now() if latest else None

    @callback
    def _handle_coordinator_update(self) -> None:
        latest = self.coordinator.data.get("latest")
        puzzle_id = latest["id"] if latest else None
        if puzzle_id != self._puzzle_id:
            self._puzzle_id = puzzle_id
            self._image = None
            self._attr_image_last_updated = dt_util.now() if puzzle_id else None
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        if not self._puzzle_id:
            return None
        if self._image is None:
            self._image = await self.coordinator.client.async_puzzle_image(self._puzzle_id)
        return self._image

    @property
    def extra_state_attributes(self) -> dict | None:
        latest = self.coordinator.data.get("latest")
        return {"puzzle_id": latest["id"], "title": latest["title"]} if latest else None
