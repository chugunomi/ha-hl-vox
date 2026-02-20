"""Expose HL VOX phrases as a media source for media_player.play_media."""

from __future__ import annotations

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> HlVoxMediaSource:
    """Return the HL VOX media source."""
    return HlVoxMediaSource(hass)


class HlVoxMediaSource(MediaSource):
    """Media source for Half-Life VOX phrase announcements."""

    name = "Half-Life VOX"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(DOMAIN)
        self.hass = hass

    def _get_config(self):
        return self.hass.data.get(DOMAIN) or {}

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """List defined phrases (or root)."""
        config = self._get_config()
        phrases = config.get("phrases") or {}
        if not phrases:
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=None,
                media_class=MediaClass.APP,
                media_content_type=MediaType.APP,
                title=self.name,
                can_play=False,
                can_expand=False,
            )
        if not item.identifier:
            children = [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=phrase_id,
                    media_class=MediaClass.MUSIC,
                    media_content_type="audio/wav",
                    title=phrase_id.replace("_", " ").title(),
                    can_play=True,
                    can_expand=False,
                )
                for phrase_id in sorted(phrases)
            ]
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=None,
                media_class=MediaClass.APP,
                media_content_type=MediaType.APP,
                title=self.name,
                can_play=False,
                can_expand=True,
                children=children,
            )
        if item.identifier in phrases:
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=item.identifier,
                media_class=MediaClass.MUSIC,
                media_content_type="audio/wav",
                title=item.identifier.replace("_", " ").title(),
                can_play=True,
                can_expand=False,
            )
        raise Unresolvable("Unknown phrase")

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve phrase to a playable URL (our HTTP endpoint)."""
        config = self._get_config()
        phrases = config.get("phrases") or {}
        if item.identifier not in phrases:
            raise Unresolvable("Unknown phrase")
        base = self.hass.config.internal_url or self.hass.config.external_url
        if not base:
            raise Unresolvable("No base URL configured")
        base = base.rstrip("/")
        url = f"{base}/api/hl_vox/audio/{item.identifier}"
        return PlayMedia(url, "audio/wav")
