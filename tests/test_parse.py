"""Parser Farside / CSV / funding. Nggak ada jaringan."""

from datetime import date, datetime, timezone
from pathlib import Path

from cryptomonitor.parse import (
    parse_binance_funding_csv,
    parse_binance_klines,
    parse_etf_csv,
    parse_farside_html,
)


def test_farside_html_total_column_is_millions():
    html = (Path(__file__).parent / "fixtures" / "farside_snippet.html").read_text(encoding="utf-8")
    rows = dict(parse_farside_html(html))
    assert rows[date(2024, 1, 11)] == 655_300_000
    assert rows[date(2024, 1, 12)] == -52_700_000
    assert rows[date(2026, 11, 16)] == -68_600_000
    assert date(2024, 1, 1) not in rows
    assert len(rows) == 3


def test_etf_csv_is_already_usd():
    text = "day,etfFlow\n2024-01-11,655300000\n2024-01-16,-52700000\n"
    rows = dict(parse_etf_csv(text))
    assert rows[date(2024, 1, 11)] == 655_300_000
    assert rows[date(2024, 1, 16)] == -52_700_000


def test_binance_funding_csv_skips_header():
    text = "calc_time,funding_interval_hours,last_funding_rate\n1704067200000,8,0.00037409\n1704096000000,8,-0.0001\n"
    rows = parse_binance_funding_csv(text)
    assert rows == [(1704067200000, 0.00037409), (1704096000000, -0.0001)]


def test_binance_kline_date_is_utc():
    # 2024-01-01 00:00 UTC
    payload = [[1704067200000, "1", "2", "0.5", "42000.5", "1", 1704153599999]]
    assert parse_binance_klines(payload) == [(date(2024, 1, 1), 42000.5)]
    assert datetime.fromtimestamp(1704067200000 / 1000, timezone.utc).date() == date(2024, 1, 1)
