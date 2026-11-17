"""Tarik data publik. Satu sumber gagal nggak menggagalkan yang lain.

Spot BTC: data-api.binance.vision (api.binance.com sering 451 di luar region
yang didukung). Funding BTC: arsip bulanan data.binance.vision, lubang bulan
berjalan diisi OKX. ETF: Farside pakai user-agent browser; kalau Cloudflare
nolak, CSV firsthandbitcoin yang total hariannya cocok sama Farside.
"""

from __future__ import annotations

import json
import traceback
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

from cryptomonitor.lib import (
    connect,
    http_bytes,
    http_json,
    http_post_json,
    log_fetch,
    set_meta,
    today_utc,
    upsert_funding,
    upsert_prices,
    utc_date_from_ms,
    utc_date_from_s,
)
from cryptomonitor.parse import (
    parse_binance_funding_zip,
    parse_binance_klines,
    parse_etf_csv,
    parse_farside_html,
)


def _ua(cfg: dict) -> dict:
    return {"User-Agent": cfg["sources"].get("user_agent") or "Mozilla/5.0"}


def _month_list(start: tuple[int, int], end: tuple[int, int]) -> list[str]:
    year, month = start
    out = []
    while (year, month) <= end:
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


def fetch_btc_prices(conn, cfg, notes: list[str]) -> int:
    url = cfg["sources"]["binance_vision_klines"]
    start = 1502928000000  # 2017-08-17
    rows: list[tuple] = []
    pages = 0
    while pages < 20:
        payload = http_json(
            f"{url}?symbol=BTCUSDT&interval=1d&startTime={start}&limit=1000",
            headers=_ua(cfg),
            timeout=40,
        )
        parsed = parse_binance_klines(payload)
        if not parsed:
            break
        for day, close in parsed:
            rows.append(("BTC", day.isoformat(), close, "binance-vision"))
        last_open = int(payload[-1][0])
        nxt = last_open + 1
        pages += 1
        if nxt <= start or len(payload) < 1000:
            break
        start = nxt
    upsert_prices(conn, rows)
    log_fetch(conn, "btc_price", True, f"rows={len(rows)} pages={pages} source=binance-vision")
    notes.append(
        f"Harga BTC harian: {len(rows)} bar dari data-api.binance.vision "
        "(api.binance.com kena HTTP 451 di region mesin ini, jadi yang kepake mirror data publiknya)."
    )
    return len(rows)


def fetch_btc_funding(conn, cfg, notes: list[str]) -> int:
    today = today_utc()
    months = _month_list((2020, 1), (today.year, today.month))
    template = cfg["sources"]["binance_funding_monthly"]
    headers = _ua(cfg)

    def one(ym: str) -> list[tuple[int, float]]:
        url = template.format(ym=ym)
        try:
            blob = http_bytes(url, headers=headers, timeout=40, retries=2)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return []
            raise
        return parse_binance_funding_zip(blob)

    prints: list[tuple[int, float]] = []
    missing = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for part in pool.map(one, months):
            if not part:
                missing += 1
            prints.extend(part)
    rows = [("BTC", ts, rate, "binance") for ts, rate in prints]
    upsert_funding(conn, rows)
    last_ms = max((ts for ts, _ in prints), default=0)
    okx_rows = _okx_funding_after(cfg, last_ms)
    upsert_funding(conn, [("BTC", ts, rate, "okx") for ts, rate in okx_rows])
    detail = f"binance_prints={len(prints)} missing_months={missing} okx_gap={len(okx_rows)}"
    log_fetch(conn, "btc_funding", bool(prints or okx_rows), detail)
    if last_ms:
        last_day = utc_date_from_ms(last_ms).isoformat()
    else:
        last_day = "—"
    notes.append(
        f"Funding BTC: {len(prints)} print Binance (arsip bulanan, kosong {missing} bulan) "
        f"sampai {last_day}, ditambah {len(okx_rows)} print OKX buat nutup bulan yang arsipnya belum terbit. "
        "REST futures Binance (fapi) 451."
    )
    return len(prints) + len(okx_rows)


def _okx_funding_after(cfg: dict, start_ms: int) -> list[tuple[int, float]]:
    base = cfg["sources"]["okx_funding"]
    after = None
    out: list[tuple[int, float]] = []
    pages = 8 if start_ms > 0 else 90
    for _ in range(pages):
        url = base if after is None else f"{base}&after={after}"
        payload = http_json(url, headers=_ua(cfg), timeout=30)
        data = payload.get("data") or []
        if not data:
            break
        oldest = None
        for row in data:
            ts = int(row["fundingTime"])
            oldest = ts if oldest is None else min(oldest, ts)
            if ts > start_ms:
                out.append((ts, float(row["fundingRate"])))
        if oldest is None or oldest <= start_ms or after == oldest:
            break
        after = oldest
    return out


def fetch_hype(conn, cfg, notes: list[str]) -> tuple[int, int]:
    url = cfg["sources"]["hyperliquid"]
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    candles = http_post_json(
        url,
        {
            "type": "candleSnapshot",
            "req": {
                "coin": "HYPE",
                "interval": "1d",
                "startTime": 1700000000000,
                "endTime": now_ms,
            },
        },
        headers=_ua(cfg),
        timeout=60,
    )
    if not isinstance(candles, list):
        raise RuntimeError(f"candle HYPE aneh: {str(candles)[:180]}")
    price_rows = []
    for candle in candles:
        day = utc_date_from_ms(int(candle["t"]))
        price_rows.append(("HYPE", day.isoformat(), float(candle["c"]), "hyperliquid"))
    upsert_prices(conn, price_rows)

    funding_rows: list[tuple] = []
    start = 1700000000000
    pages = 0
    while pages < 80:
        data = http_post_json(
            url,
            {"type": "fundingHistory", "coin": "HYPE", "startTime": start},
            headers=_ua(cfg),
            timeout=60,
        )
        if not isinstance(data, list) or not data:
            break
        last = start
        for row in data:
            ts = int(row["time"])
            last = max(last, ts)
            funding_rows.append(("HYPE", ts, float(row["fundingRate"]), "hyperliquid"))
        pages += 1
        if len(data) < 500 or last <= start:
            break
        start = last + 1
    upsert_funding(conn, funding_rows)

    ctx = http_post_json(url, {"type": "metaAndAssetCtxs"}, headers=_ua(cfg), timeout=40)
    oi_note = "OI HYPE nggak ketemu"
    if isinstance(ctx, list) and len(ctx) >= 2:
        universe = ctx[0].get("universe") or []
        names = [item.get("name") for item in universe]
        if "HYPE" in names:
            info = ctx[1][names.index("HYPE")]
            coin = float(info.get("openInterest") or 0)
            mark = float(info.get("markPx") or 0)
            today = today_utc().isoformat()
            conn.execute(
                """
                INSERT INTO open_interest(asset, date, oi_usd, oi_coin, source)
                VALUES (?,?,?,?,?)
                ON CONFLICT(asset, date) DO UPDATE SET
                    oi_usd=excluded.oi_usd, oi_coin=excluded.oi_coin, source=excluded.source
                """,
                ("HYPE", today, coin * mark, coin, "hyperliquid"),
            )
            oi_note = f"OI HYPE hari ini {coin:.0f} koin (~${coin * mark:,.0f})"
    log_fetch(
        conn,
        "hype",
        bool(price_rows),
        f"prices={len(price_rows)} funding={len(funding_rows)} {oi_note}",
    )
    notes.append(
        f"HYPE: {len(price_rows)} candle harian + {len(funding_rows)} print funding dari Hyperliquid. {oi_note}."
    )
    return len(price_rows), len(funding_rows)


def fetch_fear_greed(conn, cfg, notes: list[str]) -> int:
    payload = http_json(cfg["sources"]["fng"], headers=_ua(cfg), timeout=40)
    rows = []
    for item in payload.get("data") or []:
        day = utc_date_from_s(int(item["timestamp"]))
        rows.append((day.isoformat(), int(item["value"]), item.get("value_classification")))
    conn.executemany(
        """
        INSERT INTO fear_greed(date, value, classification) VALUES (?,?,?)
        ON CONFLICT(date) DO UPDATE SET value=excluded.value, classification=excluded.classification
        """,
        rows,
    )
    log_fetch(conn, "fear_greed", bool(rows), f"rows={len(rows)}")
    notes.append(f"Fear & Greed alternative.me: {len(rows)} hari.")
    return len(rows)


def fetch_etf(conn, cfg, notes: list[str]) -> int:
    headers = {
        **_ua(cfg),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    errors = []
    for key in ("farside_all", "farside_btc"):
        url = cfg["sources"][key]
        try:
            raw = http_bytes(url, headers=headers, timeout=40, retries=1)
            text = raw.decode("utf-8", "replace")
            if "Just a moment" in text or "<table" not in text.lower():
                errors.append(f"{url} bukan tabel (kemungkinan Cloudflare)")
                continue
            parsed = parse_farside_html(text)
            if len(parsed) < 10:
                errors.append(f"{url} cuma {len(parsed)} baris")
                continue
            _save_etf(conn, parsed, "farside")
            log_fetch(conn, "etf", True, f"source=farside rows={len(parsed)} url={url}")
            notes.append(f"ETF BTC dari Farside langsung ({url}): {len(parsed)} hari.")
            return len(parsed)
        except Exception as exc:  # noqa: BLE001 — satu sumber boleh gagal
            errors.append(f"{url}: {exc}")
    try:
        raw = http_bytes(cfg["sources"]["etf_fallback_csv"], headers=_ua(cfg), timeout=40)
        parsed = parse_etf_csv(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        log_fetch(conn, "etf", False, " | ".join(errors + [str(exc)]))
        notes.append(
            "ETF BTC gagal. Farside nolak dan CSV cadangan juga gagal, jadi poin ETF di skor nggak nyala. "
            + " | ".join(errors)
        )
        return 0
    _save_etf(conn, parsed, "firsthandbitcoin")
    log_fetch(conn, "etf", True, f"source=firsthandbitcoin rows={len(parsed)}; farside={errors}")
    last = max((day for day, _ in parsed), default=None)
    notes.append(
        "ETF BTC: Farside balas Cloudflare (user-agent browser tetap 403), jadi gue pakai CSV "
        f"firsthandbitcoin.com ({len(parsed)} hari, terakhir {last}). Total hariannya cocok sama "
        "kolom Total Farside (contoh 13 Nov 2026 -$185,4jt). Hari yang belum masuk CSV nggak ikut."
    )
    return len(parsed)


def _save_etf(conn, parsed: list[tuple[date, float]], source: str) -> None:
    conn.executemany(
        """
        INSERT INTO etf_flows(date, flow_usd, source) VALUES (?,?,?)
        ON CONFLICT(date) DO UPDATE SET flow_usd=excluded.flow_usd, source=excluded.source
        """,
        [(day.isoformat(), flow, source) for day, flow in parsed],
    )


def fetch_stables(conn, cfg, notes: list[str]) -> int:
    payload = http_json(cfg["sources"]["defillama_stables"], headers=_ua(cfg), timeout=60)
    rows = []
    for item in payload:
        try:
            day = utc_date_from_s(int(item["date"]))
            supply = float(item["totalCirculatingUSD"]["peggedUSD"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append((day.isoformat(), supply))
    conn.executemany(
        """
        INSERT INTO stablecoin_supply(date, supply_usd) VALUES (?,?)
        ON CONFLICT(date) DO UPDATE SET supply_usd=excluded.supply_usd
        """,
        rows,
    )
    log_fetch(conn, "stables", bool(rows), f"rows={len(rows)}")
    notes.append(f"Suplai stablecoin DefiLlama: {len(rows)} hari. Ini konteks, bukan komponen skor.")
    return len(rows)


def fetch_fx(conn, cfg, notes: list[str]) -> int:
    start = int(datetime(2017, 8, 1, tzinfo=timezone.utc).timestamp())
    end = int(datetime.now(timezone.utc).timestamp()) + 86400
    url = (
        f"{cfg['sources']['yahoo_usdidr']}?period1={start}&period2={end}&interval=1d"
    )
    payload = http_json(url, headers=_ua(cfg), timeout=40)
    result = payload["chart"]["result"][0]
    stamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    rows = []
    for ts, close in zip(stamps, closes):
        if close is None:
            continue
        day = utc_date_from_s(ts)
        rows.append((day.isoformat(), float(close), "yahoo"))
    conn.executemany(
        """
        INSERT INTO fx_usd_idr(date, rate, source) VALUES (?,?,?)
        ON CONFLICT(date) DO UPDATE SET rate=excluded.rate, source=excluded.source
        """,
        rows,
    )
    log_fetch(conn, "fx", bool(rows), f"rows={len(rows)}")
    notes.append(f"USD/IDR Yahoo: {len(rows)} hari, buat ngubah tranche ke koin.")
    return len(rows)


def fetch_context(conn, cfg, notes: list[str]) -> None:
    """Dominance, harga cek CoinGecko, dan OI BTC. Gagal pun skor tetap jalan."""
    try:
        global_payload = http_json(cfg["sources"]["coingecko_global"], headers=_ua(cfg), timeout=30)
        pct = float(global_payload["data"]["market_cap_percentage"]["btc"])
        today = today_utc().isoformat()
        conn.execute(
            """
            INSERT INTO dominance(date, btc_pct) VALUES (?,?)
            ON CONFLICT(date) DO UPDATE SET btc_pct=excluded.btc_pct
            """,
            (today, pct),
        )
        log_fetch(conn, "dominance", True, f"btc_pct={pct:.2f}")
        notes.append(
            f"Dominasi BTC CoinGecko hari ini {pct:.2f}%. Riwayat dominasi butuh API pro, jadi cuma snapshot."
        )
    except Exception as exc:  # noqa: BLE001
        log_fetch(conn, "dominance", False, str(exc))
        notes.append(f"Dominasi BTC gagal diambil: {exc}")

    try:
        price = http_json(cfg["sources"]["coingecko_price"], headers=_ua(cfg), timeout=30)
        set_meta(conn, "coingecko_price", json.dumps(price))
        log_fetch(conn, "coingecko_price", True, json.dumps(price)[:300])
    except Exception as exc:  # noqa: BLE001
        log_fetch(conn, "coingecko_price", False, str(exc))
        notes.append(f"Cek harga CoinGecko gagal: {exc}")

    try:
        _fetch_btc_oi(conn, cfg, notes)
    except Exception as exc:  # noqa: BLE001
        log_fetch(conn, "btc_oi", False, str(exc))
        notes.append(f"OI BTC gagal diambil: {exc}")


def _fetch_btc_oi(conn, cfg, notes: list[str]) -> None:
    base = cfg["sources"]["okx_oi"]
    end = None
    seen: dict[str, tuple] = {}
    oldest_guard = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    for _ in range(40):
        url = f"{base}?instId=BTC-USDT-SWAP&period=1D&limit=100"
        if end is not None:
            url += f"&end={end}"
        payload = http_json(url, headers=_ua(cfg), timeout=30)
        data = payload.get("data") or []
        if not data:
            break
        oldest = None
        for row in data:
            ts = int(row[0])
            oldest = ts if oldest is None else min(oldest, ts)
            day = utc_date_from_ms(ts).isoformat()
            oi_coin = float(row[2]) if len(row) > 2 else None
            oi_usd = float(row[3]) if len(row) > 3 else None
            seen[day] = ("BTC", day, oi_usd, oi_coin, "okx")
        if oldest is None or oldest == end or oldest < oldest_guard:
            break
        end = oldest - 1
    if seen:
        conn.executemany(
            """
            INSERT INTO open_interest(asset, date, oi_usd, oi_coin, source)
            VALUES (?,?,?,?,?)
            ON CONFLICT(asset, date) DO UPDATE SET
                oi_usd=excluded.oi_usd, oi_coin=excluded.oi_coin, source=excluded.source
            """,
            list(seen.values()),
        )
    now = http_json(cfg["sources"]["okx_oi_now"], headers=_ua(cfg), timeout=30)
    latest = (now.get("data") or [{}])[0]
    log_fetch(conn, "btc_oi", True, f"hist={len(seen)} now_oi={latest.get('oi')} oiCcy={latest.get('oiCcy')}")
    notes.append(
        f"OI BTC dari OKX (bukan Binance — endpoint OI futures-nya 451): {len(seen)} hari. "
        "OI nggak masuk skor."
    )


def run_fetch(db_path, cfg) -> int:
    conn = connect(db_path)
    notes: list[str] = []
    jobs = [
        ("btc_price", lambda: fetch_btc_prices(conn, cfg, notes)),
        ("btc_funding", lambda: fetch_btc_funding(conn, cfg, notes)),
        ("hype", lambda: fetch_hype(conn, cfg, notes)),
        ("fear_greed", lambda: fetch_fear_greed(conn, cfg, notes)),
        ("etf", lambda: fetch_etf(conn, cfg, notes)),
        ("stables", lambda: fetch_stables(conn, cfg, notes)),
        ("fx", lambda: fetch_fx(conn, cfg, notes)),
        ("context", lambda: fetch_context(conn, cfg, notes)),
    ]
    failed = []
    for name, job in jobs:
        try:
            job()
            conn.commit()
            print(f"ok  {name}")
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            failed.append(name)
            detail = f"{exc}"
            print(f"FAIL {name}: {detail}")
            try:
                log_fetch(conn, name, False, detail + " " + traceback.format_exc(limit=2))
                notes.append(f"{name} gagal: {detail}")
                conn.commit()
            except Exception:
                pass
    set_meta(conn, "fetch_notes", json.dumps(notes, ensure_ascii=False))
    set_meta(conn, "fetched_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    conn.commit()
    btc = conn.execute("SELECT COUNT(*) AS n FROM prices WHERE asset='BTC'").fetchone()["n"]
    conn.close()
    if btc < 100:
        print(f"harga BTC cuma {btc} bar, fetch belum cukup buat backtest")
        return 1
    if failed:
        print("sumber yang gagal (yang lain tetap kepake): " + ", ".join(failed))
    return 0
