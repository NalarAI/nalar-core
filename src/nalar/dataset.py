"""Penyiapan data latih dan penutupan menurut peran.

Pola penutupan menentukan pertanyaan apa yang bisa dijawab model saat dipakai.
Kalau hanya dilatih dengan penutupan acak, model akan mahir menebak token acak
dan payah menebak seluruh bidang tarif sekaligus. Padahal yang kita butuhkan
saat menilai upcoding adalah persis kemampuan menebak seluruh bidang tarif
dari bukti yang menyertainya.

Penanda batas bidang tidak pernah ditutup. Ia yang memberi tahu model bidang
mana yang sedang disembunyikan, seperti auditor yang tahu ia sedang menilai
tarif, bukan menebak sedang menilai apa.
"""

from __future__ import annotations

import numpy as np

from .schema import FIELD_ID, MASK_PATTERNS, RANDOM_MASK_RATE


def bangun_array(episodes, penoken):
    """Ubah daftar episode menjadi array siap latih."""
    n = len(episodes)
    from .schema import MAX_SEQ
    tok = np.zeros((n, MAX_SEQ), dtype=np.int32)
    fld = np.zeros((n, MAX_SEQ), dtype=np.int8)
    pjg = np.zeros(n, dtype=np.int16)
    dhari = np.zeros(n, dtype=np.int32)
    for i, r in enumerate(episodes):
        t, f, m = penoken.tokenkan(r)
        tok[i], fld[i], pjg[i] = t, f, m
        dhari[i] = max(r["d_prev"], 0)
    return dict(tok=tok, fld=fld, pjg=pjg, dhari=dhari)


def bangun_meta(episodes):
    """Bidang tambahan yang dipakai evaluasi, bukan oleh model."""
    return dict(
        faskes=np.array([r["faskes"] for r in episodes], dtype=np.int32),
        f_jenis=np.array([r["f_jenis"] for r in episodes], dtype=np.int8),
        peserta=np.array([r["peserta_id"] for r in episodes], dtype=np.int32),
        hari=np.array([r["hari"] for r in episodes], dtype=np.int32),
        tarif=np.array([r["tarif"] for r in episodes], dtype=np.int64),
        tarif_j=np.array([r["tarif_j"] for r in episodes], dtype=np.int64),
        selisih=np.array([r["selisih_rp"] for r in episodes], dtype=np.int64),
        curang=np.array([1 if r["modus"] else 0 for r in episodes],
                        dtype=np.int8),
        keparahan=np.array([r["keparahan"] for r in episodes], dtype=np.int8),
        keparahan_j=np.array([r["keparahan_j"] for r in episodes],
                             dtype=np.int8),
        rawat_inap=np.array([r["rawat_inap"] for r in episodes], dtype=np.int8),
        kebijakan=np.array([r.get("kebijakan", 0) for r in episodes],
                           dtype=np.int8),
    )


class PenutupPeran:
    """Pilih pola penutupan lalu terapkan pada satu tumpukan."""

    def __init__(self, id_mask: int, id_pad: int, rng: np.random.Generator,
                 hanya_acak: bool = False):
        self.id_mask = id_mask
        self.id_pad = id_pad
        self.rng = rng
        self.hanya_acak = hanya_acak
        self.nama = list(MASK_PATTERNS.keys())
        self.peluang = np.array([MASK_PATTERNS[k][0] for k in self.nama])
        self.peluang = self.peluang / self.peluang.sum()

    def terapkan(self, tok: np.ndarray, fld: np.ndarray, pjg: np.ndarray,
                 penanda_bid: set[int]):
        """Kembalikan (tok_tertutup, sasaran, pola).

        sasaran berisi id token asli pada posisi yang ditutup, dan -100 di
        posisi lain, supaya rugi hanya dihitung di posisi yang ditutup.
        """
        B, T = tok.shape
        tok_out = tok.copy()
        sasaran = np.full((B, T), -100, dtype=np.int64)
        pola = np.zeros(B, dtype=np.int8)

        for b in range(B):
            n = int(pjg[b])
            if self.hanya_acak:
                pilih = self.nama.index("tutup_acak")
            else:
                pilih = int(self.rng.choice(len(self.nama), p=self.peluang))
            pola[b] = pilih
            nama = self.nama[pilih]
            bidang = MASK_PATTERNS[nama][1]

            if bidang is None:
                kandidat = np.flatnonzero(
                    (np.arange(T) < n)
                    & ~np.isin(tok[b], list(penanda_bid)))
                if kandidat.size == 0:
                    continue
                k = max(1, int(round(RANDOM_MASK_RATE * kandidat.size)))
                idx = self.rng.choice(kandidat, size=k, replace=False)
            else:
                ids = [FIELD_ID[f] for f in bidang]
                idx = np.flatnonzero(
                    (np.arange(T) < n) & np.isin(fld[b], ids)
                    & ~np.isin(tok[b], list(penanda_bid)))
                if idx.size == 0:
                    continue

            sasaran[b, idx] = tok[b, idx]
            tok_out[b, idx] = self.id_mask

        return tok_out, sasaran, pola


def pisah_menurut_entitas(meta, frac_uji: float = 0.2, seed: int = 0):
    """Pemisahan latih dan uji menurut faskes, bukan acak per klaim.

    Pemisahan acak akan memberi angka yang jauh lebih bagus dan sepenuhnya
    menyesatkan, karena klaim dari rumah sakit yang sama akan muncul di latih
    dan di uji. Rancangan menyebut pemisahan acak sebagai protokol terlarang.
    """
    rng = np.random.default_rng(seed)
    kunci = meta["faskes"].astype(np.int64) * 2 + meta["f_jenis"]
    unik = np.unique(kunci)
    rng.shuffle(unik)
    n_uji = max(1, int(round(len(unik) * frac_uji)))
    faskes_uji = set(unik[:n_uji].tolist())
    uji = np.array([k in faskes_uji for k in kunci])
    return ~uji, uji


def pisah_menurut_waktu(meta, hari_potong: int):
    """Pemisahan luar waktu. Latih pada masa lalu, uji pada masa depan."""
    return meta["hari"] < hari_potong, meta["hari"] >= hari_potong
