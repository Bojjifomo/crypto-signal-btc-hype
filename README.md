# Monitor sinyal beli & jual BTC & HYPE

Catatan DCA gue (Andreas). Tiap 14 hari gue tetap beli, skor cuma ngatur pengalinya: BTC dasar Rp 30jt, HYPE dasar Rp 7,5jt, mentok 2x. Bukan robot trading, bukan saran buat orang lain.

HYPE punya bendera invalidation: kalau daily close di bawah $60, tranche HYPE hari itu nol. Besoknya kalau nutup lagi di atas $60, belinya boleh nyala lagi.

Ada dua lapis:

- **Skor v2 (beli).** Ngatur pengali tranche. Aturannya dikunci, nggak berubah.
- **Lapisan siklus (jual + konteks value).** Skor panas nentuin kapan mulai jual bertahap, skor value nunjukin seberapa dalam harga sudah murah. Lapisan ini nggak nyentuh tranche v2.

Keluarannya `report.md` (angka dan bukti) dan `dashboard.html` (grafik harga dengan pita zona, buka langsung di browser).

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
python -m cryptomonitor backtest   # hitung ulang, tulis report.md + dashboard.html
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

## Lapisan siklus, singkat

Tiap hari masuk satu zona: AKUMULASI DALAM, AKUMULASI, NETRAL, DISTRIBUSI, atau DISTRIBUSI KUAT.

Skor panas BTC (maks 8):

- MVRV dan Mayer multiple, masing-masing 1 poin di persentil ≥ 85 dari 4 tahun terakhir, 2 poin di persentil ≥ 95
- Ambang klasik (MVRV ≥ 3,5, Pi Cycle, harga ≥ 5x 2YMA): 2 poin
- Funding 30 hari ≥ 30% setahun: 1 poin. F&G rata-rata 30 hari ≥ 75: 1 poin

Skor panas HYPE (maks 5, eksperimental): Mayer ≥ 1,5 / ≥ 2,0, P/E di persentil ≥ 85 riwayatnya, funding, F&G.

Tangga jual, porsi dari koin yang dipegang per tanggal tranche: skor ≥ 2 → 5%, ≥ 4 → 10%, ≥ 6 → 20%. Skor panas dimatiin kalau drawdown sudah ≥ 25%, jadi satu hari nggak pernah sekaligus "beli 1,5x" dan "jual".

Skor value (maks 4, konteks doang): drawdown ≥ 50%, Mayer < 0,8, harga di bawah 200WMA, MVRV < 1.

Yang perlu lo tahu sebelum makai sisi jual:

- Skor panas ≥ 4 punya median return 365 hari negatif di backtest BTC, tapi n-nya belasan dan puncak siklus cuma ada empat.
- Skor panas **nggak nangkap puncak Okt 2025**. Di hari ATH skornya 0. Puncak yang "dingin" lolos.
- Jual lalu kasnya didiemin kalah dari tahan-terus di sebagian besar titik mulai. Yang ngasih hasil di simulasi itu jual lalu beli lagi pas drawdown ≥ 50%.
- HYPE cuma punya satu siklus. Angkanya ilustrasi.

Detail dan tabelnya di `report.md`. Ambang ada di `[cycle]` di `config.toml`, dikunci `tests/test_cycle.py`.

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
| Harga BTC 2010–2017 + MVRV | CoinMetrics community API. Cuma buat lapisan siklus |
| Pendapatan & fee Hyperliquid | DefiLlama. Buat P/E HYPE |
| Market cap HYPE | CoinGecko, 365 hari terakhir |
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

Tesnya nggak nyentuh jaringan. Yang dicek: skor v2, invalidation HYPE, lag ETF, grid 14 hari, format angka, parser Farside, plus lapisan siklus (persentil tanpa lihat masa depan, skor panas, tangga jual, simulasi).
