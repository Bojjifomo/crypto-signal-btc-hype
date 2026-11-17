# Monitor sinyal beli BTC & HYPE

Catatan DCA gue (Andreas). Tiap 14 hari gue tetap beli, skor cuma ngatur pengalinya: BTC dasar Rp 30jt, HYPE dasar Rp 7,5jt, mentok 2x. Bukan robot trading, bukan saran buat orang lain.

HYPE punya bendera invalidation: kalau daily close di bawah $60, tranche HYPE hari itu nol. Besoknya kalau nutup lagi di atas $60, belinya boleh nyala lagi.

## Pasang

Python 3.11 atau lebih baru. Nggak ada API key.

```bash
pip install -r requirements.txt
pytest
```

`pytest` cuma buat tes logika sinyal. Buat jalanin monitornya, stdlib cukup.

## Jalanin

```bash
python -m cryptomonitor fetch      # tarik data ke data/monitor.db
python -m cryptomonitor backtest   # hitung ulang, tulis report.md
python -m cryptomonitor score      # skor hari ini, sekalian segarkan laporan
python -m cryptomonitor all        # fetch + backtest + skor
./run.sh
```

Ambang ada di `config.toml`. Jangan digeser cuma biar tabelnya hijau. Kalau lo ubah, `tests/test_signals.py` yang ngunci angka itu harus diubah juga, dan laporan wajib bilang aturannya beda.

## Skor v2, singkat

v1 (F&G < 20 + di bawah 200DMA + drawdown > 25%, sinyal kalau ketiganya nyala) kalah dari beli buta. v2 buang 200DMA. F&G sendirian juga nggak dapat poin.

- Drawdown dari ATH 25% sampai di bawah 50%: 2 poin → 1,5x
- Drawdown ≥ 50%: 3 poin → 2x
- Funding rata-rata 7 hari negatif: +1, cuma kalau drawdown sudah ≥ 25%
- BTC saja: F&G < 20 dan ETF 5 hari keluar antara $500jt dan $1M: +1, juga cuma kalau drawdown sudah masuk. Alirannya di-lag 1 hari
- ETF keluar ≥ $1M: bendera doang, nggak nambah poin

Angka lengkap, dalam sampel vs luar sampel, sama simulasi DCA ada di `report.md` setelah lo jalanin backtest.

## Data

Semua sumber publik, tanpa kunci:

| Apa | Dari mana |
| --- | --- |
| Harga BTC harian | `data-api.binance.vision` (spot). `api.binance.com` sering HTTP 451 di luar region Binance |
| Funding BTC | Arsip bulanan `data.binance.vision`. Bulan yang belum terbit diisi funding OKX |
| Harga, funding, OI HYPE | `api.hyperliquid.xyz` info |
| Fear & Greed | `api.alternative.me` |
| ETF BTC | `farside.co.uk` pakai user-agent browser. Kalau Cloudflare nolak, jatuh ke CSV `firsthandbitcoin.com` yang total hariannya sama dengan kolom Total Farside. Gagal dua-duanya? Skor tetap jalan, poin ETF cuma nol |
| Stablecoin | DefiLlama. Konteks, bukan komponen skor |
| Dominasi BTC | CoinGecko, snapshot hari ini. Riwayatnya kunci pro |
| USD/IDR | Yahoo `USDIDR=X` |
| OI BTC | OKX. Endpoint OI futures Binance 451 di mesin ini. OI nggak masuk skor |

Satu sumber error nggak membatalkan yang lain.

## Cron

Ini bukan GitHub Actions. Cron biasa di mesin lo:

```cron
# tiap hari 07:15 WIB = 00:15 UTC
15 0 * * * cd /path/ke/repo && mkdir -p logs && /usr/bin/python3 -m cryptomonitor all >> logs/cron.log 2>&1
```

Ganti `/path/ke/repo` dan path `python3` sesuai mesin lo. `data/*.db` sama `logs/` nggak ikut ke git.

## Format angka

Titik buat ribuan, koma buat desimal. `jt` = juta, `M` = miliar. Rp 30jt, Rp 7,5jt, $500jt, $1M, +3,9%.

## Tes

```bash
pytest
```

Tesnya nggak nyentuh jaringan. Yang dicek: skor v2, invalidation HYPE, lag ETF, grid 14 hari, format angka, parser Farside.
