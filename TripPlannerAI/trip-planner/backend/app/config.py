from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


def _split_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    return tuple(items) if items else default


@dataclass(frozen=True)
class Settings:
    app_name: str
    openweather_api_key: str
    opentripmap_api_key: str
    openrouteservice_api_key: str
    openai_api_key: str
    openai_model: str
    request_timeout: int
    public_base_url: str
    frontend_origins: tuple[str, ...]
    use_chroma: bool
    default_currency: str
    generated_dir: Path
    memory_file: Path
    chroma_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    generated_dir = BASE_DIR / "generated"
    data_dir = BASE_DIR / "data"
    chroma_dir = data_dir / "chroma"

    generated_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        app_name=os.getenv("APP_NAME", "AI Multi-Agent Trip Planner"),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
        opentripmap_api_key=os.getenv("OPENTRIPMAP_API_KEY", "").strip(),
        openrouteservice_api_key=os.getenv("OPENROUTESERVICE_API_KEY", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "15")),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        frontend_origins=_split_csv(
            os.getenv("FRONTEND_ORIGINS"),
            ("http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"),
        ),
        use_chroma=os.getenv("USE_CHROMA", "false").strip().lower() == "true",
        default_currency=os.getenv("DEFAULT_CURRENCY", "INR").strip() or "INR",
        generated_dir=generated_dir,
        memory_file=data_dir / "preferences.json",
        chroma_dir=chroma_dir,
    )
