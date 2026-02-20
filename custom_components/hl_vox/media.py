"""Pure-Python WAV concatenation (no ffmpeg)."""

import io
import wave
import contextlib
from pathlib import Path


def concat_wavs(inputs: list[Path], output: Path, silence_ms: int = 150) -> None:
    """Concatenate WAV files with optional silence between clips (not after the last)."""
    if not inputs:
        raise ValueError("No input files")
    with contextlib.closing(wave.open(str(inputs[0]), "rb")) as first:
        params = first.getparams()

    silence_frames = int(params.framerate * silence_ms / 1000)
    silence = b"\x00" * silence_frames * params.sampwidth

    frames = []
    for i, wav in enumerate(inputs):
        with wave.open(str(wav), "rb") as w:
            if w.getparams()[:4] != params[:4]:
                raise ValueError("WAV format mismatch")
            frames.append(w.readframes(w.getnframes()))
        if i < len(inputs) - 1:
            frames.append(silence)

    with wave.open(str(output), "wb") as out:
        out.setparams(params)
        for f in frames:
            out.writeframes(f)


def concat_wavs_to_bytes(
    input_paths: list[Path], silence_ms: int = 150
) -> bytes:
    """Concatenate WAV files to an in-memory WAV and return bytes (no trailing silence after last clip)."""
    if not input_paths:
        raise ValueError("No input files")
    with contextlib.closing(wave.open(str(input_paths[0]), "rb")) as first:
        params = first.getparams()

    silence_frames = int(params.framerate * silence_ms / 1000)
    silence = b"\x00" * silence_frames * params.sampwidth

    frames = []
    for i, wav in enumerate(input_paths):
        with wave.open(str(wav), "rb") as w:
            if w.getparams()[:4] != params[:4]:
                raise ValueError("WAV format mismatch")
            frames.append(w.readframes(w.getnframes()))
        if i < len(input_paths) - 1:
            frames.append(silence)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setparams(params)
        for f in frames:
            out.writeframes(f)
    buf.seek(0)
    return buf.getvalue()
