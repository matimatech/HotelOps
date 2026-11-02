"""Fungsi parsing murni (tanpa I/O) untuk nilai yang di-scrape."""

from __future__ import annotations

import re

_STOPWORDS = {"hotel", "resort", "spa", "the", "by", "at", "villa", "homestay", "guesthouse", "and"}


def parse_price(text: str | None) -> int | None:
    """Parse harga Indonesia menjadi int IDR.

    Menangani "Rp392.015", "392,015", "Rp 1.250.000", "IDR 1.250.000,00".
    """
    if not text:
        return None
    cleaned = re.sub(r"[^0-9.,]", "", str(text))
    if not any(c.isdigit() for c in cleaned):
        return None

    if "." in cleaned and "," in cleaned:
        # titik ribuan, koma desimal
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        after_last = cleaned.rsplit(",", 1)[1]
        if len(after_last) == 3:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
    elif "." in cleaned:
        cleaned = cleaned.replace(".", "")

    try:
        value = int(float(cleaned))
    except (TypeError, ValueError):
        return None
    if value < 1000:
        return None
    return value


def parse_stars(text: str | None) -> float | None:
    """"4 dari 5" / "4" / "4,5" -> float."""
    if not text:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", str(text))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None


def parse_score(text: str | None) -> float | None:
    """"8,6" / "8.6 dari 10" -> float."""
    return parse_stars(text)


def parse_count(text: str | None) -> int | None:
    """"227 ulasan" -> 227."""
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", str(text))
    if not digits:
        return None
    return int(digits)


def normalize_name(name: str) -> str:
    """Normalisasi nama hotel untuk pencocokan lintas platform."""
    if not name:
        return ""
    text = str(name).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    tokens = [t for t in text.split() if t and t not in _STOPWORDS]
    return " ".join(tokens)
