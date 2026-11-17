"""Event study dengan dedupe 14 hari, plus DCA dan tes acak.

Sinyal dihitung di hari pertama dia nyala, lalu diam 14 hari. Baseline
"beli buta" itu aturan yang sama kalau syaratnya selalu benar, jadi jadwalnya
tetap tiap 14 hari. DCA naruh duit di jadwal itu, pengalinya dari skor hari beli.
Return ke depan diukur dari close tanggal itu ke close pertama pada atau
setelah +30/90/180 hari.
"""

from __future__ import annotations

import random
import statistics
from datetime import date, timedelta

from cryptomonitor.signals import Feature, score_v1, score_v2


def parse_start(cfg: dict) -> tuple[date, date, date]:
    window = cfg["window"]
    return (
        date.fromisoformat(window["backtest_start"]),
        date.fromisoformat(window["in_sample_end"]),
        date.fromisoformat(window["etf_era_start"]),
    )


def make_grid(features: list[Feature], start: date, step: int) -> list[Feature]:
    """Jadwal buta: satu titik tiap >= step hari, buat DCA."""
    picked: list[Feature] = []
    last: date | None = None
    for feature in features:
        if feature.day < start:
            continue
        if last is None or (feature.day - last).days >= step:
            picked.append(feature)
            last = feature.day
    return picked


def cooldown_events(features: list[Feature], start: date, step: int, pred) -> list[Feature]:
    """Hari pertama sinyal nyala, lalu diam `step` hari. Sinyal pendek nggak kepeleset."""
    events: list[Feature] = []
    last: date | None = None
    for feature in features:
        if feature.day < start or not pred(feature):
            continue
        if last is not None and (feature.day - last).days < step:
            continue
        events.append(feature)
        last = feature.day
    return events


def _index(features: list[Feature]) -> tuple[list[date], list[float]]:
    days = [feature.day for feature in features]
    closes = [feature.close for feature in features]
    return days, closes


def forward_return(
    days: list[date],
    closes: list[float],
    origin: date,
    horizon: int,
) -> float | None:
    if origin not in _pos(days, origin):
        return None
    target = origin + timedelta(days=horizon)
    # bisect
    lo, hi = 0, len(days)
    while lo < hi:
        mid = (lo + hi) // 2
        if days[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    if lo >= len(days):
        return None
    if (days[lo] - target).days > 7:
        return None
    j = _pos(days, origin)[origin]
    if closes[j] <= 0:
        return None
    return closes[lo] / closes[j] - 1.0


def _pos(days: list[date], origin: date) -> dict[date, int]:
    # helper kecil; dipanggil sering tapi n-nya ribuan, dict sekali lebih baik.
    # caller seharusnya pakai cache. Biar API-nya sederhana, cache di fungsi luar.
    return {day: i for i, day in enumerate(days)}


def _forward_cached(
    days: list[date],
    closes: list[float],
    pos: dict[date, int],
    origin: date,
    horizon: int,
) -> float | None:
    if origin not in pos:
        return None
    target = origin + timedelta(days=horizon)
    lo, hi = 0, len(days)
    while lo < hi:
        mid = (lo + hi) // 2
        if days[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    if lo >= len(days) or (days[lo] - target).days > 7:
        return None
    base = closes[pos[origin]]
    if base <= 0:
        return None
    return closes[lo] / base - 1.0


def summarize(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "win": None, "median": None}
    return {
        "n": len(values),
        "win": sum(1 for value in values if value > 0) / len(values),
        "median": statistics.median(values),
    }


def _bucket(day: date, is_end: date, etf_start: date) -> list[str]:
    keys = ["all", "is" if day <= is_end else "oos"]
    if day >= etf_start:
        keys.append("etf")
    return keys


def _collect(
    grid: list[Feature],
    pred,
    days: list[date],
    closes: list[float],
    pos: dict[date, int],
    horizons: list[int],
    is_end: date,
    etf_start: date,
) -> dict[str, dict[int, list[float]]]:
    bag: dict[str, dict[int, list[float]]] = {
        "all": {h: [] for h in horizons},
        "is": {h: [] for h in horizons},
        "oos": {h: [] for h in horizons},
        "etf": {h: [] for h in horizons},
    }
    for feature in grid:
        if not pred(feature):
            continue
        keys = _bucket(feature.day, is_end, etf_start)
        for horizon in horizons:
            ret = _forward_cached(days, closes, pos, feature.day, horizon)
            if ret is None:
                continue
            for key in keys:
                bag[key][horizon].append(ret)
    return bag


def _stats_from_bag(bag: dict, horizons: list[int]) -> dict:
    return {
        split: {horizon: summarize(bag[split][horizon]) for horizon in horizons}
        for split in bag
    }


def predicates(cfg: dict) -> list[tuple[str, callable]]:
    """Daftar sinyal ditetapkan di sini, sebelum angka dilihat."""
    v1_cut = int(cfg["v1"]["threshold"])
    dd_min = float(cfg["v1"]["drawdown_min"])
    fg_cut = int(cfg["v1"]["fg_below"])
    etf_min = float(cfg["v2"]["etf_outflow_min_usd"])
    etf_cap = float(cfg["v2"]["etf_outflow_cap_usd"])

    def v1_hit(feature: Feature) -> bool:
        return score_v1(feature, cfg).score >= v1_cut

    def fg(feature: Feature) -> bool:
        return feature.fear_greed is not None and feature.fear_greed < fg_cut

    def below_sma(feature: Feature) -> bool:
        return feature.sma200 is not None and feature.close < feature.sma200

    def dd(feature: Feature) -> bool:
        return feature.drawdown > dd_min

    def dd_deep(feature: Feature) -> bool:
        return feature.drawdown >= float(cfg["v2"]["drawdown_deep"])

    def funding(feature: Feature) -> bool:
        return feature.funding_7d is not None and feature.funding_7d < 0

    def etf_combo_raw(feature: Feature) -> bool:
        flow = feature.etf_5d
        if flow is None or feature.fear_greed is None or feature.fear_greed >= fg_cut:
            return False
        return -etf_cap < flow <= -etf_min

    def etf_cap_raw(feature: Feature) -> bool:
        return feature.etf_5d is not None and feature.etf_5d <= -etf_cap

    def v2_mid(feature: Feature) -> bool:
        return score_v2(feature, cfg).multiplier >= 1.5

    def v2_max(feature: Feature) -> bool:
        return score_v2(feature, cfg).multiplier >= 2.0

    return [
        ("baseline", lambda feature: True),
        ("v1_score", v1_hit),
        ("fg", fg),
        ("below_sma", below_sma),
        ("drawdown", dd),
        ("drawdown_deep", dd_deep),
        ("funding", funding),
        ("etf_combo", etf_combo_raw),
        ("etf_capitulation", etf_cap_raw),
        ("v2_1_5x", v2_mid),
        ("v2_2x", v2_max),
    ]


ROW_LABELS = {
    "baseline": "Baseline, beli tiap 14 hari",
    "v1_score": "v1 skor ≥ 3",
    "fg": "F&G < 20 sendirian",
    "below_sma": "Harga di bawah 200DMA",
    "drawdown": "Drawdown dari ATH > 25%",
    "drawdown_deep": "Drawdown dari ATH ≥ 50%",
    "funding": "Funding rata-rata 7H < 0",
    "etf_combo": "F&G < 20 dan ETF 5H keluar $500jt–$1M",
    "etf_capitulation": "ETF 5H keluar ≥ $1M",
    "v2_1_5x": "v2 tranche ≥ 1,5x",
    "v2_2x": "v2 tranche 2x",
}


def shuffle_test(
    features: list[Feature],
    pred,
    days: list[date],
    closes: list[float],
    pos: dict[date, int],
    horizon: int,
    iters: int,
    seed: int,
    step: int,
    start: date,
    day_pred=None,
) -> dict:
    """Null-nya jadwal 14 hari, biar jarak antar sampel sama dengan sinyal yang sudah di-dedupe."""
    population: list[float] = []
    for feature in make_grid(features, start, step):
        if day_pred is not None and not day_pred(feature.day):
            continue
        ret = _forward_cached(days, closes, pos, feature.day, horizon)
        if ret is not None:
            population.append(ret)
    hits: list[float] = []
    for feature in cooldown_events(features, start, step, pred):
        if day_pred is not None and not day_pred(feature.day):
            continue
        ret = _forward_cached(days, closes, pos, feature.day, horizon)
        if ret is not None:
            hits.append(ret)
    result = {
        "k": len(hits),
        "n_pop": len(population),
        "obs": statistics.median(hits) if hits else None,
        "p": None,
        "iters": iters,
    }
    if not hits or not population or len(hits) > len(population):
        return result
    if len(hits) == len(population):
        return result
    rng = random.Random(seed)
    beat = 0
    k = len(hits)
    for _ in range(iters):
        sample = [population[i] for i in rng.sample(range(len(population)), k)]
        if statistics.median(sample) >= result["obs"]:
            beat += 1
    result["p"] = beat / iters
    return result


def _fx_rate(fx: dict[date, float], stamps: list[date], day: date) -> float | None:
    lo, hi = 0, len(stamps)
    while lo < hi:
        mid = (lo + hi) // 2
        if stamps[mid] <= day:
            lo = mid + 1
        else:
            hi = mid
    if lo == 0:
        return None
    return fx[stamps[lo - 1]]


def simulate_dca(
    features: list[Feature],
    fx: dict[date, float],
    base_idr: float,
    step: int,
    start: date,
    mult_of,
) -> dict:
    grid = make_grid(features, start, step)
    stamps = sorted(fx)
    coins = 0.0
    spent = 0.0
    decisions = 0
    zero_tranche = 0
    skipped_fx = 0
    for feature in grid:
        decisions += 1
        mult = float(mult_of(feature))
        idr = base_idr * mult
        rate = _fx_rate(fx, stamps, feature.day)
        if idr <= 0:
            zero_tranche += 1
            continue
        if rate is None or feature.close <= 0:
            skipped_fx += 1
            continue
        coins += idr / (feature.close * rate)
        spent += idr
    last = None
    for feature in features:
        if feature.day >= start:
            last = feature
    value = None
    end_rate = None
    if last is not None and coins > 0:
        end_rate = _fx_rate(fx, stamps, last.day)
        if end_rate is not None:
            value = coins * last.close * end_rate
    avg = (spent / coins) if coins else None
    return {
        "decisions": decisions,
        "zero_tranche": zero_tranche,
        "skipped_fx": skipped_fx,
        "spent_idr": spent,
        "coins": coins,
        "value_idr": value,
        "avg_entry_idr": avg,
        "last_day": None if last is None else last.day.isoformat(),
        "last_close": None if last is None else last.close,
        "usd_idr": end_rate,
    }


def analyze_asset(features: list[Feature], fx: dict[date, float], cfg: dict) -> dict:
    start, is_end, etf_start = parse_start(cfg)
    step = int(cfg["window"]["dedupe_days"])
    horizons = [int(item) for item in cfg["window"]["forward_days"]]
    primary = int(cfg["window"]["primary_horizon"])
    grid = make_grid(features, start, step)
    days, closes = _index(features)
    pos = {day: i for i, day in enumerate(days)}

    rows = []
    bags = {}
    for key, pred in predicates(cfg):
        events = cooldown_events(features, start, step, pred)
        bag = _collect(events, lambda _feature: True, days, closes, pos, horizons, is_end, etf_start)
        bags[key] = bag
        raw_days = sum(1 for feature in features if feature.day >= start and pred(feature))
        rows.append(
            {
                "key": key,
                "label": ROW_LABELS[key],
                "stats": _stats_from_bag(bag, horizons),
                "raw_days": raw_days,
            }
        )

    base_bag = bags["baseline"]
    for row in rows:
        row["baseline"] = _stats_from_bag(base_bag, horizons)

    iters = int(cfg["window"]["shuffle_iters"])
    seed = int(cfg["window"]["shuffle_seed"])
    pred_map = dict(predicates(cfg))
    shuffles = []
    for key in ("v2_1_5x", "v2_2x", "v1_score", "drawdown"):
        for split_name, day_pred in (
            ("all", None),
            ("oos", lambda day, end=is_end: day > end),
        ):
            shuffles.append(
                {
                    "key": key,
                    "label": ROW_LABELS[key],
                    "split": split_name,
                    **shuffle_test(
                        features,
                        pred_map[key],
                        days,
                        closes,
                        pos,
                        primary,
                        iters,
                        seed,
                        step,
                        start,
                        day_pred,
                    ),
                }
            )

    asset = features[-1].asset if features else ""
    if asset.upper() == "HYPE":
        base = float(cfg["dca"]["hype_base_idr"])
    else:
        base = float(cfg["dca"]["btc_base_idr"])

    def mult_v2(feature: Feature) -> float:
        return score_v2(feature, cfg).multiplier

    def mult_flat(feature: Feature) -> float:
        return 1.0

    dca_v2 = simulate_dca(features, fx, base, step, start, mult_v2)
    dca_flat = simulate_dca(features, fx, base, step, start, mult_flat)

    invalidated_days = sum(1 for feature in features if feature.day >= start and score_v2(feature, cfg).invalidated)
    return {
        "asset": asset,
        "rows": rows,
        "shuffles": shuffles,
        "dca_v2": dca_v2,
        "dca_flat": dca_flat,
        "base_idr": base,
        "grid_n": len(grid),
        "invalidated_days": invalidated_days,
        "first_day": features[0].day.isoformat() if features else None,
        "last_day": features[-1].day.isoformat() if features else None,
        "n_days": len(features),
    }


def coverage_from_maps(
    features: list[Feature],
    funding: dict[date, float],
    etf: dict[date, float],
    fear: dict[date, int],
) -> dict:
    def span(keys: list[date]) -> tuple[str | None, str | None, int]:
        if not keys:
            return None, None, 0
        ordered = sorted(keys)
        return ordered[0].isoformat(), ordered[-1].isoformat(), len(ordered)

    f0, f1, fn = span(list(funding))
    e0, e1, en = span(list(etf))
    g0, g1, gn = span(list(fear))
    return {
        "price_first": features[0].day.isoformat() if features else None,
        "price_last": features[-1].day.isoformat() if features else None,
        "price_n": len(features),
        "funding_first": f0,
        "funding_last": f1,
        "funding_n": fn,
        "etf_first": e0,
        "etf_last": e1,
        "etf_n": en,
        "fg_first": g0,
        "fg_last": g1,
        "fg_n": gn,
    }
