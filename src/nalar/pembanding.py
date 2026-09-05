"""Garis dasar pembanding.

Model tanpa pembanding adalah klaim tanpa bukti. Yang paling menentukan adalah
mesin aturan, karena BPJS sudah menjalankan logika verifikasi terstandar lewat
Vidi. Kalau model kami tidak mengalahkan aturan, seluruh proposal tidak punya
alasan untuk ada, dan itu harus dilaporkan apa adanya.

Aturan di bawah disusun dari pemeriksaan yang wajar dilakukan verifikator:
duplikasi, keparahan tanpa bukti, kelas melampaui hak, harga di atas acuan,
lama rawat tanpa tindakan, dan pasangan prosedur yang saling meniadakan.

CATATAN YANG HARUS DIBACA SEBELUM MENAFSIRKAN HASILNYA.

Aturan ini ditulis oleh orang yang sama yang menulis injeksi modus di
fraud.py. Artinya mesin aturan ini tahu persis bentuk kecurangan yang ada di
data, sesuatu yang tidak pernah dimiliki mesin aturan di dunia nyata. Di
lapangan, aturan selalu tertinggal di belakang modus yang berkembang.

Akibatnya dua arah, dan keduanya harus disebut:

  Kalau model mengalahkan aturan ini, itu hasil yang kuat, karena
  pembandingnya diuntungkan.

  Kalau model kalah, penafsirannya tidak langsung, karena sebagian kekalahan
  berasal dari keuntungan yang tidak dimiliki aturan sungguhan.

Uji yang lebih adil adalah menahan sebagian modus dari penulis aturan, dan itu
belum dikerjakan.
"""

from __future__ import annotations

import numpy as np

from . import katalog as K
from .vocab import HARGA_ACUAN

PASANGAN_TERLARANG = [("47.01", "47.09"), ("51.23", "51.22"),
                      ("79.35", "78.55")]


def mesin_aturan(episodes) -> tuple[np.ndarray, list[list[str]]]:
    """Skor aturan per klaim, beserta aturan mana yang menyala.

    Skornya adalah nilai rupiah yang dipertaruhkan aturan yang menyala, bukan
    jumlah aturan. Auditor tidak peduli berapa aturan yang menyala, ia peduli
    berapa rupiah yang mungkin salah.
    """
    n = len(episodes)
    skor = np.zeros(n, dtype=np.float64)
    alasan: list[list[str]] = [[] for _ in range(n)]

    # duplikasi pada kunci gabungan
    kunci: dict[tuple, list[int]] = {}
    for i, r in enumerate(episodes):
        k = (r["peserta_id"], r["faskes"], r["cbg"])
        kunci.setdefault(k, []).append(i)
    for k, idxs in kunci.items():
        if len(idxs) < 2:
            continue
        idxs.sort(key=lambda i: episodes[i]["hari"])
        for a, b in zip(idxs, idxs[1:]):
            if episodes[b]["hari"] - episodes[a]["hari"] <= 3:
                alasan[b].append("duplikasi_kunci")
                skor[b] += episodes[b]["tarif"]

    for i, r in enumerate(episodes):
        tarif = float(r["tarif"])
        ada_lab = len(r["lab"]) > 0
        ada_obt = len(r["obt"]) > 0

        # keparahan tinggi tanpa bukti penunjang apa pun
        if r["keparahan"] >= 2 and not ada_lab and not ada_obt:
            alasan[i].append("keparahan_tanpa_bukti")
            skor[i] += tarif * 0.5

        # diagnosis sekunder banyak tanpa pemeriksaan
        if len(r["dxs"]) >= 3 and not ada_lab:
            alasan[i].append("komorbid_banyak_tanpa_lab")
            skor[i] += tarif * 0.35

        # lama rawat panjang tanpa tindakan apa pun
        if r["rawat_inap"] and r["los"] >= 10 and not r["prc"]:
            alasan[i].append("lama_rawat_tanpa_tindakan")
            skor[i] += tarif * 0.4

        # kelas rawat melampaui hak peserta
        if r["kelas_rawat"] < r["hak_kelas"]:
            alasan[i].append("kelas_melampaui_hak")
            skor[i] += tarif * 0.25

        # rawat inap tanpa obat sama sekali
        if r["rawat_inap"] and not ada_obt:
            alasan[i].append("rawat_inap_tanpa_obat")
            skor[i] += tarif * 0.6

        # pasangan prosedur yang seharusnya satu paket
        prc = set(r["prc"])
        for a, b in PASANGAN_TERLARANG:
            if a in prc and b in prc:
                alasan[i].append("pasangan_prosedur")
                skor[i] += tarif * 0.3

        # tagihan barang di atas harga acuan
        acuan = sum(HARGA_ACUAN.get(k, 0) * n_ for k, n_ in r["bhp"])
        if acuan > 0 and r.get("tagih_bhp", 0) > acuan * 1.15:
            alasan[i].append("harga_di_atas_acuan")
            skor[i] += r["tagih_bhp"] - acuan

    return skor, alasan


def fitur_tangan(episodes) -> np.ndarray:
    """Fitur yang direkayasa tangan, untuk garis dasar regresi dan pohon."""
    baris = []
    for r in episodes:
        acuan = sum(HARGA_ACUAN.get(k, 0) * n for k, n in r["bhp"])
        baris.append([
            r["umur"], r["sex"], r["segmen"], r["hak_kelas"], r["f_reg"],
            r["f_jenis"], r["f_dtpk"], r["rawat_inap"], r["los"],
            len(r["dxs"]), len(r["prc"]), len(r["obt"]), len(r["lab"]),
            len(r["bhp"]), r["keparahan"], r["kelas_rawat"],
            np.log1p(r["tarif"]), np.log1p(r.get("tagih_bhp", 0)),
            np.log1p(acuan),
            r.get("tagih_bhp", 0) / max(acuan, 1.0),
            max(r["d_prev"], 0), r["rujuk"],
            sum(1 for d in r["dxs"] if d in K.KOMORBID_BY_ICD
                and K.KOMORBID_BY_ICD[d]["berat"]),
            1.0 if len(r["lab"]) == 0 else 0.0,
        ])
    return np.asarray(baris, dtype=np.float64)


class RegresiLogistik:
    """Regresi logistik sederhana, ditulis dengan numpy.

    Garis dasar yang sering mengejutkan. Dipakai karena scikit-learn tidak
    terpasang di mesin ini, dan menambah ketergantungan hanya untuk satu garis
    dasar tidak sepadan.
    """

    def __init__(self, lr=0.25, langkah=800, l2=1e-4):
        self.lr, self.langkah, self.l2 = lr, langkah, l2
        self.w = None
        self.b = 0.0
        self.mu = None
        self.sd = None

    def fit(self, X, y):
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-8
        Z = (X - self.mu) / self.sd
        n, d = Z.shape
        self.w = np.zeros(d)
        y = np.asarray(y, dtype=np.float64)
        # bobot kelas, karena kecurangan jauh lebih jarang
        w_pos = (len(y) - y.sum()) / max(y.sum(), 1.0)
        bobot = np.where(y > 0, w_pos, 1.0)
        for _ in range(self.langkah):
            p = 1.0 / (1.0 + np.exp(-(Z @ self.w + self.b)))
            g = (bobot * (p - y)) / n
            self.w -= self.lr * (Z.T @ g + self.l2 * self.w)
            self.b -= self.lr * g.sum()
        return self

    def skor(self, X):
        Z = (X - self.mu) / self.sd
        return 1.0 / (1.0 + np.exp(-(Z @ self.w + self.b)))


# ---------------------------------------------------------------------------
# Pohon berpenguat, dua bentuk
# ---------------------------------------------------------------------------
#
# Rancangan menuliskan pohon berpenguat sebagai pembanding wajib, karena
# literatur pemodelan tabular menunjukkan pohon sering mengalahkan model dalam
# pada data seukuran ini. Target T3 menuntut model kami mengalahkannya.
#
# Dijalankan dalam dua bentuk, dan membedakannya penting.
#
#   terawasi   dilatih memakai label kecurangan yang sebenarnya. Ini batas
#              atas dari dunia yang tidak kita punya, sekelas dengan regresi
#              logistik berlabel. Berguna untuk mengukur jarak, bukan untuk
#              menyatakan menang atau kalah.
#
#   normatif   dilatih tanpa satu pun label kecurangan. Ia menebak tarif dan
#              nilai tagihan barang dari bukti, persis pekerjaan yang dilakukan
#              tulang punggung kami, lalu selisihnya menjadi skor. Inilah
#              pembanding yang benar benar sebanding, dan inilah uji T3 yang
#              sesungguhnya.

def fitur_bukti(episodes) -> np.ndarray:
    """Fitur yang hanya memuat bukti, tanpa tarif dan tanpa diagnosis sekunder.

    Diagnosis sekunder sengaja dibuang, dengan alasan yang sama seperti pada
    kepala K2: upcoding bekerja dengan menambahnya, jadi memberikannya kepada
    penebak berarti membocorkan jawabannya.
    """
    from .katalog import ICD_LIST, PEMERIKSAAN, pita_lab

    peta_dxp = {c: i for i, c in enumerate(ICD_LIST)}
    peta_lab = {c: i for i, c in enumerate(sorted(PEMERIKSAAN))}
    n_lab = len(peta_lab)

    baris = []
    for r in episodes:
        satu_dxp = np.zeros(len(peta_dxp) + 1)
        satu_dxp[peta_dxp.get(r["dxp"], len(peta_dxp))] = 1.0
        pita = np.zeros(n_lab)
        for kode, nilai in r["lab"]:
            j = peta_lab.get(kode)
            if j is not None:
                pita[j] = pita_lab(kode, nilai) + 1
        dasar = [
            r["umur"], r["sex"], r["segmen"], r["hak_kelas"], r["f_reg"],
            r["f_jenis"], r["f_dtpk"], r["rawat_inap"], r["los"],
            {"A": 0, "B": 1, "C": 2, "D": 3, "FKTP": 4}[r["f_kelas"]],
            r["f_milik"], len(r["prc"]), len(r["obt"]), len(r["lab"]),
            len(r["bhp"]), sum(n for _, n in r["bhp"]),
            max(r["d_prev"], 0), r["rujuk"],
        ]
        baris.append(np.concatenate([dasar, satu_dxp, pita]))
    return np.asarray(baris, dtype=np.float64)


def pohon_terawasi(X_tr, y_tr, X_te, nilai_te, seed=0):
    """Pohon berpenguat yang dilatih memakai label kecurangan."""
    from sklearn.ensemble import HistGradientBoostingClassifier

    m = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.08, max_leaf_nodes=63,
        l2_regularization=1.0, random_state=seed, class_weight="balanced")
    m.fit(X_tr, y_tr)
    p = m.predict_proba(X_te)[:, 1]
    # diperingkat menurut ekspektasi rupiah, bukan menurut peluang saja
    return p * np.asarray(nilai_te, dtype=np.float64)


def pohon_normatif(X_tr, tarif_tr, bhp_tr, X_te, tarif_te, bhp_te, seed=0):
    """Pohon berpenguat tanpa label kecurangan.

    Menebak tarif dan nilai tagihan barang dari bukti, lalu selisih terhadap
    yang benar benar ditagihkan menjadi skornya. Ini pekerjaan yang sama
    dengan tulang punggung kami, dikerjakan pohon.

    Dilatih pada seluruh klaim, bukan hanya yang jujur, karena di dunia nyata
    kita memang tidak tahu mana yang jujur. Sebagian besar klaim jujur, jadi
    pohon mempelajari pemetaan yang wajar dan klaim curang menjadi pencilan.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor

    def buat():
        return HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.08, max_leaf_nodes=63,
            l2_regularization=1.0, random_state=seed)

    m_tarif = buat().fit(X_tr, np.log1p(tarif_tr))
    m_bhp = buat().fit(X_tr, np.log1p(bhp_tr))
    harap_tarif = np.expm1(m_tarif.predict(X_te))
    harap_bhp = np.expm1(m_bhp.predict(X_te))
    selisih = ((np.asarray(tarif_te, dtype=np.float64) - harap_tarif)
               + (np.asarray(bhp_te, dtype=np.float64) - harap_bhp))
    return np.clip(selisih, 0, None), harap_tarif, harap_bhp
