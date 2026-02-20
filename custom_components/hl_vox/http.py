"""HTTP view to serve concatenated VOX phrase WAV to Cast and other players."""

from __future__ import annotations

from pathlib import Path

from aiohttp import web

from homeassistant.components import http
from homeassistant.core import HomeAssistant

from .const import DEFAULT_SILENCE_MS, DOMAIN
from .media import concat_wavs_to_bytes


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
        """Generate and return the phrase WAV."""
        data = self.hass.data.get(DOMAIN)
        if not data:
            return web.Response(status=503, text="Integration not configured")
        phrases = data.get("phrases") or {}
        sounds_path: Path = data.get("sounds_path")
        silence_ms = data.get("silence_ms", DEFAULT_SILENCE_MS)
        if not sounds_path or phrase_id not in phrases:
            return web.Response(status=404, text="Unknown phrase")
        clip_names = phrases[phrase_id]
        paths = []
        for name in clip_names:
            # Clip names are without .wav; vox files are .wav
            p = sounds_path / f"{name}.wav"
            if not p.is_file():
                return web.Response(status=404, text=f"Missing clip: {name}")
            paths.append(p)
        try:
            wav_bytes = await self.hass.async_add_executor_job(
                concat_wavs_to_bytes,
                paths,
                silence_ms,
            )
        except (ValueError, OSError):
            return web.Response(status=500, text="Failed to build audio")
        return web.Response(body=wav_bytes, content_type="audio/wav")
