"""Config flow for Half-Life VOX."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, selector

from .const import (
    CONF_AUTO_FETCH_VOX,
    CONF_PHRASES,
    CONF_SOUNDS_PATH,
    DEFAULT_AUTO_FETCH_VOX,
    DOMAIN,
)
from .download import ensure_vox_sounds


def _default_sounds_path(hass: HomeAssistant) -> str:
    return str(Path(hass.config.config_dir) / "hl_vox" / "sounds")


class HlVoxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle HL VOX config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Single step: optional sounds path and auto_fetch."""
        errors = {}
        if user_input is not None:
            sounds_path_str = user_input.get(CONF_SOUNDS_PATH) or _default_sounds_path(
                self.hass
            )
            sounds_path = Path(sounds_path_str)
            auto_fetch = user_input.get(CONF_AUTO_FETCH_VOX, DEFAULT_AUTO_FETCH_VOX)
            ok = await ensure_vox_sounds(self.hass, sounds_path, auto_fetch)
            if not ok and auto_fetch:
                errors["base"] = "failed_fetch_vox"
            if not errors:
                return self.async_create_entry(
                    title="Half-Life VOX",
                    data={
                        CONF_SOUNDS_PATH: sounds_path_str,
                        CONF_AUTO_FETCH_VOX: auto_fetch,
                    },
                    options={CONF_PHRASES: {}},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SOUNDS_PATH,
                        default=_default_sounds_path(self.hass),
                    ): cv.string,
                    vol.Optional(
                        CONF_AUTO_FETCH_VOX,
                        default=DEFAULT_AUTO_FETCH_VOX,
                    ): cv.boolean,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> HlVoxOptionsFlowHandler:
        """Return the options flow handler."""
        return HlVoxOptionsFlowHandler()


def _default_sounds_path_from_entry(hass: HomeAssistant, entry: ConfigEntry) -> Path:
    """Return sounds path from config entry or default."""
    path_str = entry.data.get(CONF_SOUNDS_PATH) or ""
    if path_str:
        return Path(path_str)
    return Path(hass.config.config_dir) / "hl_vox" / "sounds"


class HlVoxOptionsFlowHandler(OptionsFlow):
    """Handle HL VOX options (phrase builder)."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Show menu: edit phrases (text), add phrase (picker), or done."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_phrases_text", "add_phrase", "done"],
        )

    async def async_step_done(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Save current options and exit."""
        return self.async_create_entry(
            title="", data=dict(self.config_entry.options)
        )

    async def async_step_edit_phrases_text(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Edit phrases as text (one per line: phrase_id = clip1, clip2)."""
        if user_input is not None:
            phrases = _parse_phrases_text(user_input.get("phrases_text", ""))
            return self.async_create_entry(title="", data={CONF_PHRASES: phrases})

        phrases = self.config_entry.options.get(CONF_PHRASES) or {}
        phrases_text = _format_phrases_text(phrases)

        return self.async_show_form(
            step_id="edit_phrases_text",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "phrases_text",
                        default=phrases_text,
                    ): vol.All(cv.string, vol.Coerce(str)),
                }
            ),
            description_placeholders={
                "help": "One phrase per line: phrase_id = clip1, clip2, clip3\n"
                "Example: leak_detected = buzzwarn, attention, liquid, detected",
            },
        )

    _MAX_CLIP_SLOTS = 20

    async def async_step_add_phrase(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Add a phrase with clip selector; multiple clips in order, same clip allowed multiple times."""
        sounds_path = _default_sounds_path_from_entry(self.hass, self.config_entry)
        if not sounds_path.is_dir():
            return self.async_abort(reason="sounds_path_not_dir")

        def _list_wav_stems() -> list[str]:
            return sorted({f.stem for f in sounds_path.glob("*.wav")})

        clip_names = await self.hass.async_add_executor_job(_list_wav_stems)
        if not clip_names:
            return self.async_abort(reason="no_wav_clips")

        options_for_selector = [{"value": c, "label": c} for c in clip_names]

        def _clips_from_input(data: dict) -> list[str]:
            return [
                data[f"clip_{i}"]
                for i in range(1, self._MAX_CLIP_SLOTS + 1)
                if data.get(f"clip_{i}")
            ]

        def _schema(defaults: dict | None = None) -> vol.Schema:
            defaults = defaults or {}
            return vol.Schema(
                {
                    vol.Required(
                        "phrase_id",
                        default=defaults.get("phrase_id", ""),
                    ): cv.string,
                    **{
                        f"clip_{i}": vol.Optional(
                            selector.SelectSelector(
                                selector.SelectSelectorConfig(
                                    options=options_for_selector,
                                    mode=selector.SelectSelectorMode.DROPDOWN,
                                )
                            )
                        )
                        for i in range(1, self._MAX_CLIP_SLOTS + 1)
                    },
                }
            )

        if user_input is not None:
            phrase_id = (user_input.get("phrase_id") or "").strip().replace(" ", "_")
            clips = _clips_from_input(user_input)
            if not phrase_id or not clips:
                return self.async_show_form(
                    step_id="add_phrase",
                    data_schema=_schema(user_input),
                    errors={"base": "phrase_id_and_clips_required"},
                )
            phrases = dict(self.config_entry.options.get(CONF_PHRASES) or {})
            phrases[phrase_id] = clips
            return self.async_create_entry(title="", data={CONF_PHRASES: phrases})

        return self.async_show_form(
            step_id="add_phrase",
            data_schema=_schema(),
        )


def _parse_phrases_text(text: str) -> dict[str, list[str]]:
    """Parse 'phrase_id = clip1, clip2' lines into {phrase_id: [clip1, clip2]}."""
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, rest = line.partition("=")
        phrase_id = key.strip().replace(" ", "_")
        if not phrase_id or not phrase_id.replace("_", "").isalnum():
            continue
        clips = [c.strip() for c in rest.split(",") if c.strip()]
        if phrase_id:
            result[phrase_id] = clips
    return result


def _format_phrases_text(phrases: dict[str, list[str]]) -> str:
    """Format phrases dict as text for the text area."""
    if not phrases:
        return ""
    return "\n".join(
        f"{pid} = {', '.join(clips)}" for pid, clips in sorted(phrases.items())
    )


