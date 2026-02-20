"""Half-Life VOX audio announcements for Home Assistant."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_AUTO_FETCH_VOX,
    CONF_PHRASES,
    CONF_SOUNDS_PATH,
    DEFAULT_AUTO_FETCH_VOX,
    DEFAULT_SILENCE_MS,
    DOMAIN,
)
from .download import ensure_vox_sounds
from .http import HlVoxAudioView


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Optional(CONF_SOUNDS_PATH): cv.string,
                vol.Optional(
                    CONF_AUTO_FETCH_VOX, default=DEFAULT_AUTO_FETCH_VOX
                ): cv.boolean,
                vol.Optional(CONF_PHRASES, default={}): vol.Schema(
                    {cv.slug: [cv.string]}
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the HL VOX integration from YAML."""
    conf = config.get(DOMAIN) or {}
    sounds_path_str = conf.get(CONF_SOUNDS_PATH)
    if sounds_path_str:
        sounds_path = Path(sounds_path_str)
    else:
        sounds_path = Path(hass.config.config_dir) / "hl_vox" / "sounds"
    auto_fetch = conf.get(CONF_AUTO_FETCH_VOX, DEFAULT_AUTO_FETCH_VOX)
    phrases = conf.get(CONF_PHRASES) or {}

    await ensure_vox_sounds(hass, sounds_path, auto_fetch)

    hass.data[DOMAIN] = {
        "phrases": phrases,
        "sounds_path": sounds_path,
        "silence_ms": DEFAULT_SILENCE_MS,
    }

    hass.http.register_view(HlVoxAudioView(hass))

    async def play_phrase(call: ServiceCall) -> None:
        phrase_id = call.data["phrase_id"]
        entity_id = call.data["entity_id"]
        if isinstance(entity_id, str):
            entity_id = [entity_id]
        media_content_id = f"media-source://{DOMAIN}/{phrase_id}"
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": entity_id,
                "media_content_id": media_content_id,
                "media_content_type": "audio/wav",
            },
            blocking=True,
        )

    hass.services.async_register(
        DOMAIN,
        "play_phrase",
        play_phrase,
        schema=vol.Schema(
            {
                vol.Required("phrase_id"): cv.string,
                vol.Required("entity_id"): cv.comp_entity_ids,
            }
        ),
    )
    return True
