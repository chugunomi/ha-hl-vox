"""Half-Life VOX audio announcements for Home Assistant."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CACHE_DIR_NAME,
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


def _register_view_if_needed(hass: HomeAssistant) -> None:
    """Register the HTTP view once (idempotent)."""
    if getattr(HlVoxAudioView, "_registered", False):
        return
    hass.http.register_view(HlVoxAudioView(hass))
    HlVoxAudioView._registered = True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the HL VOX integration from YAML (when no config entry exists)."""
    if hass.config_entries.async_entries(DOMAIN):
        return True
    conf = config.get(DOMAIN) or {}
    sounds_path_str = conf.get(CONF_SOUNDS_PATH)
    if sounds_path_str:
        sounds_path = Path(sounds_path_str)
    else:
        sounds_path = Path(hass.config.config_dir) / "hl_vox" / "sounds"
    auto_fetch = conf.get(CONF_AUTO_FETCH_VOX, DEFAULT_AUTO_FETCH_VOX)
    phrases = conf.get(CONF_PHRASES) or {}
    cache_dir = Path(hass.config.config_dir) / "hl_vox" / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)

    await ensure_vox_sounds(hass, sounds_path, auto_fetch)

    hass.data[DOMAIN] = {
        "phrases": phrases,
        "sounds_path": sounds_path,
        "cache_dir": cache_dir,
        "silence_ms": DEFAULT_SILENCE_MS,
    }

    _register_view_if_needed(hass)

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


def _clear_phrase_cache(cache_dir: Path, phrase_ids: list[str] | None = None) -> None:
    """Remove cached WAV files. If phrase_ids is None, clear all."""
    if not cache_dir.is_dir():
        return
    if phrase_ids is not None:
        for pid in phrase_ids:
            (cache_dir / f"{pid}.wav").unlink(missing_ok=True)
    else:
        for f in cache_dir.glob("*.wav"):
            f.unlink(missing_ok=True)


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update hass.data phrases and invalidate phrase cache when options change."""
    data = hass.data.get(DOMAIN)
    if not data:
        return
    new_phrases = entry.options.get(CONF_PHRASES) or {}
    data["phrases"] = new_phrases
    cache_dir: Path | None = data.get("cache_dir")
    if cache_dir:
        _clear_phrase_cache(cache_dir, list(new_phrases.keys()))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HL VOX from a config entry."""
    sounds_path = Path(entry.data.get(CONF_SOUNDS_PATH) or "")
    if not sounds_path:
        sounds_path = Path(hass.config.config_dir) / "hl_vox" / "sounds"
    auto_fetch = entry.data.get(CONF_AUTO_FETCH_VOX, DEFAULT_AUTO_FETCH_VOX)
    phrases = entry.options.get(CONF_PHRASES) or {}
    cache_dir = Path(hass.config.config_dir) / "hl_vox" / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)

    await ensure_vox_sounds(hass, sounds_path, auto_fetch)

    hass.data[DOMAIN] = {
        "phrases": phrases,
        "sounds_path": sounds_path,
        "cache_dir": cache_dir,
        "silence_ms": DEFAULT_SILENCE_MS,
    }

    entry.async_add_update_listener(_async_options_updated)
    _register_view_if_needed(hass)

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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if DOMAIN in hass.data:
        del hass.data[DOMAIN]
    return True
