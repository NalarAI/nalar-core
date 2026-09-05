"""Penokenan episode klaim.

Satu episode menjadi barisan token bertipe. Tiap token membawa dua hal: apa
isinya, dan dari bidang mana ia berasal. Bidang itu yang nanti dipakai untuk
menutup bagian tertentu dan menebaknya dari bagian lain.

Urutan bidang tetap: konteks dulu, isi klinis di tengah, tarif di akhir.
Bukan sekadar rapi. Urutan ini membuat penutupan bidang TRF setara dengan
pertanyaan berapa tarif yang wajar untuk episode seperti ini, dan itu
pertanyaan yang paling berharga bagi pembayar.

Perbedaan antara [HILANG] dan [TUTUP] disengaja. Kalau tidak dibedakan, model
akan belajar bahwa laboratorium yang kosong sama dengan laboratorium yang
disembunyikan. Di Indonesia kosong itu wajar, terutama di FKTP tanpa alat.
"""

from __future__ import annotations

import numpy as np

from . import katalog as K
from .schema import EPS, FIELD_ID, MASK, MISS, PAD, MAX_SEQ

# batas jumlah token per bidang berulang, dipotong menurut prioritas
BATAS = {"DXS": 9, "PRC": 6, "OBT": 10, "LAB": 10, "BHP": 8}


def bid(f: str) -> str:
    return f"[BID:{f}]"


class Penoken:
    def __init__(self, kamus, tepi_tarif=None, tepi_tagih=None):
        self.kamus = kamus
        self.tepi_tarif = tepi_tarif
        self.tepi_tagih = tepi_tagih

    # -- pemitaan nilai uang ------------------------------------------------

    @staticmethod
    def pelajari_tepi(nilai, n_pita: int = 16):
        """Tepi pita dari kuantil korpus.

        Biaya klaim berekor sangat panjang. Memitakan menurut kuantil, bukan
        menurut lebar yang sama, membuat tiap pita punya contoh yang banyak.
        """
        v = np.asarray([x for x in nilai if x > 0], dtype=np.float64)
        if v.size == 0:
            return np.array([0.0])
        q = np.linspace(0, 100, n_pita + 1)[1:-1]
        return np.unique(np.percentile(v, q))

    @staticmethod
    def pita(nilai: float, tepi) -> int:
        if tepi is None or len(tepi) == 0:
            return 0
        return int(np.searchsorted(tepi, nilai, side="right"))

    # -- pemitaan lain ------------------------------------------------------

    @staticmethod
    def pita_los(los: int) -> int:
        if los <= 0:
            return 0
        for i, batas in enumerate([1, 2, 3, 4, 5, 7, 10, 14, 21, 30]):
            if los <= batas:
                return i + 1
        return 11

    @staticmethod
    def pita_dprev(d: int) -> int:
        """Selisih hari terhadap episode sebelumnya.

        Pita pertama untuk peserta yang belum punya episode sebelumnya.
        Sisanya berjenjang, rapat di awal karena selisih satu hari dan tiga
        hari berbeda besar maknanya, sedangkan tiga ratus dan tiga ratus tiga
        hampir sama.
        """
        if d < 0:
            return 0
        for i, batas in enumerate([1, 3, 7, 14, 30, 90, 180, 365]):
            if d <= batas:
                return i + 1
        return 9

    @staticmethod
    def pita_jumlah(n: int) -> int:
        """Pita jumlah barang habis pakai.

        Ditambahkan setelah pembedahan menunjukkan barang fiktif dan harga
        digelembungkan menyumbang lebih dari separuh selisih rupiah, sementara
        tidak satu pun kepala punya mekanisme melihatnya. Tanpa jumlah di
        dalam token, model hanya bisa menebak barang apa yang wajar, bukan
        berapa banyak, padahal modusnya persis menambah jumlah.
        """
        if n <= 0:
            return 0
        for i, batas in enumerate([1, 2, 4, 8, 16]):
            if n <= batas:
                return i + 1
        return 6

    @staticmethod
    def pita_tt(tt: int) -> int:
        if tt <= 0:
            return 0
        for i, batas in enumerate([50, 100, 200, 400, 800]):
            if tt <= batas:
                return i + 1
        return 5

    # -- penokenan ----------------------------------------------------------

    def tokenkan(self, r: dict):
        """Ubah satu episode menjadi (token, bidang, delta_hari)."""
        V = self.kamus
        tok: list[int] = []
        fld: list[int] = []

        def tambah(t: str, f: str):
            tok.append(V.id(t))
            fld.append(FIELD_ID[f])

        tok.append(V.id(EPS))
        fld.append(FIELD_ID["PSN"])

        # PSN
        tambah(bid("PSN"), "PSN")
        for nama, nilai in (("UMUR", r["umur"]), ("SEX", r["sex"]),
                            ("SEG", r["segmen"]), ("HAKKELAS", r["hak_kelas"] - 1),
                            ("PROV", r["prov"])):
            tambah(f"{nama}:{nilai}", "PSN")

        # RWY
        tambah(bid("RWY"), "RWY")
        tambah(f"NKRONIS:{min(r['n_kronis'], 5)}", "RWY")
        tambah(f"NEPS:{min(r['n_eps'], 5)}", "RWY")

        # FKS
        tambah(bid("FKS"), "FKS")
        kelas_idx = {"A": 0, "B": 1, "C": 2, "D": 3, "FKTP": 4}[r["f_kelas"]]
        for nama, nilai in (("FJENIS", r["f_jenis"]), ("FKELAS", kelas_idx),
                            ("FMILIK", r["f_milik"]),
                            ("FTT", self.pita_tt(r["f_tt"])),
                            ("FREG", r["f_reg"]), ("FDTPK", r["f_dtpk"])):
            tambah(f"{nama}:{nilai}", "FKS")

        # WKT
        tambah(bid("WKT"), "WKT")
        for nama, nilai in (("BULAN", min(r["bulan"], 11)), ("DOW", r["dow"]),
                            ("LIBUR", r["libur"]),
                            ("LOS", self.pita_los(r["los"])),
                            ("DPREV", self.pita_dprev(r["d_prev"]))):
            tambah(f"{nama}:{nilai}", "WKT")

        # RJK
        tambah(bid("RJK"), "RJK")
        tambah(f"RUJUK:{r['rujuk']}", "RJK")

        # DXP
        tambah(bid("DXP"), "DXP")
        tambah(f"DX:{r['dxp']}", "DXP")

        # DXS
        tambah(bid("DXS"), "DXS")
        if r["dxs"]:
            for c in r["dxs"][: BATAS["DXS"]]:
                tambah(f"DX:{c}", "DXS")
        else:
            tambah(MISS, "DXS")

        # PRC
        tambah(bid("PRC"), "PRC")
        if r["prc"]:
            for c in r["prc"][: BATAS["PRC"]]:
                tambah(f"PR:{c}", "PRC")
        else:
            tambah(MISS, "PRC")

        # OBT
        tambah(bid("OBT"), "OBT")
        if r["obt"]:
            for c in r["obt"][: BATAS["OBT"]]:
                tambah(f"OB:{c}", "OBT")
        else:
            tambah(MISS, "OBT")

        # LAB. Kosong karena faskes tidak punya alat dibedakan dari kosong
        # karena tidak ada pemeriksaan yang diminta.
        tambah(bid("LAB"), "LAB")
        if r["lab"]:
            for kode, nilai in r["lab"][: BATAS["LAB"]]:
                tambah(f"LB:{kode}:{K.pita_lab(kode, nilai)}", "LAB")
        else:
            tambah(MISS, "LAB")

        # BHP
        tambah(bid("BHP"), "BHP")
        if r["bhp"]:
            for kode, jml in r["bhp"][: BATAS["BHP"]]:
                tambah(f"BH:{kode}:{self.pita_jumlah(jml)}", "BHP")
        else:
            tambah(MISS, "BHP")

        # TRF
        tambah(bid("TRF"), "TRF")
        tambah(f"CB:{r['cbg']}", "TRF")
        tambah(f"KLSRAWAT:{r['kelas_rawat'] - 1}", "TRF")
        tambah(f"TARIF:{self.pita(r['tarif'], self.tepi_tarif)}", "TRF")
        tambah(f"TAGIH:{self.pita(r.get('tagih_bhp', 0), self.tepi_tagih)}", "TRF")

        # potong dan padatkan
        tok = tok[:MAX_SEQ]
        fld = fld[:MAX_SEQ]
        n = len(tok)
        pad = V.id(PAD)
        tok = tok + [pad] * (MAX_SEQ - n)
        fld = fld + [0] * (MAX_SEQ - n)
        return np.array(tok, dtype=np.int32), np.array(fld, dtype=np.int8), n

    def posisi_bidang(self, fld: np.ndarray, n: int, bidang: str) -> np.ndarray:
        """Indeks token milik satu bidang, tanpa penanda batasnya."""
        f = FIELD_ID[bidang]
        idx = np.flatnonzero((fld[:n] == f))
        # buang token penanda batas, yaitu token pertama tiap bidang
        return idx[1:] if len(idx) > 1 else idx
