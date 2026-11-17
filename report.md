# Laporan skor beli v2 — BTC & HYPE

Dibikin 2026-11-17 02:01 UTC. Buat Andreas, bukan saran buat orang lain.

Gue kunci aturannya dulu di `config.toml`, baru habis itu mesin ini ngitung. Ambang nggak digeser setelah angkanya keluar. Kalau hasil v2 jelek, ya gue tulis jelek.

## Skor hari ini

USD/IDR 18.126. Dominasi BTC 58,6%. Stablecoin $286,4M (2026-11-17).

### BTC

Harga $64.749 (Rp 1,17M). ATH $124.659, drawdown 48,1%. Harga ini candle yang belum tutup.

- F&G 12 (Extreme Fear). Nggak masuk skor sendirian.
- 200DMA $72.854. Cuma buat lihat skor v1, nggak dipakai v2.
- Funding rata-rata 7H +0,0037% per interval.
- ETF 5 print (lag 1 hari) -$932,9jt.
- Skor v2 **3** (drawdown 2, funding 0, ETF 1) → **2x** → tranche **Rp 60jt**.
- Skor v1 (pembanding) 3: F&G 1, di bawah 200DMA 1, drawdown 1.
- OI terakhir $1,96M (2026-11-16).

### HYPE

Harga $69,23 (Rp 1,25jt). ATH $97,27, drawdown 28,8%. Harga ini candle yang belum tutup.

- F&G 12 (Extreme Fear). Nggak masuk skor sendirian.
- 200DMA $69,48. Cuma buat lihat skor v1, nggak dipakai v2.
- Funding rata-rata 7H +0,0009% per interval.
- ETF 5 print (lag 1 hari) n/a.
- Invalidation close < $60: nggak nyala.
- Skor v2 **2** (drawdown 2, funding 0, ETF 0) → **1,5x** → tranche **Rp 11,25jt**.
- Skor v1 (pembanding) 3: F&G 1, di bawah 200DMA 1, drawdown 1.
- OI terakhir $1,32M (2026-11-17).

Cek silang CoinGecko (bukan sumber backtest): BTC CoinGecko $64709 vs DB 64748.92; HYPE CoinGecko $69.2 vs DB 69.23.


## Aturan, dikunci sebelum tes

v2 buang 200DMA. F&G sendirian juga nggak dapat poin. Intinya drawdown dari ATH.

- Drawdown < 25,0%: 0 poin, tranche tetap 1x.
- Drawdown 25,0% sampai di bawah 50,0%: 2 poin (tranche 1,5x).
- Drawdown ≥ 50,0%: 3 poin (angka bulat, bukan hasil dioptimasi). Ini sudah tranche 2x.
- Funding rata-rata 7 hari negatif: +1, cuma kalau drawdown sudah ≥ 25% dan minimal ada 4 hari data di jendela itu.
- BTC saja: F&G di bawah 20 DAN aliran ETF 5 print antara keluar $500jt dan belum tembus $1M: +1, juga cuma kalau drawdown sudah ≥ 25%. Aliran yang dipakai di-lag 1 hari.
- Aliran ETF 5 print keluar ≥ $1M: nggak dapat poin. Cuma bendera kapitulasi. Drawdown-nya nggak gue batalkan, karena yang kebukti di dua siklus cuma drawdown.
- Pengali: skor 0–1 → 1x, skor 2 → 1,5x, skor ≥ 3 → 2x. Mentok 2x.
- Dasar DCA: BTC Rp 30jt dan HYPE Rp 7,5jt tiap 14 hari. Skor cuma ngubah pengali, bukan nyuruh stop beli BTC.
- HYPE daily close di bawah $60: bendera invalidation, tranche HYPE hari itu 0. Besoknya kalau nutup lagi di atas level itu, belinya boleh nyala lagi. Bukan larangan seumur hidup (harga listing HYPE jauh di bawah $60).
- ETF nggak dipakai buat HYPE. Priornya soal BTC.

## Temuan v1 yang jadi alasan (bukan hitungan ulang)

Ini angka laporan lama. Dipakai buat milih aturan, terus ditaruh di sini biar lo lihat v2 dibanding apa.

- **v1 skor ≥ 3:** median 90H -4,1% vs baseline +3,9%.
- **F&G < 20 sendirian:** median 90H +0,2% vs baseline +3,7%, dan 180H-nya lebih jelek.
- **Harga di bawah 200DMA:** nggak ada edge.
- **Drawdown dari ATH > 25%:** satu-satunya yang ngalahin baseline di kedua siklus, median 90H +7,6% vs +3,7%.
- **Funding 7H < 0:** kuat cuma di siklus 2018–21: +14,6% vs baseline +6,9%.
- **F&G < 20 dan ETF 5H keluar > $500jt:** n=8, median +20,9%, menang 75%. Menarik, tapi sampelnya tipis.
- **ETF 5H keluar > $1M sendirian:** bearish, median -11%.

## Cara ngitungnya

Sinyal dihitung pas hari pertama dia nyala, terus diam 14 hari biar satu jurang harga nggak kehitung puluhan kali. Sinyal yang cuma nyala beberapa hari tetap ketangkap. Baseline itu aturan yang sama kalau syaratnya selalu benar, jadi jadwalnya beli buta tiap 14 hari. Return 30/90/180 hari itu close beli ke close pertama pada atau setelah tanggal itu. Kalau jaraknya lebih dari seminggu dari target, kejadiannya dibuang.

Dalam sampel = tanggal beli sampai 31 Des 2021. Luar sampel = 1 Jan 2022 sampai sekarang. Siklusnya ikut tanggal beli, bukan tanggal return-nya. Jujur: v1 sudah lihat dua siklus itu, jadi ini bukan eksperimen buta. Yang luar sampel cuma ngecek apakah polanya masih ada setelah 2021, dengan ambang yang nggak gue utak-atik.

Backtest nggak memakai candle UTC hari ini kalau candle-nya belum tutup. Skor hari ini boleh pakai harga terakhir, dan gue tandain kalau masih partial.

† artinya n di bawah 20. Jangan dibaca sebagai edge.

Satuan: `jt` juta (10^6), `M` miliar (10^9). $500jt = 500 juta dolar. $1M = 1 miliar dolar.

## BTC

Harga 2017-08-17 → 2026-11-17 (3.380 hari). Funding 2020-01-01 → 2026-11-17 (2.513 hari). F&G 3208 hari. ETF 731 hari sampai 2026-11-16.

### v2 vs baseline vs v1

| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih | n 2018–21 | Median 2018–21 | n 2022+ | Median 2022+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline, beli tiap 14 hari | 226 | 53,1% | +2,5% | +2,5% | 0,0% | 105 | +0,2% | 121 | +2,7% |
| v1 skor ≥ 3 | 42 | 50,0% | +0,1% | +2,5% | -2,4% | 24 | +4,8% | 18† | -5,8% |
| Drawdown dari ATH > 25% | 168 | 56,5% | +7,6% | +2,5% | +5,1% | 88 | +6,9% | 80 | +8,1% |
| v2 tranche ≥ 1,5x | 168 | 56,5% | +7,6% | +2,5% | +5,1% | 88 | +6,9% | 80 | +8,1% |
| v2 tranche 2x | 116 | 54,3% | +4,2% | +2,5% | +1,7% | 63 | +7,8% | 53 | +1,8% |

### Bacaan

Baseline median 90H +2,5% (n=226). v1 skor ≥ 3 median +0,1% (n=42), di 2022+ -5,8% (n=18) lawan baseline +2,7%.

Drawdown > 25% median +7,6% (n=168), 2018–21 +6,9% (n=88), 2022+ +8,1% (n=80) lawan baseline 2022+ +2,7%. v2 ≥ 1,5x median +7,6% (n=168, 2022+ +8,1%). v2 2x median +4,2% (n=116, 2022+ +1,8% lawan baseline +2,7%). Di luar sampel, pengali 2x nggak ngalahin beli buta. Yang masih di atas baseline di dua siklus cuma drawdown 25% / tranche 1,5x.

F&G < 20 sendirian median 180H -9,1% (90H +0,2%, n=50). Funding 7H negatif (arsipnya mulai 2020, jadi kolom 2018–21 cuma 2020–21): +67,3% (n=8), 2022+ -2,1% (n=22). Kombo ETF sempit nyala 11 hari, setelah dedupe yang punya return 90H tinggal n=5, median 90H +15,6%, median 180H -14,5%.

DCA v2 kelipatan 5,74x atas modal Rp 10,99M. DCA 1x kelipatan 4,95x atas modal Rp 6,96M.

### Komponen, biar kelihatan yang mana yang sebenarnya kerja

| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih | n 2018–21 | Median 2018–21 | n 2022+ | Median 2022+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 skor ≥ 3 | 42 | 50,0% | +0,1% | +2,5% | -2,4% | 24 | +4,8% | 18† | -5,8% |
| F&G < 20 sendirian | 50 | 52,0% | +0,2% | +2,5% | -2,3% | 29 | +0,7% | 21 | 0,0% |
| Harga di bawah 200DMA | 116 | 51,7% | +2,1% | +2,5% | -0,4% | 53 | +3,8% | 63 | -1,0% |
| Drawdown dari ATH > 25% | 168 | 56,5% | +7,6% | +2,5% | +5,1% | 88 | +6,9% | 80 | +8,1% |
| Drawdown dari ATH ≥ 50% | 102 | 56,9% | +7,6% | +2,5% | +5,2% | 60 | +1,8% | 42 | +10,4% |
| Funding rata-rata 7H < 0 | 30 | 60,0% | +18,4% | +2,5% | +15,9% | 8† | +67,3% | 22 | -2,1% |
| F&G < 20 dan ETF 5H keluar $500jt–$1M | 5† | 80,0% | +15,6% | +2,5% | +13,1% | 0 | — | 5† | +15,6% |
| ETF 5H keluar ≥ $1M | 15† | 33,3% | -12,1% | +2,5% | -14,6% | 0 | — | 15† | -12,1% |

### Median 30H dan 180H

| Sinyal | n 90H | Median 30H | Median 90H | Median 180H |
| --- | ---: | ---: | ---: | ---: |
| Baseline, beli tiap 14 hari | 226 | +0,8% | +2,5% | +9,4% |
| v1 skor ≥ 3 | 42 | +2,1% | +0,1% | -9,1% |
| F&G < 20 sendirian | 50 | +2,1% | +0,2% | -9,1% |
| Harga di bawah 200DMA | 116 | +1,5% | +2,1% | +5,5% |
| Drawdown dari ATH > 25% | 168 | +1,7% | +7,6% | +19,3% |
| Funding rata-rata 7H < 0 | 30 | +5,0% | +18,4% | +27,2% |
| F&G < 20 dan ETF 5H keluar $500jt–$1M | 5† | +4,3% | +15,6% | -14,5% |
| ETF 5H keluar ≥ $1M | 15† | -4,0% | -12,1% | -16,7% |
| v2 tranche ≥ 1,5x | 168 | +1,7% | +7,6% | +19,3% |
| v2 tranche 2x | 116 | +3,9% | +4,2% | +22,6% |

### Sejak ETF nyala (11 Jan 2024), masih di dalam luar-sampel

| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline, beli tiap 14 hari | 68 | 52,9% | +1,0% | +1,0% | 0,0% |
| v1 skor ≥ 3 | 11† | 45,5% | -9,4% | +1,0% | -10,4% |
| Drawdown dari ATH > 25% | 27 | 55,6% | +15,9% | +1,0% | +14,8% |
| F&G < 20 dan ETF 5H keluar $500jt–$1M | 5† | 80,0% | +15,6% | +1,0% | +14,6% |
| ETF 5H keluar ≥ $1M | 15† | 33,3% | -12,1% | +1,0% | -13,1% |
| v2 tranche ≥ 1,5x | 27 | 55,6% | +15,9% | +1,0% | +14,8% |
| v2 tranche 2x | 11† | 45,5% | -7,8% | +1,0% | -8,9% |

### Tes acak

Null-nya: ambil sejumlah tanggal yang sama dari jadwal beli-buta 14 hari, ulang 1.000 kali, seed 42. p = seberapa sering median acakan itu sama atau lebih tinggi dari sinyal asli. p gede = sinyalnya nggak beda dari beli buta. Return 90 hari masih saling tumpuk, jadi p ini kasar.

| Sinyal | Potongan | n | Median 90H | p |
| --- | --- | ---: | ---: | ---: |
| v2 tranche ≥ 1,5x | semua | 168 | +7,6% | 0,002 |
| v2 tranche ≥ 1,5x | 2022+ | 80 | +8,1% | 0,002 |
| v2 tranche 2x | semua | 116 | +4,2% | 0,214 |
| v2 tranche 2x | 2022+ | 53 | +1,8% | 0,589 |
| v1 skor ≥ 3 | semua | 42 | +0,1% | 0,653 |
| v1 skor ≥ 3 | 2022+ | 18 | -5,8% | 0,907 |
| Drawdown dari ATH > 25% | semua | 168 | +7,6% | 0,002 |
| Drawdown dari ATH > 25% | 2022+ | 80 | +8,1% | 0,002 |

### Simulasi DCA 14 hari

Tiap titik grid, beli pengali × Rp 30jt. Pembandingnya beli 1x terus, termasuk hari HYPE di bawah $60. Kelipatan = nilai akhir ÷ modal yang benar-benar kepake. Ini yang adil, soalnya 2x otomatis naro duit lebih banyak.

| | v2 | DCA 1x |
| --- | ---: | ---: |
| Keputusan grid | 232 | 232 |
| Tranche nol | 0 | 0 |
| Modal | Rp 10,99M | Rp 6,96M |
| Koin | 53,408667 | 29,153303 |
| Harga rata-rata | Rp 205,87jt | Rp 238,74jt |
| Nilai akhir | Rp 63,15M | Rp 34,47M |
| Kelipatan modal | 5,74x | 4,95x |

## HYPE

**Sampel kecil.** HYPE baru ada sehari-hari sejak akhir 2024. n di bawah puluhan itu ilustrasi, bukan bukti. Jangan disamain sama tabel BTC.

Hari dengan close di bawah $60: 573 dari 712 hari. Hari-hari itu tranche-nya 0, jadi nggak masuk baris v2.

Hari tranche naik (pengali ≥ 1,5x, artinya close ≥ $60 dan drawdown sudah masuk): 8 hari, 2026-11-10 sampai 2026-11-17. Kalau rentangnya lebih pendek dari 90 hari, median 90H v2 memang kosong. Bukan datanya ilang.

Harga 2024-12-05 → 2026-11-17 (713 hari). Funding 2024-12-05 → 2026-11-17 (713 hari). F&G 3208 hari. ETF 0 hari.

### v2 vs baseline vs v1

| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih | n 2018–21 | Median 2018–21 | n 2022+ | Median 2022+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline, beli tiap 14 hari | 45 | 66,7% | +28,5% | +28,5% | 0,0% | 0 | — | 45 | +28,5% |
| v1 skor ≥ 3 | 5† | 80,0% | +34,9% | +28,5% | +6,4% | 0 | — | 5† | +34,9% |
| Drawdown dari ATH > 25% | 30 | 70,0% | +42,4% | +28,5% | +13,9% | 0 | — | 30 | +42,4% |
| v2 tranche ≥ 1,5x | 0 | — | — | +28,5% | — | 0 | — | 0 | — |
| v2 tranche 2x | 0 | — | — | +28,5% | — | 0 | — | 0 | — |

### Bacaan

Sampel kecil. Baseline 90H +28,5% dari n=45. v2 ≥ 1,5x n=0, v2 2x n=0. DCA v2 kelipatan 0,96x dari modal Rp 75jt, DCA 1x 2,33x dari modal Rp 382,5jt. 1x ikut beli waktu harga di bawah $60; v2 nggak.

### Komponen, biar kelihatan yang mana yang sebenarnya kerja

| Sinyal | n | Menang 90H | Median 90H | Baseline 90H | Selisih | n 2018–21 | Median 2018–21 | n 2022+ | Median 2022+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 skor ≥ 3 | 5† | 80,0% | +34,9% | +28,5% | +6,4% | 0 | — | 5† | +34,9% |
| F&G < 20 sendirian | 13† | 92,3% | +39,9% | +28,5% | +11,3% | 0 | — | 13† | +39,9% |
| Harga di bawah 200DMA | 11† | 63,6% | +41,8% | +28,5% | +13,2% | 0 | — | 11† | +41,8% |
| Drawdown dari ATH > 25% | 30 | 70,0% | +42,4% | +28,5% | +13,9% | 0 | — | 30 | +42,4% |
| Drawdown dari ATH ≥ 50% | 9† | 100,0% | +94,0% | +28,5% | +65,5% | 0 | — | 9† | +94,0% |
| Funding rata-rata 7H < 0 | 3† | 66,7% | +62,9% | +28,5% | +34,4% | 0 | — | 3† | +62,9% |
| F&G < 20 dan ETF 5H keluar $500jt–$1M | 0 | — | — | +28,5% | — | 0 | — | 0 | — |
| ETF 5H keluar ≥ $1M | 0 | — | — | +28,5% | — | 0 | — | 0 | — |

### Median 30H dan 180H

| Sinyal | n 90H | Median 30H | Median 90H | Median 180H |
| --- | ---: | ---: | ---: | ---: |
| Baseline, beli tiap 14 hari | 45 | +8,8% | +28,5% | +72,8% |
| v1 skor ≥ 3 | 5† | +3,0% | +34,9% | +77,5% |
| F&G < 20 sendirian | 13† | +3,0% | +39,9% | +124,5% |
| Harga di bawah 200DMA | 11† | +9,0% | +41,8% | +112,7% |
| Drawdown dari ATH > 25% | 30 | +13,3% | +42,4% | +102,5% |
| Funding rata-rata 7H < 0 | 3† | +16,1% | +62,9% | +113,1% |
| F&G < 20 dan ETF 5H keluar $500jt–$1M | 0 | — | — | — |
| ETF 5H keluar ≥ $1M | 0 | — | — | — |
| v2 tranche ≥ 1,5x | 0 | — | — | — |
| v2 tranche 2x | 0 | — | — | — |

### Tes acak

Null-nya: ambil sejumlah tanggal yang sama dari jadwal beli-buta 14 hari, ulang 1.000 kali, seed 42. p = seberapa sering median acakan itu sama atau lebih tinggi dari sinyal asli. p gede = sinyalnya nggak beda dari beli buta. Return 90 hari masih saling tumpuk, jadi p ini kasar.

| Sinyal | Potongan | n | Median 90H | p |
| --- | --- | ---: | ---: | ---: |
| v2 tranche ≥ 1,5x | semua | 0 | — | — |
| v2 tranche ≥ 1,5x | 2022+ | 0 | — | — |
| v2 tranche 2x | semua | 0 | — | — |
| v2 tranche 2x | 2022+ | 0 | — | — |
| v1 skor ≥ 3 | semua | 5 | +34,9% | 0,309 |
| v1 skor ≥ 3 | 2022+ | 5 | +34,9% | 0,309 |
| Drawdown dari ATH > 25% | semua | 30 | +42,4% | 0,000 |
| Drawdown dari ATH > 25% | 2022+ | 30 | +42,4% | 0,000 |

### Simulasi DCA 14 hari

Tiap titik grid, beli pengali × Rp 7,5jt. Pembandingnya beli 1x terus, termasuk hari HYPE di bawah $60. Kelipatan = nilai akhir ÷ modal yang benar-benar kepake. Ini yang adil, soalnya 2x otomatis naro duit lebih banyak.

| | v2 | DCA 1x |
| --- | ---: | ---: |
| Keputusan grid | 51 | 51 |
| Tranche nol | 41 | 0 |
| Modal | Rp 75jt | Rp 382,5jt |
| Koin | 56,853570 | 700,1650 |
| Harga rata-rata | Rp 1,32jt | Rp 546.300 |
| Nilai akhir | Rp 72,24jt | Rp 889,69jt |
| Kelipatan modal | 0,96x | 2,33x |

Angka HYPE di atas tetap sampel kecil. Invalidation bikin banyak tranche nol kalau harganya di bawah $60.

## Catatan data

- Harga BTC harian: 3380 bar dari data-api.binance.vision (api.binance.com kena HTTP 451 di region mesin ini, jadi yang kepake mirror data publiknya).
- Funding BTC: 7488 print Binance (arsip bulanan, kosong 1 bulan) sampai 2026-10-31, ditambah 49 print OKX buat nutup bulan yang arsipnya belum terbit. REST futures Binance (fapi) 451.
- HYPE: 713 candle harian + 17080 print funding dari Hyperliquid. OI HYPE hari ini 19028771 koin (~$1,316,752,876).
- Fear & Greed alternative.me: 3208 hari.
- ETF BTC dari Farside langsung (https://farside.co.uk/bitcoin-etf-flow-all-data/): 731 hari.
- Suplai stablecoin DefiLlama: 3276 hari. Ini konteks, bukan komponen skor.
- USD/IDR Yahoo: 2419 hari, buat ngubah tranche ke koin.
- Dominasi BTC CoinGecko hari ini 58.57%. Riwayat dominasi butuh API pro, jadi cuma snapshot.
- OI BTC dari OKX (bukan Binance — endpoint OI futures-nya 451): 1052 hari. OI nggak masuk skor.

## Bukan saran investasi

Ini catatan DCA gue sendiri. Sampelnya terbatas, return 90 hari masih saling tumpuk, dan ETF cuma ada sejak 2024. Jangan naikkin tranche cuma karena satu sel di tabel hijau.
