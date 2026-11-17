"""Bagian laporan buat lapisan siklus: zona hari ini, peta harga, bukti backtest."""

from __future__ import annotations

from cryptomonitor.cycle import ZONES
from cryptomonitor.lib import fmt_idr, fmt_number, fmt_pct, fmt_px, fmt_win

HEAT_NAMES = {
    "mvrv": "MVRV",
    "mayer": "Mayer",
    "blowoff": "ambang klasik",
    "funding": "funding",
    "greed": "F&G",
    "pe": "P/E",
}
VALUE_NAMES = {
    "drawdown": "drawdown ≥ 50%",
    "mayer": "Mayer < 0,8",
    "wma200": "di bawah 200WMA",
    "mvrv": "MVRV < 1",
}
ZONE_TEXT = {
    "deep": "Harga sudah di wilayah yang dulu murah. Beli sesuai tranche v2, jangan jual.",
    "accumulate": "Drawdown sudah masuk inti v2. Beli sesuai tranche v2, jangan jual.",
    "neutral": "Nggak murah, nggak panas. DCA 1x jalan terus, belum ada alasan jual.",
    "trim": "Mulai panas. Jual sedikit dari yang dipegang tiap tanggal tranche, DCA dasar tetap jalan.",
    "trim_hard": "Panas. Jual porsi tangga tiap tanggal tranche.",
}


def heat_max(asset: str, cfg: dict) -> int:
    base = 2 + 2 + int(cfg["cycle"]["blowoff_points"]) if asset == "BTC" else 2 + 1
    return base + 2


def _num(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None else fmt_number(value, digits)


def _pctile(value: float | None) -> str:
    return "n/a" if value is None else "persentil " + fmt_number(value * 100, 0)


def _frac(value: float) -> str:
    return fmt_number(value * 100, 0) + "%"


def _parts(parts: dict, names: dict) -> str:
    on = [f"{names.get(key, key)} {value}" for key, value in parts.items() if value]
    return ", ".join(on) if on else "nggak ada yang nyala"


def _nearest(levels: list, close: float) -> tuple[tuple | None, tuple | None]:
    below = [item for item in levels if item[1] < close]
    above = [item for item in levels if item[1] >= close]
    return (below[-1] if below else None, above[0] if above else None)


def _level_cell(item: tuple | None, close: float) -> str:
    if item is None:
        return "—"
    label, price, _side = item
    return f"{fmt_px(price)} ({fmt_pct(price / close - 1)}): {label}"


def summary_lines(bundle: dict) -> list[str]:
    cycle = bundle.get("cycle") or {}
    live = bundle.get("live") or {}
    assets = [asset for asset in ("BTC", "HYPE") if asset in cycle and asset in live]
    if not assets:
        return []
    cfg = bundle["cfg"]

    def row(label: str, fn) -> str:
        return f"| {label} | " + " | ".join(fn(asset) for asset in assets) + " |"

    def buy(asset: str) -> str:
        snap = live[asset]
        if snap["v2"].invalidated:
            return "**Rp 0** (invalidation)"
        mult = fmt_number(snap["v2"].multiplier, 1).replace(",0", "")
        return f"**{fmt_idr(snap['tranche'], 2)}** ({mult}x)"

    def sell(asset: str) -> str:
        frac = cycle[asset]["heat"].sell_fraction
        return "**0%**, tahan" if frac <= 0 else f"**{_frac(frac)}** dari koin yang dipegang"

    lines = [
        "| | " + " | ".join(assets) + " |",
        "| --- | " + " | ".join("---" for _ in assets) + " |",
        row("Harga", lambda a: fmt_px(cycle[a]["point"].close) + (" (candle belum tutup)" if cycle[a]["partial"] else "")),
        row("Zona siklus", lambda a: f"**{ZONES[cycle[a]['zone']]}**"),
        row("Beli, per tranche 14 hari (v2)", buy),
        row("Jual, per tranche 14 hari", sell),
        row("Skor panas", lambda a: f"{cycle[a]['heat'].score} dari {heat_max(a, cfg)}"),
        row("Skor value", lambda a: f"{cycle[a]['value'].score} dari 4"),
        row("Level terdekat di atas", lambda a: _level_cell(_nearest(cycle[a]["levels"], cycle[a]["point"].close)[1], cycle[a]["point"].close)),
        row("Level terdekat di bawah", lambda a: _level_cell(_nearest(cycle[a]["levels"], cycle[a]["point"].close)[0], cycle[a]["point"].close)),
        "",
    ]
    for asset in assets:
        lines.append(f"- **{asset}:** {ZONE_TEXT[cycle[asset]['zone']]}")
    lines.append("")
    lines.append(
        "Beli itu aturan v2 yang lama, nggak berubah. Jual itu lapisan siklus yang baru. "
        "Buktinya jauh lebih tipis dari sisi beli (puncak siklus BTC cuma ada 4), baca bagiannya di bawah sebelum dipakai."
    )
    return lines


def live_lines(bundle: dict) -> list[str]:
    cycle = bundle.get("cycle") or {}
    cfg = bundle["cfg"]
    cyc = cfg["cycle"]
    lines: list[str] = []
    for asset in ("BTC", "HYPE"):
        block = cycle.get(asset)
        if not block:
            continue
        point = block["point"]
        heat = block["heat"]
        value = block["value"]
        lines.append(f"### {asset}: {ZONES[block['zone']]}")
        lines.append("")
        lines.append(f"- Tren: {block['regime']}. Konteks doang, 200DMA nggak punya edge di backtest.")
        mayer = f"- Mayer (harga ÷ 200DMA) {_num(point.mayer)}"
        if asset == "BTC":
            mayer += f", {_pctile(point.mayer_pct)} dari 4 tahun terakhir"
        lines.append(mayer + ".")
        if asset == "BTC":
            realized = None if not point.mvrv else point.close / point.mvrv
            lines.append(
                f"- MVRV {_num(point.mvrv)} ({_pctile(point.mvrv_pct)} dari 4 tahun terakhir). "
                f"Realized price kira-kira {fmt_px(realized)}. Data on-chain telat 1 hari."
            )
            wma = "n/a" if not point.sma1400 else f"{fmt_px(point.sma1400)}, harga {fmt_pct(point.close / point.sma1400 - 1)} dari situ"
            lines.append(f"- 200WMA {wma}.")
            lines.append(
                f"- Ambang klasik: Pi Cycle {_num(point.pi_ratio)} (nyala di 1), "
                f"harga {_num(point.two_year_mult)}x 2YMA (nyala di {fmt_number(float(cyc['blowoff_two_year_mult']), 0)})."
            )
        else:
            pe = "n/a" if point.pe is None else f"{fmt_number(point.pe, 1)}x ({_pctile(point.pe_pct)} riwayatnya sendiri)"
            lines.append(f"- P/E (market cap ÷ pendapatan holder 30H disetahunkan): {pe}.")
            rel = "n/a" if point.rel_btc is None else fmt_pct(point.rel_btc - 1) + " dari rata-rata 200 harinya"
            lines.append(f"- HYPE/BTC: {rel}. Konteks, nggak masuk skor.")
        funding = "n/a" if point.funding_apr_30d is None else fmt_pct(point.funding_apr_30d)
        lines.append(
            f"- Funding 30H disetahunkan {funding} (panas di {fmt_pct(float(cyc['funding_apr_hot']), 0)}). "
            f"F&G rata-rata 30H {_num(point.fg_30d, 0)} (panas di {fmt_number(float(cyc['fg_hot']), 0)})."
        )
        heat_text = f"- Skor panas **{heat.score}** dari {heat_max(asset, cfg)} ({_parts(heat.parts, HEAT_NAMES)})"
        if heat.gated:
            heat_text += f". Mentahnya {heat.raw}, tapi dimatiin karena drawdown sudah ≥ {fmt_number(float(cyc['heat_gate_drawdown']) * 100, 0)}%"
        if heat.sell_fraction > 0:
            heat_text += f" → jual **{_frac(heat.sell_fraction)}** dari koin yang dipegang di tanggal tranche"
        else:
            heat_text += " → nggak jual"
        lines.append(heat_text + ".")
        lines.append(f"- Skor value **{value.score}** dari 4 ({_parts(value.parts, VALUE_NAMES)}).")
        lines.append("")
        lines.append(f"Peta harga {asset}. Di tiap level ini ada aturan yang berubah status:")
        lines.append("")
        lines.append("| Harga | Jarak | Level | Sisi |")
        lines.append("| ---: | ---: | --- | --- |")
        placed = False
        for label, price, side in reversed(block["levels"]):
            if not placed and price < point.close:
                lines.append(f"| **{fmt_px(point.close)}** | | **harga sekarang** | |")
                placed = True
            lines.append(f"| {fmt_px(price)} | {fmt_pct(price / point.close - 1)} | {label} | {side} |")
        if not placed:
            lines.append(f"| **{fmt_px(point.close)}** | | **harga sekarang** | |")
        lines.append("")
        lines.append(
            "Level jual geser tiap hari (ikut 200DMA, realized price, sama persentilnya). "
            "Level beli ikut ATH. Jangan dihafal, lihat lagi pas tanggal tranche."
        )
        lines.append("")
    return lines


def rules_lines(cfg: dict) -> list[str]:
    cyc = cfg["cycle"]
    warm = fmt_number(float(cyc["pct_warm"]) * 100, 0)
    hot = fmt_number(float(cyc["pct_hot"]) * 100, 0)
    years = fmt_number(int(cyc["pct_window_days"]) / 365, 0)
    gate = fmt_number(float(cyc["heat_gate_drawdown"]) * 100, 0)
    bands = sorted(cyc["sell_bands"], key=lambda item: int(item["min_heat"]))
    ladder = ", ".join(f"skor ≥ {band['min_heat']} → {_frac(float(band['fraction']))}" for band in bands)
    return [
        "Ini lapisan baru di atas v2. Tranche beli nggak disentuh. Pilihan pakai persentil datang setelah gue lihat ambang klasik kelewatan puncak 2021 dan 2025. Angkanya (85/95, tangga 5/10/20%) angka bulat yang ditulis di `config.toml` sebelum event study dan simulasi dijalankan, dan nggak digeser sesudahnya.",
        "",
        "Skor panas BTC (maks 8):",
        "",
        f"- MVRV di persentil ≥ {warm} dari {years} tahun terakhir: 1 poin. Persentil ≥ {hot}: 2 poin.",
        f"- Mayer multiple, aturan persentil yang sama: 1 atau 2 poin.",
        f"- Ambang klasik (MVRV ≥ {fmt_number(float(cyc['blowoff_mvrv']), 1)}, Pi Cycle nyilang, atau harga ≥ {fmt_number(float(cyc['blowoff_two_year_mult']), 0)}x 2YMA): {cyc['blowoff_points']} poin. Terakhir nyala 2021.",
        f"- Funding rata-rata {cyc['funding_days']} hari ≥ {fmt_number(float(cyc['funding_apr_hot']) * 100, 0)}% setahun: 1 poin.",
        f"- F&G rata-rata {cyc['fg_days']} hari ≥ {fmt_number(float(cyc['fg_hot']), 0)}: 1 poin.",
        "",
        "Skor panas HYPE (maks 5, eksperimental): "
        f"Mayer ≥ {fmt_number(float(cyc['alt']['mayer_warm']), 1)} dapat 1, ≥ {fmt_number(float(cyc['alt']['mayer_hot']), 1)} dapat 2. "
        f"P/E di persentil ≥ {warm} riwayatnya sendiri dapat 1. Funding dan F&G sama kayak BTC. "
        "HYPE belum punya riwayat 4 tahun, jadi Mayer-nya pakai ambang tetap.",
        "",
        f"- Kenapa persentil: puncak tiap siklus makin rendah. Nov 2021 dan Okt 2025 nggak pernah nyentuh ambang klasik. Persentil {years} tahun (satu siklus halving) cuma pakai data sebelum hari itu.",
        f"- Skor panas dimatiin kalau drawdown sudah ≥ {gate}%. Satu hari nggak boleh sekaligus beli 1,5x dan jual.",
        f"- Tangga jual, porsi dari koin yang masih dipegang, sekali per tanggal tranche 14 hari: {ladder}.",
        "- DCA dasar tetap jalan waktu skor panas nyala. Yang dijual itu tumpukan lama, bukan jadwal belinya.",
        f"- Skor value (maks 4, konteks, bukan pengali): drawdown ≥ {fmt_number(float(cyc['value_drawdown']) * 100, 0)}%, Mayer < {fmt_number(float(cyc['value_mayer_below']), 1)}, harga di bawah 200WMA, MVRV < {fmt_number(float(cyc['value_mvrv_below']), 0)}.",
        "- Zona: AKUMULASI DALAM kalau drawdown ≥ 50% atau skor value ≥ 2. AKUMULASI kalau drawdown ≥ 25%. DISTRIBUSI kalau skor panas ≥ 2, DISTRIBUSI KUAT kalau ≥ 4. Sisanya NETRAL.",
    ]


def _n(stat: dict) -> str:
    n = stat["n"]
    return fmt_number(n, 0) + ("†" if 0 < n < 20 else "")


def _event_table(rows: list[dict], horizons: list[int], primary: int, epochs: bool) -> list[str]:
    head = f"| Sinyal | Kejadian | n {primary}H | " + " | ".join(f"Median {h}H" for h in horizons)
    head += f" | Naik di {primary}H | Titik terendah {primary}H | Titik tertinggi {primary}H |"
    sep = "| --- | ---: | ---: | " + " | ".join("---:" for _ in horizons) + " | ---: | ---: | ---: |"
    names: list[str] = []
    if epochs and rows:
        names = [name for name in rows[0]["epochs"] if any(row["epochs"][name]["n"] for row in rows)]
        head += " " + " | ".join(names) + " |"
        sep += " " + " | ".join("---:" for _ in names) + " |"
    lines = [head, sep]
    for row in rows:
        stat = row["stats"][primary]
        cells = [row["label"], fmt_number(row["events"], 0), _n(stat)]
        cells += [fmt_pct(row["stats"][h]["median"]) for h in horizons]
        cells += [fmt_win(stat["win"]), fmt_pct(row["worst"]), fmt_pct(row["best"])]
        for name in names:
            epoch = row["epochs"][name]
            cells.append("—" if not epoch["n"] else f"{fmt_pct(epoch['median'])} (n={epoch['n']})")
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _row(rows: list[dict], key: str) -> dict | None:
    for row in rows:
        if row["key"] == key:
            return row
    return None


def _mult(value: float | None) -> str:
    return "—" if value is None else fmt_number(value, 2) + "x"


def _sim_table(sims: list[dict]) -> list[str]:
    lines = [
        "| Mulai | Strategi | Kelipatan modal | Drawdown terdalam | Kali jual | Harga jual rata-rata | Sisa kas (% nilai akhir) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    names = (("hold", "Tahan terus"), ("trim", "Tangga jual, kas didiemin"), ("trim_redeploy", "Tangga jual, kas dibeliin lagi pas drawdown ≥ 50%"))
    for sim in sims:
        for key, label in names:
            item = sim[key]
            cash = "—" if not item["value"] else fmt_win(item["cash"] / item["value"], 0)
            lines.append(
                f"| {sim['start']} | {label} | {_mult(item['multiple'])} | {fmt_win(item['max_dd'], 0)} | "
                f"{item['n_sells']} | {fmt_px(item['avg_sell'])} | {cash} |"
            )
    return lines


def asset_lines(asset: str, block: dict, cfg: dict) -> list[str]:
    cyc = cfg["cycle"]
    bt = block["bt"]
    horizons = [int(item) for item in cyc["forward_days"]]
    primary = int(bt["primary"])
    lines = [f"## Lapisan siklus {asset}: buktinya", ""]
    if asset == "BTC":
        lines.append(
            f"Harga {bt['first_day']} → {bt['last_day']}: CoinMetrics sampai Binance mulai (Agu 2017), Binance sesudahnya. "
            f"Kejadian dihitung dari {cyc['start']}, cara dedupe 14 harinya sama kayak v2. "
            "Funding baru ada 2020 dan F&G 2018, jadi dua komponen itu nggak ikut di siklus awal."
        )
    else:
        lines.append(
            f"**Sampel kecil, satu siklus.** Harga {bt['first_day']} → {bt['last_day']}. Market cap cuma 365 hari terakhir, "
            "jadi P/E baru punya persentil belakangan ini. Semua angka di bagian ini ilustrasi, bukan bukti."
        )
    lines.append("")
    lines.append("### Sinyal jual: sesudah nyala, harganya ke mana")
    lines.append("")
    lines.append(
        f"Buat sinyal jual, yang bagus itu median yang LEBIH RENDAH dari baseline. Titik terendah/tertinggi = median dari harga paling rendah/tinggi dalam {primary} hari sesudah sinyal, dibanding harga pas sinyal."
    )
    lines.append("")
    lines.extend(_event_table(bt["sell_rows"], horizons, primary, asset == "BTC"))
    lines.append("")
    lines.extend(_sell_reading(asset, bt, primary))
    lines.append("")
    if bt["episodes"]:
        lines.append("### Episode jual di simulasi")
        lines.append("")
        lines.append("Tanggal jual yang berdekatan (jarak ≤ 60 hari) digabung. Kolom sesudahnya dibanding harga jual rata-rata episode itu.")
        lines.append("")
        lines.append("| Episode | Kali jual | Porsi terbesar | Harga jual rata-rata | 365H kemudian | Terendah 365H | Tertinggi 365H |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for ep in bt["episodes"]:
            span = ep["first"] if ep["first"] == ep["last"] else f"{ep['first']} → {ep['last']}"
            lines.append(
                f"| {span} | {ep['n']} | {_frac(ep['max_frac'])} | {fmt_px(ep['avg_price'])} | "
                f"{fmt_pct(ep['after_365'])} | {fmt_pct(ep['low_365'])} | {fmt_pct(ep['high_365'])} |"
            )
        lines.append("")
    lines.append("### Simulasi: tahan terus vs tangga jual")
    lines.append("")
    lines.append(
        "DCA rata $100 tiap 14 hari, dalam USD. Kelipatan = (nilai koin + kas) ÷ modal. "
        f"Versi ketiga beliin lagi {fmt_number(float(cyc['redeploy_fraction']) * 100, 1)}% dari kas tiap tanggal tranche selama drawdown ≥ {fmt_number(float(cyc['redeploy_drawdown']) * 100, 0)}%. "
        "Nggak ada pajak, fee, atau bunga kas."
    )
    lines.append("")
    lines.extend(_sim_table(bt["sims"]))
    lines.append("")
    lines.extend(_sim_reading(bt))
    lines.append("")
    lines.append("### Sisi beli: sinyal value, riwayat panjang")
    lines.append("")
    lines.append("Di sini yang bagus median yang LEBIH TINGGI dari baseline. Ini konteks buat tranche v2, bukan pengali baru.")
    lines.append("")
    lines.extend(_event_table(bt["value_rows"], horizons, primary, asset == "BTC"))
    lines.append("")
    lines.extend(_value_reading(bt, primary))
    lines.append("")
    if block.get("clock"):
        lines.extend(_clock_lines(block["clock"]))
    return lines


def _sell_reading(asset: str, bt: dict, primary: int) -> list[str]:
    rows = bt["sell_rows"]
    base = _row(rows, "baseline")["stats"][primary]
    bits = [f"Baseline {primary}H median {fmt_pct(base['median'])} (n={base['n']})."]
    tiers = sorted((row for row in rows if row["key"].startswith("heat_")), key=lambda row: int(row["key"].split("_")[1]))
    for row in tiers:
        stat = row["stats"][primary]
        if not stat["n"]:
            bits.append(f"{row['label']}: belum pernah punya kejadian dengan return {primary}H.")
            continue
        verdict = "di bawah baseline" if stat["median"] < base["median"] else "NGGAK di bawah baseline"
        bits.append(
            f"{row['label']}: median {fmt_pct(stat['median'])} (n={stat['n']}), {verdict}. "
            f"Harganya masih lebih tinggi {primary} hari kemudian di {fmt_win(stat['win'], 0)} kejadian, "
            f"dan di jalan sempat naik median {fmt_pct(row['best'])} dan turun median {fmt_pct(row['worst'])}."
        )
    out = [" ".join(bits)]
    hottest, ath = bt.get("hottest"), bt.get("ath_heat")
    if hottest and ath:
        out.append("")
        text = (
            f"{'Sejak halving terakhir' if asset == 'BTC' else 'Sepanjang riwayatnya'}, skor panas paling tinggi {hottest['score']} ({hottest['day']}, harga {fmt_px(hottest['close'])}). "
            f"Di hari ATH ({ath['day']}, {fmt_px(ath['close'])}) skornya {ath['score']}."
        )
        if ath["score"] < 2:
            text += (
                " Artinya puncak terakhir itu 'dingin': indikatornya nggak pernah panas, dan lapisan ini NGGAK nangkap puncaknya. "
                "Yang ketangkap cuma reli-reli sebelumnya (lihat tabel episode)."
            )
        trend = _row(rows, "trend_break")
        if trend and trend["stats"][primary]["n"]:
            stat = trend["stats"][primary]
            side = "di bawah" if stat["median"] < base["median"] else "di atas"
            text += (
                f" Kandidat buat puncak dingin, jual pas tren patah (close < 200DMA dalam setahun dari ATH), gue tes tapi nggak gue masukin skor: "
                f"median {primary}H sesudahnya {fmt_pct(stat['median'])} (n={stat['n']}), {side} baseline {fmt_pct(base['median'])}."
            )
            if stat["median"] >= base["median"] or stat["median"] > 0:
                text += " Itu bukan sinyal jual, dan dia tabrakan sama v2 yang justru nambah beli di drawdown ≥ 25%."
            else:
                eps = [ep for ep in trend["epochs"].values() if ep["n"]]
                pos = sum(1 for ep in eps if ep["median"] > 0)
                text += (
                    f" Kelihatannya kuat, tapi per siklus nggak konsisten ({pos} dari {len(eps)} siklus mediannya malah positif), "
                    "aturannya gue tambahin SETELAH lihat skor panas kelewatan puncak, dan dia tabrakan sama v2 yang nambah beli di drawdown ≥ 25%. "
                    "Jadi ini catatan buat diamati, bukan aturan."
                )
        if asset == "BTC":
            text += " Kolom per siklus juga nunjukin sinyal persentil 85 sendirian nyala jauh sebelum puncak 2017."
        out.append(text)
    return out


def _sim_reading(bt: dict) -> list[str]:
    bits = []
    for sim in bt["sims"]:
        hold, trim, back = sim["hold"], sim["trim"], sim["trim_redeploy"]
        if not hold["multiple"]:
            continue
        bits.append(
            f"Mulai {sim['start']}: tahan {_mult(hold['multiple'])}, tangga jual {_mult(trim['multiple'])}, "
            f"tangga jual + beli lagi {_mult(back['multiple'])}. Drawdown terdalam {fmt_win(hold['max_dd'], 0)} / "
            f"{fmt_win(trim['max_dd'], 0)} / {fmt_win(back['max_dd'], 0)}."
        )
    wins = sum(1 for sim in bt["sims"] if (sim["trim"]["multiple"] or 0) > (sim["hold"]["multiple"] or 0))
    back_wins = sum(1 for sim in bt["sims"] if (sim["trim_redeploy"]["multiple"] or 0) > (sim["hold"]["multiple"] or 0))
    total = len(bt["sims"])
    text = (
        f"Jual terus kasnya didiemin ngalahin tahan-terus di {wins} dari {total} titik mulai. "
        f"Jual terus dibeliin lagi pas drawdown dalam ngalahin di {back_wins} dari {total}."
    )
    if back_wins > wins:
        text += (
            " Jadi yang ngasih hasil itu pasangan jual-lalu-beli-lagi, bukan jualnya sendiri: "
            "kas yang nganggur kalah sama tren naik jangka panjang."
        )
    if total > 1:
        text += (
            " Titik mulainya saling tumpuk, ini bukan tes yang independen, dan selisih gede di titik mulai awal "
            "datang dari dua-tiga bear market yang turunnya 77–85%. Siklus terakhir turunnya jauh lebih dangkal."
        )
    else:
        text += " Satu titik mulai, satu siklus: ini ilustrasi mekanismenya doang."
    bits.append(text)
    return [" ".join(bits)]


def _value_reading(bt: dict, primary: int) -> list[str]:
    rows = bt["value_rows"]
    base = _row(rows, "baseline")["stats"][primary]
    bits = []
    for key in ("dd_core", "dd_deep", "wma200", "mvrv_low", "value_2", "value_3"):
        row = _row(rows, key)
        stat = row["stats"][primary]
        if not stat["n"]:
            continue
        bits.append(f"{row['label']} {fmt_pct(stat['median'])}, naik {fmt_win(stat['win'], 0)} (n={stat['n']})")
    if not bits:
        return ["Belum ada kejadian value dengan return sepanjang itu."]
    return [
        f"Baseline {primary}H median {fmt_pct(base['median'])}, naik {fmt_win(base['win'], 0)} (n={base['n']}). "
        + "; ".join(bits)
        + ". Kejadiannya ngumpul di segelintir bear market, jadi n efektifnya jauh lebih kecil dari yang tertulis."
    ]


def _clock_lines(clock: list[dict]) -> list[str]:
    lines = [
        "### Jam siklus (konteks, n=4)",
        "",
        "Puncak = close tertinggi dalam 2 tahun setelah halving. Dasar = close terendah sesudah puncak itu sampai halving berikutnya.",
        "",
        "| Halving | Puncak | Hari ke puncak | Dasar | Hari puncak → dasar | Turun |",
        "| --- | --- | ---: | --- | ---: | ---: |",
    ]
    for row in clock:
        low = "—" if row["low_day"] is None else f"{row['low_day']} ({fmt_px(row['low'])})"
        if row["open"] and row["low_day"] is not None:
            low += ", sejauh ini"
        lines.append(
            f"| {row['halving']} | {row['top_day']} ({fmt_px(row['top'])}) | {row['days_to_top']} | {low} | "
            f"{'—' if row['days_top_to_low'] is None else row['days_top_to_low']} | {fmt_win(row['low_dd'], 0)} |"
        )
    now = clock[-1]
    done = [row for row in clock[:-1] if row["days_top_to_low"] is not None]
    lines.append("")
    if now["open"] and done:
        span = f"{min(row['days_top_to_low'] for row in done)}–{max(row['days_top_to_low'] for row in done)}"
        drops = f"{fmt_win(min(row['low_dd'] for row in done), 0)}–{fmt_win(max(row['low_dd'] for row in done), 0)}"
        lines.append(
            f"Sekarang hari ke-{now['days_since_halving']} sejak halving, hari ke-{now['days_since_top']} sejak puncak. "
            f"Tiga siklus sebelumnya dasarnya jatuh {span} hari setelah puncak, turunnya {drops}. "
            "Tiga titik data bukan hukum alam: turunnya tiap siklus juga makin dangkal."
        )
        lines.append("")
    return lines
