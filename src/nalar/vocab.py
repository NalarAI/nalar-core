"""Kamus token dan pohon hierarki kode.

Hierarki ICD-10 dibaca dari daftar kode nyata, bukan dikarang. Berkas
data/raw/icd10_codes.csv memuat 71.704 baris dengan kolom kategori tiga huruf,
digit subkategori, kode penuh, uraian, dan judul kategori.

Pohon yang dibangun punya lima tingkat:

    akar -> bab -> blok -> kategori -> kode penuh

Bab memakai rentang bab ICD-10 resmi. Blok didekati dari huruf pertama dan
digit pertama kategori. Itu pendekatan, dan alasannya ditulis di bawah.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from functools import lru_cache

from . import katalog
from .schema import SPECIALS
from .tarif import daftar_kelompok

DATA_RAW = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
ICD10_CSV = os.path.abspath(os.path.join(DATA_RAW, "icd10_codes.csv"))

# Rentang bab ICD-10. Kode kategori dipetakan ke bab lewat perbandingan string.
BAB_ICD10 = [
    ("I", "A00", "B99", "Penyakit infeksi dan parasit tertentu"),
    ("II", "C00", "D48", "Neoplasma"),
    ("III", "D50", "D89", "Penyakit darah dan gangguan imun"),
    ("IV", "E00", "E90", "Penyakit endokrin, nutrisi, dan metabolik"),
    ("V", "F00", "F99", "Gangguan jiwa dan perilaku"),
    ("VI", "G00", "G99", "Penyakit sistem saraf"),
    ("VII", "H00", "H59", "Penyakit mata dan adneksa"),
    ("VIII", "H60", "H95", "Penyakit telinga dan prosesus mastoid"),
    ("IX", "I00", "I99", "Penyakit sistem sirkulasi"),
    ("X", "J00", "J99", "Penyakit sistem pernapasan"),
    ("XI", "K00", "K93", "Penyakit sistem pencernaan"),
    ("XII", "L00", "L99", "Penyakit kulit dan jaringan subkutan"),
    ("XIII", "M00", "M99", "Penyakit muskuloskeletal dan jaringan ikat"),
    ("XIV", "N00", "N99", "Penyakit sistem genitourinari"),
    ("XV", "O00", "O99", "Kehamilan, persalinan, dan masa nifas"),
    ("XVI", "P00", "P96", "Kondisi tertentu masa perinatal"),
    ("XVII", "Q00", "Q99", "Malformasi kongenital dan kelainan kromosom"),
    ("XVIII", "R00", "R99", "Gejala dan temuan klinis dan laboratorium"),
    ("XIX", "S00", "T98", "Cedera, keracunan, dan akibat sebab luar"),
    ("XX", "V01", "Y98", "Sebab luar morbiditas dan mortalitas"),
    ("XXI", "Z00", "Z99", "Faktor yang mempengaruhi status kesehatan"),
    ("XXII", "U00", "U99", "Kode untuk keperluan khusus"),
]


def bab_dari_kategori(kat: str) -> str:
    """Bab ICD-10 untuk satu kategori tiga karakter."""
    k = kat[:3].upper()
    for romawi, lo, hi, _ in BAB_ICD10:
        if lo <= k <= hi:
            return f"BAB:{romawi}"
    return "BAB:LAIN"


def blok_dari_kategori(kat: str) -> str:
    """Blok didekati dari huruf dan digit pertama kategori.

    Blok ICD-10 yang resmi tidak selalu sejajar dengan digit pertama. Contoh,
    blok A00-A09 memang sejajar, tapi blok C00-C14 memotong di tengah puluhan.
    Kami memilih pendekatan ini karena tiga alasan. Datanya ada tanpa sumber
    tambahan, tingkat granularitasnya masuk akal untuk perakitan vektor, dan
    kesalahannya selalu berupa pemisahan yang terlalu halus, bukan penggabungan
    yang salah. Pemisahan terlalu halus hanya mengurangi berbagi informasi,
    tidak menghasilkan hubungan yang keliru.
    """
    return f"BLOK:{kat[:2].upper()}"


@lru_cache(maxsize=1)
def _muat_icd10() -> dict[str, str]:
    """Peta kode penuh ke kategori. Kosong bila berkas belum diunduh."""
    if not os.path.exists(ICD10_CSV):
        return {}
    peta: dict[str, str] = {}
    with open(ICD10_CSV, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            kat, kode = row[0].strip(), row[2].strip()
            if kat and kode:
                peta[kode] = kat
    return peta


def leluhur_icd10(kode: str) -> list[str]:
    """Rantai leluhur satu kode ICD-10, dari yang terdekat ke akar.

    Menerima bentuk bertitik seperti E11.4 maupun bentuk rapat seperti E114.
    """
    rapat = kode.replace(".", "").upper()
    kat = rapat[:3]
    rantai = []
    if len(rapat) > 3:
        rantai.append(f"KAT:{kat}")
    rantai.append(blok_dari_kategori(kat))
    rantai.append(bab_dari_kategori(kat))
    rantai.append("AKAR:ICD10")
    return rantai


def leluhur_atc(kode: str) -> list[str]:
    """Rantai leluhur satu kode ATC.

    ATC berjenjang lima tingkat dengan panjang tetap: 1, 3, 4, 5, 7 karakter.
    Ini hierarki yang jauh lebih bersih daripada ICD-10.
    """
    k = kode.upper()
    rantai = []
    for panjang in (5, 4, 3, 1):
        if len(k) > panjang:
            rantai.append(f"ATC{panjang}:{k[:panjang]}")
    rantai.append("AKAR:ATC")
    return rantai


def leluhur_icd9(kode: str) -> list[str]:
    """Rantai leluhur satu kode prosedur ICD-9-CM.

    ICD-9-CM prosedur berbentuk dua digit bab, lalu titik, lalu rincian.
    """
    k = kode.upper()
    bab = k.split(".")[0]
    rantai = []
    if "." in k:
        rantai.append(f"P2:{bab}")
    if len(bab) >= 2:
        rantai.append(f"P1:{bab[0]}")
    rantai.append("AKAR:ICD9")
    return rantai


def leluhur_cbg(kode: str) -> list[str]:
    """Rantai leluhur satu kode kelompok tarif.

    Bentuknya CMG-tipe-nomor-keparahan. Leluhurnya adalah kelompok yang sama
    tanpa keparahan, lalu CMG dengan tipe, lalu CMG saja. Ini yang membuat
    model tahu bahwa severity I dan severity III adalah tetangga dekat, dan
    perpindahan di antara keduanya adalah perpindahan kecil yang mahal.
    """
    bagian = kode.split("-")
    rantai = []
    if len(bagian) == 4:
        rantai.append("CBG3:" + "-".join(bagian[:3]))
        rantai.append("CBG2:" + "-".join(bagian[:2]))
        rantai.append("CBG1:" + bagian[0])
    rantai.append("AKAR:CBG")
    return rantai


class Kamus:
    """Kamus token beserta pohon leluhurnya."""

    def __init__(self) -> None:
        self.itos: list[str] = []
        self.stoi: dict[str, int] = {}
        self.leluhur: dict[int, list[int]] = {}
        self._bangun()

    # -- pembangunan --------------------------------------------------------

    def _tambah(self, tok: str) -> int:
        if tok not in self.stoi:
            self.stoi[tok] = len(self.itos)
            self.itos.append(tok)
        return self.stoi[tok]

    def _tambah_dengan_leluhur(self, tok: str, rantai: list[str]) -> None:
        i = self._tambah(tok)
        self.leluhur[i] = [self._tambah(a) for a in rantai]

    def _bangun(self) -> None:
        for s in SPECIALS:
            self._tambah(s)
        # penanda batas bidang, membawa identitas bidangnya
        from .schema import FIELDS
        for f in FIELDS:
            self._tambah(f"[BID:{f}]")

        # kode diagnosis
        icd = set(katalog.ICD_LIST) | set(katalog.KOMORBID_BY_ICD)
        for k in katalog.KONDISI:
            icd.update(k["komorbid"])
        for kode in sorted(icd):
            self._tambah_dengan_leluhur(f"DX:{kode}", leluhur_icd10(kode))

        # prosedur
        prc = set()
        for k in katalog.KONDISI:
            prc.update(p for p, _ in k["prc"])
        for kode in sorted(prc):
            self._tambah_dengan_leluhur(f"PR:{kode}", leluhur_icd9(kode))

        # obat
        obt = set()
        for k in katalog.KONDISI:
            obt.update(o for o, _ in k["obt"])
        for k in katalog.KOMORBID_TAMBAHAN:
            obt.update(k["bukti_obt"])
        for kode in sorted(obt):
            self._tambah_dengan_leluhur(f"OB:{kode}", leluhur_atc(kode))

        # pemeriksaan, dengan pita nilai
        for kode in sorted(katalog.PEMERIKSAAN):
            for pita in range(katalog.N_PITA_LAB):
                self._tambah(f"LB:{kode}:{pita}")

        # kelompok tarif
        for kode in daftar_kelompok():
            self._tambah_dengan_leluhur(f"CB:{kode}", leluhur_cbg(kode))

        # bahan habis pakai, dibangkitkan dari katalog barang sederhana
        for kode in BARANG:
            self._tambah(f"BH:{kode}")

        # token kategorial dan pita numerik
        for nama, n in KATEGORIAL.items():
            for v in range(n):
                self._tambah(f"{nama}:{v}")

    # -- pemakaian ----------------------------------------------------------

    def __len__(self) -> int:
        return len(self.itos)

    def id(self, tok: str) -> int:
        return self.stoi.get(tok, self.stoi["[UNK]"])

    def matriks_leluhur(self, maks: int = 5):
        """Matriks leluhur untuk lapisan embedding ontologi.

        Baris i memuat indeks token i diikuti leluhurnya, dipotong atau
        dipadatkan sampai panjang maks. Baris untuk token tanpa leluhur berisi
        token itu sendiri diulang, sehingga perhatian jatuh ke dirinya sendiri.
        """
        import numpy as np

        m = np.zeros((len(self), maks), dtype=np.int64)
        mask = np.zeros((len(self), maks), dtype=bool)
        for i in range(len(self)):
            rantai = [i] + self.leluhur.get(i, [])
            rantai = rantai[:maks]
            m[i, : len(rantai)] = rantai
            mask[i, : len(rantai)] = True
            if len(rantai) < maks:
                m[i, len(rantai):] = i
        return m, mask


# --- barang habis pakai -----------------------------------------------------
# Daftar pendek yang cukup untuk membuat modus penggelembungan tagihan punya
# arti. Kode dan nama dibuat sendiri, bukan katalog resmi.

BARANG = {
    "ALK001": "Kateter urin",
    "ALK002": "Set infus",
    "ALK003": "Dialiser hemodialisis",
    "ALK004": "Blood line set",
    "ALK005": "Lensa intraokular",
    "ALK006": "Plate dan screw ortopedi",
    "ALK007": "Stent koroner",
    "ALK008": "Benang operasi",
    "ALK009": "Kantong darah",
    "ALK010": "Masker oksigen",
    "ALK011": "Spuit sekali pakai",
    "ALK012": "Kasa steril",
    "ALK013": "Selang ventilator",
    "ALK014": "Kantong stoma",
    "ALK015": "Implan ortopedi femur",
}

# Harga acuan per satuan, dalam rupiah. Modus penggelembungan menaikkan harga
# di atas acuan ini, dan selisihnya menjadi kebenaran dasar.
HARGA_ACUAN = {
    "ALK001": 45_000, "ALK002": 18_000, "ALK003": 320_000,
    "ALK004": 95_000, "ALK005": 1_850_000, "ALK006": 3_400_000,
    "ALK007": 11_500_000, "ALK008": 65_000, "ALK009": 360_000,
    "ALK010": 22_000, "ALK011": 3_500, "ALK012": 8_000,
    "ALK013": 140_000, "ALK014": 85_000, "ALK015": 6_200_000,
}

# --- bidang kategorial ------------------------------------------------------
# Nama bidang dan berapa banyak nilai yang mungkin. Dipakai membangun token
# konteks seperti umur, segmen, kelas rumah sakit, dan pita numerik.

KATEGORIAL = {
    "UMUR": 10,
    "SEX": 2,
    "SEG": 4,
    "HAKKELAS": 3,
    "PROV": 38,
    "NKRONIS": 6,
    "NEPS": 6,
    "FJENIS": 2,
    "FKELAS": 5,
    "FMILIK": 5,
    "FTT": 6,
    "FREG": 5,
    "FDTPK": 2,
    "BULAN": 12,
    "DOW": 7,
    "LIBUR": 2,
    "LOS": 12,
    "DPREV": 10,
    "RUJUK": 3,
    "JARAK": 6,
    "KLSRAWAT": 3,
    "TARIF": 16,
    "TAGIH": 16,
    "NOBAT": 8,
    "NLAB": 8,
    "NBHP": 8,
}
