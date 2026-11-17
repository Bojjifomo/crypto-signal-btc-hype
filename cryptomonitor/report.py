"""Laporan bahasa santai. Angka pakai titik ribuan, koma desimal, jt/M."""

from __future__ import annotations

from cryptomonitor import cycle_report
from cryptomonitor.lib import fmt_idr, fmt_number, fmt_pct, fmt_px, fmt_usd, fmt_win

V1_PRIOR = [
    ("v1 skor ≥ 3", "median 90H -4,1% vs baseline +3,9%"),
    ("F&G < 20 sendirian", "median 90H +0,2% vs baseline +3,7%, dan 180H-nya lebih jelek"),
    ("Harga di bawah 200DMA", "nggak ada edge"),
    ("Drawdown dari ATH > 25%", "satu-satunya yang ngalahin baseline di kedua siklus, median 90H +7,6% vs +3,7%"),
    ("Funding 7H < 0", "kuat cuma di siklus 2018–21: +14,6% vs baseline +6,9%"),
    ("F&G < 20 dan ETF 5H keluar > $500jt", "n=8, median +20,9%, menang 75%. Menarik, tapi sampelnya tipis"),
    ("ETF 5H keluar > $1M sendirian", "bearish, median -11%"),
]


def _stat(row: dict, split: str, horizon: int) -> dict:
    return row["stats"][split][horizon]


def _base(row: dict, split: str, horizon: int) -> dict:
    return row["baseline"][split][horizon]


def _excess(row: dict, split: str, horizon: int):
    med = _stat(row, split, horizon)["median"]
    base = _base(row, split, horizon)["median"]
    if med is None or base is None:
        return None
    return med - base


def _cell_n(stat: dict) -> str:
    n = stat["n"]
    text = fmt_number(n, 0)
    if 0 < n < 20:
        return text + "†"
    return text


def render(bundle: dict) -> str:
    lines: list[str] = []
    lines.append("# Laporan sinyal beli & jual — BTC & HYPE")
    lines.append("")
    lines.append(f"Dibikin {bundle['generated']}. Buat Andreas, bukan saran buat orang lain.")
    lines.append("")
    lines.append(
        "Gue kunci aturannya dulu di `config.toml`, baru habis itu mesin ini ngitung. "
        "Ambang nggak digeser setelah angkanya keluar. Kalau hasil v2 jelek, ya gue tulis jelek."
    )
    lines.append("")
    summary = cycle_report.summary_lines(bundle)
    if summary:
        lines.append("## Ringkasan: hari ini ngapain")
        lines.append("")
        lines.extend(summary)
        lines.append("")
    lines.append("## Skor beli hari ini (v2)")
    lines.append("")
    lines.extend(_live_section(bundle))
    lines.append("")
    if bundle.get("cycle"):
        lines.append("## Zona siklus hari ini")
        lines.append("")
        lines.extend(cycle_report.live_lines(bundle))
    lines.append("## Aturan beli v2, dikunci sebelum tes")
    lines.append("")
    lines.extend(_rules_section(bundle["cfg"]))
    lines.append("")
    if bundle.get("cycle"):
        lines.append("## Aturan lapisan siklus (sisi jual)")
        lines.append("")
        lines.extend(cycle_report.rules_lines(bundle["cfg"]))
        lines.append("")
    lines.append("## Temuan v1 yang jadi alasan (bukan hitungan ulang)")
    lines.append("")
    lines.append("Ini angka laporan lama. Dipakai buat milih aturan, terus ditaruh di sini biar lo lihat v2 dibanding apa.")
    lines.append("")
    for name, text in V1_PRIOR:
        lines.append(f"- **{name}:** {text}.")
    lines.append("")
    lines.append("## Cara ngitungnya")
    lines.append("")
    lines.append(
        "Sinyal dihitung pas hari pertama dia nyala, terus diam 14 hari biar satu jurang harga "
        "nggak kehitung puluhan kali. Sinyal yang cuma nyala beberapa hari tetap ketangkap. "
        "Baseline itu aturan yang sama kalau syaratnya selalu benar, jadi jadwalnya beli buta tiap 14 hari. "
        "Return 30/90/180 hari itu close beli ke close pertama pada atau setelah tanggal itu. "
        "Kalau jaraknya lebih dari seminggu dari target, kejadiannya dibuang."
    )
    lines.append("")
    lines.append(
        "Dalam sampel = tanggal beli sampai 31 Des 2021. Luar sampel = 1 Jan 2022 sampai sekarang. "
        "Siklusnya ikut tanggal beli, bukan tanggal return-nya. "
        "Jujur: v1 sudah lihat dua siklus itu, jadi ini bukan eksperimen buta. "
        "Yang luar sampel cuma ngecek apakah polanya masih ada setelah 2021, dengan ambang yang nggak gue utak-atik."
    )
    lines.append("")
    lines.append(
        "Backtest nggak memakai candle UTC hari ini kalau candle-nya belum tutup. "
        "Skor hari ini boleh pakai harga terakhir, dan gue tandain kalau masih partial."
    )
    lines.append("")
    lines.append("† artinya n di bawah 20. Jangan dibaca sebagai edge.")
    lines.append("")
    lines.append("Satuan: `jt` juta (10^6), `M` miliar (10^9). $500jt = 500 juta dolar. $1M = 1 miliar dolar.")
    lines.append("")
    for asset in ("BTC", "HYPE"):
        block = bundle["assets"].get(asset)
        if not block:
            lines.append(f"## {asset}")
            lines.append("")
            lines.append("Belum ada data.")
            lines.append("")
            continue
        lines.extend(_asset_section(asset, block, bundle["cfg"]))
        cyc_block = (bundle.get("cycle") or {}).get(asset)
        if cyc_block:
            lines.extend(cycle_report.asset_lines(asset, cyc_block, bundle["cfg"]))
    lines.append("## Catatan data")
    lines.append("")
    for note in bundle.get("notes") or ["Belum ada catatan fetch."]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## Bukan saran investasi")
    lines.append("")
    lines.append(
        "Ini catatan DCA gue sendiri. Sampelnya terbatas, return 90 hari masih saling tumpuk, "
        "dan ETF cuma ada sejak 2024. Jangan naikkin tranche cuma karena satu sel di tabel hijau. "
        "Sisi jual lebih tipis lagi buktinya: empat puncak siklus, dan indikatornya dipilih orang justru karena cocok sama puncak-puncak itu."
    )
    lines.append("")
    return "\n".join(lines)


def _rules_section(cfg: dict) -> list[str]:
    v2 = cfg["v2"]
    dca = cfg["dca"]
    lines = [
        "v2 buang 200DMA. F&G sendirian juga nggak dapat poin. Intinya drawdown dari ATH.",
        "",
        f"- Drawdown < {fmt_pct(v2['drawdown_core'])[1:]}: 0 poin, tranche tetap 1x.",
        f"- Drawdown {fmt_pct(v2['drawdown_core'])[1:]} sampai di bawah {fmt_pct(v2['drawdown_deep'])[1:]}: "
        f"{v2['drawdown_core_points']} poin (tranche 1,5x).",
        f"- Drawdown ≥ {fmt_pct(v2['drawdown_deep'])[1:]}: {v2['drawdown_deep_points']} poin "
        "(angka bulat, bukan hasil dioptimasi). Ini sudah tranche 2x.",
        "- Funding rata-rata 7 hari negatif: +1, cuma kalau drawdown sudah ≥ 25% dan minimal ada "
        f"{v2['funding_min_obs']} hari data di jendela itu.",
        "- BTC saja: F&G di bawah 20 DAN aliran ETF 5 print antara keluar "
        f"{fmt_usd(v2['etf_outflow_min_usd'])} dan belum tembus {fmt_usd(v2['etf_outflow_cap_usd'])}: +1, "
        "juga cuma kalau drawdown sudah ≥ 25%. Aliran yang dipakai di-lag 1 hari.",
        f"- Aliran ETF 5 print keluar ≥ {fmt_usd(v2['etf_capitulation_usd'])}: nggak dapat poin. Cuma bendera kapitulasi. "
        "Drawdown-nya nggak gue batalkan, karena yang kebukti di dua siklus cuma drawdown.",
        "- Pengali: skor 0–1 → 1x, skor 2 → 1,5x, skor ≥ 3 → 2x. Mentok 2x.",
        f"- Dasar DCA: BTC {fmt_idr(dca['btc_base_idr'])} dan HYPE {fmt_idr(dca['hype_base_idr'])} tiap 14 hari. "
        "Skor cuma ngubah pengali, bukan nyuruh stop beli BTC.",
        f"- HYPE daily close di bawah ${fmt_number(dca['hype_invalidation_close'], 0)}: bendera invalidation, tranche HYPE hari itu 0. "
        "Besoknya kalau nutup lagi di atas level itu, belinya boleh nyala lagi. Bukan larangan seumur hidup "
        "(harga listing HYPE jauh di bawah $60).",
        "- ETF nggak dipakai buat HYPE. Priornya soal BTC.",
    ]
    return lines


def _live_section(bundle: dict) -> list[str]:
    lines = []
    ctx = bundle.get("context") or {}
    if ctx.get("fx"):
        lines.append(f"USD/IDR {fmt_number(ctx['fx'], 0)}. Dominasi BTC { _dom(ctx) }. Stablecoin { _stables(ctx) }.")
        lines.append("")
    for asset in ("BTC", "HYPE"):
        snap = (bundle.get("live") or {}).get(asset)
        if snap is None:
            lines.append(f"**{asset}:** belum ada harga.")
            lines.append("")
            continue
        feature = snap["feature"]
        v2 = snap["v2"]
        v1 = snap["v1"]
        partial = " Harga ini candle yang belum tutup." if snap["partial"] else " Close harian sudah lewat."
        lines.append(f"### {asset}")
        lines.append("")
        lines.append(
            f"Harga {fmt_px(feature.close)} ({fmt_idr(snap.get('price_idr'), 2)}). "
            f"ATH {fmt_px(feature.ath)}, drawdown {fmt_pct(feature.drawdown)[1:]}.{partial}"
        )
        fg = "n/a" if feature.fear_greed is None else str(feature.fear_greed)
        if snap.get("fg_label"):
            fg += f" ({snap['fg_label']})"
        fund = "n/a" if feature.funding_7d is None else fmt_pct(feature.funding_7d, 4)
        etf = "n/a" if feature.etf_5d is None else fmt_usd(feature.etf_5d)
        sma = "n/a" if feature.sma200 is None else fmt_px(feature.sma200)
        lines.append("")
        lines.append(f"- F&G {fg}. Nggak masuk skor sendirian.")
        lines.append(f"- 200DMA {sma}. Cuma buat lihat skor v1, nggak dipakai v2.")
        lines.append(f"- Funding rata-rata 7H {fund} per interval.")
        lines.append(f"- ETF 5 print (lag 1 hari) {etf}.")
        if v2.etf_capitulation:
            lines.append("- Bendera kapitulasi ETF nyala (keluar ≥ $1M). Nggak nambah poin.")
        flag = "NYALA — tranche HYPE 0." if v2.invalidated else "nggak nyala."
        if asset == "HYPE":
            lines.append(f"- Invalidation close < $60: {flag}")
        lines.append(
            f"- Skor v2 **{v2.score}** (drawdown {v2.parts['drawdown']}, "
            f"funding {v2.parts['funding']}, ETF {v2.parts['etf_combo']}) "
            f"→ **{fmt_number(v2.multiplier, 1).replace(',0', '')}x** → tranche **{fmt_idr(snap['tranche'], 2)}**."
        )
        lines.append(
            f"- Skor v1 (pembanding) {v1.score}: F&G {v1.parts['fg']}, di bawah 200DMA {v1.parts['below_sma']}, "
            f"drawdown {v1.parts['drawdown']}."
        )
        if snap.get("oi_usd") is not None:
            lines.append(f"- OI terakhir {fmt_usd(snap['oi_usd'], 2)} ({snap.get('oi_day')}).")
        lines.append("")
    if ctx.get("cg_note"):
        lines.append(ctx["cg_note"])
        lines.append("")
    return lines


def _dom(ctx: dict) -> str:
    if ctx.get("dominance") is None:
        return "n/a"
    return fmt_number(ctx["dominance"], 1) + "%"


def _stables(ctx: dict) -> str:
    if ctx.get("stables") is None:
        return "n/a"
    day = ctx.get("stables_day") or ""
    return f"{fmt_usd(ctx['stables'])} ({day})"


def _asset_section(asset: str, block: dict, cfg: dict) -> list[str]:
    lines = [f"## {asset}"]
    lines.append("")
    if asset == "HYPE":
        lines.append(
            "**Sampel kecil.** HYPE baru ada sehari-hari sejak akhir 2024. "
            "n di bawah puluhan itu ilustrasi, bukan bukti. Jangan disamain sama tabel BTC."
        )
        lines.append("")
        lines.append(
            f"Hari dengan close di bawah ${fmt_number(cfg['dca']['hype_invalidation_close'], 0)}: "
            f"{fmt_number(block['invalidated_days'], 0)} dari {fmt_number(block['n_days'], 0)} hari. "
            "Hari-hari itu tranche-nya 0, jadi nggak masuk baris v2."
        )
        lines.append("")
        if block.get("boost_n"):
            lines.append(
                f"Hari tranche naik (pengali ≥ 1,5x, artinya close ≥ $60 dan drawdown sudah masuk): "
                f"{fmt_number(block['boost_n'], 0)} hari, {block['boost_first']} sampai {block['boost_last']}. "
                "Kalau rentangnya lebih pendek dari 90 hari, median 90H v2 memang kosong. Bukan datanya ilang."
            )
            lines.append("")
        elif block.get("boost_n") == 0:
            lines.append("Belum pernah ada hari di mana tranche HYPE naik di atas 1x.")
            lines.append("")
    cov = block["coverage"]
    lines.append(
        f"Harga {cov['price_first']} → {cov['price_last']} ({fmt_number(cov['price_n'], 0)} hari). "
        f"Funding {cov['funding_first'] or '—'} → {cov['funding_last'] or '—'} "
        f"({fmt_number(cov['funding_n'], 0)} hari). "
        f"F&G {cov['fg_n']} hari. ETF {cov['etf_n']} hari"
        f"{'' if not cov['etf_last'] else ' sampai ' + cov['etf_last']}."
    )
    lines.append("")
    lines.append("### v2 vs baseline vs v1")
    lines.append("")
    lines.append(
        "| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih | n 2018–21 | Median 2018–21 | n 2022+ | Median 2022+ |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in block["rows"]:
        if row["key"] not in {"baseline", "v1_score", "v2_1_5x", "v2_2x", "drawdown"}:
            continue
        lines.append(_main_row(row))
    lines.append("")
    lines.extend(_reading(asset, block))
    lines.append("### Komponen, biar kelihatan yang mana yang sebenarnya kerja")
    lines.append("")
    lines.append("| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih | n 2018–21 | Median 2018–21 | n 2022+ | Median 2022+ |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in block["rows"]:
        if row["key"] in {"baseline", "v2_1_5x", "v2_2x"}:
            continue
        lines.append(_main_row(row))
    lines.append("")
    lines.append("### Median 30H dan 180H")
    lines.append("")
    lines.append("| Sinyal | n 90H | Median 30H | Median 90H | Median 180H |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for row in block["rows"]:
        if row["key"] not in {"baseline", "fg", "below_sma", "drawdown", "funding", "v1_score", "v2_1_5x", "v2_2x", "etf_combo", "etf_capitulation"}:
            continue
        s30 = _stat(row, "all", 30)
        s90 = _stat(row, "all", 90)
        s180 = _stat(row, "all", 180)
        lines.append(
            f"| {row['label']} | {_cell_n(s90)} | {fmt_pct(s30['median'])} | {fmt_pct(s90['median'])} | {fmt_pct(s180['median'])} |"
        )
    lines.append("")
    if asset == "BTC":
        lines.append("### Sejak ETF nyala (11 Jan 2024), masih di dalam luar-sampel")
        lines.append("")
        lines.append("| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for row in block["rows"]:
            if row["key"] not in {"baseline", "v2_1_5x", "v2_2x", "etf_combo", "etf_capitulation", "v1_score", "drawdown"}:
                continue
            stat = _stat(row, "etf", 90)
            base = _base(row, "etf", 90)
            lines.append(
                f"| {row['label']} | {_cell_n(stat)} | {fmt_win(stat['win'])} | {fmt_pct(stat['median'])} | "
                f"{fmt_pct(base['median'])} | {fmt_pct(_excess(row, 'etf', 90))} |"
            )
        lines.append("")
    lines.extend(_shuffle_section(block))
    lines.extend(_dca_section(asset, block))
    return lines


def _reading(asset: str, block: dict) -> list[str]:
    rows = {row["key"]: row for row in block["rows"]}
    base = _stat(rows["baseline"], "all", 90)
    base_oos = _stat(rows["baseline"], "oos", 90)
    v1 = _stat(rows["v1_score"], "all", 90)
    v1_oos = _stat(rows["v1_score"], "oos", 90)
    dd = _stat(rows["drawdown"], "all", 90)
    dd_is = _stat(rows["drawdown"], "is", 90)
    dd_oos = _stat(rows["drawdown"], "oos", 90)
    mid = _stat(rows["v2_1_5x"], "all", 90)
    mid_oos = _stat(rows["v2_1_5x"], "oos", 90)
    top = _stat(rows["v2_2x"], "all", 90)
    top_oos = _stat(rows["v2_2x"], "oos", 90)
    fg = rows["fg"]
    fg180 = _stat(fg, "all", 180)
    fund = rows["funding"]
    fund_is = _stat(fund, "is", 90)
    fund_oos = _stat(fund, "oos", 90)
    combo = rows["etf_combo"]
    combo90 = _stat(combo, "all", 90)
    v2 = block["dca_v2"]
    flat = block["dca_flat"]
    lines = ["### Bacaan", ""]
    if asset == "HYPE":
        lines.append(
            f"Sampel kecil. Baseline 90H {fmt_pct(base['median'])} dari n={fmt_number(base['n'], 0)}. "
            f"v2 ≥ 1,5x n={fmt_number(mid['n'], 0)}, v2 2x n={fmt_number(top['n'], 0)}. "
            f"DCA v2 kelipatan {_multiple(v2)} dari modal {fmt_idr(v2['spent_idr'])}, "
            f"DCA 1x {_multiple(flat)} dari modal {fmt_idr(flat['spent_idr'])}. "
            "1x ikut beli waktu harga di bawah $60; v2 nggak."
        )
        lines.append("")
        return lines
    lines.append(
        f"Baseline median 90H {fmt_pct(base['median'])} (n={fmt_number(base['n'], 0)}). "
        f"v1 skor ≥ 3 median {fmt_pct(v1['median'])} (n={fmt_number(v1['n'], 0)}), "
        f"di 2022+ {fmt_pct(v1_oos['median'])} (n={fmt_number(v1_oos['n'], 0)}) "
        f"lawan baseline {fmt_pct(base_oos['median'])}."
    )
    lines.append("")
    lines.append(
        f"Drawdown > 25% median {fmt_pct(dd['median'])} (n={fmt_number(dd['n'], 0)}), "
        f"2018–21 {fmt_pct(dd_is['median'])} (n={fmt_number(dd_is['n'], 0)}), "
        f"2022+ {fmt_pct(dd_oos['median'])} (n={fmt_number(dd_oos['n'], 0)}) "
        f"lawan baseline 2022+ {fmt_pct(base_oos['median'])}. "
        f"v2 ≥ 1,5x median {fmt_pct(mid['median'])} (n={fmt_number(mid['n'], 0)}, "
        f"2022+ {fmt_pct(mid_oos['median'])}). "
        f"v2 2x median {fmt_pct(top['median'])} (n={fmt_number(top['n'], 0)}, "
        f"2022+ {fmt_pct(top_oos['median'])} lawan baseline {fmt_pct(base_oos['median'])}). "
        "Di luar sampel, pengali 2x nggak ngalahin beli buta. Yang masih di atas baseline di dua siklus cuma drawdown 25% / tranche 1,5x."
    )
    lines.append("")
    lines.append(
        f"F&G < 20 sendirian median 180H {fmt_pct(fg180['median'])} "
        f"(90H {fmt_pct(_stat(fg, 'all', 90)['median'])}, n={fmt_number(_stat(fg, 'all', 90)['n'], 0)}). "
        f"Funding 7H negatif (arsipnya mulai 2020, jadi kolom 2018–21 cuma 2020–21): "
        f"{fmt_pct(fund_is['median'])} (n={fmt_number(fund_is['n'], 0)}), "
        f"2022+ {fmt_pct(fund_oos['median'])} (n={fmt_number(fund_oos['n'], 0)}). "
        f"Kombo ETF sempit nyala {fmt_number(combo['raw_days'], 0)} hari, "
        f"setelah dedupe yang punya return 90H tinggal n={fmt_number(combo90['n'], 0)}, "
        f"median 90H {fmt_pct(combo90['median'])}, median 180H {fmt_pct(_stat(combo, 'all', 180)['median'])}."
    )
    lines.append("")
    lines.append(
        f"DCA v2 kelipatan {_multiple(v2)} atas modal {fmt_idr(v2['spent_idr'], 2)}. "
        f"DCA 1x kelipatan {_multiple(flat)} atas modal {fmt_idr(flat['spent_idr'], 2)}."
    )
    lines.append("")
    return lines


def _main_row(row: dict) -> str:
    all90 = _stat(row, "all", 90)
    is90 = _stat(row, "is", 90)
    oos90 = _stat(row, "oos", 90)
    base90 = _base(row, "all", 90)
    return (
        f"| {row['label']} | {_cell_n(all90)} | {fmt_win(all90['win'])} | {fmt_pct(all90['median'])} | "
        f"{fmt_pct(base90['median'])} | {fmt_pct(_excess(row, 'all', 90))} | "
        f"{_cell_n(is90)} | {fmt_pct(is90['median'])} | {_cell_n(oos90)} | {fmt_pct(oos90['median'])} |"
    )


def _shuffle_section(block: dict) -> list[str]:
    lines = ["### Tes acak", ""]
    lines.append(
        "Null-nya: ambil sejumlah tanggal yang sama dari jadwal beli-buta 14 hari, ulang 1.000 kali, seed 42. "
        "p = seberapa sering median acakan itu sama atau lebih tinggi dari sinyal asli. "
        "p gede = sinyalnya nggak beda dari beli buta. Return 90 hari masih saling tumpuk, jadi p ini kasar."
    )
    lines.append("")
    lines.append("| Sinyal | Potongan | n | Median 90H | p |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for item in block["shuffles"]:
        split = "semua" if item["split"] == "all" else "2022+"
        p = "—" if item["p"] is None else fmt_number(item["p"], 3)
        lines.append(
            f"| {item['label']} | {split} | {fmt_number(item['k'], 0)} | {fmt_pct(item['obs'])} | {p} |"
        )
    lines.append("")
    return lines


def _dca_section(asset: str, block: dict) -> list[str]:
    v2 = block["dca_v2"]
    flat = block["dca_flat"]
    lines = ["### Simulasi DCA 14 hari", ""]
    lines.append(
        f"Tiap titik grid, beli pengali × {fmt_idr(block['base_idr'])}. "
        "Pembandingnya beli 1x terus, termasuk hari HYPE di bawah $60. "
        "Kelipatan = nilai akhir ÷ modal yang benar-benar kepake. "
        "Ini yang adil, soalnya 2x otomatis naro duit lebih banyak."
    )
    lines.append("")
    lines.append("| | v2 | DCA 1x |")
    lines.append("| --- | ---: | ---: |")
    lines.append(f"| Keputusan grid | {fmt_number(v2['decisions'], 0)} | {fmt_number(flat['decisions'], 0)} |")
    lines.append(f"| Tranche nol | {fmt_number(v2['zero_tranche'], 0)} | {fmt_number(flat['zero_tranche'], 0)} |")
    lines.append(f"| Modal | {fmt_idr(v2['spent_idr'], 2)} | {fmt_idr(flat['spent_idr'], 2)} |")
    lines.append(f"| Koin | {_coins(v2['coins'])} | {_coins(flat['coins'])} |")
    lines.append(f"| Harga rata-rata | {fmt_idr(v2['avg_entry_idr'], 2)} | {fmt_idr(flat['avg_entry_idr'], 2)} |")
    lines.append(f"| Nilai akhir | {fmt_idr(v2['value_idr'], 2)} | {fmt_idr(flat['value_idr'], 2)} |")
    lines.append(f"| Kelipatan modal | {_multiple(v2)} | {_multiple(flat)} |")
    lines.append("")
    if v2["skipped_fx"] or flat["skipped_fx"]:
        lines.append(f"Ada tranche yang diskip karena USD/IDR kosong: v2 {v2['skipped_fx']}, 1x {flat['skipped_fx']}.")
        lines.append("")
    if asset == "HYPE":
        lines.append("Angka HYPE di atas tetap sampel kecil. Invalidation bikin banyak tranche nol kalau harganya di bawah $60.")
        lines.append("")
    return lines


def _coins(n: float) -> str:
    if n >= 100:
        return fmt_number(n, 4)
    return fmt_number(n, 6)


def _multiple(sim: dict) -> str:
    spent = sim["spent_idr"]
    value = sim["value_idr"]
    if not spent or value is None:
        return "—"
    return fmt_number(value / spent, 2) + "x"


def console_summary(bundle: dict) -> str:
    lines = [render_live_plain(bundle), ""]
    for asset, block in (bundle.get("cycle") or {}).items():
        heat = block["heat"]
        lines.append(
            f"{asset} zona={cycle_report.ZONES[block['zone']]} panas={heat.score}/{cycle_report.heat_max(asset, bundle['cfg'])} "
            f"value={block['value'].score}/4 jual={fmt_number(heat.sell_fraction * 100, 0)}%"
        )
    lines.append("")
    for asset in ("BTC", "HYPE"):
        block = bundle["assets"].get(asset)
        if not block:
            continue
        lines.append(f"== {asset} median 90H ==")
        for row in block["rows"]:
            if row["key"] not in {"baseline", "v1_score", "drawdown", "v2_1_5x", "v2_2x"}:
                continue
            stat = _stat(row, "all", 90)
            oos = _stat(row, "oos", 90)
            is_ = _stat(row, "is", 90)
            lines.append(
                f"{row['label']}: n={stat['n']} med={fmt_pct(stat['median'])} "
                f"base={fmt_pct(_base(row, 'all', 90)['median'])} "
                f"IS n={is_['n']} {fmt_pct(is_['median'])} "
                f"OOS n={oos['n']} {fmt_pct(oos['median'])}"
            )
        v2 = block["dca_v2"]
        flat = block["dca_flat"]
        lines.append(
            f"DCA v2 {_multiple(v2)} atas modal {fmt_idr(v2['spent_idr'])} | "
            f"1x {_multiple(flat)} atas {fmt_idr(flat['spent_idr'])}"
        )
        lines.append("")
    return "\n".join(lines)


def render_live_plain(bundle: dict) -> str:
    chunks = []
    for asset in ("BTC", "HYPE"):
        snap = (bundle.get("live") or {}).get(asset)
        if not snap:
            chunks.append(f"{asset}: tidak ada data")
            continue
        v2 = snap["v2"]
        feature = snap["feature"]
        flag = " INVALID" if v2.invalidated else ""
        chunks.append(
            f"{asset}{flag} {fmt_px(feature.close)} dd={fmt_pct(feature.drawdown)} "
            f"F&G={feature.fear_greed} fund={fmt_pct(feature.funding_7d, 4) if feature.funding_7d is not None else 'n/a'} "
            f"ETF5={fmt_usd(feature.etf_5d)} skor={v2.score} mult={v2.multiplier} tranche={fmt_idr(snap['tranche'], 2)}"
        )
    return "\n".join(chunks)
