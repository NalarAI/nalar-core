"""Mengambil data acuan pihak ketiga yang tidak ikut di repositori.

Empat berkas, semuanya publik, dan tidak satu pun memuat data peserta JKN.
Keempatnya sengaja tidak ikut di repositori karena ukurannya enam puluh satu
megabita, dan karena menyalin ulang terbitan pihak lain ke dalam repositori
sendiri bukan kebiasaan yang baik.

Tarif INA-CBG yang sudah diekstrak tetap ikut di data/processed, jadi model
bisa dilatih dan dijalankan tanpa menjalankan berkas ini sama sekali. Yang
memerlukannya hanya kalau ingin mengekstrak ulang tarifnya dari sumber asli,
atau menjalankan uji terhadap klaim Amerika.

Jalankan:
    python scripts/unduh_data.py
    python scripts/unduh_data.py --hanya tarif
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request

DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

PERAMBAN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

SUMBER = {
    "tarif": {
        "berkas": "permenkes3_2023.pdf",
        "alamat": (
            "https://peraturan.bpk.go.id/Download/298745/"
            "Permenkes%20Nomor%203%20Tahun%202023.pdf"
        ),
        "guna": "Tarif INA-CBG resmi, 76.970 baris dari 885 kode",
        "wajib": False,
    },
    "icd10": {
        "berkas": "icd10_codes.csv",
        "alamat": (
            "https://raw.githubusercontent.com/kamillamagna/ICD-10-CSV/master/codes.csv"
        ),
        "guna": "Hierarki 71.704 kode ICD-10 untuk embedding ontologi",
        "wajib": False,
    },
    "desynpuf": {
        "berkas": "desynpuf_ip.zip",
        "alamat": ("https://www.cms.gov/files/zip/de10sample1inpatientclaims.zip"),
        "guna": "Klaim Medicare untuk uji latih di sintetis uji di nyata",
        "wajib": False,
    },
    "leie": {
        "berkas": "leie.csv",
        "alamat": "https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv",
        "guna": "Daftar penyedia yang dikeluarkan, untuk kontrol negatif",
        "wajib": False,
    },
}


def unduh(nama: str, tetap: bool = False) -> bool:
    d = SUMBER[nama]
    tujuan = os.path.join(DIR, d["berkas"])
    if os.path.exists(tujuan) and not tetap:
        print(f"  {nama:9s} sudah ada, dilewati")
        return True
    req = urllib.request.Request(d["alamat"], headers={"User-Agent": PERAMBAN})
    try:
        with urllib.request.urlopen(req, timeout=180) as r, open(tujuan, "wb") as f:
            f.write(r.read())
        ukuran = os.path.getsize(tujuan) / 1e6
        print(f"  {nama:9s} berhasil, {ukuran:.1f} MB")
        return True
    except Exception as e:
        # Alamat terbitan pemerintah berpindah dari waktu ke waktu, dan itu
        # bukan kesalahan yang bisa kami perbaiki dari sini. Yang bisa
        # dilakukan adalah menyebut berkasnya supaya bisa dicari manual.
        print(f"  {nama:9s} GAGAL: {str(e)[:70]}")
        print(f"            cari manual: {d['berkas']}")
        return False


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hanya", choices=sorted(SUMBER), help="ambil satu sumber saja")
    p.add_argument(
        "--ulang", action="store_true", help="unduh ulang walaupun berkasnya sudah ada"
    )
    a = p.parse_args()

    os.makedirs(DIR, exist_ok=True)
    daftar = [a.hanya] if a.hanya else list(SUMBER)
    print(f"mengambil {len(daftar)} sumber ke data/raw\n")
    for nama in daftar:
        print(f"{SUMBER[nama]['guna']}")
        unduh(nama, a.ulang)
        print()

    print(
        "Catatan: model bisa dilatih dan dijalankan tanpa satu pun berkas "
        "ini,\nkarena tarif yang sudah diekstrak ikut di data/processed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(utama())
