"""Tes logika sinyal. Nggak ada jaringan."""

from __future__ import annotations

import copy
from datetime import date, timedelta

from cryptomonitor.backtest import analyze_asset, make_grid, simulate_dca
from cryptomonitor.lib import fmt_compact, fmt_idr, fmt_number, fmt_pct, fmt_usd, load_config
from cryptomonitor.signals import (
    Feature,
    build_features,
    etf_window,
    is_invalidated,
    score_v1,
    score_v2,
)


def _cfg():
    return copy.deepcopy(load_config())


def _feature(**kwargs) -> Feature:
    base = dict(
        asset="BTC",
        day=date(2024, 6, 1),
        close=60_000.0,
        ath=100_000.0,
        drawdown=0.40,
        sma200=70_000.0,
        fear_greed=50,
        funding_7d=0.0001,
        etf_5d=None,
    )
    base.update(kwargs)
    return Feature(**base)


def test_rules_locked():
    cfg = load_config()
    assert cfg["v2"]["drawdown_core"] == 0.25
    assert cfg["v2"]["drawdown_core_points"] == 2
    assert cfg["v2"]["drawdown_deep"] == 0.50
    assert cfg["v2"]["drawdown_deep_points"] == 3
    assert cfg["v2"]["funding_negative_points"] == 1
    assert cfg["v2"]["funding_requires_core"] is True
    assert cfg["v2"]["etf_outflow_min_usd"] == 500_000_000
    assert cfg["v2"]["etf_outflow_cap_usd"] == 1_000_000_000
    assert cfg["v2"]["etf_combo_points"] == 1
    assert cfg["v2"]["etf_combo_requires_core"] is True
    assert cfg["v2"]["etf_lag_days"] == 1
    assert cfg["v2"]["etf_assets"] == ["BTC"]
    assert "sma_days" not in cfg["v2"]
    assert cfg["v1"]["sma_days"] == 200
    assert cfg["v1"]["threshold"] == 3
    assert cfg["v1"]["fg_below"] == 20
    assert cfg["dca"]["btc_base_idr"] == 30_000_000
    assert cfg["dca"]["hype_base_idr"] == 7_500_000
    assert cfg["dca"]["hype_invalidation_close"] == 60
    assert cfg["multiplier"]["max"] == 2.0
    bands = {(int(b["min_score"]), float(b["mult"])) for b in cfg["multiplier"]["bands"]}
    assert bands == {(0, 1.0), (2, 1.5), (3, 2.0)}
    assert cfg["window"]["dedupe_days"] == 14
    assert cfg["window"]["in_sample_end"] == "2021-12-31"


def test_v2_drawdown_is_the_core_and_sma_is_ignored():
    cfg = _cfg()
    mild = _feature(drawdown=0.10, close=90_000, sma200=1)
    other = _feature(drawdown=0.10, close=90_000, sma200=1_000_000)
    assert score_v2(mild, cfg).score == score_v2(other, cfg).score == 0
    assert score_v2(mild, cfg).multiplier == 1.0
    mid = _feature(drawdown=0.25)
    assert score_v2(mid, cfg).parts["drawdown"] == 2
    assert score_v2(mid, cfg).multiplier == 1.5
    deep = _feature(drawdown=0.50)
    assert score_v2(deep, cfg).parts["drawdown"] == 3
    assert score_v2(deep, cfg).multiplier == 2.0


def test_fear_alone_adds_nothing():
    cfg = _cfg()
    scared = _feature(drawdown=0.10, fear_greed=5, etf_5d=None)
    calm = _feature(drawdown=0.10, fear_greed=80, etf_5d=None)
    assert score_v2(scared, cfg).score == score_v2(calm, cfg).score == 0
    assert score_v2(scared, cfg).parts["etf_combo"] == 0


def test_funding_only_confirms_a_drawdown():
    cfg = _cfg()
    no_dd = _feature(drawdown=0.10, funding_7d=-0.0002)
    assert score_v2(no_dd, cfg).parts["funding"] == 0
    assert score_v2(no_dd, cfg).multiplier == 1.0
    with_dd = _feature(drawdown=0.30, funding_7d=-0.0002)
    assert score_v2(with_dd, cfg).parts["funding"] == 1
    assert score_v2(with_dd, cfg).score == 3
    assert score_v2(with_dd, cfg).multiplier == 2.0
    positive = _feature(drawdown=0.30, funding_7d=0.0002)
    assert score_v2(positive, cfg).parts["funding"] == 0
    assert score_v2(positive, cfg).multiplier == 1.5
    missing = _feature(drawdown=0.30, funding_7d=None)
    assert score_v2(missing, cfg).parts["funding"] == 0


def test_etf_combo_band_and_capitulation():
    cfg = _cfg()
    combo = _feature(drawdown=0.30, fear_greed=10, etf_5d=-600_000_000)
    scored = score_v2(combo, cfg)
    assert scored.parts["etf_combo"] == 1
    assert scored.score == 3
    assert scored.etf_capitulation is False
    assert scored.multiplier == 2.0

    too_small = _feature(drawdown=0.30, fear_greed=10, etf_5d=-400_000_000)
    assert score_v2(too_small, cfg).parts["etf_combo"] == 0

    exact_billion = _feature(drawdown=0.30, fear_greed=10, etf_5d=-1_000_000_000)
    cap = score_v2(exact_billion, cfg)
    assert cap.parts["etf_combo"] == 0
    assert cap.etf_capitulation is True
    assert cap.parts["drawdown"] == 2
    assert cap.multiplier == 1.5

    bigger = _feature(drawdown=0.30, fear_greed=10, etf_5d=-1_200_000_000)
    assert score_v2(bigger, cfg).etf_capitulation is True
    assert score_v2(bigger, cfg).parts["etf_combo"] == 0

    no_core = _feature(drawdown=0.10, fear_greed=10, etf_5d=-600_000_000)
    assert score_v2(no_core, cfg).parts["etf_combo"] == 0
    assert score_v2(no_core, cfg).score == 0

    fg_not_enough = _feature(drawdown=0.30, fear_greed=20, etf_5d=-600_000_000)
    assert score_v2(fg_not_enough, cfg).parts["etf_combo"] == 0

    hype = _feature(asset="HYPE", close=80, drawdown=0.30, fear_greed=10, etf_5d=-600_000_000)
    assert score_v2(hype, cfg).parts["etf_combo"] == 0
    assert score_v2(hype, cfg).etf_capitulation is False


def test_v1_needs_all_three_and_v2_does_not_use_sma():
    cfg = _cfg()
    hit = _feature(close=50, sma200=80, fear_greed=10, drawdown=0.40)
    assert score_v1(hit, cfg).score == 3
    assert score_v1(hit, cfg).parts == {"fg": 1, "below_sma": 1, "drawdown": 1}
    missing_sma = _feature(close=90, sma200=80, fear_greed=10, drawdown=0.40)
    assert score_v1(missing_sma, cfg).score == 2
    no_sma_yet = _feature(sma200=None, fear_greed=10, drawdown=0.40, close=50)
    assert score_v1(no_sma_yet, cfg).parts["below_sma"] == 0
    # v2 tetap 2 poin drawdown, sma nggak ngaruh
    assert score_v2(hit, cfg).parts["drawdown"] == 2
    assert score_v2(missing_sma, cfg).parts["drawdown"] == 2


def test_hype_invalidation_zeros_tranche_only_below_60():
    cfg = _cfg()
    under = _feature(asset="HYPE", close=59.99, drawdown=0.60, ath=150)
    scored = score_v2(under, cfg)
    assert is_invalidated(under, cfg)
    assert scored.score == 3
    assert scored.multiplier == 0.0
    at_level = _feature(asset="HYPE", close=60.0, drawdown=0.60, ath=150)
    assert score_v2(at_level, cfg).multiplier == 2.0
    assert not is_invalidated(at_level, cfg)
    btc = _feature(asset="BTC", close=10, drawdown=0.60)
    assert score_v2(btc, cfg).multiplier == 2.0


def test_etf_lag_ignores_same_day_print():
    flows = {date(2024, 1, 10): -700_000_000}
    assert etf_window(flows, date(2024, 1, 10), prints=1, lag_days=1) is None
    assert etf_window(flows, date(2024, 1, 11), prints=1, lag_days=1) == -700_000_000
    cfg = _cfg()
    cfg["v2"]["etf_lookback_prints"] = 1
    day0 = date(2024, 1, 10)
    prices = [(day0, 50_000.0), (day0 + timedelta(days=1), 50_000.0)]
    features = build_features("BTC", prices, {}, {}, flows, cfg)
    assert features[0].etf_5d is None
    assert features[1].etf_5d == -700_000_000


def test_funding_window_needs_min_obs():
    cfg = _cfg()
    day = date(2024, 6, 8)
    funding = {day - timedelta(days=i): -0.001 for i in range(3)}
    prices = [(day - timedelta(days=i), 40_000.0) for i in range(10, -1, -1)]
    features = build_features("BTC", prices, {}, funding, {}, cfg)
    assert features[-1].funding_7d is None
    for i in range(6):
        funding[day - timedelta(days=i)] = -0.001
    features = build_features("BTC", prices, {}, funding, {}, cfg)
    assert features[-1].funding_7d is not None
    assert features[-1].funding_7d < 0


def test_running_drawdown_does_not_look_ahead():
    cfg = _cfg()
    start = date(2020, 1, 1)
    prices = [(start, 100.0), (start + timedelta(days=1), 80.0), (start + timedelta(days=2), 120.0)]
    features = build_features("BTC", prices, {}, {}, {}, cfg)
    assert features[0].drawdown == 0
    assert abs(features[1].drawdown - 0.20) < 1e-9
    assert features[2].drawdown == 0
    assert features[2].ath == 120


def test_cooldown_counts_a_short_burst_once():
    from cryptomonitor.backtest import cooldown_events

    start = date(2022, 1, 1)
    features = []
    for i in range(40):
        hot = i in {7, 8, 9, 30}
        features.append(
            _feature(
                day=start + timedelta(days=i),
                drawdown=0.30 if hot else 0.0,
                close=70 if hot else 100,
            )
        )
    events = cooldown_events(features, start, 14, lambda feature: feature.drawdown >= 0.25)
    assert [item.day for item in events] == [
        start + timedelta(days=7),
        start + timedelta(days=30),
    ]


def test_grid_is_14_days():
    cfg = _cfg()
    start = date(2022, 1, 1)
    prices = [(start + timedelta(days=i), 100.0 + i) for i in range(45)]
    features = build_features("BTC", prices, {}, {}, {}, cfg)
    grid = make_grid(features, date(2018, 1, 1), 14)
    assert [item.day for item in grid] == [
        start,
        start + timedelta(days=14),
        start + timedelta(days=28),
        start + timedelta(days=42),
    ]


def test_uptrend_never_boosts_and_crash_does():
    cfg = _cfg()
    start = date(2019, 1, 1)
    up = [(start + timedelta(days=i), 100.0 + i) for i in range(400)]
    features = build_features("BTC", up, {}, {}, {}, cfg)
    result = analyze_asset(features, {}, cfg)
    rows = {row["key"]: row for row in result["rows"]}
    assert rows["v2_2x"]["stats"]["all"][90]["n"] == 0
    assert rows["v2_1_5x"]["stats"]["all"][90]["n"] == 0
    assert rows["baseline"]["stats"]["all"][90]["n"] > 10

    crash_start = date(2022, 1, 1)
    crash = []
    for i in range(500):
        day = crash_start + timedelta(days=i)
        price = 40.0 if 250 <= i < 290 else 100.0
        crash.append((day, price))
    fear = {day: 10 for day, _ in crash}
    funding = {day: -0.0001 for day, _ in crash}
    features = build_features("BTC", crash, fear, funding, {}, cfg)
    result = analyze_asset(features, {}, cfg)
    rows = {row["key"]: row for row in result["rows"]}
    # Drawdown 60% + funding negatif → tranche 2x, dan 90 hari kemudian harga sudah balik.
    assert rows["v2_2x"]["stats"]["oos"][90]["n"] >= 1
    assert rows["v2_2x"]["stats"]["oos"][90]["median"] > 0
    # SMA200 sudah ada, close di bawahnya, F&G 10, drawdown > 25% → skor v1 = 3.
    assert rows["v1_score"]["stats"]["oos"][90]["n"] >= 1


def test_dca_flat_matches_cash_when_price_unchanged():
    cfg = _cfg()
    start = date(2022, 1, 1)
    prices = [(start + timedelta(days=i), 100.0) for i in range(45)]
    features = build_features("BTC", prices, {day: 50 for day, _ in prices}, {}, {}, cfg)
    fx = {start: 15_000.0}
    sim = simulate_dca(features, fx, 30_000_000, 14, date(2018, 1, 1), lambda feature: 1.0)
    assert sim["decisions"] == 4
    assert sim["spent_idr"] == 120_000_000
    assert abs(sim["coins"] - 80) < 1e-9
    assert abs(sim["value_idr"] - 120_000_000) < 1e-6


def test_hype_dca_skips_invalid_days():
    cfg = _cfg()
    start = date(2024, 12, 5)
    prices = [(start + timedelta(days=i), 40.0 if i < 20 else 80.0) for i in range(40)]
    features = build_features("HYPE", prices, {}, {}, {}, cfg)
    fx = {start: 16_000.0}
    from cryptomonitor.signals import score_v2 as score

    sim = simulate_dca(
        features,
        fx,
        7_500_000,
        14,
        date(2018, 1, 1),
        lambda feature: score(feature, cfg).multiplier,
    )
    assert sim["zero_tranche"] >= 1
    assert sim["spent_idr"] < sim["decisions"] * 7_500_000


def test_shuffle_is_deterministic():
    cfg = _cfg()
    start = date(2018, 1, 1)
    prices = []
    for i in range(800):
        price = 100.0 if i % 50 < 40 else 60.0
        prices.append((start + timedelta(days=i), price))
    features = build_features("BTC", prices, {}, {}, {}, cfg)
    a = analyze_asset(features, {}, cfg)
    b = analyze_asset(features, {}, cfg)
    assert a["shuffles"][0]["p"] == b["shuffles"][0]["p"]
    assert a["shuffles"][0]["iters"] == 1000


def test_indonesian_number_format():
    assert fmt_number(1234567.5, 1) == "1.234.567,5"
    assert fmt_number(-4.1, 1) == "-4,1"
    assert fmt_pct(-0.041) == "-4,1%"
    assert fmt_pct(-1e-8) == "0,0%"
    assert fmt_pct(0.076) == "+7,6%"
    assert fmt_pct(0.002) == "+0,2%"
    assert fmt_idr(30_000_000) == "Rp 30jt"
    assert fmt_idr(7_500_000) == "Rp 7,5jt"
    assert fmt_usd(500_000_000) == "$500jt"
    assert fmt_usd(-1_000_000_000) == "-$1M"
    assert fmt_usd(1_200_000_000) == "$1,2M"
    assert fmt_compact(1_500_000_000_000) == "1,5T"
