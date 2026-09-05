"""Bandingkan beberapa keluaran percobaan berdampingan.

Dipakai untuk membaca ablasi. Tanpa alat ini, membandingkan tiga berkas JSON
berarti membuka tiga berkas dan menghitung sendiri, dan di situlah kesalahan
baca terjadi.

Jalankan:
    python scripts/banding.py runs/p6_penuh.json runs/p6_ablasi_tarif.json
"""

from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")


def ambil(d: dict, jalur, bawaan=None):
    """Ambil nilai bersarang. Jalur boleh string bertitik atau daftar kunci.

    Daftar kunci dipakai untuk kunci yang mengandung titik, misalnya "0.01"
    pada bagian konformal, yang kalau dipecah menurut titik akan salah baca.
    """
    kini = d
    bagian_bagian = jalur.split(".") if isinstance(jalur, str) else jalur
    for bagian in bagian_bagian:
        if isinstance(kini, dict) and bagian in kini:
            kini = kini[bagian]
        else:
            return bawaan
    return kini


def rp(x) -> str:
    if x is None:
        return "-"
    return f"{x / 1e6:,.1f} jt"


BARIS = [
    ("episode", "data.n_episode", None),
    ("porsi klaim terpengaruh", "data.porsi_klaim_terpengaruh", None),
    ("porsi nilai terpengaruh", "data.porsi_nilai_terpengaruh", None),
    ("ukuran kamus", "kamus.ukuran", None),
    ("parameter juta", "pralatih.parameter_juta", None),
    ("rugi pralatih awal", "pralatih.rugi_awal", None),
    ("rugi pralatih akhir", "pralatih.rugi_akhir", None),
    ("selisih tersedia di uji", "metrik._total_selisih_tersedia", "rp"),
    ("rp@50 nalar", "metrik.nalar.rupiah_pada_k.50", "rp"),
    ("rp@100 nalar", "metrik.nalar.rupiah_pada_k.100", "rp"),
    ("rp@1000 nalar", "metrik.nalar.rupiah_pada_k.1000", "rp"),
    ("rp@1000 K2+K3", "metrik_dengan_k3.nalar_k2_plus_k3.rupiah_pada_k.1000",
     "rp"),
    ("rp@1000 K3 saja", "metrik_dengan_k3.nalar_k3_saja.rupiah_pada_k.1000",
     "rp"),
    ("rp@1000 mesin aturan", "metrik.mesin_aturan.rupiah_pada_k.1000", "rp"),
    ("rp@1000 regresi berlabel", "metrik.regresi_logistik.rupiah_pada_k.1000",
     "rp"),
    ("presisi@1000 nalar", "metrik.nalar.presisi_pada_k.1000", None),
    ("lift@50 atas aturan",
     "metrik_dengan_k3.nalar_k2_plus_k3.peningkatan_atas_aturan.50", None),
    ("lift@1000 atas aturan",
     "metrik_dengan_k3.nalar_k2_plus_k3.peningkatan_atas_aturan.1000", None),
    ("K3 klaim berskor", "k3_waktu.n_klaim_berskor", None),
    ("K4 presisi@10", "k4_sebaya.presisi_sepuluh_teratas", None),
    ("K5 presisi@10", "k5_kemiripan.presisi_sepuluh_teratas", None),
    ("konformal a=0.01 laju",
     ["konformal", "0.01", "laju_penandaan_klaim_bersih"], None),
    ("konformal a=0.01 lulus", ["konformal", "0.01", "lulus"], None),
    ("rp@1000 nilai klaim saja",
     ["metrik", "nilai_klaim", "rupiah_pada_k", "1000"], "rp"),
    ("K2+K3 lift atas nilai klaim @1000",
     ["metrik_dengan_k3", "nalar_k2_plus_k3",
      "peningkatan_atas_nilai_klaim", "1000"], None),
    ("KEADILAN rasio maks min",
     "keadilan.menurut_kelas_faskes._rasio_maks_min", None),
    ("KEADILAN lulus batas 2x",
     "keadilan.menurut_kelas_faskes._lulus_batas_dua_kali", None),
    ("pelaku hati hati ambil",
     "adversarial.hati_hati.total_diambil_rp", "rp"),
    ("pelaku hati hati maks/klaim",
     "adversarial.hati_hati.maks_per_klaim_rp", "rp"),
    ("T6 penurunan maks",
     "adversarial._penurunan_keuntungan_maksimum", None),
    ("waktu detik", "waktu_total_detik", None),
]


def utama(jalur_berkas: list[str]) -> int:
    data, nama = [], []
    for j in jalur_berkas:
        if not os.path.exists(j):
            print(f"lewat, tidak ada: {j}")
            continue
        with open(j, encoding="utf-8") as f:
            data.append(json.load(f))
        nama.append(os.path.basename(j).replace(".json", ""))
    if not data:
        return 1

    lebar = max(26, max(len(n) for n in nama) + 2)
    print(f"{'':<28}" + "".join(f"{n:>{lebar}}" for n in nama))
    print("-" * (28 + lebar * len(nama)))
    for label, jalur, fmt in BARIS:
        sel = []
        for d in data:
            v = ambil(d, jalur)
            sel.append(rp(v) if fmt == "rp" else
                       ("-" if v is None else str(v)))
        print(f"{label:<28}" + "".join(f"{s:>{lebar}}" for s in sel))
    return 0


if __name__ == "__main__":
    raise SystemExit(utama(sys.argv[1:] or [
        "runs/p6_penuh.json", "runs/p6_ablasi_tarif.json",
        "runs/p6_ablasi_pralatih.json"]))
