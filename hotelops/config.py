"""Konfigurasi terpusat HotelOps (env + .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_DOTENV_LOADED = False


@dataclass(frozen=True)
class Settings:
    db_path: Path
    headless: bool
    cities: list[str]
    motherduck_token: str | None


def load_settings() -> Settings:
    """Baca Settings dari environment (memuat .env tepat sekali)."""
    global _DOTENV_LOADED
    if not _DOTENV_LOADED:
        load_dotenv()
        _DOTENV_LOADED = True

    db_path = Path(os.environ.get("HOTELOPS_DB_PATH", "data/hotelops.duckdb"))
    headless = os.environ.get("HOTELOPS_HEADLESS", "1") != "0"
    raw_cities = os.environ.get("HOTELOPS_CITIES", "Bali,Jakarta,Yogyakarta")
    cities = [c.strip() for c in raw_cities.split(",") if c.strip()]
    token = os.environ.get("MOTHERDUCK_TOKEN") or None

    return Settings(
        db_path=db_path,
        headless=headless,
        cities=cities,
        motherduck_token=token,
    )
