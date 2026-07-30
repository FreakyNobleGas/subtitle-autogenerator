import logging
from pathlib import Path

from app.config import settings
from app.subtitle import subtitle_path

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
        skip_marker = path.with_suffix(".subtitle-skip")
        if skip_marker.exists() and skip_marker.stat().st_mtime >= path.stat().st_mtime:
            # A marker older than the video means the video was replaced — retry it.
            logger.debug("Skipping (marked as failed): %s", path.name)
            continue

        own_srt = subtitle_path(path)
        if own_srt.exists() and own_srt.stat().st_mtime < path.stat().st_mtime:
            logger.info("Subtitle older than video, will regenerate: %s", path.name)
            missing.append(path)
            continue

        if _has_any_srt(path):
            logger.debug("Skipping (subtitle exists): %s", path.name)
            continue
        missing.append(path)
    logger.info("Found %d video(s) missing subtitles in %s", len(missing), media_dir)
    return missing
