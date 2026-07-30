import json
import logging
import urllib.error
import urllib.request
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(settings.alert_webhook_url)


def send_language_alert(video_path: Path, detected_language: str, desired_language: str) -> None:
    if not settings.alert_webhook_url:
        return

    message = (
        f"No {desired_language} subtitles found for **{video_path.name}** "
        f"— detected audio language: {detected_language}."
    )
    data = json.dumps({"content": message}).encode("utf-8")
    request = urllib.request.Request(
        settings.alert_webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": (
                "subtitle-autogenerator "
                "(https://github.com/freakynoblegas/subtitle-autogenerator, 1.0)"
            ),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.alert_webhook_timeout):
            pass
        logger.info("Sent alert for %s", video_path.name)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        logger.warning("Alert for %s rejected: HTTP %s %s", video_path.name, exc.code, body)
    except Exception:
        logger.warning("Failed to send alert for %s", video_path.name, exc_info=True)
