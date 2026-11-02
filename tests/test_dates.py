from datetime import date, timedelta

from hotelops.dates import (
    checkin_checkout,
    fmt_dmy_dash,
    fmt_iso,
    fmt_long_day,
)


def test_checkin_checkout_defaults_to_h_plus_7():
    check_in, check_out = checkin_checkout()
    assert check_in == date.today() + timedelta(days=7)
    assert check_out == check_in + timedelta(days=1)


def test_checkin_checkout_custom_days():
    check_in, check_out = checkin_checkout(30)
    assert check_in == date.today() + timedelta(days=30)
    assert check_out == date.today() + timedelta(days=31)


def test_fmt_iso():
    assert fmt_iso(date(2026, 4, 1)) == "2026-04-01"


def test_fmt_dmy_dash():
    assert fmt_dmy_dash(date(2026, 4, 1)) == "1-4-2026"
    assert fmt_dmy_dash(date(2026, 12, 25)) == "25-12-2026"


def test_fmt_long_day():
    assert fmt_long_day(date(2026, 4, 1)) == "1 April 2026 Wednesday"
    assert fmt_long_day(date(2026, 8, 17)) == "17 Agustus 2026 Monday"
