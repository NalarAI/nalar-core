"""Menguji satu kalimat yang kami tulis sendiri sebagai kesimpulan.

Percobaan tambalan batas sumbangan bukti gagal, dan kami menulis sebabnya:
yang membuat serangan bekerja bukan bukti penyerta, melainkan kemampuan
pelaku menanyai skor sampai tahu apa yang lolos.

Kalimat itu belum diukur waktu ditulis. Ia terdengar benar, dan terdengar
benar bukan alasan menuliskannya sebagai temuan. Skrip ini mengukurnya.

Yang diubah cuma satu hal, dan bukan detektornya. Apa yang boleh dilihat
pelaku:

    penuh    melihat skor tiap varian sebelum memilih, sebanyak yang ia mau
    belajar  melihat skor pada lima puluh berkas pertama, menyimpulkan satu
             batas keuntungan yang aman, lalu memakainya tanpa bertanya lagi
    buta     tidak melihat skor sama sekali

Yang ketiga dan kedua lebih mendekati keadaan sebenarnya. Rumah sakit tidak
punya tombol yang mengembalikan skor sebuah berkas. Yang ia punya hasil
berkas yang sudah dikirim, satu pengamatan per berkas, dan itu datang
belakangan.

Kalau uang yang lolos jatuh tajam dari penuh ke belajar, kalimat itu benar
dan pertahanannya soal kebijakan, bukan model. Kalau tidak jatuh, kalimat itu
salah dan harus dicabut dari TEMUAN.

Jalankan:
    python scripts/pengetahuan_pelaku.py [--peserta 20000]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np  # noqa: E402

from nalar.agen import arena  # noqa: E402
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402


def jt(x) -> str:
    return f"{(x or 0) / 1e6:7.1f} jt"


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--klaim", type=int, default=400)
    p.add_argument("--belajar", type=int, default=50)
    p.add_argument("--keluar", default="runs/pengetahuan_pelaku.json")
    a = p.parse_args()

    print("[1] membangkitkan data dan melatih detektor yang dikirim")
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
    det = Detektor(alpha=0.02, seed=a.benih)
    det.latih([eps[i] for i in itr[nk:]]).kalibrasi([eps[i] for i in itr[:nk]])
    print(f"    {len(eps)} episode, {len(ite)} masuk uji, {time.time() - t:.0f} detik")

    amb = np.full(len(eps), np.inf)
    tahan = np.ones(len(eps), dtype=bool)
    at, tt = det.ambang_untuk([eps[i] for i in ite])
    amb[ite] = at
    tahan[ite] = tt

    def penskor(daftar):
        return det.skor(daftar)["selisih"]

    print("\n[2] uang yang lolos menurut apa yang boleh dilihat pelaku")
    print(
        f"    {'siasat':34s} {'penuh':>10s} {'belajar':>10s} {'buta':>10s} {'sisa':>8s}"
    )
    catatan = {}
    for s in arena.SELURUH:
        baris = {}
        for tahu in arena.PENGETAHUAN:
            baris[tahu] = arena.jalankan(
                eps,
                ite,
                penskor,
                amb,
                tahan,
                s,
                maks_klaim=a.klaim,
                pengetahuan=tahu,
                n_belajar=a.belajar,
            )
        catatan[s["nama"]] = baris
        penuh = baris["penuh"].get("lolos_rp", 0)
        ajar = baris["belajar"].get("lolos_rp", 0)
        buta = baris["buta"].get("lolos_rp", 0)
        sisa = ajar / penuh if penuh else 0.0
        print(f"    {s['nama']:34s} {jt(penuh)} {jt(ajar)} {jt(buta)} {sisa:7.1%}")

    terburuk = {
        tahu: max(b[tahu].get("lolos_rp", 0) for b in catatan.values())
        for tahu in arena.PENGETAHUAN
    }
    print("\n[3] pelaku terburuk pada tiap tingkat pengetahuan")
    for tahu in arena.PENGETAHUAN:
        print(f"    {tahu:10s} {jt(terburuk[tahu])}")
    sisa = terburuk["belajar"] / max(terburuk["penuh"], 1)
    print(f"    yang tersisa ketika pelaku berhenti bisa bertanya: {sisa:.1%}")

    # Laju tertangkap ikut dilaporkan. Uang yang lolos bisa turun karena dua
    # sebab yang sangat berbeda: pelaku lebih sering tertangkap, atau pelaku
    # jadi terlalu takut dan mengambil lebih sedikit. Keduanya menolong BPJS,
    # tapi hanya yang pertama yang berarti detektornya bekerja.
    print("\n[4] kenapa turun: tertangkap lebih sering, atau mengambil lebih sedikit")
    print(f"    {'siasat':34s} {'tingkat':10s} {'diambil':>10s} {'tertangkap':>11s}")
    for nama, baris in catatan.items():
        for tahu in ("penuh", "belajar"):
            h = baris[tahu]
            tg = h.get("porsi_tertangkap")
            print(
                f"    {nama:34s} {tahu:10s} {jt(h.get('diambil_rp'))} "
                f"{'-' if tg is None else f'{tg:11.1%}'}"
            )

    hasil = {
        "pengaturan": vars(a),
        "per_siasat": catatan,
        "terburuk": terburuk,
        "sisa_ketika_tidak_bisa_bertanya": sisa,
    }
    os.makedirs(os.path.dirname(a.keluar) or ".", exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nRinciannya di {a.keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
