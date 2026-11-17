"""Rangkai DB → skor hari ini + backtest + laporan."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cryptomonitor.backtest import _fx_rate, analyze_asset, coverage_from_maps
from cryptomonitor.lib import (
    connect,
    get_meta,
    latest_fetch_notes,
    load_etf,
    load_fear_greed,
    load_funding_daily,
    load_fx,
    load_prices,
    today_utc,
)
from cryptomonitor.report import console_summary, render
from cryptomonitor.signals import build_features, score_v1, score_v2, tranche_idr


def build_bundle(conn, cfg: dict) -> dict:
    today = today_utc()
    fx = load_fx(conn)
    fear = load_fear_greed(conn)
    etf = load_etf(conn)
    fx_stamps = sorted(fx)
    assets = {}
    live = {}
    for asset in ("BTC", "HYPE"):
        prices = load_prices(conn, asset)
        if not prices:
            continue
        funding = load_funding_daily(conn, asset)
        flows = etf if asset == "BTC" else {}
        closed = [(day, close) for day, close in prices if day < today]
        series = closed if len(closed) >= 30 else prices
        features = build_features(asset, series, fear, funding, flows, cfg)
        if not features:
            continue
        block = analyze_asset(features, fx, cfg)
        block["coverage"] = coverage_from_maps(features, funding, flows, fear)
        block["coverage"]["price_first"] = prices[0][0].isoformat()
        block["coverage"]["price_last"] = prices[-1][0].isoformat()
        block["coverage"]["price_n"] = len(prices)
        assets[asset] = block

        live_features = build_features(asset, prices, fear, funding, flows, cfg)
        zone = [item for item in live_features if score_v2(item, cfg).multiplier >= 1.5]
        block["boost_n"] = len(zone)
        block["boost_first"] = zone[0].day.isoformat() if zone else None
        block["boost_last"] = zone[-1].day.isoformat() if zone else None
        feature = live_features[-1]
        rate = _fx_rate(fx, fx_stamps, feature.day)
        label_row = conn.execute(
            "SELECT classification FROM fear_greed WHERE date=?",
            (feature.day.isoformat(),),
        ).fetchone()
        oi = conn.execute(
            "SELECT date, oi_usd FROM open_interest WHERE asset=? ORDER BY date DESC LIMIT 1",
            (asset,),
        ).fetchone()
        live[asset] = {
            "feature": feature,
            "v1": score_v1(feature, cfg),
            "v2": score_v2(feature, cfg),
            "tranche": tranche_idr(feature, cfg),
            "partial": feature.day >= today,
            "price_idr": None if rate is None else feature.close * rate,
            "fg_label": None if label_row is None else label_row["classification"],
            "oi_usd": None if oi is None else oi["oi_usd"],
            "oi_day": None if oi is None else oi["date"],
        }

    dom = conn.execute("SELECT date, btc_pct FROM dominance ORDER BY date DESC LIMIT 1").fetchone()
    stables = conn.execute(
        "SELECT date, supply_usd FROM stablecoin_supply ORDER BY date DESC LIMIT 1"
    ).fetchone()
    fx_last = conn.execute("SELECT date, rate FROM fx_usd_idr ORDER BY date DESC LIMIT 1").fetchone()
    context = {
        "dominance": None if dom is None else dom["btc_pct"],
        "dominance_day": None if dom is None else dom["date"],
        "stables": None if stables is None else stables["supply_usd"],
        "stables_day": None if stables is None else stables["date"],
        "fx": None if fx_last is None else fx_last["rate"],
        "fx_day": None if fx_last is None else fx_last["date"],
        "cg_note": _cg_note(conn, live),
        "fetched_at": get_meta(conn, "fetched_at"),
    }
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "cfg": cfg,
        "live": live,
        "assets": assets,
        "context": context,
        "notes": latest_fetch_notes(conn),
    }


def _cg_note(conn, live: dict) -> str | None:
    raw = get_meta(conn, "coingecko_price")
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    bits = []
    mapping = {"BTC": "bitcoin", "HYPE": "hyperliquid"}
    for asset, key in mapping.items():
        snap = live.get(asset)
        quote = (payload.get(key) or {}).get("usd")
        if snap is None or quote is None:
            continue
        bits.append(f"{asset} CoinGecko ${quote} vs DB {snap['feature'].close:.2f}")
    if not bits:
        return None
    return "Cek silang CoinGecko (bukan sumber backtest): " + "; ".join(bits) + "."


def publish(db_path: Path, cfg: dict, report_path: Path) -> int:
    if not Path(db_path).exists():
        print("DB belum ada. Jalankan dulu: python -m cryptomonitor fetch")
        return 1
    conn = connect(db_path)
    try:
        bundle = build_bundle(conn, cfg)
    finally:
        conn.close()
    if "BTC" not in bundle["assets"]:
        print("Harga BTC kosong, backtest nggak jalan.")
        return 1
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render(bundle), encoding="utf-8")
    print(console_summary(bundle))
    print(f"laporan ditulis ke {report_path}")
    return 0
