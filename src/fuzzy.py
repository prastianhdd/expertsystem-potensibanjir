# FUZZY - Mamdani Inference Engine
# Sistem Pakar Peringatan Banjir
# Mamdani FIS: Fuzzify -> Rule Eval (MIN) -> Aggregasi (MAX) -> Defuzzify (Centroid)

import yaml
import os
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_YAML = os.path.join(BASE_DIR, "base.yaml")


def load_knowledge_base():
    with open(BASE_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================
# FUZZY SET — membership function triangular / trapezoidal
# ============================================================

class FuzzySet:
    def __init__(self, nama, tipe, params):
        self.nama = nama
        self.tipe = tipe      # "segitiga" or "trapesium"
        self.params = params  # [a, b, c] or [a, b, c, d]

    def derajat(self, x):
        """Hitung derajat keanggotaan μ(x) untuk crisp value x"""
        if self.tipe == "segitiga":
            return self._segitiga(x)
        elif self.tipe == "trapesium":
            return self._trapesium(x)
        return 0.0

    def _segitiga(self, x):
        a, b, c = self.params
        if a == b and x == a:
            return 1.0
        if b == c and x == b:
            return 1.0
        if x <= a or x >= c:
            return 0.0
        if a < x <= b:
            return (x - a) / (b - a)
        if b < x < c:
            return (c - x) / (c - b)
        return 0.0

    def _trapesium(self, x):
        a, b, c, d = self.params
        if x <= a or x >= d:
            return 0.0
        if a < x < b:
            return (x - a) / (b - a)
        if b <= x <= c:
            return 1.0
        if c < x < d:
            return (d - x) / (d - c)
        return 0.0


# ============================================================
# MAMDANI FIS ENGINE
# ============================================================

class MamdaniFIS:
    def __init__(self):
        self.kb = load_knowledge_base()
        self._build_sets()

    def _build_sets(self):
        """Convert YAML definitions into FuzzySet objects"""
        # Input sets: { nama_var: { label_himpunan: FuzzySet } }
        self.input_sets = {}
        for var_name, var_data in self.kb["variabel_input"].items():
            self.input_sets[var_name] = {}
            for set_name, set_data in var_data["himpunan"].items():
                self.input_sets[var_name][set_name] = FuzzySet(
                    set_name, set_data["tipe"], set_data["params"]
                )

        # Output sets
        self.output_sets = {}
        out_data = self.kb["variabel_output"]["risiko_banjir"]
        for set_name, set_data in out_data["himpunan"].items():
            self.output_sets[set_name] = FuzzySet(
                set_name, set_data["tipe"], set_data["params"]
            )

        self.output_domain = out_data["domain"]  # [0, 100]

    def _clamp(self, var_name, nilai):
        """Clamp nilai ke domain variabel"""
        domain = self.kb["variabel_input"].get(var_name, {}).get("domain")
        if domain:
            return max(domain[0], min(domain[1], nilai))
        return nilai

    # ----------------------------------------------------------
    # LANTAI 1: FUZZIFIKASI
    # ----------------------------------------------------------
    def fuzzify(self, var_name, nilai):
        """Hitung μ untuk tiap himpunan di satu variabel input"""
        crisp = self._clamp(var_name, nilai)
        sets = self.input_sets[var_name]
        hasil = {}
        for set_name, fs in sets.items():
            mu = fs.derajat(crisp)
            if mu > 0:
                hasil[set_name] = round(mu, 4)
        return hasil, crisp

    # ----------------------------------------------------------
    # LANTAI 2: EVALUASI RULES (MIN implication / clipping)
    # ----------------------------------------------------------
    def evaluasi_rules(self, fuzzified):
        """
        Untuk tiap rule:
        1. Ambil μ dari tiap kondisi di IF
        2. Operasi AND -> MIN (μ terkecil)
        3. Clip output set di MIN tsb -> (label_output, μ_clip)
        Return: list of (rule_id, output_label, clipping_degree)
        """
        hasil = []
        for rule in self.kb["rules"]:
            kondisi = rule["if"]
            kesimpulan = rule["then"]

            min_mu = 1.0
            match = True

            for var_name, himpunan in kondisi.items():
                var_fuzz = fuzzified.get(var_name, {})
                mu = var_fuzz.get(himpunan, 0.0)
                if mu == 0.0:
                    match = False
                    break
                if mu < min_mu:
                    min_mu = mu

            if match:
                hasil.append((rule["id"], kesimpulan, round(min_mu, 4)))

        return hasil

    # ----------------------------------------------------------
    # LANTAI 3: AGREGASI (MAX dari semua clipping)
    # ----------------------------------------------------------
    def agregasi(self, rule_results):
        """
        Agregasi semua output clipping -> fungsi keanggotaan agregat.
        rule_results: list of (rule_id, output_label, clipping_degree)
        """
        a, b = self.output_domain
        agregat = {x: 0.0 for x in range(a, b + 1)}

        for _rid, label_output, clip_degree in rule_results:
            fs = self.output_sets[label_output]
            for x in range(a, b + 1):
                mu_asli = fs.derajat(x)
                mu_clipped = min(mu_asli, clip_degree)
                if mu_clipped > agregat[x]:
                    agregat[x] = mu_clipped

        return agregat

    # ----------------------------------------------------------
    # LANTAI 4: DEFUZZIFIKASI (Centroid / Center of Area)
    # ----------------------------------------------------------
    def defuzzify(self, agregat):
        """
        Centroid: Risiko = Σ(xi * μ(xi)) / Σ(μ(xi))
        Jika agregat flat 0 -> return 0
        """
        numerator = 0.0
        denominator = 0.0
        for x, mu in agregat.items():
            numerator += x * mu
            denominator += mu

        if denominator == 0:
            return 0.0

        return round(numerator / denominator, 2)

    def label_risiko(self, persen):
        """Cari label risiko — pilih yg derajat keanggotaan tertinggi"""
        best_label = "Very Low"
        best_mu = 0.0
        for set_name, fs in self.output_sets.items():
            mu = fs.derajat(persen)
            if mu > best_mu:
                best_mu = mu
                best_label = set_name
        return best_label

    def cari_saran(self, label):
        """Ambil saran dari KB"""
        saran = self.kb.get("saran", {})
        return saran.get(label, "Tidak ada saran.")

    # ----------------------------------------------------------
    # DIAGNOSA LENGKAP
    # ----------------------------------------------------------
    def diagnosa(self, jarak_air, kenaikan_air, curah_hujan):
        """
        Pipeline lengkap: fuzzify -> rules -> agregasi -> defuzzify
        Return dict detail.
        """
        # 1. FUZZIFIKASI
        fuzz_jarak, crisp_jarak = self.fuzzify("jarak_air", jarak_air)
        fuzz_kenaikan, crisp_kenaikan = self.fuzzify("kenaikan_air", kenaikan_air)
        fuzz_hujan, crisp_hujan = self.fuzzify("curah_hujan", curah_hujan)

        fuzzified = {
            "jarak_air": fuzz_jarak,
            "kenaikan_air": fuzz_kenaikan,
            "curah_hujan": fuzz_hujan,
        }

        # 2. EVALUASI RULES
        rule_results = self.evaluasi_rules(fuzzified)
        rule_results_dedup = self._dedup_rules(rule_results)

        # 3. AGREGASI
        agregat = self.agregasi(rule_results_dedup)

        # 4. DEFUZZIFIKASI
        risiko = self.defuzzify(agregat)
        label = self.label_risiko(risiko)
        saran = self.cari_saran(label)
        threshold = self.kb.get("threshold_alert", 75)
        alert = risiko >= threshold

        # Info tambahan: label dari tiap input
        label_jarak = max(fuzz_jarak, key=fuzz_jarak.get) if fuzz_jarak else "-"
        label_kenaikan = max(fuzz_kenaikan, key=fuzz_kenaikan.get) if fuzz_kenaikan else "-"
        label_hujan = max(fuzz_hujan, key=fuzz_hujan.get) if fuzz_hujan else "-"

        return {
            "input": {
                "jarak_air": {"nilai": crisp_jarak, "fuzzifikasi": fuzz_jarak, "label": label_jarak},
                "kenaikan_air": {"nilai": crisp_kenaikan, "fuzzifikasi": fuzz_kenaikan, "label": label_kenaikan},
                "curah_hujan": {"nilai": crisp_hujan, "fuzzifikasi": fuzz_hujan, "label": label_hujan},
            },
            "rule_aktif": [
                {"rule": rid, "label": label, "clip": clip}
                for rid, label, clip in rule_results_dedup
            ],
            "agregasi": agregat,
            "risiko": risiko,
            "label_risiko": label,
            "saran": saran,
            "threshold": threshold,
            "alert": alert,
        }

    def _dedup_rules(self, rule_results):
        """
        Dedup: jika ada 2 rule output label sama, simpan yg clip-nya lebih besar
        rule_results: list of (rule_id, label, clip)
        Return: list of (rule_id, label, clip) — dedup by label (keep max clip)
        """
        best = {}  # label -> (rule_id, clip)
        for rid, label, clip in rule_results:
            if label not in best or clip > best[label][1]:
                best[label] = (rid, clip)
        return [(rid, label, clip) for label, (rid, clip) in best.items()]


# ============================================================
# TEST / DEMO
# ============================================================

if __name__ == "__main__":
    fis = MamdaniFIS()

    print("=== TEST 1: Banjir (jarak=130, naik=2, hujan=80) ===")
    hasil = fis.diagnosa(130, 2, 80)
    print(f"Risiko: {hasil['risiko']}% -> {hasil['label_risiko']}")
    print(f"Alert: {hasil['alert']}")
    print()

    print("=== TEST 2: Aman (jarak=200, stabil=0, hujan=5) ===")
    hasil = fis.diagnosa(200, 0, 5)
    print(f"Risiko: {hasil['risiko']}% -> {hasil['label_risiko']}")
    print(f"Alert: {hasil['alert']}")
    print()

    print("=== TEST 3: Siaga (jarak=160, naik=3, hujan=50) ===")
    hasil = fis.diagnosa(160, 3, 50)
    print(f"Risiko: {hasil['risiko']}% -> {hasil['label_risiko']}")
    print(f"Alert: {hasil['alert']}")
