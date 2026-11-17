"""Lapisan siklus: kapan pasar "panas" (mulai jual bertahap) dan kapan "murah".

Skor v2 cuma ngatur berapa banyak BELI. Lapisan ini nambah sisi JUAL, dan
kedalaman value buat konteks. Dia nggak ngubah tranche v2.

Kenapa pakai persentil 4 tahun, bukan ambang klasik (MVRV 3,5, Mayer 2,4,
Pi Cycle): puncak tiap siklus makin rendah. Nov 2021 dan Okt 2025 nggak
pernah nyentuh ambang klasik itu. Persentil terhadap 4 tahun ke belakang
(satu siklus halving) ikut nyesuaiin diri, dan cuma pakai data masa lalu.

Semua fungsi di sini murni, nggak nyentuh jaringan atau DB.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass(frozen=True)
class CyclePoint:
    asset: str
    day: date
    close: float
    ath: float
    drawdown: float
    ath_day: date | None = None
    sma200: float | None = None
    sma1400: float | None = None  # 200 minggu
    mayer: float | None = None
    mayer_pct: float | None = None
    mvrv: float | None = None
    mvrv_pct: float | None = None
    pi_ratio: float | None = None  # 111DMA / (2 x 350DMA); >= 1 = Pi Cycle Top
    two_year_mult: float | None = None  # close / 730DMA
    funding_apr_30d: float | None = None
    fg_30d: float | None = None
    pe: float | None = None  # market cap / pendapatan holder 30H disetahunkan
    pe_pct: float | None = None
    rel_btc: float | None = None  # rasio ASET/BTC dibagi 200DMA rasionya


@dataclass(frozen=True)
class Heat:
    score: int
    raw: int
    gated: bool
    sell_fraction: float
    parts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Value:
    score: int
    parts: dict[str, int] = field(default_factory=dict)


def rolling_mean(values: list[float], n: int) -> list[float | None]:
    out: list[float | None] = []
    total = 0.0
    for i, value in enumerate(values):
        total += value
        if i >= n:
            total -= values[i - n]
        out.append(total / n if i >= n - 1 else None)
    return out


def trailing_percentile(
    days: list[date],
    values: list[float | None],
    window_days: int,
    min_days: int,
) -> list[float | None]:
    """Peringkat nilai hari ini terhadap `window_days` hari SEBELUMNYA (hari ini nggak ikut).

    0,90 artinya 90% nilai di jendela itu <= nilai hari ini. Kalau jendela
    belum nyakup `min_days` hari kalender, hasilnya None.
    """
    out: list[float | None] = []
    window: list[float] = []  # terurut
    queue: list[tuple[date, float]] = []
    head = 0
    for day, value in zip(days, values):
        cutoff = day - timedelta(days=window_days)
        while head < len(queue) and queue[head][0] < cutoff:
            old = queue[head][1]
            del window[bisect.bisect_left(window, old)]
            head += 1
        if value is None:
            out.append(None)
            continue
        span = (day - queue[head][0]).days if head < len(queue) else 0
        if span >= min_days and window:
            out.append(bisect.bisect_right(window, value) / len(window))
        else:
            out.append(None)
        bisect.insort(window, value)
        queue.append((day, value))
    return out


def _trailing_avg(
    series: dict[date, float],
    day: date,
    lookback: int,
    min_obs: int,
) -> float | None:
    vals = []
    for offset in range(lookback):
        value = series.get(day - timedelta(days=offset))
        if value is not None:
            vals.append(value)
    if len(vals) < min_obs:
        return None
    return sum(vals) / len(vals)


def _lagged(series: dict[date, float], day: date, lag: int, max_stale: int = 5) -> float | None:
    for offset in range(lag, lag + max_stale + 1):
        value = series.get(day - timedelta(days=offset))
        if value is not None:
            return value
    return None


def build_cycle(
    asset: str,
    prices: list[tuple[date, float]],
    cfg: dict,
    *,
    mvrv: dict[date, float] | None = None,
    funding_apr: dict[date, float] | None = None,
    fear_greed: dict[date, int] | None = None,
    mcap: dict[date, float] | None = None,
    revenue: dict[date, float] | None = None,
    btc_prices: dict[date, float] | None = None,
) -> list[CyclePoint]:
    cyc = cfg["cycle"]
    window = int(cyc["pct_window_days"])
    min_days = int(cyc["pct_min_days"])
    lag = int(cyc["onchain_lag_days"])
    fund_n = int(cyc["funding_days"])
    fg_n = int(cyc["fg_days"])
    rev_n = int(cyc["revenue_days"])
    pe_min = int(cyc["pe_pct_min_days"])
    mvrv = mvrv or {}
    funding_apr = funding_apr or {}
    fear_greed = fear_greed or {}
    mcap = mcap or {}
    revenue = revenue or {}

    prices = sorted(prices, key=lambda item: item[0])
    days = [day for day, _ in prices]
    closes = [close for _, close in prices]
    sma111 = rolling_mean(closes, 111)
    sma200 = rolling_mean(closes, 200)
    sma350 = rolling_mean(closes, 350)
    sma730 = rolling_mean(closes, 730)
    sma1400 = rolling_mean(closes, 1400)

    mayer = [None if avg is None or avg <= 0 else close / avg for close, avg in zip(closes, sma200)]
    mvrv_vals = [_lagged(mvrv, day, lag) for day in days] if mvrv else [None] * len(days)
    mayer_pct = trailing_percentile(days, mayer, window, min_days)
    mvrv_pct = trailing_percentile(days, mvrv_vals, window, min_days)

    pe_vals: list[float | None] = []
    for day in days:
        cap = _lagged(mcap, day, lag) if mcap else None
        rev = _trailing_avg(revenue, day - timedelta(days=lag), rev_n, max(rev_n // 2, 1)) if revenue else None
        if cap is None or rev is None or rev <= 0:
            pe_vals.append(None)
        else:
            pe_vals.append(cap / (rev * 365.0))
    pe_pct = trailing_percentile(days, pe_vals, window, pe_min)

    rel_vals: list[float | None] = [None] * len(days)
    if btc_prices:
        ratio_days = []
        ratios = []
        for i, day in enumerate(days):
            other = btc_prices.get(day)
            if other and other > 0:
                ratio_days.append(i)
                ratios.append(closes[i] / other)
        ratio_sma = rolling_mean(ratios, 200)
        for i, ratio, avg in zip(ratio_days, ratios, ratio_sma):
            if avg:
                rel_vals[i] = ratio / avg

    out: list[CyclePoint] = []
    ath = 0.0
    ath_day = None
    for i, (day, close) in enumerate(prices):
        if close > ath:
            ath, ath_day = close, day
        pi = None
        if sma111[i] is not None and sma350[i]:
            pi = sma111[i] / (2.0 * sma350[i])
        out.append(
            CyclePoint(
                asset=asset,
                day=day,
                close=close,
                ath=ath,
                drawdown=0.0 if ath <= 0 else (ath - close) / ath,
                ath_day=ath_day,
                sma200=sma200[i],
                sma1400=sma1400[i],
                mayer=mayer[i],
                mayer_pct=mayer_pct[i],
                mvrv=mvrv_vals[i],
                mvrv_pct=mvrv_pct[i],
                pi_ratio=pi,
                two_year_mult=None if not sma730[i] else close / sma730[i],
                funding_apr_30d=_trailing_avg(funding_apr, day, fund_n, max(fund_n // 2, 1)),
                fg_30d=_trailing_avg(fear_greed, day, fg_n, max(fg_n // 2, 1)),
                pe=pe_vals[i],
                pe_pct=pe_pct[i],
                rel_btc=rel_vals[i],
            )
        )
    return out


def _tier(value: float | None, warm: float, hot: float) -> int:
    if value is None:
        return 0
    if value >= hot:
        return 2
    if value >= warm:
        return 1
    return 0


def blowoff(point: CyclePoint, cfg: dict) -> bool:
    """Ambang klasik. Terakhir nyala 2021; disimpan buat puncak yang beneran gila."""
    cyc = cfg["cycle"]
    if point.mvrv is not None and point.mvrv >= float(cyc["blowoff_mvrv"]):
        return True
    if point.pi_ratio is not None and point.pi_ratio >= 1.0:
        return True
    if point.two_year_mult is not None and point.two_year_mult >= float(cyc["blowoff_two_year_mult"]):
        return True
    return False


def sell_fraction_for(score: int, cfg: dict) -> float:
    frac = 0.0
    for band in sorted(cfg["cycle"]["sell_bands"], key=lambda item: int(item["min_heat"])):
        if score >= int(band["min_heat"]):
            frac = float(band["fraction"])
    return frac


def heat_score(point: CyclePoint, cfg: dict) -> Heat:
    cyc = cfg["cycle"]
    warm = float(cyc["pct_warm"])
    hot = float(cyc["pct_hot"])
    if point.asset.upper() == "BTC":
        parts = {
            "mvrv": _tier(point.mvrv_pct, warm, hot),
            "mayer": _tier(point.mayer_pct, warm, hot),
            "blowoff": int(cyc["blowoff_points"]) if blowoff(point, cfg) else 0,
        }
    else:
        # Riwayat HYPE belum sampai 2 tahun penuh, persentil 4 tahun belum ada.
        # Mayer pakai ambang tetap; valuasi pakai persentil P/E riwayatnya sendiri.
        alt = cyc["alt"]
        parts = {
            "mayer": _tier(point.mayer, float(alt["mayer_warm"]), float(alt["mayer_hot"])),
            "pe": 1 if point.pe_pct is not None and point.pe_pct >= warm else 0,
        }
    parts["funding"] = (
        1 if point.funding_apr_30d is not None and point.funding_apr_30d >= float(cyc["funding_apr_hot"]) else 0
    )
    parts["greed"] = 1 if point.fg_30d is not None and point.fg_30d >= float(cyc["fg_hot"]) else 0
    raw = sum(parts.values())
    # Nggak boleh nyuruh jual di hari yang sama v2 nyuruh beli lebih banyak.
    gated = point.drawdown >= float(cyc["heat_gate_drawdown"])
    score = 0 if gated else raw
    return Heat(
        score=score,
        raw=raw,
        gated=gated and raw > 0,
        sell_fraction=sell_fraction_for(score, cfg),
        parts=parts,
    )


def value_score(point: CyclePoint, cfg: dict) -> Value:
    cyc = cfg["cycle"]
    parts = {
        "drawdown": 1 if point.drawdown >= float(cyc["value_drawdown"]) else 0,
        "mayer": 1 if point.mayer is not None and point.mayer < float(cyc["value_mayer_below"]) else 0,
        "wma200": 1 if point.sma1400 is not None and point.close < point.sma1400 else 0,
        "mvrv": 1 if point.mvrv is not None and point.mvrv < float(cyc["value_mvrv_below"]) else 0,
    }
    return Value(score=sum(parts.values()), parts=parts)


ZONES = {
    "deep": "AKUMULASI DALAM",
    "accumulate": "AKUMULASI",
    "neutral": "NETRAL",
    "trim": "DISTRIBUSI",
    "trim_hard": "DISTRIBUSI KUAT",
}


def zone_key(point: CyclePoint, cfg: dict) -> str:
    cyc = cfg["cycle"]
    heat = heat_score(point, cfg)
    bands = sorted(int(band["min_heat"]) for band in cyc["sell_bands"])
    if point.drawdown >= float(cyc["value_drawdown"]) or value_score(point, cfg).score >= 2:
        return "deep"
    if point.drawdown >= float(cyc["heat_gate_drawdown"]):
        return "accumulate"
    if len(bands) > 1 and heat.score >= bands[1]:
        return "trim_hard"
    if bands and heat.score >= bands[0]:
        return "trim"
    return "neutral"


def regime(point: CyclePoint, prev: CyclePoint | None) -> str:
    """Konteks tren, bukan sinyal. Di backtest v1, 200DMA nggak punya edge."""
    if point.sma200 is None:
        return "n/a"
    above = point.close >= point.sma200
    rising = prev is not None and prev.sma200 is not None and point.sma200 >= prev.sma200
    if above and rising:
        return "naik (di atas 200DMA yang nanjak)"
    if above:
        return "di atas 200DMA, tapi 200DMA masih turun"
    if rising:
        return "di bawah 200DMA, 200DMA masih nanjak"
    return "turun (di bawah 200DMA yang turun)"


def _value_at_percentile(points: list[CyclePoint], attr: str, pct: float, window_days: int) -> float | None:
    if not points:
        return None
    cutoff = points[-1].day - timedelta(days=window_days)
    vals = sorted(
        getattr(item, attr)
        for item in points[:-1]
        if item.day >= cutoff and getattr(item, attr) is not None
    )
    if not vals:
        return None
    idx = min(len(vals) - 1, max(0, int(pct * len(vals))))
    return vals[idx]


def levels(points: list[CyclePoint], cfg: dict) -> list[tuple[str, float, str]]:
    """Harga di mana tiap aturan berubah status. (label, harga, sisi) — sisi 'beli'/'jual'/'info'."""
    if not points:
        return []
    cyc = cfg["cycle"]
    v2 = cfg["v2"]
    point = points[-1]
    window = int(cyc["pct_window_days"])
    out: list[tuple[str, float, str]] = []
    out.append((f"Drawdown {float(v2['drawdown_core']) * 100:.0f}% dari ATH (v2 naik ke 1,5x)", point.ath * (1 - float(v2["drawdown_core"])), "beli"))
    out.append((f"Drawdown {float(v2['drawdown_deep']) * 100:.0f}% dari ATH (v2 naik ke 2x)", point.ath * (1 - float(v2["drawdown_deep"])), "beli"))
    if point.sma200:
        out.append(("200DMA", point.sma200, "info"))
        out.append((f"Mayer {float(cyc['value_mayer_below']):.1f} (value +1)".replace(".", ","), point.sma200 * float(cyc["value_mayer_below"]), "beli"))
    if point.sma1400:
        out.append(("200WMA (value +1 kalau di bawahnya)", point.sma1400, "beli"))
    if point.mvrv and point.mvrv > 0:
        realized = point.close / point.mvrv
        out.append((f"Realized price, MVRV {float(cyc['value_mvrv_below']):.0f} (value +1 kalau di bawahnya)", realized * float(cyc["value_mvrv_below"]), "beli"))
        for label, pct in (("hangat", float(cyc["pct_warm"])), ("panas", float(cyc["pct_hot"]))):
            level = _value_at_percentile(points, "mvrv", pct, window)
            if level is not None:
                out.append((f"MVRV {level:.2f} = persentil {pct * 100:.0f} ({label})".replace(".", ","), realized * level, "jual"))
    if point.asset.upper() == "BTC":
        if point.sma200:
            for label, pct in (("hangat", float(cyc["pct_warm"])), ("panas", float(cyc["pct_hot"]))):
                level = _value_at_percentile(points, "mayer", pct, window)
                if level is not None:
                    out.append((f"Mayer {level:.2f} = persentil {pct * 100:.0f} ({label})".replace(".", ","), point.sma200 * level, "jual"))
    elif point.sma200:
        alt = cyc["alt"]
        out.append((f"Mayer {float(alt['mayer_warm']):.1f} (hangat)".replace(".", ","), point.sma200 * float(alt["mayer_warm"]), "jual"))
        out.append((f"Mayer {float(alt['mayer_hot']):.1f} (panas)".replace(".", ","), point.sma200 * float(alt["mayer_hot"]), "jual"))
    gate = point.ath * (1 - float(cyc["heat_gate_drawdown"]))
    out.append(("Batas bawah zona jual (di bawah ini skor panas dimatiin)", gate, "info"))
    out.append(("ATH", point.ath, "info"))
    out.sort(key=lambda item: item[1])
    return out


CLOCK_TOP_DAYS = 730
HALVINGS = [date(2012, 11, 28), date(2016, 7, 9), date(2020, 5, 11), date(2024, 4, 20)]


def cycle_clock(points: list[CyclePoint]) -> list[dict]:
    """Per siklus halving: puncak, lalu dasar sesudahnya. n cuma 4, ini konteks, bukan sinyal."""
    if not points:
        return []
    rows = []
    today = points[-1].day
    for i, halving in enumerate(HALVINGS):
        end = HALVINGS[i + 1] if i + 1 < len(HALVINGS) else today + timedelta(days=1)
        # Puncak dicari di 2 tahun pertama setelah halving. Tanpa batas itu,
        # reli pra-halving berikutnya (Mar 2024) kebaca sebagai puncak siklus 2020.
        top_window = [p for p in points if halving <= p.day < min(end, halving + timedelta(days=CLOCK_TOP_DAYS))]
        if not top_window:
            continue
        top = max(top_window, key=lambda p: p.close)
        after = [p for p in points if top.day < p.day < end]
        low = min(after, key=lambda p: p.close) if after else None
        rows.append(
            {
                "halving": halving,
                "top_day": top.day,
                "top": top.close,
                "days_to_top": (top.day - halving).days,
                "low_day": None if low is None else low.day,
                "low": None if low is None else low.close,
                "days_top_to_low": None if low is None else (low.day - top.day).days,
                "low_dd": None if low is None else 1.0 - low.close / top.close,
                "open": i + 1 == len(HALVINGS),
                "days_since_halving": (today - halving).days,
                "days_since_top": (today - top.day).days,
            }
        )
    return rows
