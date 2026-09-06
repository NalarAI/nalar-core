"""Kalibrasi konformal terpisah.

Model apa pun bisa melaporkan tingkat positif palsu pada himpunan ujinya. Itu
pengamatan, bukan jaminan. Begitu dipasang di dunia nyata, angkanya tidak
berlaku lagi. Untuk sistem yang bisa menahan pembayaran rumah sakit, pengamatan
tidak cukup.

Prediksi konformal memberi jaminan bebas distribusi. Bila alpha ditetapkan satu
persen, maka di antara klaim yang berasal dari populasi yang sama dengan
himpunan kalibrasi, tidak lebih dari satu persen akan ditandai. Jaminan itu
tidak bergantung pada benar tidaknya model. Model yang buruk tetap memenuhi
jaminan, hanya saja dayanya rendah.

Dua syarat yang sering dilanggar, dan cara kami menanganinya, ditulis di bawah.
"""

from __future__ import annotations

import numpy as np


def ambang(skor_kalibrasi: np.ndarray, alpha: float) -> float:
    """Ambang konformal terpisah dengan koreksi sampel berhingga.

    Kuantil yang dipakai adalah ceil((n + 1)(1 - alpha)) / n, bukan sekadar
    kuantil ke satu dikurangi alpha. Koreksi itu yang membuat jaminannya
    berlaku pada sampel berhingga, bukan hanya secara asimtotik.
    """
    s = np.sort(np.asarray(skor_kalibrasi, dtype=np.float64))
    n = len(s)
    if n == 0:
        return float("inf")
    k = int(np.ceil((n + 1) * (1.0 - alpha)))
    if k > n:
        return float("inf")
    return float(s[k - 1])


class Kalibrator:
    """Ambang per kelompok, bukan satu ambang untuk semua.

    Syarat pertama yang sering dilanggar adalah keterpertukaran. Klaim bulan
    Januari dan bulan Desember tidak bisa dipertukarkan begitu saja. Ada musim,
    ada perubahan tarif, ada wabah. Karena itu kalibrasi dijalankan per periode.

    Syarat kedua adalah himpunan kalibrasi harus bersih. Tidak ada himpunan
    klaim yang dipastikan bersih, karena kecurangan yang tidak terdeteksi ada
    di dalamnya. Jaminan yang kami klaim karena itu adalah jaminan terhadap
    laju penandaan pada populasi umum, bukan terhadap populasi yang benar benar
    bersih. Pelemahan itu jujur dan tetap berguna.

    Kalibrasi per kelompok melemahkan jaminan menjadi jaminan bersyarat
    kelompok. Itu justru lebih berguna, karena ia menjamin rumah sakit kecil
    tidak ditandai lebih sering daripada rumah sakit besar.
    """

    def __init__(self, alpha: float = 0.01, minimal_kelompok: int = 200):
        self.alpha = alpha
        self.minimal = minimal_kelompok
        self.ambang_kelompok: dict[object, float] = {}
        self.ambang_global: float = float("inf")

    def pasang(self, skor: np.ndarray, kelompok=None):
        skor = np.asarray(skor, dtype=np.float64)
        self.ambang_global = ambang(skor, self.alpha)
        self.ambang_kelompok = {}
        if kelompok is None:
            return self
        kelompok = np.asarray(kelompok)
        for k in np.unique(kelompok):
            m = kelompok == k
            if int(m.sum()) >= self.minimal:
                self.ambang_kelompok[k] = ambang(skor[m], self.alpha)
        return self

    def ambang_untuk(self, kelompok=None) -> np.ndarray | float:
        if kelompok is None:
            return self.ambang_global
        kelompok = np.asarray(kelompok)
        out = np.full(len(kelompok), self.ambang_global, dtype=np.float64)
        for k, v in self.ambang_kelompok.items():
            out[kelompok == k] = v
        return out

    def tandai(self, skor: np.ndarray, kelompok=None) -> np.ndarray:
        return np.asarray(skor) > self.ambang_untuk(kelompok)


def periksa_jaminan(
    skor_uji: np.ndarray, bersih: np.ndarray, kal: Kalibrator, kelompok=None
) -> dict:
    """Apakah jaminannya benar benar terpenuhi secara empiris.

    Ini uji T2 pada rancangan. Bila alpha satu persen, laju penandaan terukur
    pada klaim bersih tidak boleh melebihi satu setengah persen.
    """
    tanda = kal.tandai(skor_uji, kelompok)
    b = np.asarray(bersih).astype(bool)
    laju = float(tanda[b].mean()) if b.any() else float("nan")
    return dict(
        alpha=kal.alpha,
        laju_penandaan_klaim_bersih=round(laju, 5),
        batas_lulus=round(kal.alpha * 1.5, 5),
        lulus=bool(laju <= kal.alpha * 1.5),
        n_bersih=int(b.sum()),
        n_ditandai=int(tanda.sum()),
    )


def ambang_sadar_faskes(nilai, faskes_id, alpha: float, minimal_sisa: int = 100):
    """Ambang konformal yang memperhitungkan sedikitnya jumlah faskes.

    Jaminan konformal berlaku bila klaim kalibrasi dan klaim uji saling
    terpertukarkan. Kami memisah latih dan uji menurut faskes, bukan menurut
    klaim, karena pemisahan acak per klaim menyesatkan. Konsekuensinya sering
    terlewat: ukuran contoh yang menentukan bukan lagi banyaknya klaim,
    melainkan banyaknya faskes.

    Terukurnya begini. Kelompok faskes di daerah tertinggal punya 1.522 klaim
    uji, terdengar banyak, tapi klaim itu datang dari 19 faskes saja, dan
    kalibrasinya dari 39. Ambang yang dihitung seolah olah dari 1.522 contoh
    bebas ternyata menandai 2,53 persen klaim bersih, padahal alpha dua
    persen. Selisihnya bukan kesialan, melainkan ragam antar faskes yang
    tidak pernah masuk hitungan.

    Caranya: satu faskes dikeluarkan bergantian, ambang dihitung ulang, lalu
    yang terbesar dipakai. Pada kelompok dengan banyak faskes, mengeluarkan
    satu faskes hampir tidak mengubah apa apa, jadi hasilnya kembali ke
    ambang biasa. Pada kelompok dengan sedikit faskes, satu faskes yang
    ekstrem akan terlihat, dan ambangnya melebar sesuai. Ongkosnya kelompok
    kecil menandai lebih sedikit, dan itu memang harga yang benar untuk tidak
    tahu banyak tentang mereka.
    """
    nilai = np.asarray(nilai, dtype=np.float64)
    faskes_id = np.asarray(faskes_id)
    dasar = ambang(nilai, alpha)
    unik = np.unique(faskes_id)
    if len(unik) < 2:
        return dasar
    tertinggi = dasar
    for f in unik:
        sisa = faskes_id != f
        if sisa.sum() < minimal_sisa:
            continue
        t = ambang(nilai[sisa], alpha)
        if t > tertinggi:
            tertinggi = t
    return tertinggi
