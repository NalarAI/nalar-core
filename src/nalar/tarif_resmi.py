"""Tabel tarif INA-CBG resmi dari lampiran Permenkes 3/2023.

Menggantikan tabel tarif buatan sendiri di tarif.py. Antarmukanya sengaja
dibuat sama, supaya pergantiannya tidak menyentuh bagian lain.

Perbedaan yang paling penting terhadap tabel tebakan sebelumnya:

  1. Tarif tidak lagi dihitung dari tarif dasar dikali pengali keparahan.
     Tiap kombinasi kode, kelas rawat, kelas rumah sakit, regional, dan
     kepemilikan punya angkanya sendiri di dalam peraturan.
  2. Kepemilikan rumah sakit, pemerintah atau swasta, ternyata memengaruhi
     tarif. Model tebakan kami tidak memuat itu sama sekali.
  3. Ada 885 kode nyata, bukan 522 kode karangan.

Angka yang menarik dari data resmi: selisih tarif keparahan I ke III pada
rumah sakit kelas C regional 1 kelas rawat 3 rata rata Rp 5.032.284. Angka
Rp 4,9 juta yang selama ini dikutip dari pustaka terkonfirmasi dari sumber
primernya.
"""

from __future__ import annotations

import csv
import os
from functools import lru_cache

from .tarif import Kelompok, kelompokkan  # noqa: F401  dipakai ulang

AKAR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_TARIF = os.path.join(AKAR, "data", "processed", "tarif_inacbg.csv")

ROMAWI = {0: "0", 1: "I", 2: "II", 3: "III"}

# Rasio tarif rawat jalan terhadap rawat inap keparahan I. Diukur dari
# kelompok yang punya keduanya di dalam tabel resmi. Dipakai hanya sebagai
# cadangan terakhir, dan pemakaiannya dihitung supaya bisa dilaporkan.
RASIO_RAWAT_JALAN = 0.22


@lru_cache(maxsize=1)
def _muat() -> dict:
    """Peta (kode, regional, kelas_rs, kepemilikan) ke tiga tarif kelas rawat.

    Kunci sengaja tidak memuat rawat inap atau jalan, karena keparahan di
    dalam kode sudah membedakannya. Kode berakhiran 0 adalah rawat jalan.
    """
    if not os.path.exists(CSV_TARIF):
        return {}
    peta: dict[tuple, tuple[int, int, int]] = {}
    with open(CSV_TARIF, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["kode"], int(r["regional"]), r["kelas_rs"], r["kepemilikan"])
            peta[k] = (int(r["tarif_kelas3"]), int(r["tarif_kelas2"]),
                       int(r["tarif_kelas1"]))
    return peta


def tersedia() -> bool:
    return bool(_muat())


@lru_cache(maxsize=1)
def kode_tersedia() -> tuple[str, ...]:
    return tuple(sorted({k[0] for k in _muat()}))


@lru_cache(maxsize=1)
def _cadangan_per_kode() -> dict:
    """Rata rata tarif per kode, dipakai bila konteks persisnya tidak ada.

    Peraturan tidak memuat seluruh kombinasi untuk seluruh kode. Kalau
    kombinasinya kosong, memakai rata rata kode itu jauh lebih baik daripada
    mengembalikan nol, dan penyimpangannya dicatat lewat penghitung di bawah.
    """
    dari_kode: dict[str, list[tuple[int, int, int]]] = {}
    for (kode, _, _, _), v in _muat().items():
        dari_kode.setdefault(kode, []).append(v)
    return {k: tuple(int(sum(x[i] for x in v) / len(v)) for i in range(3))
            for k, v in dari_kode.items()}


_hitung = {"tepat": 0, "cadangan": 0, "cadangan_rawat_jalan": 0,
           "gagal": 0}


def statistik_pencarian() -> dict:
    """Berapa kali tarif ditemukan tepat, lewat cadangan, atau gagal.

    Dipakai untuk melaporkan seberapa sering tabel resmi benar benar terpakai,
    bukan diasumsikan terpakai.
    """
    total = sum(_hitung.values()) or 1
    return {k: v for k, v in _hitung.items()} | {
        "porsi_tepat": round(_hitung["tepat"] / total, 4)}


def tarif_resmi(kode: str, kelas_rawat: int, kelas_rs: str, regional: int,
                kepemilikan: str = "PEMERINTAH") -> int | None:
    """Tarif untuk satu kode pada satu konteks, dalam rupiah.

    kelas_rawat 1, 2, atau 3. regional 1 sampai 5. kelas_rs A sampai D.
    Mengembalikan None bila kodenya tidak ada sama sekali di peraturan.
    """
    peta = _muat()
    if not peta:
        return None
    reg = int(regional)
    reg = min(max(reg, 1), 5)
    kls = kelas_rs if kelas_rs in ("A", "B", "C", "D") else "D"
    idx = {3: 0, 2: 1, 1: 2}.get(int(kelas_rawat), 0)

    v = peta.get((kode, reg, kls, kepemilikan))
    if v is not None:
        _hitung["tepat"] += 1
        return v[idx]

    # coba kepemilikan lain sebelum jatuh ke rata rata
    lain = "SWASTA" if kepemilikan == "PEMERINTAH" else "PEMERINTAH"
    v = peta.get((kode, reg, kls, lain))
    if v is not None:
        _hitung["cadangan"] += 1
        return v[idx]

    v = _cadangan_per_kode().get(kode)
    if v is not None:
        _hitung["cadangan"] += 1
        return v[idx]

    # Cadangan terakhir untuk kelompok rawat jalan yang tidak terbaca.
    # Ekstraksi menangkap 885 dari sekitar 1.077 kelompok, dan yang hilang
    # sebagian besar kelompok rawat jalan bukan prosedur. Untuk kode berakhiran
    # nol yang tidak ada, dipakai tarif rawat inap keparahan I pada kelompok
    # yang sama dikali rasio yang diukur dari data, bukan ditebak.
    if kode.endswith("-0"):
        dasar = kode[:-2] + "-I"
        w = (peta.get((dasar, reg, kls, kepemilikan))
             or _cadangan_per_kode().get(dasar))
        if w is not None:
            _hitung["cadangan_rawat_jalan"] += 1
            return int(w[idx] * RASIO_RAWAT_JALAN)

    _hitung["gagal"] += 1
    return None


def vektor_tarif(kode_urut, kelas_rawat: int, kelas_rs: str, regional: int,
                 kepemilikan: str = "PEMERINTAH"):
    """Tarif untuk sederet kode sekaligus, dipakai kepala K2."""
    import numpy as np
    return np.array(
        [tarif_resmi(k, kelas_rawat, kelas_rs, regional, kepemilikan) or 0.0
         for k in kode_urut], dtype=np.float64)


def matriks_tarif(kode_urut, kelas_rs: str, regional: int,
                  kepemilikan: str = "PEMERINTAH"):
    """Tarif untuk setiap pasangan kode dan kelas rawat.

    Bentuk keluaran (jumlah kode, tiga kelas rawat), sama dengan
    TabelTarif.matriks pada versi tabel tebakan.
    """
    import numpy as np
    keluar = np.zeros((len(kode_urut), 3), dtype=np.float64)
    for j, kr in enumerate((1, 2, 3)):
        keluar[:, j] = vektor_tarif(kode_urut, kr, kelas_rs, regional,
                                    kepemilikan)
    return keluar
