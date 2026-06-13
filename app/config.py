from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    media_dir: str = "/media"
    scan_interval: int = 3600
    whisper_model: str = "small"
    language: str | None = None
    video_extensions: str = ".mkv,.mp4,.avi,.mov,.m4v,.wmv"
    max_workers: int = 1
    max_words_per_line: int = 7
    max_chars_per_line: int = 42
    max_gap_seconds: float = 1.5
    dry_run: bool = False

    @property
    def video_ext_set(self) -> frozenset[str]:
        return frozenset(ext.strip().lower() for ext in self.video_extensions.split(","))


settings = Settings()
