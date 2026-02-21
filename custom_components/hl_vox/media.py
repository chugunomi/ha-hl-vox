"""Pure-Python WAV concatenation with format normalization (no ffmpeg)."""

import io
import struct
import wave
import contextlib
from pathlib import Path

# Target format for concatenation: 16-bit mono at a common rate
TARGET_NCHANNELS = 1
TARGET_SAMPWIDTH = 2  # 16-bit
TARGET_FRAMERATE = 11025  # Common for Half-Life VOX; we resample others to this


def _read_samples_and_params(path: Path) -> tuple[list[float], int, int, int]:
    """Read WAV to float samples in [-1, 1], and (nchannels, sampwidth, framerate)."""
    with contextlib.closing(wave.open(str(path), "rb")) as w:
        nch, sw, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
        nframes = w.getnframes()
        raw = w.readframes(nframes)
    n = nch * nframes
    if sw == 1:  # 8-bit unsigned
        samples_u8 = struct.unpack(f"<{n}B", raw)
        # Center at 0, scale to [-1, 1]
        samples = [(s / 127.5) - 1.0 for s in samples_u8]
    elif sw == 2:  # 16-bit signed
        samples_s16 = struct.unpack(f"<{n}h", raw)
        samples = [s / 32768.0 for s in samples_s16]
    else:
        raise ValueError(f"Unsupported sample width: {sw}")
    if nch == 2:
        # Stereo -> mono (average)
        samples = [
            (samples[i] + samples[i + 1]) / 2.0
            for i in range(0, len(samples), 2)
        ]
    return samples, nch, sw, rate


def _resample_linear(samples: list[float], orig_rate: int, target_rate: int) -> list[float]:
    """Resample to target rate using linear interpolation."""
    if orig_rate == target_rate:
        return samples
    n = len(samples)
    new_n = int(round(n * target_rate / orig_rate))
    if new_n <= 0:
        return []
    result = []
    for i in range(new_n):
        src_idx = i * (n - 1) / max(new_n - 1, 1)
        lo = int(src_idx)
        hi = min(lo + 1, n - 1)
        frac = src_idx - lo
        result.append(samples[lo] * (1 - frac) + samples[hi] * frac)
    return result


def _samples_to_frames(samples: list[float], sampwidth: int = 2) -> bytes:
    """Convert float samples in [-1, 1] to PCM bytes (16-bit little-endian)."""
    if sampwidth == 2:
        return struct.pack(
            f"<{len(samples)}h",
            *[max(-32768, min(32767, int(s * 32768))) for s in samples],
        )
    raise ValueError(f"Unsupported sampwidth: {sampwidth}")


def _normalize_to_target(
    path: Path,
    target_rate: int = TARGET_FRAMERATE,
    target_nch: int = TARGET_NCHANNELS,
    target_sw: int = TARGET_SAMPWIDTH,
) -> bytes:
    """Read WAV, normalize to target format, return raw PCM frames."""
    samples, nch, sw, rate = _read_samples_and_params(path)
    samples = _resample_linear(samples, rate, target_rate)
    return _samples_to_frames(samples, target_sw)


def concat_wavs(inputs: list[Path], output: Path, silence_ms: int = 150) -> None:
    """Concatenate WAV files with optional silence between clips (not after the last).
    All clips are normalized to 16-bit mono at 11025 Hz before concatenation.
    """
    if not inputs:
        raise ValueError("No input files")
    target_rate = TARGET_FRAMERATE
    target_sw = TARGET_SAMPWIDTH
    silence_frames = int(target_rate * silence_ms / 1000)
    silence = b"\x00" * silence_frames * target_sw

    frames_list = []
    for i, wav in enumerate(inputs):
        frames_list.append(_normalize_to_target(wav, target_rate=target_rate))
        if i < len(inputs) - 1:
            frames_list.append(silence)

    with wave.open(str(output), "wb") as out:
        out.setnchannels(TARGET_NCHANNELS)
        out.setsampwidth(target_sw)
        out.setframerate(target_rate)
        for f in frames_list:
            out.writeframes(f)


def concat_wavs_to_bytes(
    input_paths: list[Path], silence_ms: int = 150
) -> bytes:
    """Concatenate WAV files to an in-memory WAV (normalized to 16-bit mono 11025 Hz)."""
    if not input_paths:
        raise ValueError("No input files")
    target_rate = TARGET_FRAMERATE
    target_sw = TARGET_SAMPWIDTH
    silence_frames = int(target_rate * silence_ms / 1000)
    silence = b"\x00" * silence_frames * target_sw

    frames_list = []
    for i, wav in enumerate(input_paths):
        frames_list.append(_normalize_to_target(wav, target_rate=target_rate))
        if i < len(input_paths) - 1:
            frames_list.append(silence)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(TARGET_NCHANNELS)
        out.setsampwidth(target_sw)
        out.setframerate(target_rate)
        for f in frames_list:
            out.writeframes(f)
    buf.seek(0)
    return buf.getvalue()
