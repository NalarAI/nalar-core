"""Berapa harga daftar pengandaian yang kami tampilkan di portal faskes.

Portal fasilitas kesehatan hari ini menampilkan daftar bukti yang bila
dilampirkan menurunkan selisih, beserta besar penurunan tiap butirnya,
seluruhnya sekaligus, dalam satu jawaban.

Daftar itu inti janji kami. Tanpa daftar itu, penandaan cuma tuduhan yang
tidak bisa dibantah, dan faskes yang buktinya sah tetap kalah karena tidak
tahu bukti mana yang diminta.

Daftar yang sama adalah peta bagi yang ingin menghindar. Skrip ini mengukur
harganya, supaya keputusan menampilkannya diambil dengan angka.

Yang dibandingkan dua gerakan yang persis sama bentuknya, beda pada satu hal
saja. Melampirkan pemeriksaan sembarang, dan melampirkan pemeriksaan yang
paling menurunkan selisih menurut daftar itu.

Jalankan:
    python scripts/harga_pengandaian.py [--peserta 20000]
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


def pasangan(cara: dict, nama: str) -> list[dict]:
    """Dua siasat kembar, beda pada gerakan buktinya saja."""
    return [
        {
            "nama": f"{nama}, lampiran sembarang",
            "sasaran": {"jenis": "semua_rawat_inap"},
            "gerakan": [
                {"jenis": "tambah_diagnosis"},
                {"jenis": "lampirkan_lab", "n": 3},
            ],
            "pilihan": cara,
        },
        {
            "nama": f"{nama}, lampiran menurut daftar",
            "sasaran": {"jenis": "semua_rawat_inap"},
            "gerakan": [
                {"jenis": "tambah_diagnosis"},
                {"jenis": "lampirkan_lab_terbaik", "n": 3},
            ],
            "pilihan": cara,
        },
    ]


SIASAT = pasangan({"jenis": "aman_di_bawah_ambang"}, "hati hati") + pasangan(
    {"jenis": "kenaikan_skor_terkecil"}, "menyebar"
)


def jt(x) -> str:
    return f"{(x or 0) / 1e6:7.1f} jt"


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--klaim", type=int, default=400)
    p.add_argument("--belajar", type=int, default=50)
    p.add_argument("--keluar", default="runs/harga_pengandaian.json")
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

    print("\n[2] uang yang lolos, dengan dan tanpa daftar pengandaian")
    # Judul kolom disusun dari daftar tingkatnya sendiri. Versi pertama
    # menuliskannya tangan dengan urutan yang berbeda dari urutan nilainya,
    # dan tabelnya terbaca terbalik tanpa ada yang salah pada angkanya.
    judul = "".join(f"{t:>10s} " for t in arena.PENGETAHUAN)
    print(f"    {'siasat':42s} {judul}")
    catatan = {}
    for s in SIASAT:
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
        print(
            f"    {s['nama']:42s} "
            + " ".join(jt(baris[t].get("lolos_rp")) for t in arena.PENGETAHUAN)
        )

    print("\n[3] selisih antara keduanya")
    nama = list(catatan)
    for i in range(0, len(nama), 2):
        buta_nama, daftar_nama = nama[i], nama[i + 1]
        for tahu in arena.PENGETAHUAN:
            x = catatan[buta_nama][tahu].get("lolos_rp", 0)
            y = catatan[daftar_nama][tahu].get("lolos_rp", 0)
            naik = (y / x - 1) if x else 0.0
            print(
                f"    {buta_nama.split(',')[0]:12s} {tahu:8s} "
                f"sembarang {jt(x)}  menurut daftar {jt(y)}  {naik:+7.1%}"
            )

    hasil = {"pengaturan": vars(a), "per_siasat": catatan}
    os.makedirs(os.path.dirname(a.keluar) or ".", exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nRinciannya di {a.keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
