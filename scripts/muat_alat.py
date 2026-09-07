"""Memuat dua tabel yang dibutuhkan alat agen di fungsi tanpa peladen.

Alat agen membaca keadaan data di dalam memori, dan keadaan itu menuntut
proses Python besar. Fungsi tanpa peladen tidak bisa memuatnya, jadi dua
sumbernya dipindahkan ke basis data.

Tabel berkas berisi keluaran alat ambil_berkas apa adanya, medan demi medan.
Tidak disederhanakan, karena menyederhanakannya mengubah apa yang dilihat
model dan membuat seluruh angka yang sudah diukur tidak berlaku lagi.

Tabel tarif berisi lampiran Permenkes utuh. Tidak disaring sesuai klaim yang
ada di peragaan, karena penyaringan membuat cari_tarif menolak kode yang
sebenarnya ada, dan penolakan palsu itu terbawa ke berkas perkara.

Skema keduanya di db/berkas.sql dan db/tarif.sql, pasang lebih dulu.

Jalankan:
    python scripts/muat_alat.py --tarif
    python scripts/muat_alat.py --berkas
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from muat_db import Db, baca_env  # noqa: E402


def muat_tarif(db: Db) -> int:
    """Salin seluruh lampiran tarif. Tidak butuh keadaan data sama sekali."""
    from nalar.tarif_resmi import CSV_TARIF

    if not os.path.exists(CSV_TARIF):
        print(f"Tabel tarif tidak ada di {CSV_TARIF}")
        return 2

    # Kuncinya ganda di dalam berkasnya sendiri. Versi di memori memakai
    # kamus, jadi baris terakhir menang tanpa ada yang tahu. Tabelnya
    # harus meniru itu persis, karena kalau yang menang berbeda maka
    # alat cari_tarif menjawab angka lain di fungsi tanpa peladen
    # daripada di peladen, dan bedanya tidak akan terlihat siapa pun.
    peta = {}
    with open(CSV_TARIF, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kunci = (r["kode"], int(r["regional"]), r["kelas_rs"], r["kepemilikan"])
            peta[kunci] = {
                "kode": r["kode"],
                "regional": int(r["regional"]),
                "kelas_rs": r["kelas_rs"],
                "kepemilikan": r["kepemilikan"],
                "tarif_kelas3": int(r["tarif_kelas3"]),
                "tarif_kelas2": int(r["tarif_kelas2"]),
                "tarif_kelas1": int(r["tarif_kelas1"]),
            }
    baris = list(peta.values())
    print(f"    {len(baris)} baris tarif, sesudah kunci ganda dipilih yang terakhir")
    t = time.time()
    for i in range(0, len(baris), 1000):
        db._panggil(
            "POST",
            "tarif",
            baris[i : i + 1000],
            {"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
        if (i // 1000) % 10 == 0:
            print(f"    {min(i + 1000, len(baris))}/{len(baris)}")
    print(f"    selesai dalam {time.time() - t:.0f} detik")
    return 0


def muat_berkas(
    db: Db, peserta: int, tahun: int, benih: int, fktp: int, fkrtl: int
) -> int:
    """Salin keluaran ambil_berkas untuk klaim yang ada di antrean peragaan.

    Yang dimuat cuma klaim yang sudah punya barisnya di tabel perkara, karena
    itu yang bisa dibuka pengunjung. Memuat seluruh klaim berarti menyalin
    ratusan ribu baris yang tidak pernah dilihat siapa pun.
    """
    import json

    from nalar.agen.alat import Perkakas
    from nalar.agen.jejak import Jejak
    from nalar.api.keadaan import Keadaan

    ada = json.loads(db._panggil("GET", "perkara?select=klaim_id").decode())
    perlu = {r["klaim_id"] for r in ada}
    print(f"    {len(perlu)} klaim ada di tabel perkara")

    print("    menyiapkan keadaan, ini yang paling lama")
    t = time.time()
    K = Keadaan(n_peserta=peserta, tahun=tahun, seed=benih, n_fktp=fktp, n_fkrtl=fkrtl)
    K.bangun(alpha=0.02)
    print(f"    siap dalam {time.time() - t:.0f} detik, {len(K.episodes)} klaim")

    p = Perkakas(K, Jejak(perkara="muat"))
    baris = []
    for kid in sorted(perlu):
        try:
            r = p.panggil("ambil_berkas", id=kid)
        except Exception as e:  # noqa: BLE001
            print(f"    {kid} dilewati: {type(e).__name__}")
            continue
        baris.append(r)
    print(f"    {len(baris)} baris disusun")

    for i in range(0, len(baris), 500):
        db._panggil(
            "POST",
            "berkas",
            baris[i : i + 500],
            {"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
    print(f"    {len(baris)} baris ditulis ke nalar.berkas")
    return 0


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tarif", action="store_true")
    p.add_argument("--berkas", action="store_true")
    p.add_argument("--peserta", type=int, default=8000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--fktp", type=int, default=400)
    p.add_argument("--fkrtl", type=int, default=80)
    p.add_argument("--benih", type=int, default=7)
    a = p.parse_args()
    if not (a.tarif or a.berkas):
        print("Pilih --tarif atau --berkas, atau keduanya.")
        return 2

    url, kunci = baca_env()
    db = Db(url, kunci)
    if a.tarif:
        print("[1] tabel tarif")
        if muat_tarif(db):
            return 2
    if a.berkas:
        print("[2] tabel berkas")
        if muat_berkas(db, a.peserta, a.tahun, a.benih, a.fktp, a.fkrtl):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
