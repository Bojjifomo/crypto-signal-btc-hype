"""Backtest lapisan siklus: event study sinyal jual/value + simulasi tangga jual.

Event study-nya sama kayak backtest v2: hari pertama sinyal nyala, lalu diam
14 hari. Buat sinyal JUAL, yang bagus itu return ke depan yang LEBIH RENDAH
dari baseline. Simulasinya dalam USD (kurs IDR baru ada 2017, harga dari 2010).
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta

from cryptomonitor.backtest import _forward_cached, cooldown_events, make_grid, summarize
from cryptomonitor.cycle import HALVINGS, CyclePoint, blowoff, heat_score, value_score

# Siklus halving. Tanggal beli/jual yang nentuin masuk siklus mana.
EPOCHS = [
    ("≤2016", date(2010, 1, 1), date(2016, 7, 8)),
    ("2016–20", date(2016, 7, 9), date(2020, 5, 10)),
    ("2020–24", date(2020, 5, 11), date(2024, 4, 19)),
    ("2024+", date(2024, 4, 20), date(2100, 1, 1)),
]

SELL_LABELS = {
    "baseline": "Baseline, tiap 14 hari",
    "mvrv_warm": "MVRV ≥ persentil 85 (4 thn)",
    "mvrv_hot": "MVRV ≥ persentil 95 (4 thn)",
    "mayer_warm": "Mayer ≥ persentil 85 (4 thn)",
    "mayer_hot": "Mayer ≥ persentil 95 (4 thn)",
    "blowoff": "Ambang klasik (MVRV 3,5 / Pi Cycle / 5x 2YMA)",
    "funding_hot": "Funding 30H ≥ 30% setahun",
    "greed": "F&G rata-rata 30H ≥ 75",
    "alt_mayer_warm": "Mayer ≥ 1,5",
    "alt_mayer_hot": "Mayer ≥ 2,0",
    "pe_warm": "P/E ≥ persentil 85 riwayatnya",
    "trend_break": "Tes doang: close < 200DMA, ATH ≤ 365 hari lalu",
    "heat_2": "Skor panas ≥ 2 (jual 5%)",
    "heat_4": "Skor panas ≥ 4 (jual 10%)",
    "heat_6": "Skor panas ≥ 6 (jual 20%)",
}

VALUE_LABELS = {
    "baseline": "Baseline, tiap 14 hari",
    "dd_core": "Drawdown ≥ 25% (inti v2)",
    "dd_deep": "Drawdown ≥ 50%",
    "mayer_low": "Mayer < 0,8",
    "wma200": "Harga di bawah 200WMA",
    "mvrv_low": "MVRV < 1",
    "value_2": "Skor value ≥ 2",
    "value_3": "Skor value ≥ 3",
}


def sell_predicates(asset: str, cfg: dict) -> list[tuple[str, callable]]:
    cyc = cfg["cycle"]
    warm = float(cyc["pct_warm"])
    hot = float(cyc["pct_hot"])

    def ge(attr: str, level: float):
        return lambda p: getattr(p, attr) is not None and getattr(p, attr) >= level

    def heat_at(level: int):
        return lambda p: heat_score(p, cfg).score >= level

    preds: list[tuple[str, callable]] = [("baseline", lambda p: True)]
    if asset.upper() == "BTC":
        preds += [
            ("mvrv_warm", ge("mvrv_pct", warm)),
            ("mvrv_hot", ge("mvrv_pct", hot)),
            ("mayer_warm", ge("mayer_pct", warm)),
            ("mayer_hot", ge("mayer_pct", hot)),
            ("blowoff", lambda p: blowoff(p, cfg)),
        ]
    else:
        preds += [
            ("alt_mayer_warm", ge("mayer", float(cyc["alt"]["mayer_warm"]))),
            ("alt_mayer_hot", ge("mayer", float(cyc["alt"]["mayer_hot"]))),
            ("pe_warm", ge("pe_pct", warm)),
        ]
    preds += [
        ("funding_hot", ge("funding_apr_30d", float(cyc["funding_apr_hot"]))),
        ("greed", ge("fg_30d", float(cyc["fg_hot"]))),
    ]
    preds.append(
        (
            "trend_break",
            lambda p: p.sma200 is not None
            and p.close < p.sma200
            and p.ath_day is not None
            and (p.day - p.ath_day).days <= 365,
        )
    )
    preds += [(f"heat_{band['min_heat']}", heat_at(int(band["min_heat"]))) for band in cyc["sell_bands"]]
    return preds


def value_predicates(cfg: dict) -> list[tuple[str, callable]]:
    cyc = cfg["cycle"]
    core = float(cfg["v2"]["drawdown_core"])
    deep = float(cyc["value_drawdown"])
    return [
        ("baseline", lambda p: True),
        ("dd_core", lambda p: p.drawdown >= core),
        ("dd_deep", lambda p: p.drawdown >= deep),
        ("mayer_low", lambda p: p.mayer is not None and p.mayer < float(cyc["value_mayer_below"])),
        ("wma200", lambda p: p.sma1400 is not None and p.close < p.sma1400),
        ("mvrv_low", lambda p: p.mvrv is not None and p.mvrv < float(cyc["value_mvrv_below"])),
        ("value_2", lambda p: value_score(p, cfg).score >= 2),
        ("value_3", lambda p: value_score(p, cfg).score >= 3),
    ]


def _epoch(day: date) -> str:
    for name, first, last in EPOCHS:
        if first <= day <= last:
            return name
    return EPOCHS[-1][0]


def _path_extremes(days: list[date], closes: list[float], pos: dict, origin: date, horizon: int):
    """(titik terendah, titik tertinggi) relatif ke harga origin dalam `horizon` hari ke depan."""
    start = pos.get(origin)
    if start is None:
        return None
    limit = origin + timedelta(days=horizon)
    if days[-1] < limit:
        return None
    lo = hi = closes[start]
    i = start + 1
    while i < len(days) and days[i] <= limit:
        lo = min(lo, closes[i])
        hi = max(hi, closes[i])
        i += 1
    return lo / closes[start] - 1.0, hi / closes[start] - 1.0


def primary_horizon(asset: str, cfg: dict) -> int:
    cyc = cfg["cycle"]
    if asset.upper() == "BTC":
        return int(cyc["primary_horizon"])
    return int(cyc["alt"]["primary_horizon"])


def event_rows(points: list[CyclePoint], preds, labels: dict, cfg: dict) -> list[dict]:
    cyc = cfg["cycle"]
    start = date.fromisoformat(cyc["start"])
    step = int(cfg["window"]["dedupe_days"])
    horizons = [int(item) for item in cyc["forward_days"]]
    primary = primary_horizon(points[-1].asset, cfg) if points else int(cyc["primary_horizon"])
    days = [p.day for p in points]
    closes = [p.close for p in points]
    pos = {day: i for i, day in enumerate(days)}
    rows = []
    for key, pred in preds:
        events = cooldown_events(points, start, step, pred)
        by_h = {h: [] for h in horizons}
        by_epoch: dict[str, list[float]] = {name: [] for name, _, _ in EPOCHS}
        lows, highs = [], []
        for event in events:
            for h in horizons:
                ret = _forward_cached(days, closes, pos, event.day, h)
                if ret is None:
                    continue
                by_h[h].append(ret)
                if h == primary:
                    by_epoch[_epoch(event.day)].append(ret)
            ext = _path_extremes(days, closes, pos, event.day, primary)
            if ext is not None:
                lows.append(ext[0])
                highs.append(ext[1])
        rows.append(
            {
                "key": key,
                "label": labels.get(key, key),
                "events": len(events),
                "first": events[0].day.isoformat() if events else None,
                "last": events[-1].day.isoformat() if events else None,
                "raw_days": sum(1 for p in points if p.day >= start and pred(p)),
                "stats": {h: summarize(by_h[h]) for h in horizons},
                "epochs": {name: summarize(vals) for name, vals in by_epoch.items()},
                "worst": statistics.median(lows) if lows else None,
                "best": statistics.median(highs) if highs else None,
            }
        )
    return rows


def simulate_ladder(
    points: list[CyclePoint],
    cfg: dict,
    start: date,
    *,
    sell: bool,
    redeploy: bool,
    unit_usd: float = 100.0,
) -> dict:
    """DCA rata `unit_usd` tiap grid. Kalau `sell`, jual porsi tangga pas skor panas nyala.

    Kalau `redeploy`, kas hasil jual dibeliin lagi sedikit-sedikit selama drawdown dalam.
    """
    cyc = cfg["cycle"]
    step = int(cfg["window"]["dedupe_days"])
    deep = float(cyc["redeploy_drawdown"])
    frac_back = float(cyc["redeploy_fraction"])
    grid = {p.day for p in make_grid(points, start, step)}
    coins = cash = invested = 0.0
    sold_coins = sold_usd = 0.0
    rebought_usd = 0.0
    sells: list[tuple[date, float, float]] = []
    peak = 0.0
    max_dd = 0.0
    last = None
    for p in points:
        if p.day < start:
            continue
        last = p
        if p.day in grid:
            coins += unit_usd / p.close
            invested += unit_usd
            if sell:
                frac = heat_score(p, cfg).sell_fraction
                if frac > 0 and coins > 0:
                    qty = coins * frac
                    coins -= qty
                    cash += qty * p.close
                    sold_coins += qty
                    sold_usd += qty * p.close
                    sells.append((p.day, p.close, frac))
            if redeploy and cash > 0 and p.drawdown >= deep:
                spend = cash * frac_back
                coins += spend / p.close
                cash -= spend
                rebought_usd += spend
        value = coins * p.close + cash
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, 1.0 - value / peak)
    value = 0.0 if last is None else coins * last.close + cash
    return {
        "start": start.isoformat(),
        "invested": invested,
        "coins": coins,
        "cash": cash,
        "value": value,
        "multiple": value / invested if invested else None,
        "max_dd": max_dd,
        "n_sells": len(sells),
        "avg_sell": sold_usd / sold_coins if sold_coins else None,
        "sold_usd": sold_usd,
        "rebought_usd": rebought_usd,
        "sells": sells,
    }


def sell_episodes(points: list[CyclePoint], sells: list[tuple[date, float, float]], gap_days: int = 60) -> list[dict]:
    """Kelompokin tanggal jual yang berdekatan jadi satu episode, terus lihat harga sesudahnya."""
    if not sells:
        return []
    days = [p.day for p in points]
    closes = [p.close for p in points]
    pos = {day: i for i, day in enumerate(days)}
    groups: list[list[tuple[date, float, float]]] = [[sells[0]]]
    for item in sells[1:]:
        if (item[0] - groups[-1][-1][0]).days > gap_days:
            groups.append([item])
        else:
            groups[-1].append(item)
    out = []
    for group in groups:
        weight = sum(frac for _, _, frac in group)
        avg = sum(price * frac for _, price, frac in group) / weight
        end = group[-1][0]
        after = _forward_cached(days, closes, pos, end, 365)
        ext = _path_extremes(days, closes, pos, end, 365)
        end_px = closes[pos[end]]
        out.append(
            {
                "first": group[0][0].isoformat(),
                "last": end.isoformat(),
                "n": len(group),
                "avg_price": avg,
                "max_frac": max(frac for _, _, frac in group),
                # dibanding harga rata-rata jual, bukan harga hari terakhir
                "after_365": None if after is None else end_px * (1 + after) / avg - 1.0,
                "low_365": None if ext is None else end_px * (1 + ext[0]) / avg - 1.0,
                "high_365": None if ext is None else end_px * (1 + ext[1]) / avg - 1.0,
            }
        )
    return out


def analyze_cycle(points: list[CyclePoint], cfg: dict, sim_starts: list[date]) -> dict:
    asset = points[-1].asset if points else ""
    first = points[0].day if points else None
    sims = []
    for start in sim_starts:
        if first is None or start < first:
            start = first
        sims.append(
            {
                "start": start.isoformat(),
                "hold": simulate_ladder(points, cfg, start, sell=False, redeploy=False),
                "trim": simulate_ladder(points, cfg, start, sell=True, redeploy=False),
                "trim_redeploy": simulate_ladder(points, cfg, start, sell=True, redeploy=True),
            }
        )
    episodes = sell_episodes(points, sims[0]["trim"]["sells"]) if sims else []
    # Skor panas tertinggi sejak halving terakhir, dan skor di hari ATH.
    since = [p for p in points if p.day >= HALVINGS[-1]] if asset.upper() == "BTC" else points
    since = since or points
    hottest = max(since, key=lambda p: heat_score(p, cfg).score) if since else None
    ath_point = max(points, key=lambda p: p.close) if points else None
    return {
        "asset": asset,
        "sell_rows": event_rows(points, sell_predicates(asset, cfg), SELL_LABELS, cfg),
        "value_rows": event_rows(points, value_predicates(cfg), VALUE_LABELS, cfg),
        "sims": sims,
        "episodes": episodes,
        "primary": primary_horizon(asset, cfg),
        "hottest": None
        if hottest is None
        else {"day": hottest.day.isoformat(), "score": heat_score(hottest, cfg).score, "close": hottest.close},
        "ath_heat": None
        if ath_point is None
        else {"day": ath_point.day.isoformat(), "score": heat_score(ath_point, cfg).score, "close": ath_point.close},
        "first_day": None if first is None else first.isoformat(),
        "last_day": points[-1].day.isoformat() if points else None,
    }
