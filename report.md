# Laporan sinyal beli & jual — BTC & HYPE

Dibikin 2026-11-17 06:11 UTC. Buat Andreas, bukan saran buat orang lain.

Gue kunci aturannya dulu di `config.toml`, baru habis itu mesin ini ngitung. Ambang nggak digeser setelah angkanya keluar. Kalau hasil v2 jelek, ya gue tulis jelek.

## Ringkasan: hari ini ngapain

| | BTC | HYPE |
| --- | --- | --- |
| Harga | $64.753 (candle belum tutup) | $69,98 (candle belum tutup) |
| Zona siklus | **AKUMULASI** | **AKUMULASI** |
| Beli, per tranche 14 hari (v2) | **Rp 60jt** (2x) | **Rp 11,25jt** (1,5x) |
| Jual, per tranche 14 hari | **0%**, tahan | **0%**, tahan |
| Skor panas | 0 dari 8 | 0 dari 5 |
| Skor value | 1 dari 4 | 0 dari 4 |
| Level terdekat di atas | $68.007 (+5,0%): 200WMA (value +1 kalau di bawahnya) | $72,96 (+4,3%): Drawdown 25% dari ATH (v2 naik ke 1,5x) |
| Level terdekat di bawah | $62.329 (-3,7%): Drawdown 50% dari ATH (v2 naik ke 2x) | $69,48 (-0,7%): 200DMA |

- **BTC:** Drawdown sudah masuk inti v2. Beli sesuai tranche v2, jangan jual.
- **HYPE:** Drawdown sudah masuk inti v2. Beli sesuai tranche v2, jangan jual.

Beli itu aturan v2 yang lama, nggak berubah. Jual itu lapisan siklus yang baru. Buktinya jauh lebih tipis dari sisi beli (puncak siklus BTC cuma ada 4), baca bagiannya di bawah sebelum dipakai.

## Skor beli hari ini (v2)

USD/IDR 18.255. Dominasi BTC 58,5%. Stablecoin $286,4M (2026-11-17).

### BTC

Harga $64.753 (Rp 1,18M). ATH $124.659, drawdown 48,1%. Harga ini candle yang belum tutup.

- F&G 12 (Extreme Fear). Nggak masuk skor sendirian.
- 200DMA $72.854. Cuma buat lihat skor v1, nggak dipakai v2.
- Funding rata-rata 7H +0,0037% per interval.
- ETF 5 print (lag 1 hari) -$932,9jt.
- Skor v2 **3** (drawdown 2, funding 0, ETF 1) → **2x** → tranche **Rp 60jt**.
- Skor v1 (pembanding) 3: F&G 1, di bawah 200DMA 1, drawdown 1.
- OI terakhir $1,99M (2026-11-16).

### HYPE

Harga $69,98 (Rp 1,28jt). ATH $97,27, drawdown 28,1%. Harga ini candle yang belum tutup.

- F&G 12 (Extreme Fear). Nggak masuk skor sendirian.
- 200DMA $69,48. Cuma buat lihat skor v1, nggak dipakai v2.
- Funding rata-rata 7H +0,0009% per interval.
- ETF 5 print (lag 1 hari) n/a.
- Invalidation close < $60: nggak nyala.
- Skor v2 **2** (drawdown 2, funding 0, ETF 0) → **1,5x** → tranche **Rp 11,25jt**.
- Skor v1 (pembanding) 2: F&G 1, di bawah 200DMA 0, drawdown 1.
- OI terakhir $1,32M (2026-11-17).

Cek silang CoinGecko (bukan sumber backtest): BTC CoinGecko $64704 vs DB 64752.57; HYPE CoinGecko $70.05 vs DB 69.98.


## Zona siklus hari ini

### BTC: AKUMULASI

- Tren: turun (di bawah 200DMA yang turun). Konteks doang, 200DMA nggak punya edge di backtest.
- Mayer (harga ÷ 200DMA) 0,89, persentil 18 dari 4 tahun terakhir.
- MVRV 1,21 (persentil 12 dari 4 tahun terakhir). Realized price kira-kira $53.438. Data on-chain telat 1 hari.
- 200WMA $68.007, harga -4,8% dari situ.
- Ambang klasik: Pi Cycle 0,51 (nyala di 1), harga 0,73x 2YMA (nyala di 5).
- Funding 30H disetahunkan +6,6% (panas di +30%). F&G rata-rata 30H 37 (panas di 75).
- Skor panas **0** dari 8 (nggak ada yang nyala) → nggak jual.
- Skor value **1** dari 4 (di bawah 200WMA 1).

Peta harga BTC. Di tiap level ini ada aturan yang berubah status:

| Harga | Jarak | Level | Sisi |
| ---: | ---: | --- | --- |
| $131.832 | +103,6% | MVRV 2,47 = persentil 95 (panas) | jual |
| $124.659 | +92,5% | ATH | info |
| $121.131 | +87,1% | MVRV 2,27 = persentil 85 (hangat) | jual |
| $105.724 | +63,3% | Mayer 1,45 = persentil 95 (panas) | jual |
| $97.339 | +50,3% | Mayer 1,34 = persentil 85 (hangat) | jual |
| $93.494 | +44,4% | Batas bawah zona jual (di bawah ini skor panas dimatiin) | info |
| $93.494 | +44,4% | Drawdown 25% dari ATH (v2 naik ke 1,5x) | beli |
| $72.854 | +12,5% | 200DMA | info |
| $68.007 | +5,0% | 200WMA (value +1 kalau di bawahnya) | beli |
| **$64.753** | | **harga sekarang** | |
| $62.329 | -3,7% | Drawdown 50% dari ATH (v2 naik ke 2x) | beli |
| $58.283 | -10,0% | Mayer 0,8 (value +1) | beli |
| $53.438 | -17,5% | Realized price, MVRV 1 (value +1 kalau di bawahnya) | beli |

Level jual geser tiap hari (ikut 200DMA, realized price, sama persentilnya). Level beli ikut ATH. Jangan dihafal, lihat lagi pas tanggal tranche.

### HYPE: AKUMULASI

- Tren: naik (di atas 200DMA yang nanjak). Konteks doang, 200DMA nggak punya edge di backtest.
- Mayer (harga ÷ 200DMA) 1,01.
- P/E (market cap ÷ pendapatan holder 30H disetahunkan): 18,6x (persentil 46 riwayatnya sendiri).
- HYPE/BTC: +13,1% dari rata-rata 200 harinya. Konteks, nggak masuk skor.
- Funding 30H disetahunkan +11,7% (panas di +30%). F&G rata-rata 30H 37 (panas di 75).
- Skor panas **0** dari 5 (nggak ada yang nyala) → nggak jual.
- Skor value **0** dari 4 (nggak ada yang nyala).

Peta harga HYPE. Di tiap level ini ada aturan yang berubah status:

| Harga | Jarak | Level | Sisi |
| ---: | ---: | --- | --- |
| $138,96 | +98,6% | Mayer 2,0 (panas) | jual |
| $104,22 | +48,9% | Mayer 1,5 (hangat) | jual |
| $97,27 | +39,0% | ATH | info |
| $72,96 | +4,3% | Batas bawah zona jual (di bawah ini skor panas dimatiin) | info |
| $72,96 | +4,3% | Drawdown 25% dari ATH (v2 naik ke 1,5x) | beli |
| **$69,98** | | **harga sekarang** | |
| $69,48 | -0,7% | 200DMA | info |
| $55,58 | -20,6% | Mayer 0,8 (value +1) | beli |
| $48,64 | -30,5% | Drawdown 50% dari ATH (v2 naik ke 2x) | beli |

Level jual geser tiap hari (ikut 200DMA, realized price, sama persentilnya). Level beli ikut ATH. Jangan dihafal, lihat lagi pas tanggal tranche.

## Aturan beli v2, dikunci sebelum tes

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

## Aturan lapisan siklus (sisi jual)

Ini lapisan baru di atas v2. Tranche beli nggak disentuh. Pilihan pakai persentil datang setelah gue lihat ambang klasik kelewatan puncak 2021 dan 2025. Angkanya (85/95, tangga 5/10/20%) angka bulat yang ditulis di `config.toml` sebelum event study dan simulasi dijalankan, dan nggak digeser sesudahnya.

Skor panas BTC (maks 8):

- MVRV di persentil ≥ 85 dari 4 tahun terakhir: 1 poin. Persentil ≥ 95: 2 poin.
- Mayer multiple, aturan persentil yang sama: 1 atau 2 poin.
- Ambang klasik (MVRV ≥ 3,5, Pi Cycle nyilang, atau harga ≥ 5x 2YMA): 2 poin. Terakhir nyala 2021.
- Funding rata-rata 30 hari ≥ 30% setahun: 1 poin.
- F&G rata-rata 30 hari ≥ 75: 1 poin.

Skor panas HYPE (maks 5, eksperimental): Mayer ≥ 1,5 dapat 1, ≥ 2,0 dapat 2. P/E di persentil ≥ 85 riwayatnya sendiri dapat 1. Funding dan F&G sama kayak BTC. HYPE belum punya riwayat 4 tahun, jadi Mayer-nya pakai ambang tetap.

- Kenapa persentil: puncak tiap siklus makin rendah. Nov 2021 dan Okt 2025 nggak pernah nyentuh ambang klasik. Persentil 4 tahun (satu siklus halving) cuma pakai data sebelum hari itu.
- Skor panas dimatiin kalau drawdown sudah ≥ 25%. Satu hari nggak boleh sekaligus beli 1,5x dan jual.
- Tangga jual, porsi dari koin yang masih dipegang, sekali per tanggal tranche 14 hari: skor ≥ 2 → 5%, skor ≥ 4 → 10%, skor ≥ 6 → 20%.
- DCA dasar tetap jalan waktu skor panas nyala. Yang dijual itu tumpukan lama, bukan jadwal belinya.
- Skor value (maks 4, konteks, bukan pengali): drawdown ≥ 50%, Mayer < 0,8, harga di bawah 200WMA, MVRV < 1.
- Zona: AKUMULASI DALAM kalau drawdown ≥ 50% atau skor value ≥ 2. AKUMULASI kalau drawdown ≥ 25%. DISTRIBUSI kalau skor panas ≥ 2, DISTRIBUSI KUAT kalau ≥ 4. Sisanya NETRAL.

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

## Lapisan siklus BTC: buktinya

Harga 2010-07-18 → 2026-11-16: CoinMetrics sampai Binance mulai (Agu 2017), Binance sesudahnya. Kejadian dihitung dari 2013-01-01, cara dedupe 14 harinya sama kayak v2. Funding baru ada 2020 dan F&G 2018, jadi dua komponen itu nggak ikut di siklus awal.

### Sinyal jual: sesudah nyala, harganya ke mana

Buat sinyal jual, yang bagus itu median yang LEBIH RENDAH dari baseline. Titik terendah/tertinggi = median dari harga paling rendah/tinggi dalam 365 hari sesudah sinyal, dibanding harga pas sinyal.

| Sinyal | Kejadian | n 365H | Median 90H | Median 180H | Median 365H | Naik di 365H | Titik terendah 365H | Titik tertinggi 365H | ≤2016 | 2016–20 | 2020–24 | 2024+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline, tiap 14 hari | 362 | 336 | +8,2% | +26,3% | +71,7% | 68,8% | -20,4% | +107,1% | +102,4% (n=92) | +87,9% (n=100) | +71,8% (n=103) | -11,9% (n=41) |
| MVRV ≥ persentil 85 (4 thn) | 53 | 53 | +11,9% | +10,3% | +10,0% | 50,9% | -24,4% | +72,5% | -4,4% (n=3) | +155,3% (n=23) | -10,7% (n=17) | -25,3% (n=10) |
| MVRV ≥ persentil 95 (4 thn) | 20 | 20 | +38,9% | +9,3% | +0,8% | 50,0% | -29,4% | +120,5% | -31,0% (n=1) | +31,0% (n=12) | -21,7% (n=7) | — |
| Mayer ≥ persentil 85 (4 thn) | 50 | 50 | +44,8% | +20,2% | +21,2% | 70,0% | -22,3% | +129,8% | +242,1% (n=7) | +49,0% (n=25) | +20,1% (n=16) | -12,0% (n=2) |
| Mayer ≥ persentil 95 (4 thn) | 14 | 14† | -31,5% | -18,6% | -27,0% | 28,6% | -52,7% | +34,8% | +93,0% (n=2) | -57,7% (n=7) | -5,0% (n=5) | — |
| Ambang klasik (MVRV 3,5 / Pi Cycle / 5x 2YMA) | 38 | 38 | -1,1% | -10,2% | -30,5% | 39,5% | -48,3% | +72,5% | +74,7% (n=23) | -59,3% (n=10) | -23,8% (n=5) | — |
| Funding 30H ≥ 30% setahun | 19 | 19† | -4,4% | +2,4% | +14,0% | 52,6% | -39,3% | +53,9% | — | +438,4% (n=3) | -8,4% (n=16) | — |
| F&G rata-rata 30H ≥ 75 | 18 | 18† | +7,5% | +3,9% | +17,6% | 61,1% | -18,1% | +56,9% | — | -23,8% (n=1) | +28,4% (n=13) | -9,1% (n=4) |
| Tes doang: close < 200DMA, ATH ≤ 365 hari lalu | 105 | 85 | -9,1% | -22,8% | -18,9% | 40,0% | -51,3% | +48,0% | -45,4% (n=19) | +31,4% (n=22) | -30,6% (n=33) | +80,1% (n=11) |
| Skor panas ≥ 2 (jual 5%) | 45 | 45 | +26,4% | +18,3% | +19,2% | 62,2% | -22,2% | +132,6% | +53,8% (n=8) | +88,8% (n=18) | +11,5% (n=16) | -11,2% (n=3) |
| Skor panas ≥ 4 (jual 10%) | 19 | 19† | +5,0% | -9,2% | -10,7% | 36,8% | -33,5% | +53,9% | -4,4% (n=3) | -43,5% (n=6) | +0,4% (n=10) | — |
| Skor panas ≥ 6 (jual 20%) | 9 | 9† | +6,2% | -12,4% | -23,8% | 33,3% | -39,1% | +45,5% | — | -67,3% (n=4) | -4,4% (n=5) | — |

Baseline 365H median +71,7% (n=336). Skor panas ≥ 2 (jual 5%): median +19,2% (n=45), di bawah baseline. Harganya masih lebih tinggi 365 hari kemudian di 62% kejadian, dan di jalan sempat naik median +132,6% dan turun median -22,2%. Skor panas ≥ 4 (jual 10%): median -10,7% (n=19), di bawah baseline. Harganya masih lebih tinggi 365 hari kemudian di 37% kejadian, dan di jalan sempat naik median +53,9% dan turun median -33,5%. Skor panas ≥ 6 (jual 20%): median -23,8% (n=9), di bawah baseline. Harganya masih lebih tinggi 365 hari kemudian di 33% kejadian, dan di jalan sempat naik median +45,5% dan turun median -39,1%.

Sejak halving terakhir, skor panas paling tinggi 3 (2024-11-21, harga $98.317). Di hari ATH (2025-10-06, $124.659) skornya 0. Artinya puncak terakhir itu 'dingin': indikatornya nggak pernah panas, dan lapisan ini NGGAK nangkap puncaknya. Yang ketangkap cuma reli-reli sebelumnya (lihat tabel episode). Kandidat buat puncak dingin, jual pas tren patah (close < 200DMA dalam setahun dari ATH), gue tes tapi nggak gue masukin skor: median 365H sesudahnya -18,9% (n=85), di bawah baseline +71,7%. Kelihatannya kuat, tapi per siklus nggak konsisten (2 dari 4 siklus mediannya malah positif), aturannya gue tambahin SETELAH lihat skor panas kelewatan puncak, dan dia tabrakan sama v2 yang nambah beli di drawdown ≥ 25%. Jadi ini catatan buat diamati, bukan aturan. Kolom per siklus juga nunjukin sinyal persentil 85 sendirian nyala jauh sebelum puncak 2017.

### Episode jual di simulasi

Tanggal jual yang berdekatan (jarak ≤ 60 hari) digabung. Kolom sesudahnya dibanding harga jual rata-rata episode itu.

| Episode | Kali jual | Porsi terbesar | Harga jual rata-rata | 365H kemudian | Terendah 365H | Tertinggi 365H |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2013-03-12 → 2013-04-09 | 3 | 10% | $146,10 | +203,1% | -54,6% | +676,8% |
| 2013-11-05 → 2013-12-03 | 3 | 10% | $688,93 | -45,4% | -53,1% | +64,7% |
| 2017-05-02 → 2018-01-09 | 17 | 20% | $8.445 | -53,0% | -62,0% | +76,5% |
| 2020-12-22 → 2021-04-13 | 9 | 20% | $44.607 | -7,8% | -33,2% | +51,4% |
| 2021-11-09 | 1 | 5% | $66.948 | -76,2% | -76,2% | 0,0% |
| 2024-03-12 → 2024-04-09 | 3 | 10% | $70.405 | +17,3% | -23,4% | +50,8% |
| 2024-11-19 → 2024-12-17 | 3 | 5% | $98.098 | -12,1% | -22,2% | +27,1% |

### Simulasi: tahan terus vs tangga jual

DCA rata $100 tiap 14 hari, dalam USD. Kelipatan = (nilai koin + kas) ÷ modal. Versi ketiga beliin lagi 12,5% dari kas tiap tanggal tranche selama drawdown ≥ 50%. Nggak ada pajak, fee, atau bunga kas.

| Mulai | Strategi | Kelipatan modal | Drawdown terdalam | Kali jual | Harga jual rata-rata | Sisa kas (% nilai akhir) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2013-01-01 | Tahan terus | 119,56x | 83% | 0 | — | 0% |
| 2013-01-01 | Tangga jual, kas didiemin | 27,57x | 68% | 39 | $12.704 | 81% |
| 2013-01-01 | Tangga jual, kas dibeliin lagi pas drawdown ≥ 50% | 207,64x | 77% | 39 | $34.485 | 34% |
| 2018-01-01 | Tahan terus | 3,95x | 75% | 0 | — | 0% |
| 2018-01-01 | Tangga jual, kas didiemin | 3,39x | 52% | 15 | $50.470 | 59% |
| 2018-01-01 | Tangga jual, kas dibeliin lagi pas drawdown ≥ 50% | 6,15x | 52% | 15 | $58.352 | 33% |
| 2022-01-01 | Tahan terus | 1,52x | 49% | 0 | — | 0% |
| 2022-01-01 | Tangga jual, kas didiemin | 1,58x | 41% | 5 | $79.868 | 20% |
| 2022-01-01 | Tangga jual, kas dibeliin lagi pas drawdown ≥ 50% | 1,58x | 41% | 5 | $79.868 | 18% |

Mulai 2013-01-01: tahan 119,56x, tangga jual 27,57x, tangga jual + beli lagi 207,64x. Drawdown terdalam 83% / 68% / 77%. Mulai 2018-01-01: tahan 3,95x, tangga jual 3,39x, tangga jual + beli lagi 6,15x. Drawdown terdalam 75% / 52% / 52%. Mulai 2022-01-01: tahan 1,52x, tangga jual 1,58x, tangga jual + beli lagi 1,58x. Drawdown terdalam 49% / 41% / 41%. Jual terus kasnya didiemin ngalahin tahan-terus di 1 dari 3 titik mulai. Jual terus dibeliin lagi pas drawdown dalam ngalahin di 3 dari 3. Jadi yang ngasih hasil itu pasangan jual-lalu-beli-lagi, bukan jualnya sendiri: kas yang nganggur kalah sama tren naik jangka panjang. Titik mulainya saling tumpuk, ini bukan tes yang independen, dan selisih gede di titik mulai awal datang dari dua-tiga bear market yang turunnya 77–85%. Siklus terakhir turunnya jauh lebih dangkal.

### Sisi beli: sinyal value, riwayat panjang

Di sini yang bagus median yang LEBIH TINGGI dari baseline. Ini konteks buat tranche v2, bukan pengali baru.

| Sinyal | Kejadian | n 365H | Median 90H | Median 180H | Median 365H | Naik di 365H | Titik terendah 365H | Titik tertinggi 365H | ≤2016 | 2016–20 | 2020–24 | 2024+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline, tiap 14 hari | 362 | 336 | +8,2% | +26,3% | +71,7% | 68,8% | -20,4% | +107,1% | +102,4% (n=92) | +87,9% (n=100) | +71,8% (n=103) | -11,9% (n=41) |
| Drawdown ≥ 25% (inti v2) | 276 | 249 | +10,0% | +28,6% | +99,5% | 73,1% | -18,0% | +125,7% | +119,8% (n=85) | +81,1% (n=78) | +101,4% (n=82) | +46,6% (n=4) |
| Drawdown ≥ 50% | 172 | 169 | +8,1% | +35,8% | +95,8% | 82,2% | -17,9% | +134,5% | +119,9% (n=69) | +58,2% (n=54) | +125,3% (n=46) | — |
| Mayer < 0,8 | 76 | 67 | -3,4% | -7,5% | +44,7% | 67,2% | -34,0% | +71,8% | +25,2% (n=20) | +103,9% (n=23) | +23,7% (n=24) | — |
| Harga di bawah 200WMA | 37 | 31 | +24,9% | +55,9% | +127,9% | 100,0% | -5,5% | +157,9% | +155,6% (n=5) | +1.092,1% (n=1) | +110,2% (n=25) | — |
| MVRV < 1 | 50 | 50 | +6,8% | +54,5% | +87,9% | 96,0% | -12,5% | +126,9% | +87,9% (n=24) | +104,4% (n=11) | +48,3% (n=15) | — |
| Skor value ≥ 2 | 90 | 87 | +9,0% | +30,8% | +88,1% | 81,6% | -18,4% | +113,6% | +67,0% (n=32) | +99,1% (n=24) | +75,5% (n=31) | — |
| Skor value ≥ 3 | 43 | 41 | +9,2% | +46,0% | +82,1% | 95,1% | -10,4% | +108,1% | +69,0% (n=16) | +117,5% (n=10) | +48,3% (n=15) | — |

Baseline 365H median +71,7%, naik 69% (n=336). Drawdown ≥ 25% (inti v2) +99,5%, naik 73% (n=249); Drawdown ≥ 50% +95,8%, naik 82% (n=169); Harga di bawah 200WMA +127,9%, naik 100% (n=31); MVRV < 1 +87,9%, naik 96% (n=50); Skor value ≥ 2 +88,1%, naik 82% (n=87); Skor value ≥ 3 +82,1%, naik 95% (n=41). Kejadiannya ngumpul di segelintir bear market, jadi n efektifnya jauh lebih kecil dari yang tertulis.

### Jam siklus (konteks, n=4)

Puncak = close tertinggi dalam 2 tahun setelah halving. Dasar = close terendah sesudah puncak itu sampai halving berikutnya.

| Halving | Puncak | Hari ke puncak | Dasar | Hari puncak → dasar | Turun |
| --- | --- | ---: | --- | ---: | ---: |
| 2012-11-28 | 2013-12-04 ($1.135) | 371 | 2015-01-14 ($175,64) | 406 | 85% |
| 2016-07-09 | 2017-12-16 ($19.103) | 525 | 2018-12-15 ($3.212) | 364 | 83% |
| 2020-05-11 | 2021-11-08 ($67.526) | 546 | 2022-11-21 ($15.781) | 378 | 77% |
| 2024-04-20 | 2025-10-06 ($124.659) | 534 | 2026-06-30 ($58.625), sejauh ini | 267 | 53% |

Sekarang hari ke-941 sejak halving, hari ke-407 sejak puncak. Tiga siklus sebelumnya dasarnya jatuh 364–406 hari setelah puncak, turunnya 77%–85%. Tiga titik data bukan hukum alam: turunnya tiap siklus juga makin dangkal.

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

## Lapisan siklus HYPE: buktinya

**Sampel kecil, satu siklus.** Harga 2024-12-05 → 2026-11-16. Market cap cuma 365 hari terakhir, jadi P/E baru punya persentil belakangan ini. Semua angka di bagian ini ilustrasi, bukan bukti.

### Sinyal jual: sesudah nyala, harganya ke mana

Buat sinyal jual, yang bagus itu median yang LEBIH RENDAH dari baseline. Titik terendah/tertinggi = median dari harga paling rendah/tinggi dalam 90 hari sesudah sinyal, dibanding harga pas sinyal.

| Sinyal | Kejadian | n 90H | Median 90H | Median 180H | Median 365H | Naik di 90H | Titik terendah 90H | Titik tertinggi 90H |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline, tiap 14 hari | 51 | 45 | +28,5% | +72,8% | +75,8% | 66,7% | -15,1% | +45,4% |
| Mayer ≥ 1,5 | 16 | 12† | +7,4% | -32,0% | +77,1% | 58,3% | -22,4% | +32,4% |
| Mayer ≥ 2,0 | 1 | 1† | +15,7% | — | — | 100,0% | -27,6% | +17,5% |
| P/E ≥ persentil 85 riwayatnya | 7 | 7† | +21,9% | +34,6% | — | 100,0% | -16,3% | +56,0% |
| Funding 30H ≥ 30% setahun | 7 | 7† | -26,4% | +60,0% | +12,5% | 28,6% | -50,6% | +17,3% |
| F&G rata-rata 30H ≥ 75 | 3 | 3† | -37,5% | +60,1% | +6,0% | 33,3% | -49,3% | +28,6% |
| Tes doang: close < 200DMA, ATH ≤ 365 hari lalu | 12 | 11† | +41,8% | +112,7% | +117,2% | 63,6% | -19,2% | +52,3% |
| Skor panas ≥ 2 (jual 5%) | 8 | 7† | +8,1% | +60,1% | +1,6% | 71,4% | -26,7% | +28,6% |
| Skor panas ≥ 4 (jual 10%) | 0 | 0 | — | — | — | — | — | — |
| Skor panas ≥ 6 (jual 20%) | 0 | 0 | — | — | — | — | — | — |

Baseline 90H median +28,5% (n=45). Skor panas ≥ 2 (jual 5%): median +8,1% (n=7), di bawah baseline. Harganya masih lebih tinggi 90 hari kemudian di 71% kejadian, dan di jalan sempat naik median +28,6% dan turun median -26,7%. Skor panas ≥ 4 (jual 10%): belum pernah punya kejadian dengan return 90H. Skor panas ≥ 6 (jual 20%): belum pernah punya kejadian dengan return 90H.

Sepanjang riwayatnya, skor panas paling tinggi 3 (2026-05-31, harga $72,05). Di hari ATH (2026-09-22, $97,27) skornya 1. Artinya puncak terakhir itu 'dingin': indikatornya nggak pernah panas, dan lapisan ini NGGAK nangkap puncaknya. Yang ketangkap cuma reli-reli sebelumnya (lihat tabel episode). Kandidat buat puncak dingin, jual pas tren patah (close < 200DMA dalam setahun dari ATH), gue tes tapi nggak gue masukin skor: median 90H sesudahnya +41,8% (n=11), di atas baseline +28,5%. Itu bukan sinyal jual, dan dia tabrakan sama v2 yang justru nambah beli di drawdown ≥ 25%.

### Episode jual di simulasi

Tanggal jual yang berdekatan (jarak ≤ 60 hari) digabung. Kolom sesudahnya dibanding harga jual rata-rata episode itu.

| Episode | Kali jual | Porsi terbesar | Harga jual rata-rata | 365H kemudian | Terendah 365H | Tertinggi 365H |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-12-19 | 1 | 5% | $24,96 | -0,4% | -58,9% | +134,9% |
| 2026-05-21 → 2026-06-18 | 3 | 5% | $63,79 | — | — | — |

### Simulasi: tahan terus vs tangga jual

DCA rata $100 tiap 14 hari, dalam USD. Kelipatan = (nilai koin + kas) ÷ modal. Versi ketiga beliin lagi 12,5% dari kas tiap tanggal tranche selama drawdown ≥ 50%. Nggak ada pajak, fee, atau bunga kas.

| Mulai | Strategi | Kelipatan modal | Drawdown terdalam | Kali jual | Harga jual rata-rata | Sisa kas (% nilai akhir) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2024-12-05 | Tahan terus | 2,13x | 53% | 0 | — | 0% |
| 2024-12-05 | Tangga jual, kas didiemin | 2,10x | 53% | 4 | $62,54 | 12% |
| 2024-12-05 | Tangga jual, kas dibeliin lagi pas drawdown ≥ 50% | 2,10x | 53% | 4 | $62,54 | 12% |

Mulai 2024-12-05: tahan 2,13x, tangga jual 2,10x, tangga jual + beli lagi 2,10x. Drawdown terdalam 53% / 53% / 53%. Jual terus kasnya didiemin ngalahin tahan-terus di 0 dari 1 titik mulai. Jual terus dibeliin lagi pas drawdown dalam ngalahin di 0 dari 1. Satu titik mulai, satu siklus: ini ilustrasi mekanismenya doang.

### Sisi beli: sinyal value, riwayat panjang

Di sini yang bagus median yang LEBIH TINGGI dari baseline. Ini konteks buat tranche v2, bukan pengali baru.

| Sinyal | Kejadian | n 90H | Median 90H | Median 180H | Median 365H | Naik di 90H | Titik terendah 90H | Titik tertinggi 90H |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline, tiap 14 hari | 51 | 45 | +28,5% | +72,8% | +75,8% | 66,7% | -15,1% | +45,4% |
| Drawdown ≥ 25% (inti v2) | 31 | 30 | +42,4% | +102,5% | +97,7% | 70,0% | -14,7% | +75,9% |
| Drawdown ≥ 50% | 9 | 9† | +94,0% | +191,3% | +179,5% | 100,0% | -12,4% | +112,8% |
| Mayer < 0,8 | 7 | 7† | +45,7% | +138,8% | — | 100,0% | -17,3% | +65,9% |
| Harga di bawah 200WMA | 0 | 0 | — | — | — | — | — | — |
| MVRV < 1 | 0 | 0 | — | — | — | — | — | — |
| Skor value ≥ 2 | 6 | 6† | +50,9% | +166,0% | — | 100,0% | -10,5% | +65,4% |
| Skor value ≥ 3 | 0 | 0 | — | — | — | — | — | — |

Baseline 90H median +28,5%, naik 67% (n=45). Drawdown ≥ 25% (inti v2) +42,4%, naik 70% (n=30); Drawdown ≥ 50% +94,0%, naik 100% (n=9); Skor value ≥ 2 +50,9%, naik 100% (n=6). Kejadiannya ngumpul di segelintir bear market, jadi n efektifnya jauh lebih kecil dari yang tertulis.

## Catatan data

- Harga BTC harian: 3380 bar dari data-api.binance.vision (api.binance.com kena HTTP 451 di region mesin ini, jadi yang kepake mirror data publiknya).
- Funding BTC: 7488 print Binance (arsip bulanan, kosong 1 bulan) sampai 2026-10-31, ditambah 49 print OKX buat nutup bulan yang arsipnya belum terbit. REST futures Binance (fapi) 451.
- HYPE: 713 candle harian + 17085 print funding dari Hyperliquid. OI HYPE hari ini 18876746 koin (~$1,321,202,304).
- Fear & Greed alternative.me: 3208 hari.
- ETF BTC dari Farside langsung (https://farside.co.uk/bitcoin-etf-flow-all-data/): 731 hari.
- Suplai stablecoin DefiLlama: 3276 hari. Ini konteks, bukan komponen skor.
- USD/IDR Yahoo: 2419 hari, buat ngubah tranche ke koin.
- Dominasi BTC CoinGecko hari ini 58.45%. Riwayat dominasi butuh API pro, jadi cuma snapshot.
- OI BTC dari OKX (bukan Binance — endpoint OI futures-nya 451): 1052 hari. OI nggak masuk skor.
- CoinMetrics community: 5966 hari harga BTC (dari 2010) + 5966 hari MVRV, terakhir 2026-11-16. Cuma dipakai lapisan siklus, skor v2 nggak nyentuh ini.
- Fundamental HYPE: 690 hari pendapatan holder + 690 hari fee (DefiLlama), 366 hari market cap (CoinGecko gratis cuma kasih 365 hari).

## Bukan saran investasi

Ini catatan DCA gue sendiri. Sampelnya terbatas, return 90 hari masih saling tumpuk, dan ETF cuma ada sejak 2024. Jangan naikkin tranche cuma karena satu sel di tabel hijau. Sisi jual lebih tipis lagi buktinya: empat puncak siklus, dan indikatornya dipilih orang justru karena cocok sama puncak-puncak itu.
