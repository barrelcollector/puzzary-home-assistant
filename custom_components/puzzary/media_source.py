"""Browse printable Puzzary puzzles in Home Assistant's media library."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
import re

from aiohttp import web

from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.components.http.auth import async_sign_path
from homeassistant.components.media_player import BrowseError, MediaClass
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant

from .api import PuzzaryAuthenticationError, PuzzaryError
from .const import DOMAIN
from .coordinator import PuzzaryCoordinator

MEDIA_PATH = "/api/puzzary/media/{entry_id}/{puzzle_id}.png"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_CATEGORIES = {
    "active": ("Active puzzles", "active", "any"),
    "in-progress": ("In-progress puzzles", "active", "in_progress"),
    "completed": ("Completed puzzles", "active", "completed"),
    "archived": ("Archived puzzles", "archived", "any"),
}


async def async_get_media_source(hass: HomeAssistant) -> PuzzaryMediaSource:
    """Set up the Puzzary media source."""
    return PuzzaryMediaSource(hass)


class PuzzaryMediaSource(MediaSource):
    """Expose printable puzzle images as browsable media folders."""

    name = "Puzzary"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(DOMAIN)
        self.hass = hass

    def _loaded_entries(self) -> list[ConfigEntry]:
        return [
            entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED
            and isinstance(getattr(entry, "runtime_data", None), PuzzaryCoordinator)
        ]

    def _entry(self, entry_id: str) -> ConfigEntry:
        entry = next((item for item in self._loaded_entries() if item.entry_id == entry_id), None)
        if entry is None:
            raise BrowseError("Puzzary connection is not loaded")
        return entry

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Browse servers, status folders, puzzle types, and puzzle images."""
        parts = [part for part in (item.identifier or "").strip("/").split("/") if part]
        if not parts:
            entries = self._loaded_entries()
            if len(entries) == 1:
                return self._entry_folder(entries[0], title="Puzzary")
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier="",
                media_class=MediaClass.APP,
                media_content_type="",
                title="Puzzary",
                can_play=False,
                can_expand=True,
                children_media_class=MediaClass.DIRECTORY,
                children=[self._entry_folder(entry) for entry in entries],
            )

        entry = self._entry(parts[0])
        if len(parts) == 1:
            return self._entry_folder(entry)
        category = parts[1]
        if category not in _CATEGORIES:
            raise BrowseError("Unknown Puzzary media folder")
        if len(parts) == 2:
            return await self._category_folder(entry, category)
        if len(parts) == 4 and parts[2] == "type":
            return await self._type_folder(entry, category, parts[3])
        raise BrowseError("Unknown Puzzary media item")

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve one puzzle to a short-lived authenticated Home Assistant URL."""
        parts = [part for part in (item.identifier or "").strip("/").split("/") if part]
        if len(parts) != 5 or parts[2] != "type":
            raise Unresolvable("Select a puzzle image")
        entry_id, puzzle_id = parts[0], parts[4]
        try:
            self._entry(entry_id)
        except BrowseError as exc:
            raise Unresolvable(str(exc)) from exc
        if not _SAFE_ID.fullmatch(puzzle_id):
            raise Unresolvable("Puzzle ID is not valid")
        path = MEDIA_PATH.format(entry_id=entry_id, puzzle_id=puzzle_id)
        return PlayMedia(
            async_sign_path(self.hass, path, timedelta(minutes=5), use_content_user=True),
            "image/png",
        )

    def _entry_folder(self, entry: ConfigEntry, title: str | None = None) -> BrowseMediaSource:
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=entry.entry_id,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=title or entry.title,
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.DIRECTORY,
            children=[
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{entry.entry_id}/{key}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title=label,
                    can_play=False,
                    can_expand=True,
                    children_media_class=MediaClass.DIRECTORY,
                )
                for key, (label, _, _) in _CATEGORIES.items()
            ],
        )

    async def _category_folder(self, entry: ConfigEntry, category: str) -> BrowseMediaSource:
        label, availability, status = _CATEGORIES[category]
        payload = await self._puzzles(entry, availability=availability, status=status)
        grouped: dict[str, list[dict]] = defaultdict(list)
        for puzzle in payload["items"]:
            grouped[puzzle["puzzle_type"]].append(puzzle)
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"{entry.entry_id}/{category}/type/{puzzle_type}",
                media_class=MediaClass.DIRECTORY,
                media_content_type="",
                title=puzzles[0].get("puzzle_type_label", puzzle_type.replace("_", " ").title()),
                can_play=False,
                can_expand=True,
                children_media_class=MediaClass.IMAGE,
            )
            for puzzle_type, puzzles in sorted(grouped.items())
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{entry.entry_id}/{category}",
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=label,
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.DIRECTORY,
            children=children,
            not_shown=max(0, payload["count"] - payload["returned"]),
        )

    async def _type_folder(self, entry: ConfigEntry, category: str, puzzle_type: str) -> BrowseMediaSource:
        if not _SAFE_ID.fullmatch(puzzle_type):
            raise BrowseError("Puzzle type is not valid")
        label, availability, status = _CATEGORIES[category]
        payload = await self._puzzles(
            entry,
            availability=availability,
            status=status,
            puzzle_type=puzzle_type,
        )
        items = payload["items"]
        type_label = items[0].get("puzzle_type_label", puzzle_type.replace("_", " ").title()) if items else puzzle_type.replace("_", " ").title()
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{entry.entry_id}/{category}/type/{puzzle_type}",
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=f"{label} · {type_label}",
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.IMAGE,
            children=[self._puzzle_item(entry, category, puzzle) for puzzle in items],
            not_shown=max(0, payload["count"] - payload["returned"]),
        )

    def _puzzle_item(self, entry: ConfigEntry, category: str, puzzle: dict) -> BrowseMediaSource:
        puzzle_type = puzzle["puzzle_type"]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{entry.entry_id}/{category}/type/{puzzle_type}/{puzzle['id']}",
            media_class=MediaClass.IMAGE,
            media_content_type="image/png",
            title=f"{puzzle['title']} · {puzzle['difficulty'].title()}",
            can_play=True,
            can_expand=False,
        )

    async def _puzzles(self, entry: ConfigEntry, **filters) -> dict:
        coordinator: PuzzaryCoordinator = entry.runtime_data
        try:
            return await coordinator.client.async_puzzles(**filters)
        except PuzzaryError as exc:
            raise BrowseError(str(exc)) from exc


class PuzzaryMediaView(HomeAssistantView):
    """Proxy an authenticated Puzzary PNG through Home Assistant."""

    name = "api:puzzary:media"
    url = MEDIA_PATH
    requires_auth = True

    async def get(self, request: web.Request, entry_id: str, puzzle_id: str) -> web.Response:
        hass: HomeAssistant = request.app[KEY_HASS]
        if not _SAFE_ID.fullmatch(puzzle_id):
            raise web.HTTPNotFound
        entry = hass.config_entries.async_get_entry(entry_id)
        if (
            entry is None
            or entry.domain != DOMAIN
            or entry.state is not ConfigEntryState.LOADED
            or not isinstance(getattr(entry, "runtime_data", None), PuzzaryCoordinator)
        ):
            raise web.HTTPNotFound
        try:
            image = await entry.runtime_data.client.async_puzzle_image(puzzle_id)
        except PuzzaryAuthenticationError as exc:
            raise web.HTTPUnauthorized(text=str(exc)) from exc
        except PuzzaryError as exc:
            raise web.HTTPBadGateway(text=str(exc)) from exc
        return web.Response(
            body=image,
            content_type="image/png",
            headers={"Cache-Control": "private, max-age=300"},
        )
