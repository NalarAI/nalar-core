"""Latih di data karangan, uji di data nyata.

Rancangan bagian 12.6 menuliskan uji ini sebagai syarat kelulusan, dan
alasannya lugas. Seluruh angka kami sampai sekarang berdiri di atas data yang
kami karang sendiri. Kalau data itu tidak memuat struktur yang juga ada pada
klaim betulan, maka semua yang kami ukur cuma gema dari asumsi kami sendiri.

Caranya. Sebuah tugas dipilih yang bisa dikerjakan di kedua dunia, yaitu
menebak biaya klaim rawat inap dari umur, jenis kelamin, lama rawat, banyak
diagnosis, dan banyak prosedur. Kode diagnosis tidak dipakai karena Amerika
memakai ICD-9 dan kami ICD-10. Lalu tiga model diadu:

    pindah    dilatih di data kami, diuji di klaim Amerika
    pribumi   dilatih dan diuji di klaim Amerika, ini batas atasnya
    tebakan   selalu menjawab rata rata, ini lantainya

Syarat lulus dari rancangan: yang pindah harus jauh di atas tebakan, dan
jaraknya terhadap pribumi harus kurang dari sepertiga.

Jalankan:
    python scripts/uji_transfer.py
"""

from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar import nyata  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402


def _pohon(seed):
    from sklearn.ensemble import HistGradientBoostingRegressor

    return HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.08,
        max_leaf_nodes=63,
        l2_regularization=1.0,
        random_state=seed,
    )


def _spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    return float((ra @ rb) / (np.linalg.norm(ra) * np.linalg.norm(rb) + 1e-12))


def _r2(y, p):
    ss = float(((y - p) ** 2).sum())
    st = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss / (st + 1e-12)


def utama(n_peserta=20000, tahun=3, seed=7, keluaran="runs/transfer.json"):
    catatan = {}

    print("[1] memuat klaim rawat inap Amerika")
    baris = nyata.muat_rawat_inap()
    Xn = nyata.matriks_bersama(baris)
    yn = nyata.bakukan([r["biaya"] for r in baris])
    print(f"    {len(baris)} klaim, {Xn.shape[1]} kolom bersama")

    # Dipisah menurut faskes, bukan menurut klaim, dengan alasan yang sama
    # seperti pada seluruh percobaan kami. Klaim dari satu rumah sakit saling
    # mirip, jadi memisah acak per klaim akan membocorkan jawaban.
    faskes = np.array([r["faskes"] for r in baris])
    unik = np.unique(faskes)
    rng = np.random.default_rng(seed)
    rng.shuffle(unik)
    uji_faskes = set(unik[: len(unik) // 4])
    m_uji = np.array([f in uji_faskes for f in faskes])
    print(f"    {len(unik)} faskes, {m_uji.sum()} klaim masuk himpunan uji")

    print("[2] membangkitkan data karangan")
    g = Pembangkit(n_peserta=n_peserta, tahun=tahun, seed=seed, n_fktp=900, n_fkrtl=150)
    eps = g.jalankan()
    Xk, yk_rp, inap = nyata.matriks_dari_episode(eps)
    yk = nyata.bakukan(yk_rp)
    print(f"    {len(eps)} episode, {len(inap)} di antaranya rawat inap")

    catatan["ukuran"] = {
        "klaim_amerika": len(baris),
        "klaim_amerika_uji": int(m_uji.sum()),
        "faskes_amerika": len(unik),
        "episode_karangan": len(eps),
        "rawat_inap_karangan": len(inap),
        "nilai_biaya_unik_amerika": int(len(np.unique([r["biaya"] for r in baris]))),
    }

    print("[3] membandingkan sebaran kolom bersama")
    banding = {}
    for j, k in enumerate(nyata.KOLOM_BERSAMA):
        banding[k] = {
            "karangan_rata": round(float(Xk[:, j].mean()), 3),
            "amerika_rata": round(float(Xn[:, j].mean()), 3),
            "karangan_sd": round(float(Xk[:, j].std()), 3),
            "amerika_sd": round(float(Xn[:, j].std()), 3),
        }
        print(
            f"    {k:6s} karangan {Xk[:, j].mean():7.2f} "
            f"± {Xk[:, j].std():5.2f}   "
            f"amerika {Xn[:, j].mean():7.2f} ± {Xn[:, j].std():5.2f}"
        )
    catatan["sebaran_kolom"] = banding

    print("[4] melatih tiga model")
    X_tr, y_tr = Xn[~m_uji], yn[~m_uji]
    X_te, y_te = Xn[m_uji], yn[m_uji]

    m_pindah = _pohon(seed).fit(Xk, yk)
    p_pindah = m_pindah.predict(X_te)

    m_pribumi = _pohon(seed).fit(X_tr, y_tr)
    p_pribumi = m_pribumi.predict(X_te)

    p_tebak = np.full_like(y_te, y_tr.mean())

    def ukur(p):
        return {
            "r2": round(_r2(y_te, p), 4),
            "spearman": round(_spearman(y_te, p), 4),
            "mae": round(float(np.abs(y_te - p).mean()), 4),
        }

    hasil = {
        "pindah": ukur(p_pindah),
        "pribumi": ukur(p_pribumi),
        "tebakan": ukur(p_tebak),
    }

    # Transfer yang ditera ulang. Model yang dilatih di dunia lain bisa benar
    # bentuknya tapi salah skalanya. Satu garis lurus dicocokkan pada seperempat
    # data nyata untuk membetulkan skala saja, bukan bentuknya. Dilaporkan
    # terpisah supaya tidak tertukar dengan angka mentahnya.
    p_lat = m_pindah.predict(X_tr)
    A = np.stack([p_lat, np.ones_like(p_lat)], axis=1)
    koef, *_ = np.linalg.lstsq(A, y_tr, rcond=None)
    hasil["pindah_ditera"] = ukur(koef[0] * p_pindah + koef[1])
    hasil["pindah_ditera"]["kemiringan"] = round(float(koef[0]), 4)

    catatan["hasil"] = hasil

    print("[5] menilai terhadap syarat rancangan")
    for nama in ["pindah", "pindah_ditera", "pribumi", "tebakan"]:
        h = hasil[nama]
        print(
            f"    {nama:14s} r2 {h['r2']:+.4f}   "
            f"spearman {h['spearman']:+.4f}   mae {h['mae']:.4f}"
        )

    r2_p, r2_n = hasil["pindah_ditera"]["r2"], hasil["pribumi"]["r2"]
    sp_p, sp_n = hasil["pindah_ditera"]["spearman"], hasil["pribumi"]["spearman"]
    turun_r2 = 1.0 - (r2_p / r2_n) if r2_n > 0 else float("nan")
    turun_sp = 1.0 - (sp_p / sp_n) if sp_n > 0 else float("nan")

    catatan["penilaian"] = {
        "jauh_di_atas_tebakan": bool(sp_p > 0.15 and r2_p > 0.05),
        "penurunan_r2_terhadap_pribumi": round(float(turun_r2), 4),
        "penurunan_spearman_terhadap_pribumi": round(float(turun_sp), 4),
        "batas_penurunan": 0.3333,
        "lulus_r2": bool(turun_r2 < 1 / 3),
        "lulus_spearman": bool(turun_sp < 1 / 3),
    }
    print(
        f"    penurunan r2       {turun_r2:+.1%}  "
        f"(batas 33,3%)  {'lulus' if turun_r2 < 1 / 3 else 'GAGAL'}"
    )
    print(
        f"    penurunan spearman {turun_sp:+.1%}  "
        f"(batas 33,3%)  {'lulus' if turun_sp < 1 / 3 else 'GAGAL'}"
    )

    print("[6] pentingnya tiap kolom, untuk tahu apa yang berpindah")
    # Diukur dengan mengacak satu kolom lalu melihat berapa yang runtuh.
    dasar = _spearman(y_te, p_pindah)
    penting = {}
    for j, k in enumerate(nyata.KOLOM_BERSAMA):
        Xs = X_te.copy()
        Xs[:, j] = rng.permutation(Xs[:, j])
        penting[k] = round(dasar - _spearman(y_te, m_pindah.predict(Xs)), 4)
        print(f"    {k:6s} turun {penting[k]:+.4f} bila diacak")
    catatan["pentingnya_kolom_saat_pindah"] = penting

    print("[7] varian tanpa kolom diagnosis sekunder")
    # Alasannya ditetapkan dari bentuk sebarannya, bukan dari hasilnya.
    # Pada klaim Amerika, 59 persen klaim berisi persis delapan diagnosis
    # sekunder dari sembilan slot yang tersedia. Itu perilaku mengisi slot,
    # bukan sebaran klinis, dan korelasinya dengan biaya hanya 0,15 melawan
    # 0,46 milik jumlah prosedur. Kolom yang sebarannya rusak di dunia tujuan
    # tidak bisa dipakai menghakimi dunia asal. Keduanya tetap dilaporkan.
    j_buang = nyata.KOLOM_BERSAMA.index("n_dxs")
    sisa = [j for j in range(len(nyata.KOLOM_BERSAMA)) if j != j_buang]
    m_p2 = _pohon(seed).fit(Xk[:, sisa], yk)
    p_p2 = m_p2.predict(X_te[:, sisa])
    m_n2 = _pohon(seed).fit(X_tr[:, sisa], y_tr)
    p_n2 = m_n2.predict(X_te[:, sisa])
    pl2 = m_p2.predict(X_tr[:, sisa])
    A2 = np.stack([pl2, np.ones_like(pl2)], axis=1)
    k2, *_ = np.linalg.lstsq(A2, y_tr, rcond=None)
    tanpa = {"pindah_ditera": ukur(k2[0] * p_p2 + k2[1]), "pribumi": ukur(p_n2)}
    tanpa["penurunan_spearman"] = round(
        1 - tanpa["pindah_ditera"]["spearman"] / tanpa["pribumi"]["spearman"], 4
    )
    tanpa["lulus_spearman"] = bool(tanpa["penurunan_spearman"] < 1 / 3)
    catatan["tanpa_n_dxs"] = tanpa
    print(
        f"    pindah  spearman {tanpa['pindah_ditera']['spearman']:+.4f}"
        f"   pribumi {tanpa['pribumi']['spearman']:+.4f}"
        f"   turun {tanpa['penurunan_spearman']:+.1%}"
    )

    print("[8] arah sebaliknya, latih di Amerika uji di data karangan")
    # Kalau jatuhnya setara di kedua arah, yang kita lihat adalah dua dunia
    # yang memang berbeda. Kalau arah ini jauh lebih mulus, maka data kamilah
    # yang miskin. Pertanyaan ini tidak bisa dijawab oleh satu arah saja.
    rng2 = np.random.default_rng(seed + 1)
    fk = np.array([r["faskes"] for r in inap])
    uk = np.unique(fk)
    rng2.shuffle(uk)
    uji_k = set(uk[: max(1, len(uk) // 4)])
    mk = np.array([f in uji_k for f in fk])
    m_balik = _pohon(seed).fit(X_tr, y_tr)
    pb = m_balik.predict(Xk[mk])
    pb_tr = m_balik.predict(Xk[~mk])
    Ab = np.stack([pb_tr, np.ones_like(pb_tr)], axis=1)
    kb, *_ = np.linalg.lstsq(Ab, yk[~mk], rcond=None)
    m_pri_k = _pohon(seed).fit(Xk[~mk], yk[~mk])

    def ukur2(p):
        return {
            "r2": round(_r2(yk[mk], p), 4),
            "spearman": round(_spearman(yk[mk], p), 4),
        }

    balik = {
        "pindah_ditera": ukur2(kb[0] * pb + kb[1]),
        "pribumi": ukur2(m_pri_k.predict(Xk[mk])),
    }
    balik["penurunan_spearman"] = round(
        1 - balik["pindah_ditera"]["spearman"] / balik["pribumi"]["spearman"], 4
    )
    catatan["arah_sebaliknya"] = balik
    print(
        f"    pindah  spearman {balik['pindah_ditera']['spearman']:+.4f}"
        f"   pribumi {balik['pribumi']['spearman']:+.4f}"
        f"   turun {balik['penurunan_spearman']:+.1%}"
    )

    os.makedirs(os.path.dirname(keluaran), exist_ok=True)
    with open(keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)
    print(f"\nditulis ke {keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
