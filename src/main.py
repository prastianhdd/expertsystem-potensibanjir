# MAIN - Menu Utama Sistem Pakar Peringatan Banjir
# Mamdani Fuzzy Inference System

import sys
import random
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt
from rich import box
from rich.columns import Columns

from fuzzy import MamdaniFIS, load_knowledge_base

console = Console()
kb = load_knowledge_base()
fis = MamdaniFIS()


def header():
    """Tampilkan header aplikasi"""
    header_panel = Panel(
        "[bold cyan]SISTEM PAKAR PERINGATAN BANJIR[/]\n"
        "[white]Mamdani Fuzzy Inference System[/]\n"
        "[dim]3 Parameter: Jarak Air + Kenaikan Air + Curah Hujan[/]",
        box=box.DOUBLE_EDGE,
        border_style="cyan"
    )
    console.print(header_panel)


def menu_utama():
    """Tampilkan menu utama dan return pilihan user"""
    console.clear()
    header()
    console.print()

    menu_panel = Panel(
        "[bold]Pilih menu:[/]\n\n"
        "  [cyan]1.[/] Diagnosa Risiko Banjir\n"
        "  [cyan]2.[/] Lihat Variabel Fuzzy\n"
        "  [cyan]3.[/] Lihat Semua Rule\n"
        "  [cyan]4.[/] Ambang Peringatan & Saran\n"
        "  [cyan]5.[/] Simulasi (Demo Acak)\n"
        "  [cyan]6.[/] Keluar",
        box=box.ROUNDED,
        border_style="white"
    )
    console.print(menu_panel)
    console.print()
    pilihan = Prompt.ask("[cyan]>[/]", choices=["1", "2", "3", "4", "5", "6"], default="1")
    return pilihan


# ============================================================
# MENU 1: DIAGNOSA
# ============================================================

def diagnosa():
    """Input 3 parameter -> tampilkan hasil fuzzy lengkap"""
    console.clear()
    header()
    console.print()
    console.print("[bold yellow]INPUT PARAMETER[/]")
    console.print("[dim]Masukkan nilai untuk 3 parameter berikut:[/]")
    console.print()

    jarak = float_input(
        "Jarak sensor ke muka air (cm) [0-210]",
        min_v=0, max_v=210, default=130
    )
    kenaikan = float_input(
        "Kenaikan air (cm/menit, negatif=turun) [-6 to 6]",
        min_v=-6, max_v=6, default=2
    )
    hujan = float_input(
        "Curah hujan (mm) [0-150]",
        min_v=0, max_v=150, default=40
    )

    console.print()
    with console.status("[bold cyan]Memproses Fuzzy Inference...[/]", spinner="dots"):
        hasil = fis.diagnosa(jarak, kenaikan, hujan)

    cetak_hasil(hasil)


def float_input(prompt_text, min_v, max_v, default):
    """Helper: input float dengan range dan default"""
    while True:
        inp = Prompt.ask(f"[cyan]>[/] {prompt_text}", default=str(default))
        try:
            val = float(inp)
            val = max(min_v, min(max_v, val))
            return val
        except ValueError:
            console.print("[red]Input tidak valid. Masukkan angka.[/]")


def cetak_hasil(hasil):
    """Tampilkan hasil diagnosa lengkap + detail fuzzy"""
    console.clear()
    header()
    console.print()

    d = hasil["input"]

    # ---- INPUT CRISP ----
    table_in = Table(title="[bold cyan]INPUT PARAMETER[/]", box=box.ROUNDED, header_style="bold cyan")
    table_in.add_column("Parameter", style="yellow")
    table_in.add_column("Nilai", style="bold white")
    table_in.add_column("Label Fuzzy", style="green")
    table_in.add_row("Jarak Air", f"{d['jarak_air']['nilai']} cm", d['jarak_air']['label'])
    table_in.add_row("Kenaikan Air", f"{d['kenaikan_air']['nilai']} cm/mnt", d['kenaikan_air']['label'])
    table_in.add_row("Curah Hujan", f"{d['curah_hujan']['nilai']} mm", d['curah_hujan']['label'])
    console.print(table_in)

    # ---- FUZZIFIKASI DETAIL ----
    console.print()
    for var_key, var_data in d.items():
        label_var = kb["variabel_input"][var_key]["label"] if var_key in kb["variabel_input"] else var_key
        if var_data["fuzzifikasi"]:
            fuzz_text = "  " + "\n  ".join(
                f"[yellow]{k}[/] -> [green]{v}[/]"
                for k, v in sorted(var_data["fuzzifikasi"].items())
            )
            panel = Panel(
                fuzz_text,
                title=f"[bold]{label_var}[/]",
                border_style="cyan",
                box=box.ROUNDED
            )
            console.print(panel)
        else:
            console.print(f"[dim]{label_var}: tidak ada himpunan aktif[/]")

    # ---- RULE AKTIF ----
    console.print()
    if hasil["rule_aktif"]:
        table_rules = Table(
            title="[bold yellow]RULE AKTIF[/]",
            box=box.ROUNDED,
            header_style="bold yellow",
            show_lines=True
        )
        table_rules.add_column("Rule", style="yellow", width=6)
        table_rules.add_column("Output", style="green")
        table_rules.add_column("Clipping", style="cyan", width=12)
        for item in hasil["rule_aktif"]:
            table_rules.add_row(item["rule"], item["label"], f"{item['clip']:.4f}")
        console.print(table_rules)
    else:
        panel = Panel(
            "  [dim]Tidak ada rule yang aktif[/]",
            title="[bold yellow]RULE AKTIF[/]",
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(panel)

    # ---- OUTPUT AGREGASI (grafik ASCII sederhana) ----
    console.print()
    cetak_grafik_fuzzy(hasil["agregasi"])

    # ---- RISIKO FINAL ----
    console.print()
    risiko = hasil["risiko"]
    label = hasil["label_risiko"]
    threshold = hasil["threshold"]
    alert = hasil["alert"]

    # Warna label sesuai level
    warna = {
        "Very Low": "green",
        "Low": "cyan",
        "Moderate": "yellow",
        "High": "red",
        "Very High": "bold red"
    }.get(label, "white")

    # Progress bar
    bar_len = 40
    filled = int((risiko / 100) * bar_len)
    bar = "#" * filled + "." * (bar_len - filled)

    console.print("[bold]RISIKO BANJIR[/]")
    console.print(f"  [{warna}]{bar}[/]  [bold]{risiko:.1f}%[/]")
    console.print(f"  Level: [{warna}]{label}[/]")

    # Threshold line
    thresh_pos = int((threshold / 100) * bar_len)
    thresh_line = " " * thresh_pos + "^"
    console.print(f"  [dim]{thresh_line} threshold {threshold}%[/]")

    # Alert
    if alert:
        alert_panel = Panel(
            f"[bold red]!! PERINGATAN! Risiko banjir >= {threshold}%[/]\n[white]{hasil['saran']}[/]",
            border_style="red",
            box=box.HEAVY
        )
    else:
        alert_panel = Panel(
            f"  [cyan]{hasil['saran']}[/]",
            border_style="green",
            box=box.ROUNDED
        )
    console.print(alert_panel)


def cetak_grafik_fuzzy(agregat):
    """Tampilkan grafik ASCII fungsi keanggotaan agregat hasil"""
    console.print("[bold]AGREGASI OUTPUT (Fungsi Keanggotaan)[/]")
    if not agregat or max(agregat.values()) == 0:
        console.print("  [dim]Tidak ada area aktif[/]")
        return

    max_mu = max(agregat.values())
    chart_h = 6
    points = list(agregat.items())
    step = max(1, len(points) // 50)

    for row in range(chart_h, -1, -1):
        thresh = row / chart_h * max_mu
        line = ""
        for i in range(0, len(points), step):
            _, mu = points[i]
            line += "#" if mu >= thresh else " "
        console.print(f"  {line}")

    console.print(f"  0{' ' * (len(line) - 4)}100")
    console.print(f"  [dim]|{'-' * (len(line) - 2)}|[/]")
    console.print()


# ============================================================
# MENU 2: LIHAT VARIABEL
# ============================================================

def lihat_variabel():
    """Tampilkan semua variabel fuzzy + membership function"""
    console.clear()
    header()
    console.print()

    # Input variables
    console.print("[bold cyan]VARIABEL INPUT[/]\n")
    for var_name, var_data in kb["variabel_input"].items():
        domain = var_data["domain"]
        console.print(f"[bold yellow]{var_name}[/]: {var_data['label']}")
        console.print(f"  Domain: [{domain[0]}, {domain[1]}]")
        console.print(f"  Keterangan: [dim]{var_data.get('keterangan', '-')}[/]")

        table = Table(box=box.SIMPLE, show_header=True, header_style="green")
        table.add_column("Himpunan", style="green")
        table.add_column("Tipe", style="cyan")
        table.add_column("Parameter", style="white")
        for set_name, set_data in var_data["himpunan"].items():
            params = ", ".join(str(p) for p in set_data["params"])
            table.add_row(set_name, set_data["tipe"], params)
        console.print(table)
        console.print()

    # Output variable
    console.print("[bold red]VARIABEL OUTPUT[/]\n")
    out_data = kb["variabel_output"]["risiko_banjir"]
    domain = out_data["domain"]
    console.print(f"[bold yellow]risiko_banjir[/]: {out_data['label']}")
    console.print(f"  Domain: [{domain[0]}, {domain[1]}]")

    table = Table(box=box.SIMPLE, show_header=True, header_style="green")
    table.add_column("Himpunan", style="green")
    table.add_column("Tipe", style="cyan")
    table.add_column("Parameter", style="white")
    for set_name, set_data in out_data["himpunan"].items():
        params = ", ".join(str(p) for p in set_data["params"])
        table.add_row(set_name, set_data["tipe"], params)
    console.print(table)
    console.print()


# ============================================================
# MENU 3: LIHAT RULES
# ============================================================

def lihat_rules():
    """Tampilkan semua 29 rule fuzzy"""
    console.clear()
    header()
    console.print()

    table = Table(
        title="[bold yellow]FUZZY RULES (IF ... AND ... AND ... -> THEN ...)[/]",
        box=box.ROUNDED,
        header_style="bold yellow",
        show_lines=True
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Level Air", style="cyan")
    table.add_column("Kenaikan", style="cyan")
    table.add_column("Curah Hujan", style="cyan")
    table.add_column("-> Risiko", style="green")

    for rule in kb["rules"]:
        kondisi = rule["if"]
        air = kondisi.get("jarak_air", "-")
        kenaikan = kondisi.get("kenaikan_air", "-")
        hujan = kondisi.get("curah_hujan", "-")
        no = rule["id"].replace("R", "")
        table.add_row(no, air, kenaikan, hujan, rule["then"])

    console.print(table)
    console.print("[dim]Tanda '-' = faktor tidak menentukan[/]")
    console.print()


# ============================================================
# MENU 4: AMBANG & SARAN
# ============================================================

def lihat_ambang():
    """Tampilkan threshold alert dan saran tiap level risiko"""
    console.clear()
    header()
    console.print()

    threshold = kb.get("threshold_alert", 75)
    panel = Panel(
        f"[bold]Ambang peringatan banjir:[/] [red]{threshold}%[/]\n"
        f"[dim]Peringatan dikirim jika risiko >= {threshold}%[/]",
        border_style="red",
        box=box.ROUNDED
    )
    console.print(panel)
    console.print()

    saran = kb.get("saran", {})
    warna = {
        "Very Low": "green",
        "Low": "cyan",
        "Moderate": "yellow",
        "High": "red",
        "Very High": "bold red"
    }

    table = Table(
        title="[bold]LEVEL RISIKO & SARAN[/]",
        box=box.ROUNDED,
        header_style="bold",
        show_lines=True
    )
    table.add_column("Level", style="bold")
    table.add_column("Saran Penanganan", style="white")

    for level in ["Very Low", "Low", "Moderate", "High", "Very High"]:
        w = warna.get(level, "white")
        text = saran.get(level, "-")
        table.add_row(f"[{w}]{level}[/]", text)

    console.print(table)
    console.print()


# ============================================================
# MENU 5: SIMULASI
# ============================================================

def simulasi():
    """Generate random input, diagnosa, repeat"""
    console.clear()
    header()
    console.print()
    console.print("[bold yellow]SIMULASI DIAGNOSA ACAK[/]")
    console.print("[dim]Sistem akan generate nilai acak untuk simulasi.[/]")
    console.print()

    n = Prompt.ask("[cyan]>[/] Berapa kali simulasi?", choices=["1", "3", "5", "10"], default="3")
    n = int(n)

    for i in range(n):
        jarak = random.uniform(0, 210)
        kenaikan = random.uniform(-6, 6)
        hujan = random.uniform(0, 150)

        with console.status(f"[cyan]Simulasi {i+1}/{n}...[/]", spinner="dots"):
            hasil = fis.diagnosa(jarak, kenaikan, hujan)

        console.print(f"\n[bold]--- Simulasi #{i+1} ---[/]")
        console.print(f"  Jarak: {jarak:.1f} cm | Kenaikan: {kenaikan:+.1f} cm/mnt | Hujan: {hujan:.1f} mm")
        console.print(f"  | [bold]Risiko: {hasil['risiko']:.1f}%[/] | Level: {hasil['label_risiko']} | {'!! ALERT' if hasil['alert'] else 'OK'}")
        console.print(f"  [dim]{hasil['saran']}[/]")

    console.print()
    console.print("[green]Simulasi selesai![/]")


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    while True:
        pilihan = menu_utama()

        if pilihan == "1":
            diagnosa()
        elif pilihan == "2":
            lihat_variabel()
        elif pilihan == "3":
            lihat_rules()
        elif pilihan == "4":
            lihat_ambang()
        elif pilihan == "5":
            simulasi()
        elif pilihan == "6":
            console.print()
            bye = Panel("[bold yellow]Terima kasih! Tetap waspada banjir.[/]", box=box.DOUBLE_EDGE, border_style="yellow")
            console.print(bye)
            console.print()
            sys.exit(0)

        Prompt.ask("\n[dim]Tekan Enter untuk lanjut...[/]", default="")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Program dihentikan.[/]")
        sys.exit(0)
