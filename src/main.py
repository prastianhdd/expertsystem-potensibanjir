import os
import sys
import random
from colorama import init, Fore, Style
from fuzzy import load_kb, diagnosa

init(autoreset=True)   

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def garis(kar="=", n=60, warna=Fore.CYAN):
    print(warna + kar * n)

def header():
    garis()
    print(Fore.CYAN + Style.BRIGHT + "  SISTEM PAKAR PERINGATAN BANJIR")
    print(Fore.WHITE + "  Metode: Mamdani Fuzzy Inference System")
    print(Style.DIM  + "  Input: Jarak Air | Kenaikan Air | Curah Hujan")
    garis()

def tabel(headers, rows, warna_h=Fore.CYAN):
    """Cetak tabel rata kiri, lebar kolom otomatis"""
    lebar = [len(h) for h in headers]
    for row in rows:
        for i, sel in enumerate(row):
            lebar[i] = max(lebar[i], len(str(sel)))

    print(warna_h + Style.BRIGHT + "  ".join(h.ljust(lebar[i]) for i, h in enumerate(headers)))
    print(warna_h + "  ".join("-" * w for w in lebar))
    for row in rows:
        print(Fore.WHITE + "  ".join(str(sel).ljust(lebar[i]) for i, sel in enumerate(row)))

def enter():
    input(Style.DIM + "\n  Tekan Enter untuk lanjut..." + Style.RESET_ALL)

def input_angka(prompt, lo, hi, default):
    """Input float dengan validasi dan nilai default (tekan Enter)"""
    while True:
        raw = input(Fore.CYAN + f"  > {prompt} [{default}]: " + Style.RESET_ALL).strip()
        if raw == "":
            return float(default)
        try:
            return max(lo, min(hi, float(raw)))
        except ValueError:
            print(Fore.RED + "  Input tidak valid. Masukkan angka.")


def tampil_hasil(h):
    """Tampilkan detail lengkap satu hasil diagnosa"""
    clear()
    header()
    print()

    # --- Input ---
    print(Fore.CYAN + Style.BRIGHT + "[ INPUT ]")
    tabel(
        ["Parameter", "Nilai", "Label Fuzzy"],
        [
            ["Jarak Air",    f"{h['input']['jarak_air']['nilai']} cm",        h['input']['jarak_air']['label']],
            ["Kenaikan Air", f"{h['input']['kenaikan_air']['nilai']} cm/mnt", h['input']['kenaikan_air']['label']],
            ["Curah Hujan",  f"{h['input']['curah_hujan']['nilai']} mm",      h['input']['curah_hujan']['label']],
        ]
    )
    print()

    # --- Fuzzifikasi ---
    # Tampilkan derajat keanggotaan tiap himpunan beserta mini bar-chart
    print(Fore.CYAN + Style.BRIGHT + "[ FUZZIFIKASI ]")
    print(Style.DIM + "  Derajat keanggotaan tiap himpunan (0.0 = tidak aktif, tidak ditampilkan)")
    nama_var = {"jarak_air": "Jarak Air", "kenaikan_air": "Kenaikan Air", "curah_hujan": "Curah Hujan"}
    for var, data in h["input"].items():
        print(Fore.YELLOW + f"\n  {nama_var[var]}:")
        if data["fuzzifikasi"]:
            for himpunan, mu in sorted(data["fuzzifikasi"].items()):
                bar = "#" * int(mu * 20)
                print(f"    {Fore.WHITE}{himpunan:<16}{Fore.GREEN}{mu:.4f}  {bar}")
        else:
            print(Style.DIM + "    (tidak ada himpunan aktif)")
    print()

    # --- Rule Aktif ---
    # Rule aktif = semua kondisi IF-nya terpenuhi, AND = MIN
    print(Fore.CYAN + Style.BRIGHT + "[ RULE AKTIF ]")
    if h["rule_aktif"]:
        tabel(
            ["Rule", "Output", "Clipping (MIN)"],
            [[r["rule"], r["output"], f"{r['clip']:.4f}"] for r in h["rule_aktif"]],
            warna_h=Fore.YELLOW
        )
    else:
        print(Style.DIM + "  Tidak ada rule yang aktif")
    print()

    # --- Hasil Akhir ---
    risiko = h["risiko"]
    label  = h["label_risiko"]
    warna  = {"Rendah": Fore.GREEN, "Sedang": Fore.YELLOW, "Tinggi": Fore.RED + Style.BRIGHT}.get(label, Fore.WHITE)

    isi = int((risiko / 100) * 40)
    bar = "#" * isi + "." * (40 - isi)

    print(Fore.CYAN + Style.BRIGHT + "[ HASIL DEFUZZIFIKASI ]")
    print(f"  {warna}{bar}  {Style.BRIGHT}{risiko:.1f}%")
    print(f"  Level Risiko : {warna}{Style.BRIGHT}{label}")
    print()

    if h["alert"]:
        garis("!", 60, Fore.RED)
        print(Fore.RED + Style.BRIGHT + f"  !! PERINGATAN BANJIR! Risiko {risiko:.1f}% >= threshold {h['threshold']}%")
        print(Fore.WHITE + f"  {h['saran']}")
        garis("!", 60, Fore.RED)
    else:
        garis("-", 60, Fore.GREEN)
        print(Fore.GREEN + f"  {h['saran']}")
        garis("-", 60, Fore.GREEN)



def menu_diagnosa(kb):
    clear()
    header()
    print()
    garis("-", 60, Fore.YELLOW)
    print(Fore.YELLOW + Style.BRIGHT + "  Masukkan nilai sensor (Enter = pakai default):")
    garis("-", 60, Fore.YELLOW)
    print()
    jarak    = input_angka("Jarak sensor ke muka air (cm)   [0-210]",  0,  210, 130)
    kenaikan = input_angka("Kenaikan air (cm/mnt, - = turun) [-6-6]", -6,   6,   2)
    hujan    = input_angka("Curah hujan (mm)                [0-150]",  0,  150,  40)

    print()
    print(Fore.CYAN + "  Memproses...")
    h = diagnosa(kb, jarak, kenaikan, hujan)
    tampil_hasil(h)


def menu_variabel(kb):
    clear()
    header()
    print()

    print(Fore.CYAN + Style.BRIGHT + "[ VARIABEL INPUT ]\n")
    for var_name, var in kb["variabel_input"].items():
        print(Fore.YELLOW + Style.BRIGHT + f"  {var['label']}")
        print(f"  Domain    : {var['domain']}")
        print(Style.DIM + f"  Keterangan: {var.get('keterangan', '-')}")
        tabel(
            ["Himpunan", "Bentuk MF", "Parameter"],
            [[n, d["tipe"], str(d["params"])] for n, d in var["himpunan"].items()],
            warna_h=Fore.GREEN
        )
        print()

    print(Fore.RED + Style.BRIGHT + "[ VARIABEL OUTPUT ]\n")
    out = kb["variabel_output"]["risiko_banjir"]
    print(Fore.YELLOW + Style.BRIGHT + f"  {out['label']}")
    print(f"  Domain: {out['domain']}")
    tabel(
        ["Himpunan", "Bentuk MF", "Parameter"],
        [[n, d["tipe"], str(d["params"])] for n, d in out["himpunan"].items()],
        warna_h=Fore.GREEN
    )
    print()


def menu_rules(kb):
    clear()
    header()
    print()
    print(Fore.YELLOW + Style.BRIGHT + "[ FUZZY RULES — IF ... AND ... AND ... THEN ... ]\n")
    tabel(
        ["#", "Jarak Air", "Kenaikan Air", "Curah Hujan", "-> Risiko"],
        [
            [r["id"], r["if"].get("jarak_air","-"), r["if"].get("kenaikan_air","-"),
             r["if"].get("curah_hujan","-"), r["then"]]
            for r in kb["rules"]
        ],
        warna_h=Fore.YELLOW
    )
    print(Style.DIM + f"\n  Total: {len(kb['rules'])} rule")
    print()


def menu_saran(kb):
    clear()
    header()
    print()
    threshold = kb.get("threshold_alert", 75)
    garis("-", 60, Fore.RED)
    print(Style.BRIGHT + f"  Threshold peringatan : " + Fore.RED + f"{threshold}%")
    print(Style.DIM   + f"  Alert aktif jika risiko >= {threshold}%")
    garis("-", 60, Fore.RED)
    print()
    print(Style.BRIGHT + "[ SARAN TIAP LEVEL ]\n")
    warna = {"Rendah": Fore.GREEN, "Sedang": Fore.YELLOW, "Tinggi": Fore.RED + Style.BRIGHT}
    for level, teks in kb["saran"].items():
        print(f"  {warna.get(level, Fore.WHITE)}{Style.BRIGHT}{level:<10}{Style.RESET_ALL}: {teks}")
    print()


def menu_simulasi(kb):
    clear()
    header()
    print()
    print(Fore.YELLOW + Style.BRIGHT + "  SIMULASI ACAK\n")

    while True:
        n = input(Fore.CYAN + "  > Berapa simulasi? (1/3/5) [3]: " + Style.RESET_ALL).strip() or "3"
        if n in ["1", "3", "5"]:
            break
        print(Fore.RED + "  Pilihan tidak valid.")

    for i in range(int(n)):
        j = round(random.uniform(0,   210), 1)
        k = round(random.uniform(-6,    6), 1)
        h = round(random.uniform(0,   150), 1)
        hasil = diagnosa(kb, j, k, h)

        warna = {"Rendah": Fore.GREEN, "Sedang": Fore.YELLOW, "Tinggi": Fore.RED+Style.BRIGHT}.get(hasil["label_risiko"], Fore.WHITE)
        status = Fore.RED + Style.BRIGHT + "ALERT" if hasil["alert"] else Fore.GREEN + "OK"

        print(f"  #{i+1}  Jarak:{j}cm  Naik:{k:+}cm/mnt  Hujan:{h}mm")
        print(f"       {warna}{hasil['risiko']:.1f}% ({hasil['label_risiko']}){Style.RESET_ALL}  [{status}{Style.RESET_ALL}]")
        print()



def main():
    kb = load_kb()

    while True:
        clear()
        header()
        print()
        print(Style.BRIGHT + "  Pilih menu:")
        print()
        print(Fore.CYAN + "  1." + Fore.WHITE + " Diagnosa Risiko Banjir")
        print(Fore.CYAN + "  2." + Fore.WHITE + " Lihat Variabel Fuzzy")
        print(Fore.CYAN + "  3." + Fore.WHITE + " Lihat Semua Rule")
        print(Fore.CYAN + "  4." + Fore.WHITE + " Threshold & Saran")
        print(Fore.CYAN + "  5." + Fore.WHITE + " Simulasi Acak")
        print(Fore.CYAN + "  6." + Fore.WHITE + " Keluar")
        print()

        pilihan = input(Fore.CYAN + "  > " + Style.RESET_ALL).strip() or "1"

        if   pilihan == "1": menu_diagnosa(kb)
        elif pilihan == "2": menu_variabel(kb)
        elif pilihan == "3": menu_rules(kb)
        elif pilihan == "4": menu_saran(kb)
        elif pilihan == "5": menu_simulasi(kb)
        elif pilihan == "6":
            print()
            garis("=", 60, Fore.YELLOW)
            print(Fore.YELLOW + Style.BRIGHT + "  Terima kasih. Tetap waspada banjir!")
            garis("=", 60, Fore.YELLOW)
            print()
            sys.exit(0)
        else:
            print(Fore.RED + "  Pilihan tidak valid (1-6).")

        if pilihan != "6":
            enter()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n  Program dihentikan.")
        sys.exit(0)