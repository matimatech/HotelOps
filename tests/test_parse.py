import pytest

from hotelops.parse import (
    normalize_name,
    parse_count,
    parse_price,
    parse_score,
    parse_stars,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Rp392.015", 392015),
        ("392,015", 392015),
        ("Rp 1.250.000", 1250000),
        ("IDR 1.250.000,00", 1250000),
        ("392015", 392015),
        ("N/A", None),
        ("", None),
        (None, None),
        ("Rp 0", None),
        ("Rp 1.250.000 /malam", 1250000),
        ("Habis", None),
    ],
)
def test_parse_price(text, expected):
    assert parse_price(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("4 dari 5", 4.0),
        ("4", 4.0),
        ("4,5", 4.5),
        ("N/A", None),
        ("", None),
    ],
)
def test_parse_stars(text, expected):
    assert parse_stars(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("8,6", 8.6),
        ("8.6 dari 10", 8.6),
        (None, None),
    ],
)
def test_parse_score(text, expected):
    assert parse_score(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("227 ulasan", 227),
        ("1.234 ulasan", 1234),
        ("", None),
        (None, None),
    ],
)
def test_parse_count(text, expected):
    assert parse_count(text) == expected


@pytest.mark.parametrize(
    "left,right",
    [
        ("Amed Sea Resort & Spa", "Amed Sea Resort and Spa Hotel"),
        ("The Amarta Villa", "Amarta"),
        ("Alila Villas Uluwatu", "ALILA VILLAS ULUWATU"),
    ],
)
def test_normalize_name_matches_variants(left, right):
    assert normalize_name(left) == normalize_name(right)


def test_normalize_name_keeps_location_tokens():
    assert normalize_name("Amed Sea Resort & Spa") == "amed sea"
    assert normalize_name("Amed Sea Resort and Spa Hotel") == "amed sea"
    assert "bali" in normalize_name("Amed Beach Bali")
    assert normalize_name("Kuta Homestay") == "kuta"
