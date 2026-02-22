"""HTTP view to serve concatenated VOX phrase WAV to Cast and other players."""

from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web

from homeassistant.components import http
from homeassistant.core import HomeAssistant

from .const import DEFAULT_SILENCE_MS, DOMAIN
from .media import concat_wavs

LOGGER = logging.getLogger(__name__)


class HlVoxClipsView(http.HomeAssistantView):
    """Return list of available clip names (WAV stems) for the phrase builder."""

    name = "api:hl_vox:clips"
    url = "/api/hl_vox/clips"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return JSON array of clip base names."""
        data = self.hass.data.get(DOMAIN)
        if not data:
            return web.json_response({"clips": []})
        sounds_path: Path = data.get("sounds_path")
        if not sounds_path or not sounds_path.is_dir():
            return web.json_response({"clips": []})

        def _stems() -> list[str]:
            return sorted({f.stem for f in sounds_path.glob("*.wav")})

        clips = await self.hass.async_add_executor_job(_stems)
        return web.json_response({"clips": clips})


class HlVoxAudioView(http.HomeAssistantView):
    """Serve a phrase as a single WAV file; no auth so Cast can fetch the URL."""

    name = "api:hl_vox:audio"
    url = "/api/hl_vox/audio/{phrase_id}"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(
        self,
        request: web.Request,
        phrase_id: str,
    ) -> web.Response:
        """Serve phrase WAV from cache or build and cache it."""
        data = self.hass.data.get(DOMAIN)
        if not data:
            return web.Response(status=503, text="Integration not configured")
        phrases = data.get("phrases") or {}
        sounds_path: Path = data.get("sounds_path")
        cache_dir: Path | None = data.get("cache_dir")
        silence_ms = data.get("silence_ms", DEFAULT_SILENCE_MS)
        if not sounds_path or phrase_id not in phrases:
            return web.Response(status=404, text="Unknown phrase")
        if not cache_dir:
            return web.Response(status=503, text="Cache not configured")
        cache_path = cache_dir / f"{phrase_id}.wav"
        if cache_path.is_file():
            wav_bytes = await self.hass.async_add_executor_job(
                cache_path.read_bytes,
            )
            return web.Response(body=wav_bytes, content_type="audio/wav")
        clip_names = phrases[phrase_id]
        paths = []
        for name in clip_names:
            p = sounds_path / f"{name}.wav"
            if not p.is_file():
                return web.Response(status=404, text=f"Missing clip: {name}")
            paths.append(p)
        try:
            await self.hass.async_add_executor_job(
                concat_wavs,
                paths,
                cache_path,
                silence_ms,
            )
        except (ValueError, OSError) as err:
            LOGGER.exception(
                "Failed to build phrase %s: %s",
                phrase_id,
                err,
            )
            msg = (
                "WAV format mismatch between clips"
                if isinstance(err, ValueError) and "format" in str(err).lower()
                else "Failed to build audio"
            )
            return web.Response(status=500, text=msg)
        wav_bytes = await self.hass.async_add_executor_job(
            cache_path.read_bytes,
        )
        return web.Response(body=wav_bytes, content_type="audio/wav")
