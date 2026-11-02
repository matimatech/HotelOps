"""Formatter tanggal per platform. Tidak ada tanggal yang dihitung saat import."""

from __future__ import annotations

import locale
from datetime import date, timedelta

_MONTHS_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}

_DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def checkin_checkout(days_ahead: int = 7) -> tuple[date, date]:
    """(today+7, today+8) — dipanggil runtime, bukan saat import."""
    today = date.today()
    return today + timedelta(days=days_ahead), today + timedelta(days=days_ahead + 1)


def fmt_iso(d: date) -> str:
    """"2026-04-01" — Agoda."""
    return d.strftime("%Y-%m-%d")


def fmt_dmy_dash(d: date) -> str:
    """"1-4-2026" — Traveloka."""
    return f"{d.day}-{d.month}-{d.year}"


def fmt_long_day(d: date) -> str:
    """"1 April 2026 Wednesday" — Tiket (locale-independent, bulan Indonesia)."""
    try:
        locale.setlocale(locale.LC_TIME, "C")
    except locale.Error:
        pass
    return f"{d.day} {_MONTHS_ID[d.month]} {d.year} {_DAYS_EN[d.weekday()]}"
