"""Seberapa kokoh angka kami. Tiga hal yang belum pernah diperiksa.

Seluruh angka detektor sampai sekarang berasal dari satu benih acak, satu
tingkat prevalensi, dan satu cara memisah latih dan uji. Tiga hal itu bisa
membuat angka yang bagus menjadi kebetulan. Berkas ini memeriksanya.

Kestabilan benih. Kalau rupiah yang ditemukan bergeser puluhan persen antar
benih, maka angka yang kami kutip tidak berarti apa apa tanpa selangnya.

Kepekaan prevalensi. Rancangan memakai 22 persen faskes nakal, dan angka itu
asumsi. Kalau hasilnya runtuh pada prevalensi yang lebih rendah, maka yang
kami tunjukkan hanya berlaku pada dunia yang kebetulan penuh kecurangan.

Pemisahan menurut waktu. Target T7 menuntut model bertahan pada faskes dan
periode yang tidak pernah dilihat. Bagian faskes sudah dikerjakan sejak awal.
Bagian periode belum pernah dijalankan sama sekali, dan inilah bentuk
pemakaian yang sebenarnya: dilatih pada tahun lalu, dipakai pada tahun ini.

Jalankan:
    python scripts/uji_ketahanan.py
"""

from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar import metrik  # noqa: E402
from nalar.dataset import (  # noqa: E402
    bangun_meta,
    pisah_menurut_entitas,
    pisah_menurut_waktu,
)
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402
from nalar.pembanding import mesin_aturan  # noqa: E402


def _ukur(det, e_te, k=1000):
    s = det.skor(e_te)["selisih"]
    sel = np.array([max(r["selisih_rp"], 0) for r in e_te], dtype=np.float64)
    curang = np.array([1 if r["modus"] else 0 for r in e_te])
    bersih = curang == 0
    tanda = det.tandai(e_te)
    kelas = np.array([r["f_kelas"] for r in e_te])
    urut = np.argsort(-s)[:k]
    rp = float(sel[urut].sum())
    laju = [
        tanda[(kelas == kk) & bersih].mean()
        for kk in ("FKTP", "A", "B", "C", "D")
        if ((kelas == kk) & bersih).sum() >= 50
    ]
    lk = float(tanda[bersih].mean())
    aturan = mesin_aturan(e_te)[0]
    rp_aturan = float(sel[np.argsort(-aturan)[:k]].sum())
    return {
        "n_uji": len(e_te),
        "rupiah_pada_k_jt": round(rp / 1e6, 1),
        "porsi_batas_atas": round(rp / max(metrik.batas_atas(sel, k), 1), 4),
        "peningkatan_atas_aturan": round(rp / max(rp_aturan, 1), 3),
        "laju_penandaan_bersih": round(lk, 5),
        "keadilan_simetris": round(max(laju) / max(min(laju), 1e-9), 3),
        "keadilan_berarah": round(max(laju) / max(lk, 1e-9), 3),
        "porsi_menahan_diri": round(float(det.ambang_untuk(e_te)[1].mean()), 4),
    }


def _siapkan(seed, prevalensi=0.22, n_peserta=20000, tahun=3):
    g = Pembangkit(
        n_peserta=n_peserta,
        tahun=tahun,
        seed=seed,
        n_fktp=900,
        n_fkrtl=150,
        prevalensi_faskes_nakal=prevalensi,
    )
    return g, g.jalankan()


def _latih_pisah_faskes(eps, seed):
    meta = bangun_meta(eps)
    m_tr, _ = pisah_menurut_entitas(meta, frac_uji=0.25, seed=seed)
    itr, ite = np.flatnonzero(m_tr), np.flatnonzero(~m_tr)
    rng = np.random.default_rng(seed)
    rng.shuffle(itr)
    nk = min(20000, len(itr) // 3)
    det = Detektor(alpha=0.02, seed=seed)
    det.latih([eps[i] for i in itr[nk:]]).kalibrasi([eps[i] for i in itr[:nk]])
    return det, [eps[i] for i in ite]


def utama(keluaran="runs/ketahanan.json"):
    catatan = {}

    print("[1] kestabilan terhadap benih acak, lima benih")
    baris = []
    for seed in (7, 11, 23, 42, 101):
        _, eps = _siapkan(seed)
        det, e_te = _latih_pisah_faskes(eps, seed)
        h = _ukur(det, e_te)
        h["seed"] = seed
        baris.append(h)
        print(
            f"    benih {seed:4d}  Rp {h['rupiah_pada_k_jt']:7.1f} jt  "
            f"porsi {h['porsi_batas_atas']:.3f}  "
            f"atas aturan {h['peningkatan_atas_aturan']:.3f}  "
            f"berarah {h['keadilan_berarah']:.3f}"
        )

    def selang(kunci):
        v = np.array([b[kunci] for b in baris], dtype=np.float64)
        return {
            "rata": round(float(v.mean()), 4),
            "sd": round(float(v.std(ddof=1)), 4),
            "min": round(float(v.min()), 4),
            "maks": round(float(v.max()), 4),
            "sebaran_relatif": round(
                float(v.std(ddof=1) / max(abs(v.mean()), 1e-9)), 4
            ),
        }

    catatan["kestabilan_benih"] = {
        "baris": baris,
        "ringkas": {
            k: selang(k)
            for k in (
                "rupiah_pada_k_jt",
                "porsi_batas_atas",
                "peningkatan_atas_aturan",
                "laju_penandaan_bersih",
                "keadilan_berarah",
            )
        },
    }
    for k, v in catatan["kestabilan_benih"]["ringkas"].items():
        print(
            f"      {k:26s} rata {v['rata']:9.4f}  sd {v['sd']:8.4f}  "
            f"sebaran relatif {v['sebaran_relatif']:.1%}"
        )

    print("[2] kepekaan terhadap prevalensi faskes nakal")
    # Angka 22 persen adalah asumsi kami, dan seluruh hasil berdiri di atasnya.
    # Yang diperiksa: apakah detektornya masih berguna kalau kecurangan jauh
    # lebih jarang, yang justru lebih mungkin terjadi.
    prev = []
    for p in (0.08, 0.15, 0.22, 0.35):
        _, eps = _siapkan(7, prevalensi=p)
        det, e_te = _latih_pisah_faskes(eps, 7)
        h = _ukur(det, e_te)
        h["prevalensi"] = p
        h["porsi_klaim_curang"] = round(
            float(np.mean([1 if r["modus"] else 0 for r in e_te])), 4
        )
        prev.append(h)
        print(
            f"    prevalensi {p:.2f}  klaim curang "
            f"{h['porsi_klaim_curang']:.3f}  "
            f"Rp {h['rupiah_pada_k_jt']:7.1f} jt  "
            f"porsi {h['porsi_batas_atas']:.3f}  "
            f"atas aturan {h['peningkatan_atas_aturan']:.3f}  "
            f"berarah {h['keadilan_berarah']:.3f}"
        )
    catatan["kepekaan_prevalensi"] = prev

    print("[3] pemisahan menurut waktu, target T7 yang belum pernah diuji")
    # Dilatih pada dua tahun pertama, dipakai pada tahun ketiga. Inilah bentuk
    # pemakaian yang sebenarnya, dan satu satunya yang menguji apakah model
    # bertahan ketika dunianya bergeser, bukan hanya ketika faskesnya berganti.
    g, eps = _siapkan(7)
    meta = bangun_meta(eps)
    potong = int(g.n_hari * 2 / 3)
    m_lalu, m_depan = pisah_menurut_waktu(meta, potong)
    ilalu, idepan = np.flatnonzero(m_lalu), np.flatnonzero(m_depan)
    rng = np.random.default_rng(7)
    rng.shuffle(ilalu)
    nk = min(20000, len(ilalu) // 3)
    det_w = Detektor(alpha=0.02, seed=7)
    det_w.latih([eps[i] for i in ilalu[nk:]])
    det_w.kalibrasi([eps[i] for i in ilalu[:nk]])
    h_waktu = _ukur(det_w, [eps[i] for i in idepan])
    h_waktu["hari_potong"] = potong
    h_waktu["n_latih"] = len(ilalu)
    print(f"    latih hari 0 sampai {potong}, uji hari {potong} ke atas")
    print(
        f"    Rp {h_waktu['rupiah_pada_k_jt']:.1f} jt  "
        f"porsi {h_waktu['porsi_batas_atas']:.3f}  "
        f"atas aturan {h_waktu['peningkatan_atas_aturan']:.3f}  "
        f"laju bersih {h_waktu['laju_penandaan_bersih']:.5f}  "
        f"berarah {h_waktu['keadilan_berarah']:.3f}"
    )

    # Pembanding yang benar bukan angka pemisahan faskes pada seluruh data,
    # melainkan angka pada jumlah klaim uji yang sebanding. Kalau tidak, yang
    # terbaca perbedaan ukuran himpunan, bukan perbedaan cara memisah.
    det_f, e_f = _latih_pisah_faskes(eps, 7)
    h_faskes = _ukur(det_f, e_f)
    catatan["pemisahan_waktu"] = {
        "menurut_waktu": h_waktu,
        "menurut_faskes": h_faskes,
        "rasio_porsi_batas_atas": round(
            h_waktu["porsi_batas_atas"] / max(h_faskes["porsi_batas_atas"], 1e-9), 3
        ),
        "jaminan_konformal_masih_berlaku": bool(
            h_waktu["laju_penandaan_bersih"] <= 0.03
        ),
    }
    print(
        f"    pembanding menurut faskes: porsi "
        f"{h_faskes['porsi_batas_atas']:.3f}, "
        f"rasio {catatan['pemisahan_waktu']['rasio_porsi_batas_atas']}"
    )

    os.makedirs(os.path.dirname(keluaran), exist_ok=True)
    with open(keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)
    print(f"\nditulis ke {keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
