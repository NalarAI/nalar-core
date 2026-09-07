"""Harga jaring pengaman untuk kelompok yang menahan diri.

A5 gagal tiga kali, dan yang ketiga menunjukkan sebabnya. Ruang pelaku bukan
jarak di bawah ambang, melainkan berkas yang tidak punya ambang sama sekali.
Pada seratus tujuh berkas rawat inap yang bisa diserang, tujuh puluh lima ada
di kelompok yang menahan diri, dan lima puluh satu serangan lolos dari situ.
Menaikkan alpha lima kali cuma memindahkan dua berkas, karena alpha tidak
menyentuh kelompok yang tidak punya ambang.

Menahan diri sendiri bukan kesalahan. Ia dipasang supaya tidak ada faskes
yang dipersoalkan berdasarkan ambang yang dihitung dari tiga rumah sakit.
Yang salah menganggap menahan diri berarti tidak melakukan apa apa.

Skrip ini mengukur satu jalan tengah. Berkas di kelompok yang menahan diri
tetap tidak dibandingkan dengan sebayanya, karena sebayanya memang tidak
cukup. Yang berlaku baginya satu ambang tunggal dari seluruh klaim
kalibrasi, pada alpha yang jauh lebih kecil, sehingga yang tersaring cuma
berkas yang selisihnya jauh di luar kewajaran siapa pun.

Yang dilaporkan untung dan ongkosnya berdampingan. T6 dan uang yang lolos di
satu sisi. Di sisi lain berkas bersih yang ikut tertandai, dipisah menurut
siapa yang menanggungnya: seluruh berkas, berkas di kelompok yang menahan
diri, dan berkas dari daerah tertinggal.

Kalau ongkosnya jatuh pada daerah tertinggal, jaringnya tidak dipasang.
Menutup lubang dengan menghukum faskes yang paling sedikit sebayanya bukan
perbaikan, itu memindahkan kerugian ke pihak yang paling tidak bisa
membantah.

Jalankan:
    python scripts/jaring_pengaman.py [--peserta 20000] [--tahun 3]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

import numpy as np

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar.agen import arena  # noqa: E402
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402


def jt(x) -> str:
    return f"Rp {x / 1e6:,.1f} jt".replace(",", ".")


def ukur_lawan(eps, idx, det, klaim: int) -> dict:
    amb = np.full(len(eps), np.inf)
    tahan = np.ones(len(eps), dtype=bool)
    a, t = det.ambang_untuk([eps[i] for i in idx])
    amb[idx] = a
    tahan[idx] = t

    def penskor(daftar):
        return det.skor(daftar)["selisih"]

    return {
        s["nama"]: arena.jalankan(eps, idx, penskor, amb, tahan, s, maks_klaim=klaim)
        for s in arena.BAKU + arena.DITEMUKAN
    }


def t6_dari(h) -> float:
    serakah = h["serakah"].get("maks_per_klaim_rp", 0)
    adaptif = max(v.get("maks_lolos_rp", 0) for k, v in h.items() if k != "serakah")
    return 1.0 - adaptif / max(serakah, 1)


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--klaim", type=int, default=400)
    p.add_argument("--alpha", type=float, default=0.02)
    p.add_argument("--jaring", default="mati,0.02,0.005,0.001")
    p.add_argument("--keluar", default="runs/jaring_pengaman.json")
    a = p.parse_args()
    daftar = [None if x == "mati" else float(x) for x in a.jaring.split(",")]

    print("[1] membangkitkan data")
    t = time.time()
    g = Pembangkit(
        n_peserta=a.peserta, tahun=a.tahun, seed=a.benih, n_fktp=900, n_fkrtl=150
    )
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=a.benih)
    itr, ite = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(a.benih)
    rng.shuffle(itr)
    nk = min(20000, len(itr) // 3)
    print(f"    {len(eps)} episode, {len(ite)} masuk uji, {time.time() - t:.0f} detik")

    print("[2] melatih satu detektor, dipakai untuk seluruh pengaturan")
    t = time.time()
    det = Detektor(alpha=a.alpha, seed=a.benih)
    det.latih([eps[i] for i in itr[nk:]])
    kal = [eps[i] for i in itr[:nk]]
    print(f"    selesai dalam {time.time() - t:.0f} detik")

    uji = [eps[i] for i in ite]
    curang = np.array([bool(r.get("modus")) for r in uji])
    dtpk = np.array([int(r["f_dtpk"]) == 1 for r in uji])
    kelas = np.array([r["f_kelas"] for r in uji])
    daftar_kelas = sorted(set(kelas.tolist()))

    print("\n[3] menyapu alpha jaring")
    print(
        f"    {'jaring':>8s} {'T6':>7s} {'lolos terburuk':>16s} "
        f"{'bersih semua':>13s} {'bersih tahan':>13s} {'bersih dtpk':>12s}"
    )
    baris = []
    for aj in daftar:
        det.alpha_jaring = aj
        det.kalibrasi(kal)
        _, tahan = det.ambang_untuk(uji)
        tanda = np.asarray(det.tandai(uji))

        bersih = ~curang

        def laju(pilih, tanda=tanda) -> float:
            n = int(pilih.sum())
            return float(tanda[pilih].mean()) if n else 0.0

        h = ukur_lawan(eps, ite, det, a.klaim)
        t6 = t6_dari(h)
        lolos = max(v.get("lolos_rp", 0) for v in h.values())

        b = {
            "alpha_jaring": aj,
            "ambang_jaring_rp": (
                None if not np.isfinite(det.ambang_jaring) else round(det.ambang_jaring)
            ),
            "T6": round(t6, 4),
            "lolos_terburuk_rp": round(lolos),
            "laju_bersih_semua": round(laju(bersih), 4),
            "laju_bersih_menahan_diri": round(laju(bersih & tahan), 4),
            "laju_bersih_dtpk": round(laju(bersih & dtpk), 4),
            "laju_curang_menahan_diri": round(laju(curang & tahan), 4),
            "n_bersih_menahan_diri": int((bersih & tahan).sum()),
            "n_curang_menahan_diri": int((curang & tahan).sum()),
            "n_bersih_dtpk": int((bersih & dtpk).sum()),
            # Siapa yang menanggung ongkosnya. Jaring yang menutup lubang
            # dengan menandai lebih banyak berkas bersih milik satu kelas
            # faskes saja bukan perbaikan, dan tanpa kolom ini ia tidak
            # terlihat sama sekali.
            "laju_bersih_per_kelas": {
                str(k): round(laju(bersih & (kelas == k)), 4) for k in daftar_kelas
            },
            "n_bersih_per_kelas": {
                str(k): int((bersih & (kelas == k)).sum()) for k in daftar_kelas
            },
        }
        baris.append(b)
        nama = "mati" if aj is None else f"{aj:g}"
        print(
            f"    {nama:>8s} {t6:6.1%} {jt(lolos):>16s} "
            f"{b['laju_bersih_semua']:13.4f} {b['laju_bersih_menahan_diri']:13.4f} "
            f"{b['laju_bersih_dtpk']:12.4f}"
        )

    print("\n[4] siapa yang tertangkap jaringnya")
    print(
        f"    {'jaring':>8s} {'ambang jaring':>16s} "
        f"{'curang tertandai di kelompok menahan diri':>44s}"
    )
    for b in baris:
        nama = "mati" if b["alpha_jaring"] is None else f"{b['alpha_jaring']:g}"
        amb = (
            "tak hingga" if b["ambang_jaring_rp"] is None else jt(b["ambang_jaring_rp"])
        )
        print(f"    {nama:>8s} {amb:>16s} {b['laju_curang_menahan_diri']:>44.4f}")

    print("\n[5] siapa yang menanggung ongkosnya, laju berkas bersih per kelas")
    print("    " + f"{'jaring':>8s}" + "".join(f"{k:>10s}" for k in daftar_kelas))
    for b in baris:
        nama = "mati" if b["alpha_jaring"] is None else f"{b['alpha_jaring']:g}"
        print(
            f"    {nama:>8s}"
            + "".join(f"{b['laju_bersih_per_kelas'][k]:10.4f}" for k in daftar_kelas)
        )
    print(
        "    cacah berkas bersih: "
        + ", ".join(f"{k} {baris[0]['n_bersih_per_kelas'][k]}" for k in daftar_kelas)
    )
    print(
        f"    berkas bersih di kelompok menahan diri: "
        f"{baris[0]['n_bersih_menahan_diri']}, daerah tertinggal: "
        f"{baris[0]['n_bersih_dtpk']}"
    )

    print("\n[6] jawabannya")
    dasar, terbaik = baris[0], max(baris, key=lambda b: b["T6"])
    if terbaik["T6"] - dasar["T6"] < 0.05:
        print("    Jaring pengaman tidak menggerakkan T6. Dugaan keempat salah juga.")
    else:
        print(
            f"    T6 naik dari {dasar['T6']:.1%} ke {terbaik['T6']:.1%} "
            f"pada alpha jaring {terbaik['alpha_jaring']}."
        )
        print(
            f"    Ongkosnya berkas bersih di kelompok yang menahan diri, dari "
            f"{dasar['laju_bersih_menahan_diri']:.4f} ke "
            f"{terbaik['laju_bersih_menahan_diri']:.4f}."
        )
        print(
            f"    Pada daerah tertinggal, dari {dasar['laju_bersih_dtpk']:.4f} ke "
            f"{terbaik['laju_bersih_dtpk']:.4f}."
        )

    os.makedirs(os.path.dirname(a.keluar), exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(
            {"pengaturan": vars(a), "baris": baris}, f, ensure_ascii=False, indent=2
        )
    print(f"\nRinciannya di {a.keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
