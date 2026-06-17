import io
import logging
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info("Loading Whisper model '%s' on cpu (int8)", settings.whisper_model)
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
        logger.info("Model loaded")
    return _model


def get_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return float(result.stdout.strip())


def extract_audio(video_path: Path) -> bytes:
    result = subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y",
            "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000",
            "-f", "wav", "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return result.stdout


def transcribe(video_path: Path) -> tuple[list, str]:
    """Return (words, detected_language). words is a flat list of faster-whisper Word objects."""
    duration = get_duration(video_path)
    limit = settings.max_duration_seconds
    if duration > limit:
        raise ValueError(
            f"File duration {duration/3600:.1f}h exceeds limit ({limit/3600:.1f}h), skipping"
        )

    logger.info("Extracting audio from %s", video_path.name)
    audio_bytes = extract_audio(video_path)

    model = get_model()
    lang = settings.language or None
    logger.info("Transcribing %s (language=%s)", video_path.name, lang or "auto-detect")
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language=lang,
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
        condition_on_previous_text=False,
    )

    words = [w for seg in segments for w in (seg.words or [])]
    logger.info(
        "Transcription done: %d words, detected language '%s'",
        len(words), info.language,
    )
    return words, info.language
