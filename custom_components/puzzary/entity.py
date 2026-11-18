"""Base entity for Puzzary."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PuzzaryCoordinator


class PuzzaryEntity(CoordinatorEntity[PuzzaryCoordinator]):
    """Common identity and device information."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PuzzaryCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Puzzary",
            manufacturer="Puzzary",
            model="Puzzle library",
            configuration_url=coordinator.client.base_url,
        )
