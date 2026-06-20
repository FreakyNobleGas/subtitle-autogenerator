import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import settings
from app.scanner import find_videos_missing_subtitles
from app.subtitle import write_subtitle
from app.transcriber import get_duration, get_model, transcribe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def process(video_path: Path) -> None:
    if settings.dry_run:
        logger.info("[DRY RUN] Would transcribe: %s", video_path)
        return
    duration = get_duration(video_path)
    if duration > settings.max_duration_seconds:
        logger.warning(
            "Skipping %s — duration %.1fh exceeds limit %.1fh",
            video_path.name, duration / 3600, settings.max_duration_seconds / 3600,
        )
        return
    try:
        segments, language = transcribe(video_path)
        write_subtitle(video_path, segments, language)
    except Exception:
        logger.exception("Failed to process %s", video_path)
        skip_marker = video_path.with_suffix(".subtitle-skip")
        skip_marker.touch()
        logger.warning("Marked as skipped — remove %s to retry", skip_marker.name)


def run_scan(media_dir: Path, executor: ThreadPoolExecutor) -> None:
    videos = find_videos_missing_subtitles(media_dir)
    if not videos:
        logger.info("All videos have subtitles — nothing to do")
        return
    futures = [executor.submit(process, v) for v in videos]
    for f in futures:
        f.result()


def main() -> None:
    media_dir = Path(settings.media_dir)
    if not media_dir.exists():
        raise SystemExit(f"MEDIA_DIR does not exist: {media_dir}")

    logger.info(
        "Starting subtitle generator | model=%s scan_interval=%ds media_dir=%s",
        settings.whisper_model,
        settings.scan_interval,
        media_dir,
    )

    if not settings.dry_run:
        # Pre-load model so the first scan doesn't pay the loading penalty mid-transcription
        get_model()

    with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
        while True:
            logger.info("Starting scan")
            run_scan(media_dir, executor)
            logger.info("Scan complete. Sleeping %ds until next scan", settings.scan_interval)
            time.sleep(settings.scan_interval)


if __name__ == "__main__":
    main()
