"""Kontrak tunggal untuk semua scraper platform.

Semua scraper mengembalikan list[dict] dengan kunci BRONZE_COLUMNS plus
kolom metadata yang ditambahkan CLI (scraped_at, run_id, source_file).
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Iterator

from playwright.sync_api import Page, sync_playwright
from playwright_stealth import Stealth

from ..config import load_settings
from .stealth import apply_stealth_mode, random_delay, simulate_human_mouse  # noqa: F401

logger = logging.getLogger(__name__)

BRONZE_COLUMNS: tuple[str, ...] = (
    "platform",
    "platform_hotel_id",
    "hotel_name",
    "final_price",
    "list_price",
    "hotel_stars",
    "guest_score",
    "review_count",
    "subdistrict",
    "regency",
    "booking_url",
    "image_url",
    "city_search",
    "check_in_date",
    "check_out_date",
)

REQUIRED_KEYS = ("platform", "platform_hotel_id", "hotel_name", "final_price")

_FLOAT_KEYS = ("hotel_stars", "guest_score")
_INT_KEYS = ("review_count",)


@dataclass(frozen=True)
class SearchQuery:
    city: str
    check_in: date
    check_out: date


class ScrapeError(RuntimeError):
    """Kegagalan scraping yang tidak bisa dipulihkan."""


class SelectorError(ScrapeError):
    """Selector tidak menemukan elemen yang diharapkan."""


@contextmanager
def browser_page(headless: bool) -> Iterator[Page]:
    """Buka Chromium dengan context stabil + stealth, tutup semuanya di finally."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        apply_stealth_mode(context)
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        try:
            yield page
        finally:
            for closer in (context.close, browser.close):
                try:
                    closer()
                except Exception:  # pragma: no cover - best effort cleanup
                    pass


def empty_row(platform: str, q: SearchQuery) -> dict:
    row = {col: None for col in BRONZE_COLUMNS}
    row["platform"] = platform
    row["city_search"] = q.city
    row["check_in_date"] = q.check_in
    row["check_out_date"] = q.check_out
    return row


def _clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text or text.upper() in {"N/A", "NA", "NONE", "NULL", "-"}:
            return None
        return text
    return value


def validate_row(row: dict) -> dict:
    """Buang nilai 'N/A'/None, cast tipe, raise ValueError bila kunci wajib kosong."""
    cleaned = {col: _clean(row.get(col)) for col in BRONZE_COLUMNS}

    for key in REQUIRED_KEYS:
        if cleaned.get(key) is None:
            raise ValueError(f"kolom wajib kosong: {key}")

    for key in _FLOAT_KEYS:
        if cleaned.get(key) is not None:
            cleaned[key] = float(cleaned[key])
    for key in _INT_KEYS:
        if cleaned.get(key) is not None:
            cleaned[key] = int(cleaned[key])

    cleaned["final_price"] = int(cleaned["final_price"])
    if cleaned.get("list_price") is not None:
        cleaned["list_price"] = int(cleaned["list_price"])
        if cleaned["list_price"] <= cleaned["final_price"]:
            cleaned["list_price"] = None
    if cleaned["final_price"] <= 0:
        raise ValueError("final_price <= 0")

    cleaned["platform_hotel_id"] = str(cleaned["platform_hotel_id"])
    return cleaned


def debug_dump(page: Page, platform: str, tag: str) -> Path:
    """Simpan screenshot + HTML ke data/debug/ untuk diagnosis selector."""
    out_dir = Path("data") / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    base = out_dir / f"{platform}-{tag}-{ts}"
    png_path = base.with_suffix(".png")
    html_path = base.with_suffix(".html")
    try:
        page.screenshot(path=str(png_path), full_page=False)
    except Exception as exc:  # pragma: no cover - page bisa sudah tertutup
        logger.warning("gagal screenshot %s: %s", png_path, exc)
    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception as exc:  # pragma: no cover
        logger.warning("gagal dump html %s: %s", html_path, exc)
    logger.warning("debug dump: %s / %s", png_path, html_path)
    return html_path


def run_scraper(
    platform: str,
    scrape_fn: Callable[..., list[dict]],
    q: SearchQuery,
    *,
    headless: bool,
    max_pages: int | None,
) -> list[dict]:
    """Jalankan scrape_fn lewat kontrak: validasi, hitung skip, raise bila kosong."""
    raw_rows = scrape_fn(q, headless=headless, max_pages=max_pages)

    rows: list[dict] = []
    skipped: dict[str, int] = {}
    for raw in raw_rows:
        try:
            rows.append(validate_row(raw))
        except (ValueError, TypeError) as exc:
            reason = str(exc) or "invalid"
            skipped[reason] = skipped.get(reason, 0) + 1

    print(f"[{platform}] rows_ok={len(rows)} rows_skipped={sum(skipped.values())}")
    for reason, count in sorted(skipped.items(), key=lambda kv: -kv[1]):
        print(f"  skip x{count}: {reason}")

    if not rows:
        raise ScrapeError(
            f"{platform}: 0 baris valid untuk {q.city} ({q.check_in}..{q.check_out}); "
            f"skipped={sum(skipped.values())}"
        )
    return rows


def run_with_settings(
    platform: str,
    scrape_fn: Callable[..., list[dict]],
    q: SearchQuery,
    *,
    headless: bool | None = None,
    max_pages: int | None = None,
) -> list[dict]:
    """Helper CLI: pakai headless dari Settings bila tidak diberikan eksplisit."""
    if headless is None:
        headless = load_settings().headless
    return run_scraper(platform, scrape_fn, q, headless=headless, max_pages=max_pages)


def describe_rows(rows: list[dict]) -> str:
    """Ringkasan singkat untuk log CLI."""
    if not rows:
        return "0 baris"
    prices = [r["final_price"] for r in rows if r.get("final_price")]
    lo, hi = (min(prices), max(prices)) if prices else (0, 0)
    with_list = sum(1 for r in rows if r.get("list_price"))
    return f"{len(rows)} baris, harga {lo}-{hi} IDR, {with_list} punya list_price"
