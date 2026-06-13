# subtitle-autogenerator

A Docker service that automatically generates SRT subtitle files for video files using [faster-whisper](https://github.com/SYSTRAN/faster-whisper). It scans a media directory on a configurable interval and creates subtitles for any video that doesn't already have one.

## How it works

1. Scans the media directory recursively for video files
2. Skips any video that already has a `.srt` file with a matching name
3. Extracts audio via ffmpeg and transcribes it with Whisper (CPU, int8)
4. Groups word-level timestamps into readable subtitle lines
5. Writes an SRT file next to the video: `{name}.{language}.{label}.srt`
6. Sleeps for `SCAN_INTERVAL` seconds and repeats

## Quick start

```bash
HOST_MEDIA_DIR=/path/to/your/media docker compose up -d
```

## Configuration

All settings are read from environment variables.

| Variable | Default | Description |
|---|---|---|
| `MEDIA_DIR` | `/media` | Path to the media directory **inside the container** |
| `SCAN_INTERVAL` | `3600` | Seconds between scans |
| `WHISPER_MODEL` | `small` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `LANGUAGE` | _(auto-detect)_ | Force a specific language code (e.g. `en`, `es`, `fr`) |
| `VIDEO_EXTENSIONS` | `.mkv,.mp4,.avi,.mov,.m4v,.wmv` | Comma-separated list of video extensions to process |
| `MAX_WORKERS` | `1` | Number of videos to transcribe in parallel |
| `SUBTITLE_LABEL` | `Media Server Autogen Sub` | Label appended to the SRT filename |
| `MAX_WORDS_PER_LINE` | `7` | Max words per subtitle line |
| `MAX_CHARS_PER_LINE` | `42` | Max characters per subtitle line |
| `MAX_GAP_SECONDS` | `1.5` | Silence gap (seconds) that forces a new subtitle line |
| `DRY_RUN` | `false` | Log what would be transcribed without writing any files |

## Docker Compose

```yaml
services:
  app:
    build: .
    environment:
      MEDIA_DIR: /media
      WHISPER_MODEL: medium
      SCAN_INTERVAL: 1800
    volumes:
      - /path/to/your/media:/media
      - whisper-cache:/root/.cache/huggingface
    restart: unless-stopped

volumes:
  whisper-cache:
```

The `whisper-cache` volume persists the downloaded model weights so they aren't re-downloaded on container restart.

## Multiple drives

If your media is spread across multiple hard drives, mount each one as a subdirectory under `/media`. The scanner recurses into all subdirectories, so every drive will be picked up automatically — no extra configuration needed.

```yaml
volumes:
  - /mnt/drive1:/media/drive1
  - /mnt/drive2:/media/drive2
  - /mnt/drive3:/media/drive3
  - whisper-cache:/root/.cache/huggingface
```

## Dry run

Set `DRY_RUN=true` to scan and log which videos would be transcribed without actually running Whisper or writing any files. Useful for verifying your volume mounts before a full run.

```yaml
environment:
  DRY_RUN: "true"
```

## Model sizes

Larger models are more accurate but use more RAM and take longer to transcribe.

| Model | VRAM | Relative speed |
|---|---|---|
| `tiny` | ~1 GB | Fastest |
| `base` | ~1 GB | Fast |
| `small` | ~2 GB | Good balance |
| `medium` | ~5 GB | More accurate |
| `large-v3` | ~10 GB | Most accurate |

This service runs on CPU (int8) by default, so `small` or `medium` are the recommended starting points.

## Requirements

- Docker and Docker Compose
- ffmpeg (included in the Docker image)
