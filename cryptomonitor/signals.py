"""Skor beli.

Aturan v2 dikunci di config.toml sebelum backtest dijalankan. Modul ini cuma
nerapin aturan itu. F&G sendirian dan harga di bawah 200DMA nggak dapat poin
di v2 — dua-duanya nggak punya edge di v1. 200DMA masih dihitung buat skor v1
biar perbandingannya adil.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass(frozen=True)
class Feature:
    asset: str
    day: date
    close: float
    ath: float
    drawdown: float
    sma200: float | None
    fear_greed: int | None
    funding_7d: float | None
    etf_5d: float | None


@dataclass(frozen=True)
class Score:
    version: str
    score: int
    multiplier: float
    invalidated: bool
    etf_capitulation: bool
    parts: dict[str, int] = field(default_factory=dict)


def funding_window(
    funding: dict[date, float],
    day: date,
    lookback: int,
    min_obs: int,
) -> float | None:
    vals = []
    for offset in range(lookback):
        value = funding.get(day - timedelta(days=offset))
        if value is not None:
            vals.append(value)
    if len(vals) < min_obs:
        return None
    return sum(vals) / len(vals)


def etf_window(
    flows: dict[date, float],
    day: date,
    prints: int,
    lag_days: int,
) -> float | None:
    """Jumlah `prints` aliran terakhir yang tanggalnya <= day - lag.

    Lag 1 hari: aliran yang baru terbit hari ini belum dipakai. Farside biasanya
    nongol setelah tutup pasar AS.
    """
    cutoff = day - timedelta(days=lag_days)
    usable = [stamp for stamp in flows if stamp <= cutoff]
    if len(usable) < prints:
        return None
    usable.sort()
    chosen = usable[-prints:]
    return sum(flows[stamp] for stamp in chosen)


def build_features(
    asset: str,
    prices: list[tuple[date, float]],
    fear_greed: dict[date, int],
    funding: dict[date, float],
    etf: dict[date, float],
    cfg: dict,
) -> list[Feature]:
    v1 = cfg["v1"]
    v2 = cfg["v2"]
    sma_n = int(v1["sma_days"])
    lookback = int(v2["funding_lookback_days"])
    min_obs = int(v2["funding_min_obs"])
    prints = int(v2["etf_lookback_prints"])
    lag = int(v2["etf_lag_days"])
    closes: list[float] = []
    ath = 0.0
    out: list[Feature] = []
    prices = sorted(prices, key=lambda item: item[0])
    for day, close in prices:
        closes.append(close)
        if close > ath:
            ath = close
        drawdown = 0.0 if ath <= 0 else (ath - close) / ath
        sma = None
        if len(closes) >= sma_n:
            window = closes[-sma_n:]
            sma = sum(window) / sma_n
        out.append(
            Feature(
                asset=asset,
                day=day,
                close=close,
                ath=ath,
                drawdown=drawdown,
                sma200=sma,
                fear_greed=fear_greed.get(day),
                funding_7d=funding_window(funding, day, lookback, min_obs),
                etf_5d=etf_window(etf, day, prints, lag),
            )
        )
    return out


def _core_on(feature: Feature, cfg: dict) -> bool:
    return feature.drawdown >= float(cfg["v2"]["drawdown_core"])


def etf_capitulation(feature: Feature, cfg: dict) -> bool:
    flow = feature.etf_5d
    if flow is None:
        return False
    if feature.asset.upper() not in {item.upper() for item in cfg["v2"]["etf_assets"]}:
        return False
    return flow <= -float(cfg["v2"]["etf_capitulation_usd"])


def is_invalidated(feature: Feature, cfg: dict) -> bool:
    if feature.asset.upper() != "HYPE":
        return False
    level = cfg["dca"].get("hype_invalidation_close")
    if level is None:
        return False
    return feature.close < float(level)


def multiplier_for(score: int, cfg: dict, *, invalidated: bool) -> float:
    if invalidated:
        return 0.0
    mult = 1.0
    for band in sorted(cfg["multiplier"]["bands"], key=lambda item: int(item["min_score"])):
        if score >= int(band["min_score"]):
            mult = float(band["mult"])
    return min(mult, float(cfg["multiplier"]["max"]))


def score_v1(feature: Feature, cfg: dict) -> Score:
    v1 = cfg["v1"]
    parts = {
        "fg": 1 if feature.fear_greed is not None and feature.fear_greed < int(v1["fg_below"]) else 0,
        "below_sma": 1
        if feature.sma200 is not None and feature.close < feature.sma200
        else 0,
        "drawdown": 1 if feature.drawdown > float(v1["drawdown_min"]) else 0,
    }
    total = sum(parts.values())
    invalidated = is_invalidated(feature, cfg)
    # v1 nggak punya invalidation. Pengali di sini cuma biar bentuknya sama;
    # laporan v1 pakai ambang skor, bukan pengali.
    return Score(
        version="v1",
        score=total,
        multiplier=multiplier_for(total, cfg, invalidated=False),
        invalidated=invalidated,
        etf_capitulation=False,
        parts=parts,
    )


def score_v2(feature: Feature, cfg: dict) -> Score:
    v2 = cfg["v2"]
    if feature.drawdown >= float(v2["drawdown_deep"]):
        dd_pts = int(v2["drawdown_deep_points"])
    elif feature.drawdown >= float(v2["drawdown_core"]):
        dd_pts = int(v2["drawdown_core_points"])
    else:
        dd_pts = 0

    fund_pts = 0
    if feature.funding_7d is not None and feature.funding_7d < 0:
        if (not v2["funding_requires_core"]) or _core_on(feature, cfg):
            fund_pts = int(v2["funding_negative_points"])

    etf_pts = 0
    capitulation = etf_capitulation(feature, cfg)
    allowed = feature.asset.upper() in {item.upper() for item in v2["etf_assets"]}
    fg_ok = feature.fear_greed is not None and feature.fear_greed < int(v2["fg_combo_below"])
    flow = feature.etf_5d
    combo_band = False
    if allowed and flow is not None and fg_ok:
        low = -float(v2["etf_outflow_cap_usd"])
        high = -float(v2["etf_outflow_min_usd"])
        # high = -500jt, low = -1M. Kombo = outflow minimal $500jt tapi belum tembus $1M.
        combo_band = low < flow <= high
    if combo_band and ((not v2["etf_combo_requires_core"]) or _core_on(feature, cfg)):
        etf_pts = int(v2["etf_combo_points"])

    parts = {"drawdown": dd_pts, "funding": fund_pts, "etf_combo": etf_pts}
    total = dd_pts + fund_pts + etf_pts
    invalidated = is_invalidated(feature, cfg)
    return Score(
        version="v2",
        score=total,
        multiplier=multiplier_for(total, cfg, invalidated=invalidated),
        invalidated=invalidated,
        etf_capitulation=capitulation,
        parts=parts,
    )


def tranche_idr(feature: Feature, cfg: dict) -> float:
    scored = score_v2(feature, cfg)
    if feature.asset.upper() == "HYPE":
        base = float(cfg["dca"]["hype_base_idr"])
    else:
        base = float(cfg["dca"]["btc_base_idr"])
    return base * scored.multiplier
