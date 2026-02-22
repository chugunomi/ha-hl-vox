"""Serve the phrase builder card and optionally register it in Lovelace resources."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from ..const import URL_BASE

_LOGGER = logging.getLogger(__name__)


class JSModuleRegistration:
    """Register static path for the phrase builder card."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_register(self) -> None:
        """Register the static path so the card JS is served at /hl_vox/hl-vox-phrase-builder.js."""
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, Path(__file__).parent, False)]
            )
            _LOGGER.debug("Registered static path %s", URL_BASE)
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)
