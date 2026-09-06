"""Definisi bidang episode klaim dan konstanta bersama.

Dua belas bidang, urutannya tetap: konteks dulu, isi klinis di tengah,
tarif di akhir. Urutan ini yang membuat penutupan bidang TRF setara dengan
pertanyaan berapa tarif yang wajar untuk episode seperti ini.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- bidang -----------------------------------------------------------------

FIELDS = [
    "PSN",  # peserta
    "RWY",  # riwayat
    "FKS",  # fasilitas kesehatan
    "WKT",  # waktu
    "RJK",  # rujukan
    "DXP",  # diagnosis primer
    "DXS",  # diagnosis sekunder
    "PRC",  # prosedur
    "OBT",  # obat
    "LAB",  # pemeriksaan penunjang
    "BHP",  # bahan habis pakai dan alkes
    "TRF",  # tarif
]
FIELD_ID = {f: i for i, f in enumerate(FIELDS)}
N_FIELDS = len(FIELDS)

# bidang klinis yang menjadi bukti bagi bidang tarif
EVIDENCE_FIELDS = ["DXP", "DXS", "PRC", "OBT", "LAB", "BHP"]

# --- token khusus -----------------------------------------------------------

PAD = "[PAD]"
EPS = "[EPS]"  # awal episode
MASK = "[TUTUP]"  # posisi yang sengaja ditutup saat pralatih
MISS = "[HILANG]"  # bidang yang memang tidak ada datanya
UNK = "[UNK]"
SPECIALS = [PAD, EPS, MASK, MISS, UNK]

# --- pita numerik -----------------------------------------------------------

N_BINS = 16

# --- pola penutupan menurut peran -------------------------------------------
# peluang tiap pola, dipakai saat pralatih. Lihat rancangan bagian 9.6.

MASK_PATTERNS = {
    "tutup_tarif": (0.25, ["TRF"]),
    "tutup_dxs": (0.20, ["DXS"]),
    "tutup_bukti": (0.20, ["LAB", "OBT"]),
    "tutup_prosedur": (0.10, ["PRC"]),
    "tutup_acak": (0.25, None),  # 15 persen token acak
}
RANDOM_MASK_RATE = 0.15

# Panjang terpakai pada data sintetis: rata rata 43, persentil 99 sebesar 49,
# maksimum 58. Biaya perhatian tumbuh kuadratik terhadap panjang, jadi menahan
# batas di 64 memangkas waktu latih tanpa memotong satu episode pun.
MAX_SEQ = 64


@dataclass(frozen=True)
class Segmen:
    """Segmen kepesertaan JKN."""

    PBI = 0  # penerima bantuan iuran
    PPU = 1  # pekerja penerima upah
    PBPU = 2  # pekerja bukan penerima upah, peserta mandiri
    BP = 3  # bukan pekerja

    NAMES = ("PBI", "PPU", "PBPU", "BP")


@dataclass(frozen=True)
class JenisFaskes:
    FKTP = 0
    FKRTL = 1
    NAMES = ("FKTP", "FKRTL")


# kelas rumah sakit: A, B, C, D untuk FKRTL. FKTP dipetakan ke 4.
KELAS_RS = ("A", "B", "C", "D", "FKTP")

KEPEMILIKAN = ("Pemerintah Pusat", "Pemerintah Daerah", "TNI Polri", "Swasta", "BUMN")

# regional tarif INA-CBG. Permenkes membagi tarif ke lima regional.
N_REGIONAL = 5

# hak kelas rawat peserta
KELAS_RAWAT = (1, 2, 3)
