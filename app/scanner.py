import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _has_any_srt(video_path: Path) -> bool:
    """True if any .srt file with the same stem exists (regardless of label/language suffix)."""
    stem = video_path.stem
    return any(
        f.suffix.lower() == ".srt" and f.stem.startswith(stem)
        for f in video_path.parent.iterdir()
        if f.is_file()
    )


def find_videos_missing_subtitles(media_dir: Path) -> list[Path]:
    missing: list[Path] = []
    for path in sorted(media_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in settings.video_ext_set:
            continue
        if path.with_suffix(".subtitle-skip").exists():
            logger.debug("Skipping (marked as failed): %s", path.name)
            continue
        if _has_any_srt(path):
            logger.debug("Skipping (subtitle exists): %s", path.name)
            continue
        missing.append(path)
    logger.info("Found %d video(s) missing subtitles in %s", len(missing), media_dir)
    return missing
