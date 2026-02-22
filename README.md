# Half-Life VOX for Home Assistant

Play Half-Life-style VOX announcements (e.g. "Leak detected in sector B") on Cast devices and other media players in Home Assistant. Uses WAV clips from [sourcesounds/hl1](https://github.com/sourcesounds/hl1), concatenated in pure Python (no ffmpeg).

## Installation (HACS)

1. Add this repository as a custom repository in HACS.
2. Install the "Half-Life VOX" integration.
3. Restart Home Assistant.
4. Go to **Settings → Integrations → Half-Life VOX** and configure (sounds path, auto-fetch VOX). No YAML is required for phrases.

On first run, if a sounds path is not set, the integration uses `<config>/hl_vox/sounds` and can auto-download the `sound/vox` folder from [sourcesounds/hl1](https://github.com/sourcesounds/hl1).

## Configuration

- **Phrases** are defined in the integration’s **Configure** (Edit phrases text, or Add phrase with comma-separated clips), or via the **Phrase Builder card** (recommended), or by calling `hl_vox.play_clips` in automations (built and cached on first use).
- **Phrase Builder card** (custom frontend): Autocomplete and repeating clips. Add the card to a dashboard:
  1. **Settings → Dashboards → Resources** → Add resource → URL: `/hl_vox/hl-vox-phrase-builder.js`, Type: **JavaScript Module** → Create.
  2. Edit a dashboard → Add card → **Custom: Half-Life VOX Phrase Builder**. Enter a phrase ID, add clips (type to search), reorder or repeat clips, then **Save phrase**.
- **Integration Configure**: Use **Edit phrases (text)** for comma-separated lists, or **Add phrase** (phrase ID + comma-separated clips). Same clip can appear multiple times.

## Usage

- **Media source**: Use `media_content_id: media-source://hl_vox/<phrase_id>` with `media_player.play_media` (phrase_id from the phrase builder or from `play_clips`).
- **Services**:
  - **`hl_vox.play_phrase`** — Play a phrase. Data: `phrase_id`, `entity_id` (media player).
  - **`hl_vox.play_clips`** — Play a sequence of clips (built and cached on first use). Data: `entity_id`, `clips` (list of WAV base names).
  - **`hl_vox.set_phrase`** — Save or update a phrase (used by the Phrase Builder card). Data: `phrase_id`, `clips` (list).

### Example automations

Using a phrase built in the integration UI:

```yaml
action:
  - service: hl_vox.play_phrase
    data:
      phrase_id: leak_detected
      entity_id: media_player.google_home_mini
```

Using an inline clip list (no pre-defined phrase):

```yaml
action:
  - service: hl_vox.play_clips
    data:
      entity_id: media_player.google_home_mini
      clips:
        - doop
        - vox_login
```

## Requirements

- Home Assistant (tested on recent versions)
- No ffmpeg or Node; uses only Python stdlib for WAV handling

## License

This integration is not affiliated with Valve or the Half-Life franchise. Sound assets are from the [sourcesounds/hl1](https://github.com/sourcesounds/hl1) repository.
