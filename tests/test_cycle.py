"""Tes lapisan siklus. Nggak ada jaringan."""

from __future__ import annotations

import copy
from datetime import date, timedelta

from cryptomonitor.cycle import (
    CyclePoint,
    build_cycle,
    cycle_clock,
    heat_score,
    levels,
    rolling_mean,
    sell_fraction_for,
    trailing_percentile,
    value_score,
    zone_key,
)
from cryptomonitor.cycle_backtest import analyze_cycle, sell_episodes, simulate_ladder
from cryptomonitor.lib import load_config


def _cfg():
    return copy.deepcopy(load_config())


def _point(**kwargs) -> CyclePoint:
    base = dict(asset="BTC", day=date(2024, 6, 1), close=100.0, ath=100.0, drawdown=0.0)
    base.update(kwargs)
    return CyclePoint(**base)


def _days(n: int, start: date = date(2015, 1, 1)) -> list[date]:
    return [start + timedelta(days=i) for i in range(n)]


def test_cycle_rules_locked():
    cyc = _cfg()["cycle"]
    assert cyc["pct_window_days"] == 1460
    assert cyc["pct_min_days"] == 730
    assert cyc["pct_warm"] == 0.85
    assert cyc["pct_hot"] == 0.95
    assert cyc["onchain_lag_days"] == 1
    assert cyc["blowoff_mvrv"] == 3.5
    assert cyc["blowoff_two_year_mult"] == 5.0
    assert cyc["funding_apr_hot"] == 0.30
    assert cyc["fg_hot"] == 75
    assert cyc["heat_gate_drawdown"] == 0.25
    assert cyc["value_drawdown"] == 0.50
    assert cyc["value_mayer_below"] == 0.8
    assert cyc["value_mvrv_below"] == 1.0
    assert [(b["min_heat"], b["fraction"]) for b in cyc["sell_bands"]] == [(2, 0.05), (4, 0.10), (6, 0.20)]
    assert cyc["alt"]["mayer_warm"] == 1.5
    assert cyc["alt"]["mayer_hot"] == 2.0


def test_rolling_mean():
    assert rolling_mean([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]


def test_trailing_percentile_uses_only_the_past():
    days = _days(10)
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 10.0, None, 3.0, 3.0]
    out = trailing_percentile(days, values, window_days=100, min_days=3)
    assert out[:3] == [None, None, None]
    assert out[3] == 1.0  # 4 lebih besar dari semua yang sebelumnya
    assert out[5] == 0.0
    assert out[6] == 1.0
    assert out[7] is None
    # 3.0 dibanding [1,2,3,4,5,0,10]: empat nilai <= 3
    assert abs(out[8] - 4 / 7) < 1e-9
    # Lonjakan masa depan nggak ngubah persentil hari sebelumnya.
    again = trailing_percentile(days, values[:6] + [999.0, None, 3.0, 3.0], 100, 3)
    assert again[:6] == out[:6]


def test_trailing_percentile_window_drops_old_values():
    days = _days(6)
    out = trailing_percentile(days, [100.0, 1.0, 1.0, 1.0, 1.0, 50.0], window_days=3, min_days=2)
    # Hari terakhir cuma lihat 3 hari ke belakang (semua 1.0); 100 sudah keluar jendela.
    assert out[5] == 1.0


def test_heat_tiers_and_ladder():
    cfg = _cfg()
    cold = _point(mvrv_pct=0.5, mayer_pct=0.5)
    assert heat_score(cold, cfg).score == 0
    assert heat_score(cold, cfg).sell_fraction == 0.0
    warm = _point(mvrv_pct=0.86, mayer_pct=0.90)
    assert heat_score(warm, cfg).score == 2
    assert heat_score(warm, cfg).sell_fraction == 0.05
    hot = _point(mvrv_pct=0.96, mayer_pct=0.97, funding_apr_30d=0.31, fg_30d=80)
    assert heat_score(hot, cfg).score == 6
    assert heat_score(hot, cfg).sell_fraction == 0.20
    blow = _point(mvrv=3.6, mvrv_pct=0.99, mayer_pct=0.99, funding_apr_30d=0.5, fg_30d=90)
    assert heat_score(blow, cfg).score == 8
    assert sell_fraction_for(1, cfg) == 0.0
    assert sell_fraction_for(4, cfg) == 0.10


def test_blowoff_any_classic_trigger():
    cfg = _cfg()
    assert heat_score(_point(pi_ratio=1.0), cfg).parts["blowoff"] == 2
    assert heat_score(_point(two_year_mult=5.0), cfg).parts["blowoff"] == 2
    assert heat_score(_point(mvrv=3.49, pi_ratio=0.99, two_year_mult=4.9), cfg).parts["blowoff"] == 0


def test_heat_gated_when_v2_core_is_on():
    cfg = _cfg()
    point = _point(close=75.0, drawdown=0.25, mvrv_pct=0.99, mayer_pct=0.99)
    heat = heat_score(point, cfg)
    assert heat.raw == 4
    assert heat.score == 0
    assert heat.gated
    assert heat.sell_fraction == 0.0
    assert zone_key(point, cfg) == "accumulate"


def test_missing_data_never_adds_heat():
    cfg = _cfg()
    assert heat_score(_point(), cfg).score == 0
    assert heat_score(_point(asset="HYPE"), cfg).score == 0


def test_alt_heat_uses_fixed_mayer_and_pe():
    cfg = _cfg()
    point = _point(asset="HYPE", mayer=1.6, pe_pct=0.9, funding_apr_30d=0.4)
    heat = heat_score(point, cfg)
    assert heat.parts == {"mayer": 1, "pe": 1, "funding": 1, "greed": 0}
    assert heat_score(_point(asset="HYPE", mayer=2.0), cfg).parts["mayer"] == 2
    # Persentil MVRV/Mayer BTC nggak dipakai buat HYPE.
    assert heat_score(_point(asset="HYPE", mvrv_pct=0.99, mayer_pct=0.99), cfg).score == 0


def test_value_score_and_zones():
    cfg = _cfg()
    deep = _point(close=40.0, drawdown=0.6, mayer=0.7, sma1400=50.0, mvrv=0.9)
    assert value_score(deep, cfg).score == 4
    assert zone_key(deep, cfg) == "deep"
    assert zone_key(_point(close=70.0, drawdown=0.30), cfg) == "accumulate"
    assert zone_key(_point(), cfg) == "neutral"
    assert zone_key(_point(mvrv_pct=0.9, mayer_pct=0.9), cfg) == "trim"
    assert zone_key(_point(mvrv_pct=0.96, mayer_pct=0.96), cfg) == "trim_hard"


def test_build_cycle_lags_onchain_by_one_day():
    cfg = _cfg()
    days = _days(5)
    prices = [(day, 100.0 + i) for i, day in enumerate(days)]
    mvrv = {day: float(i + 1) for i, day in enumerate(days)}
    points = build_cycle("BTC", prices, cfg, mvrv=mvrv)
    assert points[0].mvrv is None
    assert points[3].mvrv == 3.0  # nilai hari ke-3 (kemarin), bukan hari ini
    assert points[4].ath == 104.0 and points[4].ath_day == days[4]


def test_build_cycle_mayer_and_drawdown():
    cfg = _cfg()
    days = _days(260)
    prices = [(day, 100.0) for day in days[:250]] + [(day, 50.0) for day in days[250:]]
    points = build_cycle("BTC", prices, cfg)
    assert points[198].mayer is None
    assert points[199].mayer == 1.0
    assert points[-1].drawdown == 0.5
    assert points[-1].mayer < 0.8
    assert points[-1].ath_day == days[0]


def test_levels_sorted_and_cover_buy_side():
    cfg = _cfg()
    days = _days(300)
    prices = [(day, 100.0 + i * 0.1) for i, day in enumerate(days)]
    points = build_cycle("HYPE", prices, cfg)
    lv = levels(points, cfg)
    assert [price for _, price, _ in lv] == sorted(price for _, price, _ in lv)
    ath = points[-1].ath
    assert any(abs(price - ath * 0.75) < 1e-9 and side == "beli" for _, price, side in lv)
    assert any(abs(price - ath * 0.5) < 1e-9 and side == "beli" for _, price, side in lv)
    assert any(side == "jual" for _, _, side in lv)


def _hot_then_crash():
    """200 hari datar, 60 hari 'panas' di harga 200, lalu ambruk ke 50."""
    days = _days(400, date(2020, 1, 1))
    pts = []
    for i, day in enumerate(days):
        if i < 200:
            pts.append(_point(day=day, close=100.0, ath=100.0, drawdown=0.0))
        elif i < 260:
            pts.append(_point(day=day, close=200.0, ath=200.0, drawdown=0.0, mvrv_pct=0.96, mayer_pct=0.96))
        else:
            pts.append(_point(day=day, close=50.0, ath=200.0, drawdown=0.75))
    return pts


def test_ladder_sells_only_when_hot_and_redeploys_in_deep_drawdown():
    cfg = _cfg()
    pts = _hot_then_crash()
    start = pts[0].day
    hold = simulate_ladder(pts, cfg, start, sell=False, redeploy=False)
    trim = simulate_ladder(pts, cfg, start, sell=True, redeploy=False)
    back = simulate_ladder(pts, cfg, start, sell=True, redeploy=True)
    assert hold["n_sells"] == 0 and hold["cash"] == 0
    assert trim["n_sells"] > 0
    assert all(pts[0].day + timedelta(days=200) <= day < pts[0].day + timedelta(days=260) for day, _, _ in trim["sells"])
    assert all(price == 200.0 and frac == 0.10 for _, price, frac in trim["sells"])
    assert abs(trim["avg_sell"] - 200.0) < 1e-9
    # Jual di 200 sebelum ambruk ke 50: nilai akhir harus di atas tahan-terus.
    assert trim["value"] > hold["value"]
    assert back["rebought_usd"] > 0
    assert back["coins"] > trim["coins"]
    assert hold["invested"] == trim["invested"] == back["invested"]
    assert trim["max_dd"] < hold["max_dd"]


def test_sell_episodes_group_and_measure_after():
    cfg = _cfg()
    pts = _hot_then_crash()
    trim = simulate_ladder(pts, cfg, pts[0].day, sell=True, redeploy=False)
    episodes = sell_episodes(pts, trim["sells"])
    assert len(episodes) == 1
    assert episodes[0]["n"] == trim["n_sells"]
    assert abs(episodes[0]["avg_price"] - 200.0) < 1e-9
    assert episodes[0]["after_365"] is None  # belum ada data 365 hari


def test_analyze_cycle_shapes():
    cfg = _cfg()
    pts = _hot_then_crash()
    out = analyze_cycle(pts, cfg, [pts[0].day])
    keys = [row["key"] for row in out["sell_rows"]]
    assert keys[0] == "baseline" and "heat_4" in keys and "trend_break" in keys
    heat4 = next(row for row in out["sell_rows"] if row["key"] == "heat_4")
    assert heat4["events"] > 0
    # Sinyal panas di 200 lalu harga 50: return 90 hari ke depan negatif.
    assert heat4["stats"][90]["median"] < 0
    assert out["hottest"]["score"] == 4
    assert out["sims"][0]["trim"]["n_sells"] > 0


def test_cycle_clock_picks_top_within_two_years_of_halving():
    days = [date(2020, 5, 11) + timedelta(days=i) for i in range(1500)]
    pts = []
    for i, day in enumerate(days):
        close = 100.0
        if i == 500:
            close = 300.0  # puncak siklus
        if i == 900:
            close = 40.0  # dasar
        if i == 1400:
            close = 500.0  # reli pra-halving berikutnya, bukan puncak siklus ini
        pts.append(_point(day=day, close=close, ath=close, drawdown=0.0))
    rows = cycle_clock(pts)
    row = next(item for item in rows if item["halving"] == date(2020, 5, 11))
    assert row["days_to_top"] == 500
    assert row["days_top_to_low"] == 400
    assert abs(row["low_dd"] - (1 - 40 / 300)) < 1e-9
