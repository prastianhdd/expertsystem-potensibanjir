# SISTEM PAKAR PERINGATAN BANJIR

Sistem pakar berbasis CLI untuk mendiagnosis potensi banjir menggunakan **Mamdani Fuzzy Inference System**.

| Parameter | Nilai |
|---|---|
| Metode | Mamdani Fuzzy (Fuzzify → MIN Implication → MAX Aggregation → Centroid Defuzzify) |
| Input | 3 parameter lingkungan |
| Output | Risiko banjir 0–100% + 5 level linguistik |
| Threshold peringatan | ≥ 75% |
| Total rules | 29 |
| Stack | Python 3 + YAML + Rich |

---

## Alur Inferensi

```
Input Crisp (jarak, kenaikan, curah hujan)
    │
    ▼
┌─────────────────────────────┐
│ 1. FUZZIFIKASI              │
│    hitung μ tiap himpunan   │
│    (segitiga / trapesium)   │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 2. EVALUASI RULES           │
│    AND = MIN(μ1, μ2, ...)   │
│    clipping output di μ_MIN │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 3. AGREGASI                 │
│    OR = MAX dari clipping   │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 4. DEFUZZIFIKASI            │
│    centroid = Σ(x·μ)/Σ(μ)   │
└──────────┬──────────────────┘
           ▼
    Risiko Banjir (%)
    Level + Saran
    Alert jika ≥ 75%
```

---

## Variabel Fuzzy

### Input

| Variabel | Domain | Himpunan |
|---|---|---|
| Jarak Air (cm) | [0, 210] | Banjir / Siaga II / Siaga I / Normal |
| Kenaikan Air (cm/mnt) | [-6, 6] | Turun / Stabil / Naik |
| Curah Hujan (mm) | [0, 150] | (tidak lebat) / Lebat / Sangat Lebat |

### Output

| Variabel | Domain | Himpunan |
|---|---|---|
| Risiko Banjir (%) | [0, 100] | Very Low / Low / Moderate / High / Very High |

### Rules (29)

Tabel lengkap rule ada di menu `Lihat Semua Rule` atau file `laporan.md`.

---

## Struktur Project

```
.
├── src/
│   ├── base.yaml        ← Base pengetahuan (variabel, MF, rules, saran)
│   ├── fuzzy.py         ← Engine Mamdani FIS (FuzzySet, MamdaniFIS)
│   └── main.py          ← CLI menu utama (Rich)
├── laporan.md           ← Dokumentasi lengkap sistem
├── base.txt             ← Dokumentasi mentah (sistem lama)
├── README.md            ← File ini
└── CLAUDE.md            ← Konfigurasi AI assistant
```

---

## Instalasi & Run

### Prasyarat
- Python 3.8+
- pip

### Instalasi

```bash
cd src/
pip install rich pyyaml
```

### Jalankan

```bash
python src/main.py
```

### Menu

```
 1. Diagnosa Risiko Banjir   — input 3 parameter, lihat hasil detail
 2. Lihat Variabel Fuzzy     — membership function tiap variabel
 3. Lihat Semua Rule         — 29 rule IF-THEN
 4. Ambang Peringatan & Saran — threshold + saran tiap level
 5. Simulasi (Demo Acak)     — random input, batch simulasi
 6. Keluar
```

---

## Contoh Penggunaan

### Skenario Banjir

```
Input:
  Jarak Air:     130 cm
  Kenaikan Air:    2 cm/mnt
  Curah Hujan:    80 mm

→ Risiko: 78.2% — Level: High
→ PERINGATAN! Risiko ≥ 75%
→ Saran: Siaga banjir! Pantau terus ketinggian air...
```

### Skenario Aman

```
Input:
  Jarak Air:     200 cm
  Kenaikan Air:    0 cm/mnt
  Curah Hujan:     5 mm

→ Risiko: 6.3% — Level: Very Low
→ Kondisi aman.
```

---

## File Utama

### `src/base.yaml`
Knowledge base dalam format YAML. Berisi definisi variabel fuzzy, membership function (segitiga/trapesium), 29 rules, threshold, dan saran.

### `src/fuzzy.py`
Engine inti:
- `FuzzySet` — class membership function triangular & trapezoidal
- `MamdaniFIS` — pipeline lengkap: fuzzify → rule eval → agregasi → defuzzify
- `diagnosa(jarak, kenaikan, hujan)` → return dict hasil detail

### `src/main.py`
CLI dengan Rich UI. 6 menu, input parameter, output detail (fuzzifikasi, rule aktif, agregasi grafik, progress bar risiko, alert).

---

## Referensi

Tuah, B. A., Lestari, A., & Parhusip, J. (2025). *Rancang Bangun Alat Monitoring dan Peringatan Banjir*. Universitas Palangkaraya.

---
