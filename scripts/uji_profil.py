"""Menguji kepala K4 yang ditulis ulang, mencurigai faskes bukan klaim.

Versi lama presisinya 0,2 sampai 0,3 pada sepuluh teratas melawan tebakan
acak 0,16, jadi praktis tidak berguna. Berkas ini mengukur apakah versi baru
benar benar lebih baik, dan terhadap tiga pembanding sekaligus supaya
peningkatannya tidak bisa diklaim tanpa bukti:

    acak        prevalensi faskes nakal, ini lantainya
    mentah      urutkan menurut rata rata selisih tanpa penyusutan
    volume      urutkan menurut total nilai klaim, garis dasar yang bodoh
    susut       versi baru, Bayes empiris terhadap kelompok sebaya teramati

Kalau susut tidak mengalahkan mentah, maka penyusutannya tidak berguna dan
harus dibuang, bukan dipertahankan karena terdengar canggih.

Jalankan:
    python scripts/uji_profil.py
"""

from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402
from nalar.profil import (  # noqa: E402
    peringkat_faskes,
    profil_faskes,
)


def _presisi(urut, kebenaran, daftar_k, dasar):
    out = {}
    for k in daftar_k:
        sel = urut[:k]
        if not sel:
            continue
        p = float(np.mean([kebenaran.get(x, 0) for x in sel]))
        out[f"presisi@{k}"] = round(p, 4)
        out[f"peningkatan@{k}"] = round(p / dasar, 3) if dasar > 0 else None
    return out


def utama(n_peserta=20000, tahun=3, seed=7, keluaran="runs/profil.json"):
    catatan = {}
    print("[1] membangkitkan data")
    g = Pembangkit(n_peserta=n_peserta, tahun=tahun, seed=seed, n_fktp=900, n_fkrtl=150)
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=seed)
    idx_tr, idx_te = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(seed)
    rng.shuffle(idx_tr)
    n_kal = min(20000, len(idx_tr) // 3)
    e_latih = [eps[i] for i in idx_tr[n_kal:]]
    e_kal = [eps[i] for i in idx_tr[:n_kal]]
    e_te = [eps[i] for i in idx_te]
    print(f"    {len(eps)} episode, {len(e_te)} masuk uji")

    print("[2] melatih detektor dan menskor")
    det = Detektor(alpha=0.02, seed=seed).latih(e_latih).kalibrasi(e_kal)
    sel = det.skor(e_te)["selisih"]

    print("[3] menyusun kebenaran tingkat faskes")
    # Satu faskes dinyatakan nakal bila kebijakannya bukan jujur. Kebijakan
    # itu melekat pada faskes, jadi seluruh klaimnya membawa kode yang sama.
    kebenaran, nilai_total = {}, {}
    for r, s in zip(e_te, sel):
        k = (int(r["f_jenis"]), int(r["faskes"]))
        kebenaran[k] = max(kebenaran.get(k, 0), 1 if r["kebijakan"] else 0)
        nilai_total[k] = nilai_total.get(k, 0.0) + r["tarif"] + r.get("tagih_bhp", 0)

    print("[4] membuat profil dengan penyusutan")
    prof = profil_faskes(e_te, sel, minimal_klaim=20, minimal_sebaya=3)
    dinilai = set(prof)
    dasar = float(np.mean([kebenaran[k] for k in dinilai])) if dinilai else 0.0
    daftar_k = (10, 25, 50, 100)
    print(
        f"    {len(prof)} faskes bisa dinilai, "
        f"prevalensi nakal di antaranya {dasar:.3f}"
    )

    print("[5] tiga pembanding pada himpunan faskes yang sama")
    # Himpunan faskesnya disamakan, kalau tidak yang dibandingkan adalah
    # keputusan siapa yang dinilai, bukan kualitas peringkatnya.
    per_faskes = {}
    for i, r in enumerate(e_te):
        per_faskes.setdefault((int(r["f_jenis"]), int(r["faskes"])), []).append(i)
    urut_mentah = sorted(dinilai, key=lambda k: -float(np.mean(sel[per_faskes[k]])))
    urut_volume = sorted(dinilai, key=lambda k: -nilai_total[k])
    urut_susut = [k for k, _ in peringkat_faskes(prof)]
    urut_z = sorted(dinilai, key=lambda k: -prof[k]["z"])

    hasil = {
        "prevalensi_dasar": round(dasar, 4),
        "n_faskes_dinilai": len(dinilai),
        "susut": _presisi(urut_susut, kebenaran, daftar_k, dasar),
        "z_susut": _presisi(urut_z, kebenaran, daftar_k, dasar),
        "mentah": _presisi(urut_mentah, kebenaran, daftar_k, dasar),
        "volume": _presisi(urut_volume, kebenaran, daftar_k, dasar),
    }
    for nama in ("susut", "z_susut", "mentah", "volume"):
        baris = "  ".join(
            f"@{k} {hasil[nama].get(f'presisi@{k}', float('nan')):.3f}"
            f" ({hasil[nama].get(f'peningkatan@{k}')}x)"
            for k in daftar_k
        )
        print(f"    {nama:8s} {baris}")

    print("[6] apakah faskes kecil masih naik ke atas")
    # Ini penyakit versi lama. Diperiksa dengan melihat rata rata banyak klaim
    # pada dua puluh lima teratas dibanding keseluruhan.
    n_semua = float(np.mean([prof[k]["n"] for k in dinilai]))
    diag = {"rata_klaim_semua": round(n_semua, 1)}
    for nama, urut in (("susut", urut_susut), ("mentah", urut_mentah)):
        v = float(np.mean([prof[k]["n"] for k in urut[:25]]))
        diag[f"rata_klaim_25_teratas_{nama}"] = round(v, 1)
        diag[f"rasio_{nama}"] = round(v / max(n_semua, 1e-9), 3)
        print(
            f"    {nama:8s} klaim rata rata di 25 teratas {v:7.1f} "
            f"melawan {n_semua:7.1f} keseluruhan  "
            f"(rasio {v / max(n_semua, 1e-9):.2f})"
        )
    hasil["ukuran_faskes_teratas"] = diag

    print("[7] kebijakan apa yang tertangkap")
    nama_keb = ("jujur", "oportunis", "sistematis", "ekstrem")
    keb_faskes = {}
    for r in e_te:
        keb_faskes[(int(r["f_jenis"]), int(r["faskes"]))] = int(r["kebijakan"])
    tangkap = {}
    for j, nm in enumerate(nama_keb):
        punya = [k for k in dinilai if keb_faskes.get(k) == j]
        if not punya:
            continue
        ada = sum(1 for k in urut_susut[:25] if keb_faskes.get(k) == j)
        tangkap[nm] = {
            "ada": len(punya),
            "di_25_teratas": ada,
            "tertangkap": round(ada / len(punya), 3),
        }
        print(
            f"    {nm:11s} ada {len(punya):3d}, "
            f"di 25 teratas {ada:2d} ({ada / len(punya):.1%})"
        )
    hasil["tangkapan_per_kebijakan"] = tangkap

    catatan["profil"] = hasil
    catatan["contoh_baris_teratas"] = [
        {"faskes": f"{k[0]}:{k[1]}", **v} for k, v in peringkat_faskes(prof, atas=5)
    ]
    catatan["putusan"] = {
        "susut_mengalahkan_mentah": bool(
            hasil["susut"].get("presisi@25", 0) > hasil["mentah"].get("presisi@25", 0)
        ),
        "susut_mengalahkan_volume": bool(
            hasil["susut"].get("presisi@25", 0) > hasil["volume"].get("presisi@25", 0)
        ),
        "peningkatan_atas_acak_pada_25": hasil["susut"].get("peningkatan@25"),
    }
    print(f"\n    putusan: {catatan['putusan']}")

    os.makedirs(os.path.dirname(keluaran), exist_ok=True)
    with open(keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)
    print(f"\nditulis ke {keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
