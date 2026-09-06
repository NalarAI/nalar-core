"""Penjaga A1: tidak ada angka pada teks yang tidak berasal dari alat.

Target A1 berbunyi nol pelanggaran dari lima ratus berkas, dan target itu
yang paling keras di antara tujuh target lapisan agen. Satu angka karangan
pada surat yang dikirim ke rumah sakit cukup untuk menghabisi kepercayaan
pada seluruh sistem, dan tidak ada peringatan di antarmuka yang bisa
menambalnya.

Penjaga ini dibuat sebelum ada agen sama sekali. Alasannya: kalau penjaganya
baru ditulis setelah agennya jadi, yang terjadi bukan penjagaan melainkan
penyesuaian penjaga terhadap kelakuan agen.

Cara kerjanya sederhana dan sengaja tidak pintar. Seluruh angka pada teks
diambil, lalu tiap satunya dicari pada himpunan angka yang pernah
dikembalikan alat. Angka yang lolos hanya yang benar benar sama, atau yang
merupakan pembulatan sah dari angka alat, atau yang tercatat pada daftar
angka yang boleh muncul tanpa alat.
"""

from __future__ import annotations

import re

from .jejak import Jejak

# Angka yang boleh muncul tanpa berasal dari alat, karena ia bagian dari
# nama, bukan besaran yang dihitung. Ditulis satu satu, tidak dibuat aturan
# umum, supaya tiap penambahan harus disengaja.
BEBAS = {
    3.0,  # Permenkes 3 Tahun 2023
    16.0,  # Permenkes 16 Tahun 2019
    2019.0,
    2023.0,
    2026.0,
}

_ANGKA = re.compile(r"\d[\d.]*(?:,\d+)?")

# Penanda: potongan tanpa spasi yang memuat huruf sekaligus angka. Nomor
# berkas K00000401, kode modus M04, dan kelompok tarif C-4-10-III semuanya
# nama, bukan besaran, dan angkanya tidak berasal dari perhitungan apa pun.
_PENANDA = re.compile(r"\S*[A-Za-z]\S*")


def _tanpa_penanda(teks: str) -> str:
    return " ".join(
        "" if (_PENANDA.fullmatch(t) and any(c.isdigit() for c in t)) else t
        for t in teks.split()
    )


def angka_pada(teks: str) -> list[float]:
    """Seluruh besaran pada teks, titik ribuan dan koma desimal.

    Penanda dibuang lebih dulu. Tanpa itu, nomor berkas K00000401 terbaca
    sebagai angka 401 dan penjaganya menuduh penyusun mengarang angka yang
    sebenarnya bagian dari nama.
    """
    keluar = []
    for m in _ANGKA.finditer(_tanpa_penanda(teks)):
        s = m.group(0).rstrip(".")
        try:
            keluar.append(float(s.replace(".", "").replace(",", ".")))
        except ValueError:
            continue
    return keluar


def _cocok(n: float, sumber: set[float]) -> bool:
    if n in sumber or n in BEBAS:
        return True
    # Pembulatan sah: angka alat yang dibulatkan ke rupiah penuh, ke satu
    # angka di belakang koma, atau ke juta rupiah.
    for s in sumber:
        if abs(s - n) < 0.51:
            return True
        if abs(round(s, 1) - n) < 1e-9 or abs(round(s, 2) - n) < 1e-9:
            return True
        if s and abs(s / 1e6 - n) < 0.051:
            return True
    return False


def angka_tak_bersumber(teks: str, jejak: Jejak) -> list[float]:
    """Angka pada teks yang tidak bisa ditelusuri ke satu pun hasil alat."""
    sumber = jejak.angka_terkumpul()
    return [n for n in angka_pada(teks) if not _cocok(n, sumber)]


def periksa_a1(teks: str, jejak: Jejak) -> dict:
    """Putusan A1 untuk satu berkas perkara, beserta angka yang melanggar."""
    liar = angka_tak_bersumber(teks, jejak)
    utuh, sebab = jejak.periksa_rantai()
    return {
        "lulus": not liar and utuh,
        "angka_tak_bersumber": liar,
        "rantai_utuh": utuh,
        "sebab_rantai": sebab,
        "n_angka_diperiksa": len(angka_pada(teks)),
    }
