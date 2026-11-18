"""Statistics sensors for Puzzary."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import PuzzaryCoordinator
from .entity import PuzzaryEntity


@dataclass(frozen=True, kw_only=True)
class PuzzarySensorDescription(SensorEntityDescription):
    stats_key: str | None = None


DESCRIPTIONS = (
    PuzzarySensorDescription(key="played", translation_key="played", icon="mdi:puzzle", stats_key="played"),
    PuzzarySensorDescription(key="completed", translation_key="completed", icon="mdi:check-circle", stats_key="completed"),
    PuzzarySensorDescription(key="in_progress", translation_key="in_progress", icon="mdi:progress-clock", stats_key="in_progress"),
    PuzzarySensorDescription(key="attempts", translation_key="attempts", icon="mdi:counter", stats_key="attempts"),
    PuzzarySensorDescription(key="correct_attempts", translation_key="correct_attempts", icon="mdi:check-bold", stats_key="correct_attempts"),
    PuzzarySensorDescription(key="latest_puzzle", translation_key="latest_puzzle", icon="mdi:image-outline"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PuzzaryCoordinator = entry.runtime_data
    async_add_entities(PuzzarySensor(coordinator, description) for description in DESCRIPTIONS)


class PuzzarySensor(PuzzaryEntity, SensorEntity):
    """A statistic or latest-puzzle sensor."""

    entity_description: PuzzarySensorDescription

    def __init__(self, coordinator: PuzzaryCoordinator, description: PuzzarySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        if self.entity_description.stats_key:
            return self.coordinator.data["stats"]["totals"][self.entity_description.stats_key]
        latest = self.coordinator.data.get("latest")
        return latest["title"] if latest else None

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.entity_description.key != "latest_puzzle":
            return None
        latest = self.coordinator.data.get("latest")
        if not latest:
            return None
        return {
            "puzzle_id": latest["id"],
            "puzzle_type": latest["puzzle_type"],
            "difficulty": latest["difficulty"],
            "theme": latest["theme"],
            "publication_state": latest["publication_state"],
            "url": latest["url"],
        }
