# Half-Life VOX for Home Assistant

Play Half-Life-style VOX announcements (e.g. "Leak detected in sector B") on Cast devices and other media players in Home Assistant. Uses WAV clips from [sourcesounds/hl1](https://github.com/sourcesounds/hl1), concatenated in pure Python (no ffmpeg).

## Installation (HACS)

1. Add this repository as a custom repository in HACS.
2. Install the "Half-Life VOX" integration.
3. Restart Home Assistant.
4. Add configuration to `configuration.yaml` (see below) and restart again.

## Configuration

```yaml
hl_vox:
  # Optional: path to WAV files (default: <config>/hl_vox/sounds)
  # sounds_path: /config/hl_vox_sounds
  # Optional: auto-download VOX from GitHub on first run (default: true)
  # auto_fetch_vox: true
  phrases:
    leak_detected_b:
      - buzwarn
      - attention
      - liquid
      - materials
      - detected
      - in
      - sector
      - b
      - authorized
      - personnel
      - check
      - area
      - immediately
```

On first run, if `sounds_path` is empty, the integration downloads the `sound/vox` folder from [sourcesounds/hl1](https://github.com/sourcesounds/hl1) automatically.

## Usage

- **Media source**: In the Media browser or in automations, use `media_content_id: media-source://hl_vox/<phrase_id>` with the `media_player.play_media` service.
- **Service**: Call `hl_vox.play_phrase` with `phrase_id` and `entity_id` (media player entity).

### Example automation

```yaml
action:
  - service: hl_vox.play_phrase
    data:
      phrase_id: leak_detected
      entity_id: media_player.google_home_mini
```

## Requirements

- Home Assistant (tested on recent versions)
- No ffmpeg or Node; uses only Python stdlib for WAV handling

## License

This integration is not affiliated with Valve or the Half-Life franchise. Sound assets are from the [sourcesounds/hl1](https://github.com/sourcesounds/hl1) repository.
