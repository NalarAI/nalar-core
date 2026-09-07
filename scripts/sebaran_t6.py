"""Sebaran T6 pada beberapa benih, karena satu angka ternyata tidak cukup.

T6 dilaporkan 25,6 persen selama empat percobaan, dan hari ini terbaca 55
persen pada kode yang sama sekali tidak menyentuh detektornya. Sebabnya
ditelusuri sampai satu baris di fraud.py yang urutannya diubah saat gaya
kode diseragamkan. Yang lama memanggil pengacak lebih dulu lalu memeriksa
lama rawat, yang baru sebaliknya. Jumlah undian yang terpakai berubah,
seluruh arus acak sesudahnya bergeser, dan dunia sintetisnya jadi dunia
lain. Bukan detektornya yang membaik.

Artinya angka T6 selama ini dilaporkan dari satu dunia saja, dan tidak ada
yang pernah menanyakan berapa lebarnya kalau dunianya diganti. Skrip ini
menanyakannya.

Yang dilaporkan dua hal untuk tiap benih. T6, yang dihitung dari keuntungan
maksimum satu berkas, jadi ia bergantung pada satu klaim saja dan wajar
kalau goyah. Dan uang yang lolos pelaku, yang menjumlahkan ratusan berkas,
jadi ia seharusnya jauh lebih tenang.

Kalau sebarannya lebar, targetnya tidak bisa dinilai dengan satu angka, dan
itu yang harus ditulis di papan skor, bukan angka yang kebetulan bagus.

Jalankan:
    python scripts/sebaran_t6.py [--benih 7,8,9,10,11,12]
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

from nalar import adversarial  # noqa: E402
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402


def satu_benih(benih: int, peserta: int, tahun: int) -> dict:
    g = Pembangkit(n_peserta=peserta, tahun=tahun, seed=benih, n_fktp=900, n_fkrtl=150)
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=benih)
    itr, ite = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(benih)
    rng.shuffle(itr)
    nk = min(20000, len(itr) // 3)

    det = Detektor(alpha=0.02, seed=benih)
    det.latih([eps[i] for i in itr[nk:]]).kalibrasi([eps[i] for i in itr[:nk]])

    # Ambangnya per kelompok, sedangkan pengukur pelaku menerima satu ambang.
    # Skornya digeser jadi selisih dikurangi ambang berkas itu sendiri, persis
    # seperti pada scripts/uji_lawan.py, supaya angkanya sebanding.
    def penskor(daftar):
        s = det.skor(daftar)["selisih"]
        amb, tahan = det.ambang_untuk(daftar)
        keluar = s - amb
        keluar[tahan] = -1e18
        return keluar

    h = adversarial.bandingkan(eps, ite, penskor, 0.0, seed=benih)
    return {
        "benih": benih,
        "n_episode": len(eps),
        "T6": h.get("_penurunan_keuntungan_maksimum"),
        "maks_serakah_rp": h["serakah"]["maks_per_klaim_rp"],
        "maks_hati_hati_rp": h["hati_hati"]["maks_per_klaim_rp"],
        "diambil_hati_hati_rp": h["hati_hati"]["total_diambil_rp"],
        "diambil_serakah_rp": h["serakah"]["total_diambil_rp"],
    }


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benih", default="7,8,9,10,11,12")
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--keluar", default="runs/sebaran_t6.json")
    a = p.parse_args()
    benih = [int(x) for x in a.benih.split(",")]

    print(f"{len(benih)} benih, {a.peserta} peserta, {a.tahun} tahun\n")
    print(
        f"  {'benih':>6s} {'T6':>8s} {'maks serakah':>15s} "
        f"{'maks hati hati':>15s} {'diambil hati hati':>19s}"
    )
    baris = []
    t0 = time.time()
    for b in benih:
        h = satu_benih(b, a.peserta, a.tahun)
        baris.append(h)
        print(
            f"  {h['benih']:6d} {h['T6']:8.3f} "
            f"{h['maks_serakah_rp'] / 1e6:14.2f} jt"
            f"{h['maks_hati_hati_rp'] / 1e6:14.2f} jt"
            f"{h['diambil_hati_hati_rp'] / 1e6:17.1f} jt"
        )
    print(f"\nselesai dalam {time.time() - t0:.0f} detik")

    t6 = np.array([b["T6"] for b in baris], dtype=np.float64)
    ambil = np.array([b["diambil_hati_hati_rp"] for b in baris], dtype=np.float64)
    print("\nsebaran T6")
    print(
        f"  terkecil {t6.min():.3f}  tengah {np.median(t6):.3f}  "
        f"terbesar {t6.max():.3f}"
    )
    print(f"  simpangan baku {t6.std(ddof=1):.3f}")
    print(
        f"  benih yang melewati batas 0,40 : {int((t6 >= 0.40).sum())} dari {len(t6)}"
    )
    # Ukuran pengganti yang diusulkan. Ia menjumlahkan ratusan berkas,
    # bukan mengambil satu yang terbesar, dan ia menjawab pertanyaan yang
    # sejak awal ditulis di adversarial.py: apakah kecurangan jadi tidak
    # sepadan, bukan apakah pelakunya tertangkap.
    serakah = np.array([b["diambil_serakah_rp"] for b in baris], dtype=np.float64)
    susut = 1.0 - ambil / serakah
    print("\npenyusutan uang yang diambil, terhadap pelaku serakah")
    print(
        f"  terkecil {susut.min():.3f}  tengah {np.median(susut):.3f}  "
        f"terbesar {susut.max():.3f}  simpangan {susut.std(ddof=1):.3f}"
    )
    print(
        f"  ragam relatifnya {susut.std(ddof=1) / susut.mean():.3f}, "
        f"melawan {t6.std(ddof=1) / max(t6.mean(), 1e-9):.3f} pada T6"
    )

    print("\nsebagai pembanding, uang yang diambil pelaku hati hati")
    print(
        f"  terkecil Rp {ambil.min() / 1e6:.1f} jt  "
        f"tengah Rp {np.median(ambil) / 1e6:.1f} jt  "
        f"terbesar Rp {ambil.max() / 1e6:.1f} jt"
    )
    ragam = ambil.std(ddof=1) / max(ambil.mean(), 1)
    print(
        f"  ragam relatifnya {ragam:.3f}, melawan "
        f"{t6.std(ddof=1) / max(t6.mean(), 1e-9):.3f} pada T6"
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
