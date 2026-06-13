import logging
from pathlib import Path

import pysubs2

from app.config import settings

logger = logging.getLogger(__name__)


def words_to_subs(words: list, max_words: int, max_chars: int, max_gap: float) -> pysubs2.SSAFile:
    subs = pysubs2.SSAFile()
    group: list = []

    def flush() -> None:
        if not group:
            return
        start_ms = int(group[0].start * 1000)
        end_ms = int(group[-1].end * 1000)
        text = " ".join(w.word.strip() for w in group)
        subs.append(pysubs2.SSAEvent(start=start_ms, end=end_ms, text=text))
        group.clear()

    for word in words:
        token = word.word.strip()
        if not token:
            continue
        gap = (word.start - group[-1].end) if group else 0
        projected = sum(len(w.word.strip()) for w in group) + len(group) + len(token)
        if group and (gap > max_gap or len(group) >= max_words or projected > max_chars):
            flush()
        group.append(word)

    flush()
    return subs


def subtitle_path(video_path: Path) -> Path:
    return video_path.with_suffix(".srt")


def write_subtitle(video_path: Path, words: list, language: str) -> Path:
    srt_path = subtitle_path(video_path)
    subs = words_to_subs(words, settings.max_words_per_line, settings.max_chars_per_line, settings.max_gap_seconds)
    subs.save(str(srt_path))
    logger.info("Wrote %d subtitle lines: %s", len(subs), srt_path.name)
    return srt_path
