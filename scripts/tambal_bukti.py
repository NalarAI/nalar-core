"""Menguji tambalan batas sumbangan bukti, beserta ongkosnya.

Lapisan lawan menemukan satu siasat yang meloloskan Rp 427,2 juta tanpa satu
berkas pun tertangkap: tambahkan diagnosis sekunder, lalu lampirkan hasil
pemeriksaan penunjang. Naik lewat pintu yang tidak diawasi, turun lewat pintu
yang diawasi.

Tambalannya membatasi seberapa jauh lampiran boleh menurunkan kecurigaan.
Batasnya dipelajari dari himpunan latih, bukan ditulis tangan.

Skrip ini menimbang tambalan itu, dan menimbang berarti mengukur ongkosnya
juga. Tiga hal diukur pada dua detektor yang dilatih pada data yang sama
persis, satu bertambal dan satu tidak.

T6, keuntungan pelaku yang beradaptasi. Ini yang seharusnya membaik.

T2, laju penandaan berkas bersih. Ini yang tidak boleh rusak, dan kalau ia
rusak tambalannya dicabut, bukan dijelaskan.

Tugas biasa, rupiah yang ditemukan pada anggaran seribu berkas. Tambalan yang
menyelamatkan T6 dengan merusak kegunaan sehari hari bukan tambalan.

Jalankan:
    python scripts/tambal_bukti.py [--peserta 20000]
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

# Siasat yang ditemukan lapisan lawan, disalin apa adanya dari
# runs/agen_lawan.json. Ditulis di sini supaya skrip ini bisa dijalankan
# sendiri, dan supaya yang diuji tambalannya persis siasat yang menembusnya.
SIASAT_BARU = [
    {
        "nama": "upcode berlapis bukti",
        "sasaran": {"jenis": "semua_rawat_inap"},
        "gerakan": [
            {"jenis": "tambah_diagnosis"},
            {"jenis": "lampirkan_lab", "n": 3},
        ],
        "pilihan": {"jenis": "aman_di_bawah_ambang"},
    },
    {
        "nama": "upcode berlapis bukti, berkas kecil",
        "sasaran": {"jenis": "selisih_awal_kecil", "batas_rp": 1_000_000},
        "gerakan": [
            {"jenis": "tambah_diagnosis"},
            {"jenis": "lampirkan_lab", "n": 3},
        ],
        "pilihan": {"jenis": "aman_di_bawah_ambang"},
    },
    {
        "nama": "upcode berlapis bukti, menyebar",
        "sasaran": {"jenis": "semua_rawat_inap"},
        "gerakan": [
            {"jenis": "tambah_diagnosis"},
            {"jenis": "lampirkan_lab", "n": 3},
        ],
        "pilihan": {"jenis": "kenaikan_skor_terkecil"},
    },
    {
        "nama": "upcode berlapis barang",
        "sasaran": {"jenis": "semua_rawat_inap"},
        "gerakan": [
            {"jenis": "tambah_diagnosis"},
            {"jenis": "gelembungkan_barang", "persen": 30},
        ],
        "pilihan": {"jenis": "aman_di_bawah_ambang"},
    },
]


def jt(x) -> str:
    return f"{(x or 0) / 1e6:8.1f} jt"


def latih_dua(eps, itr, nk, seed, kuantil: float = 0.8):
    """Dua detektor pada data yang sama persis, satu bertambal satu tidak."""
    latih = [eps[i] for i in itr[nk:]]
    kal = [eps[i] for i in itr[:nk]]

    bertambal = Detektor(alpha=0.02, seed=seed)
    bertambal.kuantil_batas = kuantil
    bertambal.latih(latih).kalibrasi(kal)

    polos = Detektor(alpha=0.02, seed=seed).latih(latih)
    # Batas tak hingga berarti tanpa potongan, yaitu perilaku sebelum
    # tambalan. Dilatih ulang, bukan disalin, supaya tidak ada satu pun
    # perbedaan lain yang ikut terbawa.
    polos.batas_bukti = float("inf")
    polos.kalibrasi(kal)
    return polos, bertambal


def ukur_lawan(eps, idx, det, klaim: int) -> dict:
    amb = np.full(len(eps), np.inf)
    tahan = np.ones(len(eps), dtype=bool)
    a, t = det.ambang_untuk([eps[i] for i in idx])
    amb[idx] = a
    tahan[idx] = t

    def penskor(daftar):
        return det.skor(daftar)["selisih"]

    hasil = {}
    for s in arena.BAKU + SIASAT_BARU:
        h = arena.jalankan(eps, idx, penskor, amb, tahan, s, maks_klaim=klaim)
        hasil[s["nama"]] = h
    return hasil


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--klaim", type=int, default=400)
    # Kuantil sumbangan bukti yang dipakai jadi batas. Nol koma delapan
    # berarti larangan penuh, karena sumbangannya nol pada delapan puluh
    # persen berkas. Nol koma sembilan sembilan berarti potongan ekor saja.
    p.add_argument("--kuantil", type=float, default=0.8)
    p.add_argument("--keluar", default="runs/tambal_bukti.json")
    a = p.parse_args()

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

    print("[2] melatih dua detektor pada data yang sama")
    t = time.time()
    polos, bertambal = latih_dua(eps, itr, nk, a.benih, a.kuantil)
    print(f"    selesai dalam {time.time() - t:.0f} detik")
    print(f"    batas sumbangan bukti yang dipelajari: Rp {bertambal.batas_bukti:,.0f}")
    # Sebaran sumbangannya ikut dicetak. Batas yang kecil bisa berarti dua
    # hal yang sangat berbeda: bukti memang hampir tidak menggeser tebakan,
    # atau kuantilnya salah pilih. Yang membedakan cuma sebarannya.
    naik = bertambal._sumbangan_bukti([eps[i] for i in itr[nk : nk + 4000]])
    q = np.quantile(naik, [0.5, 0.8, 0.95, 0.99, 1.0])
    print("    sumbangan bukti pada tebakan tarif, per kuantil:")
    nama = ("p50", "p80", "p95", "p99", "maks")
    print("      " + "  ".join(f"{n} Rp {v:,.0f}" for n, v in zip(nama, q)))

    print("\n[3] T6, pelaku yang beradaptasi")
    hp = ukur_lawan(eps, ite, polos, a.klaim)
    hb = ukur_lawan(eps, ite, bertambal, a.klaim)
    print(f"    {'siasat':32s} {'polos':>12s} {'bertambal':>12s} {'beda':>12s}")
    for nama in hp:
        x, y = hp[nama].get("lolos_rp", 0), hb[nama].get("lolos_rp", 0)
        print(f"    {nama:32s} {jt(x)} {jt(y)} {jt(y - x)}")

    lolos_polos = max(h.get("lolos_rp", 0) for h in hp.values())
    lolos_tambal = max(h.get("lolos_rp", 0) for h in hb.values())
    turun = 1.0 - lolos_tambal / max(lolos_polos, 1)
    print(f"    uang lolos terburuk: {jt(lolos_polos)} lalu {jt(lolos_tambal)}")
    print(f"    turun {turun:.1%}")

    # T6 versi rancangan: keuntungan maksimum per berkas milik pelaku yang
    # beradaptasi, dibanding milik pelaku serakah yang tidak peduli tertangkap.
    def t6(h) -> float:
        serakah = h["serakah"].get("maks_per_klaim_rp", 0)
        adaptif = max(v.get("maks_lolos_rp", 0) for k, v in h.items() if k != "serakah")
        return 1.0 - adaptif / max(serakah, 1)

    t6_polos, t6_tambal = t6(hp), t6(hb)
    print(f"    T6 polos {t6_polos:.1%}, bertambal {t6_tambal:.1%}, batas 50%")

    print("\n[4] T2, laju penandaan berkas bersih")
    uji = [eps[i] for i in ite]
    bersih = [i for i, r in enumerate(uji) if not r.get("modus")]
    for nama, det in (("polos", polos), ("bertambal", bertambal)):
        tanda = det.tandai(uji)
        laju = float(np.asarray(tanda)[bersih].mean())
        print(f"    {nama:10s} laju penandaan berkas bersih {laju:.4f}, batas 0,03")

    print("\n[5] tugas biasa, rupiah yang ditemukan pada anggaran seribu berkas")
    sel_nyata = np.array([float(r.get("selisih_rp", 0)) for r in uji])
    for nama, det in (("polos", polos), ("bertambal", bertambal)):
        s = det.skor(uji)["selisih"]
        urut = np.argsort(-s)[:1000]
        rp = float(sel_nyata[urut].sum())
        tepat = float((sel_nyata[urut] > 0).mean())
        print(f"    {nama:10s} rp@1000 {jt(rp)}  presisi@1000 {tepat:.3f}")

    catatan = {
        "pengaturan": vars(a),
        "batas_bukti_rp": bertambal.batas_bukti,
        "lawan_polos": hp,
        "lawan_bertambal": hb,
        "T6": {"polos": t6_polos, "bertambal": t6_tambal, "batas": 0.5},
        "A5": {
            "lolos_terburuk_polos_rp": lolos_polos,
            "lolos_terburuk_bertambal_rp": lolos_tambal,
            "turun": turun,
        },
    }
    os.makedirs(os.path.dirname(a.keluar) or ".", exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(catatan, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nRinciannya di {a.keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
