"""Download and extract Half-Life VOX sounds from sourcesounds/hl1."""

import zipfile
import io
from pathlib import Path

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import HL1_VOX_REPO_ZIP, HL1_VOX_ZIP_PREFIX


def _extract_vox_from_zip(zip_bytes: bytes, sounds_path: Path) -> None:
    """Extract only sound/vox contents from the hl1 repo ZIP into sounds_path (blocking)."""
    sounds_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        for name in zf.namelist():
            if not name.startswith(HL1_VOX_ZIP_PREFIX):
                continue
            inner = name[len(HL1_VOX_ZIP_PREFIX) :].lstrip("/")
            if not inner or name.endswith("/"):
                continue
            # Flatten: e.g. buzzwarn.wav -> sounds_path/buzzwarn.wav
            out_name = Path(inner).name
            out_path = sounds_path / out_name
            out_path.write_bytes(zf.read(name))


def _sounds_dir_has_wavs(sounds_path: Path) -> bool:
    """Return True if the directory exists and contains at least one .wav file."""
    if not sounds_path.is_dir():
        return False
    return any(sounds_path.glob("*.wav"))


async def ensure_vox_sounds(hass, sounds_path: Path, auto_fetch: bool) -> bool:
    """
    Ensure the VOX sounds directory is populated. If auto_fetch is True and the
    directory is empty or missing, download and extract from sourcesounds/hl1.
    Returns True if sounds are available (pre-existing or after fetch), False otherwise.
    """
    if _sounds_dir_has_wavs(sounds_path):
        return True
    if not auto_fetch:
        return False
    sounds_path.mkdir(parents=True, exist_ok=True)
    session = async_get_clientsession(hass)
    try:
        async with session.get(HL1_VOX_REPO_ZIP) as resp:
            resp.raise_for_status()
            zip_bytes = await resp.read()
    except Exception:
        return False
    await hass.async_add_executor_job(_extract_vox_from_zip, zip_bytes, sounds_path)
    return _sounds_dir_has_wavs(sounds_path)
