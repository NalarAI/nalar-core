"""Pemuat data nyata, untuk menguji apakah data karangan kami ada gunanya.

Dua berkas dipakai.

CMS DE-SynPUF. Klaim Medicare, dirilis publik. Perlu satu peringatan yang
harus ikut disebut setiap kali angkanya dikutip: berkas ini sendiri sudah
disintesis oleh CMS dari klaim asli demi perlindungan privasi. Jadi uji ini
bukan sintetis melawan nyata, melainkan sintetis kami melawan sintetis yang
diturunkan dari klaim asli. Struktur bersamanya diambil dari klaim betulan,
dan itulah yang membuatnya tetap berguna, tapi menyebutnya data nyata akan
melebih lebihkan.

LEIE. Daftar orang dan badan yang dikeluarkan dari program kesehatan federal
Amerika oleh kantor inspektur jenderal. Ini label kecurangan yang benar benar
terjadi, ditetapkan di luar kendali kami.

Kolom yang dipakai sengaja dibatasi pada yang ada di kedua dunia, yaitu umur,
jenis kelamin, lama rawat, banyak diagnosis, banyak prosedur. Kode diagnosis
tidak ikut, karena Amerika memakai ICD-9 dan kami ICD-10. Membiarkan kode ikut
akan membuat uji ini mustahil karena alasan yang salah.
"""

from __future__ import annotations

import csv
import io
import os
import zipfile
from datetime import date

import numpy as np

DIR_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

# Kolom yang dibagi kedua dunia. Urutannya mengikat, karena matriks fitur dari
# kedua sumber harus sejajar kolom per kolom.
KOLOM_BERSAMA = ["umur", "sex", "los", "n_dxs", "n_prc"]

# Batas atas tiap pita umur, mengikut katalog kami: 0-4, 5-14, 15-24, 25-34,
# 35-44, 45-54, 55-64, 65-74, 75-84, 85 ke atas. Umur Amerika yang satuannya
# tahun harus dipetakan ke pita yang sama sebelum diadu, kalau tidak model
# melihat angka nol sampai sembilan saat latih lalu dua puluh lima sampai
# seratus saat uji, dan kolom umur otomatis mati tanpa memberi tahu.
BATAS_PITA_UMUR = [4, 14, 24, 34, 44, 54, 64, 74, 84]


def pita_umur(tahun):
    """Umur dalam tahun menjadi indeks pita nol sampai sembilan."""
    for i, b in enumerate(BATAS_PITA_UMUR):
        if tahun <= b:
            return i
    return len(BATAS_PITA_UMUR)


def _tanggal(s):
    s = (s or "").strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def _baca_zip(nama):
    jalan = os.path.join(DIR_DATA, nama)
    z = zipfile.ZipFile(jalan)
    dalam = z.namelist()[0]
    with z.open(dalam) as f:
        t = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
        r = csv.reader(t)
        hdr = next(r)
        for baris in r:
            yield dict(zip(hdr, baris))


def muat_penerima():
    """Peta id penerima manfaat ke tanggal lahir dan jenis kelamin."""
    peta = {}
    for d in _baca_zip("desynpuf_Beneficiary_Summary_File_Sample_1.zip"):
        lahir = _tanggal(d.get("BENE_BIRTH_DT"))
        if lahir is None:
            continue
        sx = d.get("BENE_SEX_IDENT_CD", "").strip()
        peta[d["DESYNPUF_ID"]] = (lahir, 0 if sx == "1" else 1)
    return peta


def muat_rawat_inap(batas=None):
    """Klaim rawat inap DE-SynPUF sebagai baris yang sebentuk dengan episode kami.

    Yang dikembalikan hanya kolom bersama ditambah biaya dan pengenal faskes.
    """
    peta = muat_penerima()
    keluar = []
    for d in _baca_zip("desynpuf_ip.zip"):
        b = peta.get(d["DESYNPUF_ID"])
        if b is None:
            continue
        lahir, sex = b
        mulai = _tanggal(d.get("CLM_FROM_DT"))
        selesai = _tanggal(d.get("CLM_THRU_DT"))
        if mulai is None or selesai is None:
            continue
        try:
            biaya = float(d.get("CLM_PMT_AMT") or 0)
        except ValueError:
            continue
        if biaya <= 0:
            continue
        los = (selesai - mulai).days + 1
        if los < 1 or los > 120:
            continue
        umur = (mulai - lahir).days / 365.25
        if not (0 <= umur <= 110):
            continue
        n_dxs = sum(1 for i in range(2, 11)
                    if (d.get(f"ICD9_DGNS_CD_{i}") or "").strip())
        n_prc = sum(1 for i in range(1, 7)
                    if (d.get(f"ICD9_PRCDR_CD_{i}") or "").strip())
        keluar.append({
            "umur": pita_umur(umur), "umur_tahun": umur, "sex": sex,
            "los": los,
            "n_dxs": n_dxs, "n_prc": n_prc,
            "biaya": biaya, "faskes": d.get("PRVDR_NUM", ""),
            "dokter": (d.get("AT_PHYSN_NPI") or "").strip(),
        })
        if batas and len(keluar) >= batas:
            break
    return keluar


def matriks_bersama(baris):
    """Matriks fitur dari daftar kamus, memakai KOLOM_BERSAMA."""
    return np.asarray(
        [[float(r[k]) for k in KOLOM_BERSAMA] for r in baris],
        dtype=np.float64)


def matriks_dari_episode(episodes):
    """Matriks fitur yang sama, tapi dari episode buatan kami.

    Hanya episode rawat inap, karena pembandingnya klaim rawat inap.
    """
    inap = [r for r in episodes if r["rawat_inap"]]
    X = np.asarray(
        [[float(r["umur"]), float(r["sex"]), float(r["los"]),
          float(len(r["dxs"])), float(len(r["prc"]))] for r in inap],
        dtype=np.float64)
    y = np.asarray([float(r["tarif"]) for r in inap], dtype=np.float64)
    return X, y, inap


def bakukan(y):
    """Log lalu skor baku, supaya rupiah dan dolar bisa dibandingkan.

    Tanpa ini uji transfer akan gagal karena satuan mata uang, bukan karena
    strukturnya tidak berpindah. Yang diuji adalah bentuk hubungannya.
    """
    v = np.log1p(np.asarray(y, dtype=np.float64))
    return (v - v.mean()) / (v.std() + 1e-12)


def muat_leie():
    """Himpunan NPI yang dikeluarkan, beserta jumlah baris yang terbaca."""
    jalan = os.path.join(DIR_DATA, "leie.csv")
    npi = set()
    n = 0
    with open(jalan, encoding="utf-8", errors="replace", newline="") as f:
        for d in csv.DictReader(f):
            n += 1
            v = (d.get("NPI") or "").strip()
            if v and v != "0000000000" and v != "0":
                npi.add(v)
    return npi, n
