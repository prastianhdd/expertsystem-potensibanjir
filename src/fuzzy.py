# ============================================================
# fuzzy.py  —  Engine Mamdani Fuzzy Inference System
# ============================================================
#
# File ini bertugas SATU hal: menerima 3 angka input lalu
# mengembalikan nilai risiko banjir dalam persen (0-100).
#
# Alur Mamdani (dari atas ke bawah):
#   Input crisp
#       |
#   [FUZZIFIKASI]   ubah angka -> derajat keanggotaan (0.0-1.0)
#       |
#   [EVALUASI RULE] cocokkan IF-kondisi, AND = ambil MIN
#       |
#   [AGREGASI]      gabungkan semua output rule, pakai MAX
#       |
#   [DEFUZZIFIKASI] ubah kurva agregat -> angka risiko (Centroid)
#       |
#   Output: persen risiko
# ============================================================

import yaml
import os

# Path file knowledge base
BASE_YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base.yaml")


# ------------------------------------------------------------
# LOAD KNOWLEDGE BASE
# ------------------------------------------------------------

def load_kb():
    """Baca base.yaml dan kembalikan isinya sebagai dict Python"""
    with open(BASE_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ------------------------------------------------------------
# FUNGSI KEANGGOTAAN (Membership Function)
# ------------------------------------------------------------
#
# Mengukur "seberapa cocok" nilai x masuk ke suatu himpunan.
# Hasil selalu antara 0.0 (tidak cocok) sampai 1.0 (cocok penuh).

def mf_segitiga(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    if x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    return (c - x) / (c - b) if c != b else 1.0


def mf_trapesium(x, a, b, c, d):
    if x <= a or x >= d:
        return 0.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    if x <= c:
        return 1.0
    return (d - x) / (d - c) if d != c else 1.0


def hitung_mf(x, tipe, params):
    """Pilih fungsi keanggotaan berdasarkan tipe dari base.yaml"""
    if tipe == "segitiga":
        return mf_segitiga(x, *params)
    elif tipe == "trapesium":
        return mf_trapesium(x, *params)
    return 0.0

def fuzzifikasi(kb, nama_var, nilai):
    """
    Hitung derajat keanggotaan untuk semua himpunan pada satu variabel.

    Return:
      nilai  — nilai setelah di-clamp ke domain (tidak keluar batas)
      hasil  — dict {nama_himpunan: derajat}, hanya yang > 0
    """
    var = kb["variabel_input"][nama_var]

    # Clamp: pastikan nilai tidak keluar dari domain variabel
    lo, hi = var["domain"]
    nilai = max(lo, min(hi, nilai))

    hasil = {}
    for nama_himpunan, data in var["himpunan"].items():
        mu = hitung_mf(nilai, data["tipe"], data["params"])
        if mu > 0:
            hasil[nama_himpunan] = round(mu, 4)

    return nilai, hasil


def evaluasi_rules(kb, fuzz):
    """
    Cocokkan semua rule dengan hasil fuzzifikasi.
    Rule aktif = semua kondisi IF-nya terpenuhi (derajat > 0).

    fuzz: dict hasil fuzzifikasi ketiga variabel
          {nama_var: {nama_himpunan: derajat}}

    Return: list of dict — tiap item = 1 rule yang aktif
      {"rule": "R01", "output": "Tinggi", "clip": 0.5}
    """
    aktif = []

    for rule in kb["rules"]:
        alpha = 1.0       
        cocok = True

        for nama_var, nama_himpunan in rule["if"].items():
            
            mu = fuzz.get(nama_var, {}).get(nama_himpunan, 0.0)

            if mu == 0.0:
                cocok = False   
                break

            alpha = min(alpha, mu)  

        if cocok:
            aktif.append({
                "rule":   rule["id"],
                "output": rule["then"],
                "clip":   round(alpha, 4)
            })

    terbaik = {}
    for item in aktif:
        label = item["output"]
        if label not in terbaik or item["clip"] > terbaik[label]["clip"]:
            terbaik[label] = item

    return list(terbaik.values())



def agregasi(kb, rule_aktif):
    """
    Buat fungsi keanggotaan agregat dari semua rule aktif.

    Return: dict {x: derajat} untuk x = 0 sampai 100
    """
    out_data   = kb["variabel_output"]["risiko_banjir"]
    lo, hi     = out_data["domain"]
    himpunan   = out_data["himpunan"]

    agregat = {x: 0.0 for x in range(lo, hi + 1)}

    for item in rule_aktif:
        data = himpunan[item["output"]]

        for x in range(lo, hi + 1):
            mu_asli    = hitung_mf(x, data["tipe"], data["params"])
            mu_clipped = min(mu_asli, item["clip"])           
            agregat[x] = max(agregat[x], mu_clipped)         

    return agregat


def defuzzifikasi(agregat):
    """
    Hitung nilai crisp (persen risiko) dari fungsi keanggotaan agregat.

    Return: float — nilai risiko dalam persen (0-100)
    """
    pembilang = sum(x * mu for x, mu in agregat.items())
    penyebut  = sum(mu     for mu    in agregat.values())

    if penyebut == 0:
        return 0.0   

    return round(pembilang / penyebut, 2)



def diagnosa(kb, jarak_air, kenaikan_air, curah_hujan):
    """
    Jalankan semua tahap Mamdani FIS dari input sampai output.

    Return: dict lengkap berisi detail tiap tahap + hasil akhir
    """

    # TAHAP 1: Fuzzifikasi ketiga variabel input
    jarak_v,    fuzz_jarak    = fuzzifikasi(kb, "jarak_air",    jarak_air)
    kenaikan_v, fuzz_kenaikan = fuzzifikasi(kb, "kenaikan_air", kenaikan_air)
    hujan_v,    fuzz_hujan    = fuzzifikasi(kb, "curah_hujan",  curah_hujan)

    fuzz_semua = {
        "jarak_air":    fuzz_jarak,
        "kenaikan_air": fuzz_kenaikan,
        "curah_hujan":  fuzz_hujan,
    }

    # TAHAP 2: Evaluasi rules
    rule_aktif = evaluasi_rules(kb, fuzz_semua)

    # TAHAP 3: Agregasi
    agregat = agregasi(kb, rule_aktif)

    # TAHAP 4: Defuzzifikasi
    risiko = defuzzifikasi(agregat)

    # Label risiko: himpunan output mana yang derajatnya paling tinggi
    himpunan_out = kb["variabel_output"]["risiko_banjir"]["himpunan"]
    label = max(
        himpunan_out,
        key=lambda n: hitung_mf(risiko, himpunan_out[n]["tipe"], himpunan_out[n]["params"])
    )

    threshold = kb.get("threshold_alert", 75)

    return {
        "input": {
            "jarak_air":    {"nilai": jarak_v,    "fuzzifikasi": fuzz_jarak,    "label": max(fuzz_jarak,    key=fuzz_jarak.get)    if fuzz_jarak    else "-"},
            "kenaikan_air": {"nilai": kenaikan_v, "fuzzifikasi": fuzz_kenaikan, "label": max(fuzz_kenaikan, key=fuzz_kenaikan.get) if fuzz_kenaikan else "-"},
            "curah_hujan":  {"nilai": hujan_v,    "fuzzifikasi": fuzz_hujan,    "label": max(fuzz_hujan,    key=fuzz_hujan.get)    if fuzz_hujan    else "-"},
        },
        "rule_aktif":   rule_aktif,
        "risiko":       risiko,
        "label_risiko": label,
        "saran":        kb["saran"].get(label, "-"),
        "threshold":    threshold,
        "alert":        risiko >= threshold,
    }