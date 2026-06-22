# INFERENSI - Forward Chaining
# Sistem Pakar Teknisi Laptop
# Forward Chaining: dari fakta (gejala) -> kesimpulan (kerusakan)
# Bisa chain: G001 -> K01 -> K02 (adaptor rusak -> baterai gak ngecas)

import yaml
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Path ke base.yaml (di folder yang sama dengan file ini)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_YAML = os.path.join(BASE_DIR, "base.yaml")


def load_knowledge_base():
    """Baca file base.yaml dan return data-nya"""
    with open(BASE_YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def diagnose(gejala_dipilih):
    """
    Forward Chaining - iterative.
    Putaran 1: cocokin gejala dengan rule.
    Putaran 2: hasil kerusakan dipake lagi buat rule chain (K jadi IF).
    Putaran 3 dan seterusnya sampe gak ada kerusakan baru.
    """
    kb = load_knowledge_base()

    # Fakta awal: gejala yang dipilih user
    fakta = set(gejala_dipilih)
    kerusakan_terdeteksi = {}
    rule_match = []

    # Forward chaining: loop sampe fakta gak bertambah
    while True:
        ada_fakta_baru = False

        for rule in kb["rules"]:
            kondisi = rule["if"]
            kesimpulan = rule["then"]

            # Cek apa rule ini udah pernah diproses
            if rule["id"] in rule_match:
                continue

            # Cek apa semua kondisi ada di fakta saat ini
            kondisi_terpenuhi = True
            for g in kondisi:
                if g not in fakta:
                    kondisi_terpenuhi = False
                    break

            if kondisi_terpenuhi:
                rule_match.append(rule["id"])

                for kode in kesimpulan:
                    if kode in kb["kerusakan"]:
                        if kode not in kerusakan_terdeteksi:
                            data_kerusakan = kb["kerusakan"][kode]
                            kerusakan_terdeteksi[kode] = {
                                "kode": kode,
                                "nama": data_kerusakan["nama"],
                                "saran": data_kerusakan["saran"],
                                "rule": rule["id"]
                            }
                            fakta.add(kode)
                            ada_fakta_baru = True

        if not ada_fakta_baru:
            break

    output = {
        "gejala_input": [],
        "rule_match": rule_match,
        "hasil_kerusakan": list(kerusakan_terdeteksi.values())
    }

    for g in gejala_dipilih:
        nama = kb["gejala"].get(g, g)
        output["gejala_input"].append({"kode": g, "nama": nama})

    return output


def cetak_hasil(data):
    """Tampilkan hasil diagnosa ke layar pake rich (chalk versi python)"""

    # ---- GEJALA YANG DIPILIH ----
    console.print()
    gejala_panel = Panel(
        "\n".join([f"  [yellow]{g['kode']}[/]  [white]{g['nama']}[/]" for g in data["gejala_input"]]),
        title="[bold cyan]GEJALA YANG DIPILIH[/]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(gejala_panel)

    # ---- RULE YANG COCOK ----
    console.print()
    if data["rule_match"]:
        rule_text = ""
        for r in data["rule_match"]:
            rule_text += f"  [green]>[/] [bold yellow]{r}[/]\n"
        rule_panel = Panel(
            rule_text.strip(),
            title="[bold yellow]RULE YANG COCOK[/]",
            border_style="yellow",
            box=box.ROUNDED
        )
    else:
        rule_panel = Panel(
            "  [dim]Tidak ada rule yang cocok[/]",
            title="[bold yellow]RULE YANG COCOK[/]",
            border_style="yellow",
            box=box.ROUNDED
        )
    console.print(rule_panel)

    # ---- HASIL DIAGNOSA ----
    console.print()
    if data["hasil_kerusakan"]:
        # Pake tabel biar rapi
        table = Table(
            title="[bold green]HASIL DIAGNOSA[/]",
            box=box.ROUNDED,
            header_style="bold green",
            border_style="green"
        )
        table.add_column("No", style="dim", width=4)
        table.add_column("Kode", style="red", width=6)
        table.add_column("Kerusakan", style="bold white")
        table.add_column("Saran", style="cyan", no_wrap=False)
        table.add_column("Rule", style="yellow", width=8)

        for i, item in enumerate(data["hasil_kerusakan"], 1):
            table.add_row(
                str(i),
                item["kode"],
                item["nama"],
                item["saran"],
                item["rule"]
            )

        console.print(table)
    else:
        no_result = Panel(
            "  [red]Tidak ada kerusakan yang cocok dengan gejala tersebut.[/]",
            border_style="red",
            box=box.ROUNDED
        )
        console.print(no_result)

    console.print()
