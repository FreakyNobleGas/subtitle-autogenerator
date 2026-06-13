FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
RUN uv pip install --system faster-whisper pydantic-settings pysubs2 ffmpeg-python

COPY app/ app/

CMD ["python", "-m", "app.main"]
