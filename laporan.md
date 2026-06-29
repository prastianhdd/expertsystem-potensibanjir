# LAPORAN SISTEM PAKAR PERINGATAN BANJIR

## Metode: Mamdani Fuzzy Inference System
**Referensi:** Tuah, Lestari, Parhusip (2025) — Rancang Bangun Alat Monitoring dan Peringatan Banjir

---

## 1. PENDAHULUAN

Sistem Pakar Peringatan Banjir adalah program berbasis CLI yang mendiagnosis potensi banjir berdasarkan tiga parameter lingkungan:

1. **Jarak sensor ke muka air** (cm) — seberapa dekat air dengan batas daratan
2. **Kenaikan air** (cm/menit) — kecepatan perubahan tinggi muka air
3. **Curah hujan** (mm) — intensitas hujan saat itu

Ketiga parameter diproses menggunakan **Mamdani Fuzzy Inference System** dengan alur:

```
Input Crisp → Fuzzifikasi → Evaluasi Rules (MIN) → Agregasi (MAX) → Defuzzifikasi (Centroid) → Output Risiko (%)
```

Output berupa persentase risiko banjir (0–100%), label linguistik (Sangat Rendah s/d Sangat Tinggi), serta peringatan jika >= 75%.

---

## 2. KNOWLEDGE BASE (Base Pengetahuan)

### 2.1 Variabel Input Fuzzy

#### a) Jarak Sensor ke Muka Air (cm)
Domain: [0, 210]

| Himpunan | Tipe MF | Parameter | Keterangan |
|---|---|---|---|
| Bahaya | Trapesium | [0, 0, 100, 160] | Air tinggi, dekat/melewati batas aman |
| Waspada | Trapesium | [110, 150, 170, 200] | Air menengah, mulai waspada |
| Aman | Trapesium | [180, 200, 210, 210] | Air masih jauh, kondisi aman |

> **Catatan:** Makin kecil nilai jarak = makin tinggi air = makin berbahaya.

#### b) Kenaikan Air (cm/menit)
Domain: [-6, 6]

| Himpunan | Tipe MF | Parameter | Keterangan |
|---|---|---|---|
| Turun | Segitiga | [-6, -6, 0] | Air surut |
| Stabil | Segitiga | [-5, 0, 5] | Air tidak berubah signifikan |
| Naik | Segitiga | [0, 6, 6] | Air naik |

> **Catatan:** Negatif = air turun, positif = air naik.

#### c) Curah Hujan (mm)
Domain: [0, 150]

| Himpunan | Tipe MF | Parameter | Keterangan |
|---|---|---|---|
| Ringan | Trapesium | [0, 0, 40, 60] | Hujan kecil / tidak hujan |
| Lebat | Trapesium | [40, 60, 90, 110] | Hujan deras |
| Sangat Lebat | Trapesium | [90, 110, 150, 150] | Hujan sangat deras |

### 2.2 Variabel Output

#### Risiko Banjir (%)
Domain: [0, 100]

| Himpunan | Tipe MF | Parameter |
|---|---|---|
| Rendah | Segitiga | [0, 0, 50] |
| Sedang | Segitiga | [25, 50, 75] |
| Tinggi | Segitiga | [50, 100, 100] |

---

## 3. FUZZY RULES (27 Rules)

Rules menggunakan operasi **AND** (irisan / MIN) untuk menghubungkan kondisi-kondisi dalam IF. Setiap rule mengisi ketiga indikator (jarak air + kenaikan air + curah hujan), sehingga semua kombinasi 3 × 3 × 3 = 27 tercakup.

### 3.1 Kelompok Bahaya (air tinggi / dekat batas)

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R01 | Bahaya | Naik | Sangat Lebat | Tinggi |
| R02 | Bahaya | Naik | Lebat | Tinggi |
| R03 | Bahaya | Naik | Ringan | Tinggi |
| R04 | Bahaya | Stabil | Sangat Lebat | Tinggi |
| R05 | Bahaya | Stabil | Lebat | Tinggi |
| R06 | Bahaya | Stabil | Ringan | Tinggi |
| R07 | Bahaya | Turun | Sangat Lebat | Tinggi |
| R08 | Bahaya | Turun | Lebat | Sedang |
| R09 | Bahaya | Turun | Ringan | Sedang |

### 3.2 Kelompok Waspada (air menengah)

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R10 | Waspada | Naik | Sangat Lebat | Tinggi |
| R11 | Waspada | Naik | Lebat | Tinggi |
| R12 | Waspada | Naik | Ringan | Sedang |
| R13 | Waspada | Stabil | Sangat Lebat | Sedang |
| R14 | Waspada | Stabil | Lebat | Sedang |
| R15 | Waspada | Stabil | Ringan | Rendah |
| R16 | Waspada | Turun | Sangat Lebat | Sedang |
| R17 | Waspada | Turun | Lebat | Rendah |
| R18 | Waspada | Turun | Ringan | Rendah |

### 3.3 Kelompok Aman (air masih jauh / normal)

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R19 | Aman | Naik | Sangat Lebat | Tinggi |
| R20 | Aman | Naik | Lebat | Sedang |
| R21 | Aman | Naik | Ringan | Rendah |
| R22 | Aman | Stabil | Sangat Lebat | Sedang |
| R23 | Aman | Stabil | Lebat | Rendah |
| R24 | Aman | Stabil | Ringan | Rendah |
| R25 | Aman | Turun | Sangat Lebat | Rendah |
| R26 | Aman | Turun | Lebat | Rendah |
| R27 | Aman | Turun | Ringan | Rendah |

---

## 4. INFERENCE ENGINE (Mesin Inferensi)

Proses inferensi Mamdani terdiri dari 4 tahap:

### 4.1 Fuzzifikasi

Nilai crisp (numerik) dikonversi ke derajat keanggotaan (μ) untuk setiap himpunan fuzzy menggunakan fungsi keanggotaan **segitiga** dan **trapesium**.

**Fungsi Segitiga** (a, b, c):
```
μ(x) = 0                          jika x ≤ a atau x ≥ c
μ(x) = (x - a) / (b - a)         jika a < x ≤ b
μ(x) = (c - x) / (c - b)         jika b < x < c
μ(x) = 1                          jika x = b
```

**Fungsi Trapesium** (a, b, c, d):
```
μ(x) = 0                          jika x ≤ a atau x ≥ d
μ(x) = (x - a) / (b - a)         jika a < x < b
μ(x) = 1                          jika b ≤ x ≤ c
μ(x) = (d - x) / (d - c)         jika c < x < d
```

### 4.2 Evaluasi Rules (Implikasi MIN)

Setiap rule dievaluasi dengan operator AND (irisan):
```
α = min(μ_A, μ_B, μ_C)
```

Kemudian fungsi keanggotaan output dipotong (_clipping_) pada derajat α tersebut.

### 4.3 Agregasi (MAX)

Semua output yang sudah di-clipping digabungkan menggunakan operator OR (gabungan):
```
μ_agregat(x) = max(μ_rule1(x), μ_rule2(x), ..., μ_rulen(x))
```

### 4.4 Defuzzifikasi (Centroid)

Nilai crisp akhir dihitung dengan metode centroid / center of area:

```
Risiko = Σ(xi × μ(xi)) / Σ(μ(xi))
```

dengan xi = {0, 1, 2, ..., 100} (diskrit, step 1).

### 4.5 Ambang Peringatan

- **Threshold:** 75%
- Jika risiko ≥ 75%, sistem mengeluarkan peringatan **BAHAYA BANJIR!**
- Jika < 75%, status aman/waspada sesuai level risiko.

---

## 5. STRUKTUR PROGRAM

```
Sistem Pakar/
├── src/
│   ├── base.yaml          ← Knowledge Base (variabel, MF, rules, saran)
│   ├── fuzzy.py           ← Engine: FuzzySet, MamdaniFIS, centroid
│   └── main.py            ← CLI menu: diagnosa, variabel, rules, simulasi
├── base.txt               ← Dokumentasi mentah
├── laporan.md             ← Laporan ini
└── CLAUDE.md
```

### 5.1 base.yaml

Berisi seluruh data pengetahuan:
- `variabel_input`: definisi 3 variabel input + membership functions
- `variabel_output`: definisi output risiko banjir + MF
- `rules`: 29 rule fuzzy IF-THEN
- `threshold_alert`: 75%
- `saran`: teks saran tiap level risiko

### 5.2 fuzzy.py — Engine

**Class FuzzySet:**
- `derajat(x)` → hitung μ untuk segitiga/trapesium
- Anti-simetris untuk titik batas (a==b, b==c)

**Class MamdaniFIS:**
- `fuzzify(nama_var, nilai)` → clamp + hitung μ tiap himpunan
- `evaluasi_rules(fuzzified)` → AND = MIN untuk tiap rule
- `agregasi(rule_results)` → MAX dari clipping di [0..100]
- `defuzzify(agregat)` → centroid diskrit
- `diagnosa(jarak, kenaikan, hujan)` → pipeline lengkap, return dict detail

### 5.3 main.py — CLI

6 menu:
1. **Diagnosa Risiko Banjir** — input 3 parameter, tampilkan hasil detail
2. **Lihat Variabel Fuzzy** — MF parameters tabel
3. **Lihat Semua Rule** — 29 rules dalam tabel
4. **Ambang Peringatan & Saran** — threshold + saran tiap level
5. **Simulasi (Demo Acak)** — generate random input batch
6. **Keluar**

Output diagnosa meliputi:
- Input crisp + label fuzzy
- Derajat fuzzifikasi tiap himpunan aktif
- Rule aktif + nilai clipping
- Grafik ASCII agregasi output
- Progress bar risiko + threshold marker
- Level risiko + saran
- Peringatan jika ≥ 75%

---

## 6. CONTOH KASUS

### Kasus 1: Air dekat batas (jarak=130, naik=2, hujan=80)
```
Jarak Air:    130.0 cm   → Bahaya (μ=0.5) + Waspada (μ=0.5)
Kenaikan Air:   2.0 cm   → Stabil (μ=0.6) + Naik (μ=0.3333)
Curah Hujan:   80.0 mm   → Lebat (μ=1.0)

Rule Aktif: R05 (Tinggi, clip=0.5), R14 (Sedang, clip=0.5)
Risiko: 65.7% → Level: Sedang
Alert: OK (di bawah 75%)
```

### Kasus 2: Aman (jarak=200, kenaikan=0, hujan=5)
```
Jarak Air:    200.0 cm   → Aman (μ=1.0)
Kenaikan Air:   0.0 cm   → Stabil (μ=1.0)
Curah Hujan:    5.0 mm   → Ringan (μ=1.0)

Rule Aktif: R24 (Rendah, clip=1.0)
Risiko: 16.3% → Level: Rendah
Alert: OK
```

### Kasus 3: Ekstrem (jarak=20, naik=5, hujan=120)
```
Jarak Air:     20.0 cm   → Bahaya (μ=1.0)
Kenaikan Air:   5.0 cm   → Naik (μ=0.8333)
Curah Hujan:  120.0 mm   → Sangat Lebat (μ=1.0)

Rule Aktif: R01 (Tinggi, clip=0.8333)
Risiko: 83.2% → Level: Tinggi
Alert: !! PERINGATAN! Risiko >= 75%
```

---

## 7. KESIMPULAN

1. **Sistem** mengubah sistem pakar teknisi laptop (forward chaining) menjadi sistem peringatan banjir (Mamdani fuzzy)
2. **Knowledge Base** mencakup 3 variabel input dengan total 9 himpunan fuzzy (3 + 3 + 3), 1 variabel output dengan 3 himpunan, dan 27 rule inferensi
3. **Metode Mamdani** diimplementasikan dengan 4 tahap: fuzzifikasi → implikasi MIN → agregasi MAX → defuzzifikasi centroid
4. **Output** berupa persentase risiko (0–100%), label linguistik, dan peringatan otomatis jika ≥ threshold 75%
5. **Saran penanganan** disediakan untuk 5 level risiko: Sangat Rendah, Rendah, Sedang, Tinggi, Sangat Tinggi
6. **Simulasi acak** disediakan untuk demonstrasi tanpa data sensor real

---
*Dibuat: Juni 2026*
*Source: github.com/...*
