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

Output berupa persentase risiko banjir (0–100%), label linguistik (Very Low s/d Very High), serta peringatan jika >= 75%.

---

## 2. KNOWLEDGE BASE (Base Pengetahuan)

### 2.1 Variabel Input Fuzzy

#### a) Jarak Sensor ke Muka Air (cm)
Domain: [0, 210]

| Himpunan | Tipe MF | Parameter | Keterangan |
|---|---|---|---|
| Banjir | Segitiga | [0, 0, 145] | Air sudah melampaui batas aman |
| Siaga II | Trapesium | [120, 145, 160, 175] | Mendekati banjir, waspada tinggi |
| Siaga I | Trapesium | [150, 170, 185, 200] | Mulai waspada |
| Normal | Trapesium | [180, 200, 210, 210] | Aman, air masih jauh |

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
| Lebat | Trapesium | [20, 40, 60, 80] | Hujan deras |
| Sangat Lebat | Trapesium | [60, 80, 150, 150] | Hujan sangat deras |

> **Catatan:** Jika curah hujan di bawah 20 mm, dianggap tidak lebat (tidak menjadi faktor penentu dalam rules).

### 2.2 Variabel Output

#### Risiko Banjir (%)
Domain: [0, 100]

| Himpunan | Tipe MF | Parameter |
|---|---|---|
| Very Low | Segitiga | [0, 0, 20] |
| Low | Segitiga | [8, 25, 42] |
| Moderate | Segitiga | [30, 50, 70] |
| High | Segitiga | [55, 70, 85] |
| Very High | Segitiga | [72, 100, 100] |

---

## 3. FUZZY RULES (29 Rules)

Rules menggunakan operasi **AND** (irisan / MIN) untuk menghubungkan kondisi-kondisi dalam IF.

### 3.1 Kelompok Banjir

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R01 | Banjir | Naik | Sangat Lebat | Very High |
| R02 | Banjir | Naik | Lebat | Very High |
| R03 | Banjir | Naik | - | Very High |
| R04 | Banjir | Stabil | Sangat Lebat | Very High |
| R05 | Banjir | Stabil | - | Very High |
| R06 | Banjir | Turun | Lebat | Very High |
| R07 | Banjir | Turun | - | High |

### 3.2 Kelompok Siaga II

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R08 | Siaga II | Naik | Sangat Lebat | Very High |
| R09 | Siaga II | Naik | Lebat | Very High |
| R10 | Siaga II | Naik | - | High |
| R11 | Siaga II | Stabil | Lebat | High |
| R12 | Siaga II | Stabil | - | High |
| R13 | Siaga II | Turun | Lebat | High |
| R14 | Siaga II | Turun | - | Moderate |

### 3.3 Kelompok Siaga I

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R15 | Siaga I | Naik | Sangat Lebat | Very High |
| R16 | Siaga I | Naik | Lebat | High |
| R17 | Siaga I | Naik | - | Moderate |
| R18 | Siaga I | Stabil | Lebat | Moderate |
| R19 | Siaga I | Stabil | - | Low |
| R20 | Siaga I | Turun | Sangat Lebat | Moderate |
| R21 | Siaga I | Turun | Lebat | Low |
| R22 | Siaga I | Turun | - | Low |

### 3.4 Kelompok Normal

| No | Level Air | Kenaikan | Curah Hujan | THEN |
|---|---|---|---|---|
| R23 | Normal | Naik | Sangat Lebat | High |
| R24 | Normal | Naik | Lebat | Moderate |
| R25 | Normal | Naik | - | Low |
| R26 | Normal | Stabil | Sangat Lebat | Low |
| R27 | Normal | Stabil | Lebat | Low |
| R28 | Normal | Stabil | - | Very Low |
| R29 | Normal | Turun | - | Very Low |

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

### Kasus 1: Banjir (jarak=130, naik=2, hujan=80)
```
Jarak Air:    130.0 cm   → Siaga II (μ=0.4) + Banjir (μ=0.1034)
Kenaikan Air:   2.0 cm   → Stabil (μ=0.6) + Naik (μ=0.3333)
Curah Hujan:   80.0 mm   → Sangat Lebat (μ=1.0)

Rule Aktif: R08 (Very High, clip=0.3333), R12 (High, clip=0.4)
Risiko: 78.2% → Level: High
Alert: !! PERINGATAN! Risiko >= 75%
```

### Kasus 2: Aman (jarak=200, kenaikan=0, hujan=5)
```
Jarak Air:    200.0 cm   → Normal (μ=1.0)
Kenaikan Air:   0.0 cm   → Stabil (μ=1.0)
Curah Hujan:    5.0 mm   → (tidak masuk himpunan manapun)

Rule Aktif: R28 (Very Low, clip=1.0)
Risiko: 6.3% → Level: Very Low
Alert: OK
```

### Kasus 3: Ekstrem Banjir (jarak=10, naik=5, hujan=150)
```
Risiko: 90.7% → Level: Very High
Alert: !! PERINGATAN!
```

---

## 7. KESIMPULAN

1. **Sistem** mengubah sistem pakar teknisi laptop (forward chaining) menjadi sistem peringatan banjir (Mamdani fuzzy)
2. **Knowledge Base** mencakup 3 variabel input dengan total 10 himpunan fuzzy, 1 variabel output dengan 5 himpunan, dan 29 rule inferensi
3. **Metode Mamdani** diimplementasikan dengan 4 tahap: fuzzifikasi → implikasi MIN → agregasi MAX → defuzzifikasi centroid
4. **Output** berupa persentase risiko (0–100%), label linguistik, dan peringatan otomatis jika ≥ threshold 75%
5. **Saran penanganan** disediakan untuk 5 level risiko: Very Low, Low, Moderate, High, Very High
6. **Simulasi acak** disediakan untuk demonstrasi tanpa data sensor real

---
*Dibuat: Juni 2026*
*Source: github.com/...*
