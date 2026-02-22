"""Constants for the Half-Life VOX integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

DOMAIN: Final[str] = "hl_vox"

CONF_SOUNDS_PATH = "sounds_path"
CONF_AUTO_FETCH_VOX = "auto_fetch_vox"
CONF_PHRASES = "phrases"

DEFAULT_AUTO_FETCH_VOX = True
DEFAULT_SILENCE_MS = 150

# Cache for built phrase WAVs (filesystem)
CACHE_DIR_NAME = "cache"

# GitHub repo ZIP for Half-Life sound files (sound/vox only)
HL1_VOX_REPO_ZIP = "https://github.com/sourcesounds/hl1/archive/refs/heads/master.zip"
HL1_VOX_ZIP_PREFIX = "hl1-master/sound/vox/"

# Frontend (phrase builder card)
URL_BASE: Final[str] = "/hl_vox"
_MANIFEST_PATH = Path(__file__).parent / "manifest.json"
if _MANIFEST_PATH.is_file():
    with open(_MANIFEST_PATH, encoding="utf-8") as f:
        INTEGRATION_VERSION: Final[str] = json.load(f).get("version", "0.0.0")
else:
    INTEGRATION_VERSION = "0.0.0"

JSMODULES: Final[list[dict[str, str]]] = [
    {
        "name": "Half-Life VOX Phrase Builder",
        "filename": "hl-vox-phrase-builder.js",
        "version": INTEGRATION_VERSION,
    },
]
