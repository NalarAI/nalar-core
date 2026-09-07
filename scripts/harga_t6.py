"""Berapa harga menutup ruang pelaku, diukur pada beberapa nilai alpha.

A5 gagal dua kali, dan dua duanya lewat jalur model. Tambalan yang membatasi
sumbangan bukti menurunkan uang yang lolos kurang dari lima persen. Mencabut
kemampuan pelaku menanyai skor bernilai sepertiga, tapi ia bukan tombol yang
bisa dipasang di dunia nyata.

Skrip ini menguji dugaan ketiga, dan dugaan ini tidak menyalahkan modelnya.

Penebak tarif sudah tidak melihat diagnosis sekunder sama sekali, jadi
upcoding menaikkan yang ditagihkan tanpa menaikkan tebakan. Selisihnya
seharusnya melebar dan pelakunya tertangkap. Yang membuatnya tetap lolos
bukan tebakan yang tertipu melainkan jarak antara selisih berkas itu dan
ambang penandaan. Selama masih ada jarak, pelaku yang sabar mengisi jarak
itu sampai penuh dan berhenti tepat sebelum garis.

Kalau dugaan ini benar, T6 bukan sifat modelnya melainkan pilihan operasi.
Ia ditentukan alpha, dan alpha ditentukan berapa banyak berkas bersih yang
sanggup diperiksa manusia. Menaikkan alpha menutup jarak itu dan menaikkan
T6, dengan ongkos yang bisa dihitung: berkas bersih yang ikut ditandai.

Yang dilaporkan empat kolom pada tiap alpha. T6, laju penandaan berkas
bersih, presisi pada anggaran seribu berkas, dan uang yang lolos pelaku
terburuk. Kalau T6 tidak bergerak sama sekali, dugaan ini juga salah, dan
itu ditulis apa adanya.

Jalankan:
    python scripts/harga_t6.py [--peserta 20000] [--tahun 3]
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
    """Jalankan seluruh siasat yang kami punya pada satu ambang."""
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
    """Keuntungan maksimum pelaku yang beradaptasi, dibanding yang serakah.

    Rumusnya sama persis dengan yang dipakai melaporkan T6 selama ini, jadi
    angkanya bisa ditaruh bersebelahan dengan angka percobaan sebelumnya.
    """
    serakah = h["serakah"].get("maks_per_klaim_rp", 0)
    adaptif = max(v.get("maks_lolos_rp", 0) for k, v in h.items() if k != "serakah")
    return 1.0 - adaptif / max(serakah, 1)


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--klaim", type=int, default=400)
    p.add_argument("--alpha", default="0.005,0.01,0.02,0.05,0.10,0.20")
    p.add_argument("--keluar", default="runs/harga_t6.json")
    a = p.parse_args()
    daftar_alpha = [float(x) for x in a.alpha.split(",")]

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

    print("[2] melatih satu detektor, dipakai untuk seluruh alpha")
    # Yang bergantung pada alpha cuma kalibrasinya, bukan latihannya. Melatih
    # ulang tiap alpha akan menambahkan ragam yang tidak ada hubungannya
    # dengan yang sedang diukur.
    t = time.time()
    det = Detektor(alpha=daftar_alpha[0], seed=a.benih)
    det.latih([eps[i] for i in itr[nk:]])
    kal = [eps[i] for i in itr[:nk]]
    print(f"    selesai dalam {time.time() - t:.0f} detik")

    uji = [eps[i] for i in ite]
    bersih = [i for i, r in enumerate(uji) if not r.get("modus")]
    sel_nyata = np.array([float(r.get("selisih_rp", 0)) for r in uji])

    print("\n[3] menyapu alpha")
    print(
        f"    {'alpha':>7s} {'T6':>7s} {'laju bersih':>12s} "
        f"{'presisi@1000':>13s} {'lolos terburuk':>16s}"
    )
    baris = []
    for alpha in daftar_alpha:
        det.alpha = alpha
        det.kalibrasi(kal)

        tanda = np.asarray(det.tandai(uji))
        laju = float(tanda[bersih].mean())

        s = det.skor(uji)["selisih"]
        urut = np.argsort(-s)[:1000]
        presisi = float((sel_nyata[urut] > 0).mean())

        h = ukur_lawan(eps, ite, det, a.klaim)
        t6 = t6_dari(h)
        lolos = max(v.get("lolos_rp", 0) for v in h.values())

        print(
            f"    {alpha:7.3f} {t6:6.1%} {laju:12.4f} {presisi:13.3f} {jt(lolos):>16s}"
        )
        baris.append(
            {
                "alpha": alpha,
                "T6": round(t6, 4),
                "laju_penandaan_bersih": round(laju, 4),
                "presisi_pada_1000": round(presisi, 4),
                "lolos_terburuk_rp": round(lolos),
                "per_siasat": {k: v.get("lolos_rp", 0) for k, v in h.items()},
            }
        )

    print("\n[4] jawabannya")
    t6_awal, t6_akhir = baris[0]["T6"], baris[-1]["T6"]
    if t6_akhir - t6_awal < 0.05:
        print("    T6 hampir tidak bergerak sepanjang alpha.")
        print("    Dugaan ketiga salah juga, dan A5 tetap gagal.")
    else:
        cukup = [b for b in baris if b["T6"] >= 0.40]
        if cukup:
            b = cukup[0]
            print(f"    T6 mencapai 40 persen pada alpha {b['alpha']}.")
            print(
                "    Harganya laju penandaan berkas bersih "
                f"{b['laju_penandaan_bersih']:.4f} dan presisi "
                f"{b['presisi_pada_1000']:.3f}."
            )
        else:
            print(
                f"    T6 bergerak, tapi belum sampai 40 persen. "
                f"Tertinggi {t6_akhir:.1%}."
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
