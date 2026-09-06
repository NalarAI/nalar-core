"""Uji detektor yang benar benar diusulkan, ujung ke ujung.

Berbeda dari percobaan.py yang membandingkan banyak penskor. Berkas ini
menjalankan satu konfigurasi saja, yaitu yang dipilih setelah dua belas
percobaan, dan memeriksa apakah ia memenuhi seluruh syarat yang ditetapkan
rancangan sebagai keluaran yang bisa dipakai.

Jalankan:
    python scripts/uji_detektor.py
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
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402
from nalar.pembanding import mesin_aturan  # noqa: E402


def utama(
    n_peserta=20000, tahun=3, seed=7, fktp=900, fkrtl=150, keluaran="runs/detektor.json"
):
    catatan = {}
    print("[1] membangkitkan data")
    g = Pembangkit(
        n_peserta=n_peserta, tahun=tahun, seed=seed, n_fktp=fktp, n_fkrtl=fkrtl
    )
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=seed)
    idx_tr, idx_te = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(seed)
    rng.shuffle(idx_tr)
    n_kal = min(20000, len(idx_tr) // 3)
    idx_kal, idx_latih = idx_tr[:n_kal], idx_tr[n_kal:]
    print(
        f"    {len(eps)} episode | latih {len(idx_latih)} "
        f"| kalibrasi {len(idx_kal)} | uji {len(idx_te)}"
    )

    e_latih = [eps[i] for i in idx_latih]
    e_kal = [eps[i] for i in idx_kal]
    e_te = [eps[i] for i in idx_te]

    print("[2] melatih penebak normatif, tanpa satu pun label kecurangan")
    # Himpunan kalibrasi diperbesar, karena kelompok gabungan lebih banyak
    # sehingga tiap kelompok butuh cukup anggota.
    det = Detektor(alpha=0.02, seed=seed).latih(e_latih).kalibrasi(e_kal)
    catatan["n_kelompok_kalibrasi"] = len(det.ambang_tingkat)

    print("[3] menskor dan mengukur")
    s = det.skor(e_te)["selisih"]
    sel_benar = np.array([max(r["selisih_rp"], 0) for r in e_te], dtype=np.float64)
    curang = np.array([1 if r["modus"] else 0 for r in e_te])
    skor_aturan, _ = mesin_aturan(e_te)
    daftar_k = [50, 100, 250, 500, 1000]

    hasil = metrik.kurva(
        {
            "detektor": s,
            "mesin_aturan": skor_aturan,
            "nilai_klaim": np.array(
                [r["tarif"] + r.get("tagih_bhp", 0) for r in e_te], dtype=np.float64
            ),
        },
        sel_benar,
        curang,
        daftar_k,
    )
    hasil["detektor"]["peningkatan_atas_aturan"] = metrik.peningkatan_atas(
        hasil, "detektor", "mesin_aturan", daftar_k
    )
    hasil["detektor"]["peningkatan_atas_nilai_klaim"] = metrik.peningkatan_atas(
        hasil, "detektor", "nilai_klaim", daftar_k
    )
    catatan["metrik"] = hasil

    print("[4] memeriksa jaminan konformal")
    kel_te = np.array([r["f_kelas"] for r in e_te])
    tanda_semua = det.tandai(e_te)
    _, tahan = det.ambang_untuk(e_te)
    bersih_te = curang == 0
    catatan["konformal"] = {
        "alpha": det.alpha,
        "laju_penandaan_klaim_bersih": round(float(tanda_semua[bersih_te].mean()), 5),
        "batas_lulus": round(det.alpha * 1.5, 5),
        "lulus": bool(tanda_semua[bersih_te].mean() <= det.alpha * 1.5),
        "n_ditandai": int(tanda_semua.sum()),
        "n_menahan_diri": int(tahan.sum()),
        "porsi_menahan_diri": round(float(tahan.mean()), 4),
    }

    print("[5] memeriksa keadilan")
    tanda = det.tandai(e_te)
    dtpk_te = np.array([r["f_dtpk"] for r in e_te])
    catatan["keadilan"] = {
        "simetris_kelas_faskes": metrik.keadilan_kelompok(tanda, kel_te, curang == 0),
        "simetris_daerah_tertinggal": metrik.keadilan_kelompok(
            tanda, dtpk_te, curang == 0
        ),
        "berarah_kelas_faskes": metrik.keadilan_berarah(tanda, kel_te, curang == 0),
        "berarah_daerah_tertinggal": metrik.keadilan_berarah(
            tanda, dtpk_te, curang == 0
        ),
    }

    print("[6] menyusun antrean audit dengan biaya dan batas per faskes")
    antre = det.antrean_audit(
        e_te, kapasitas=1000, batas_per_faskes=40, porsi_acak=0.05
    )
    rp_antre = float(sel_benar[antre].sum())
    catatan["antrean"] = {
        "kapasitas": 1000,
        "terisi": len(antre),
        "rupiah_ditemukan": round(rp_antre),
        "porsi_batas_atas": round(
            rp_antre / metrik.batas_atas(sel_benar, len(antre)), 4
        ),
        "biaya_audit_total": det.biaya_audit_rp * len(antre),
        "rasio_pengembalian": round(
            rp_antre / max(det.biaya_audit_rp * len(antre), 1), 2
        ),
    }

    print("[7] profil faskes, kepala K4 yang ditulis ulang")
    from nalar.profil import peringkat_faskes, profil_faskes

    prof = profil_faskes(e_te, s, minimal_klaim=20, minimal_sebaya=3)
    keb = {}
    for r in e_te:
        keb[(int(r["f_jenis"]), int(r["faskes"]))] = 1 if r["kebijakan"] else 0
    urut = [k for k, _ in peringkat_faskes(prof)]
    dasar = float(np.mean([keb[k] for k in prof])) if prof else 0.0
    catatan["profil_faskes"] = {
        "n_dinilai": len(prof),
        "prevalensi_dasar": round(dasar, 4),
        **{
            f"presisi@{k}": round(float(np.mean([keb.get(x, 0) for x in urut[:k]])), 4)
            for k in (10, 25, 50)
            if len(urut) >= k
        },
    }
    print(f"    {catatan['profil_faskes']}")

    catatan["penyaringan_kalibrasi"] = {
        "z_saring": det.z_saring,
        "n_faskes_dibuang": det.n_faskes_dibuang,
        "porsi_klaim_dibuang": det.porsi_klaim_dibuang,
    }

    print("[8] posisi terhadap garis, ukuran yang menjawab pelaku beradaptasi")
    pos = det.posisi(e_te)
    per_f = {}
    for i, r in enumerate(e_te):
        per_f.setdefault((int(r["f_jenis"]), int(r["faskes"])), []).append(i)
    rata_f = [float(np.mean(pos[v])) for v in per_f.values() if len(v) >= 100]
    catatan["posisi"] = {
        "rata_seluruh_klaim": round(float(pos.mean()), 5),
        "rata_antar_faskes_besar": round(float(np.mean(rata_f)), 5),
        "sd_antar_faskes_besar": round(float(np.std(rata_f)), 5),
        "n_faskes_besar": len(rata_f),
    }
    print(f"    {catatan['posisi']}")

    print("[9] contoh penjelasan")
    urut = np.argsort(-s)
    contoh = []
    for j in urut[:3]:
        contoh.append(det.jelaskan(e_te, int(j)))
    catatan["contoh_penjelasan"] = contoh

    det.simpan("runs/detektor.pkl")
    os.makedirs(os.path.dirname(keluaran), exist_ok=True)
    with open(keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)

    print("\n=== RINGKAS ===")
    r = {int(k): v for k, v in hasil["detektor"]["rupiah_pada_k"].items()}
    p = {int(k): v for k, v in hasil["detektor"]["porsi_batas_atas"].items()}
    for k in daftar_k:
        print(f"  k={k:5d}  Rp {r[k] / 1e6:8.1f} juta   porsi batas atas {p[k]:.3f}")
    print(f"  lift atas aturan     : {hasil['detektor']['peningkatan_atas_aturan']}")
    print(
        f"  lift atas nilai klaim: {hasil['detektor']['peningkatan_atas_nilai_klaim']}"
    )
    print(f"  konformal            : {catatan['konformal']}")
    ks = catatan["keadilan"]["simetris_kelas_faskes"]
    kb = catatan["keadilan"]["berarah_kelas_faskes"]
    print(
        f"  keadilan simetris    : rasio {ks.get('_rasio_maks_min')} "
        f"lulus {ks.get('_lulus_batas_dua_kali')}"
    )
    print(
        f"  keadilan berarah     : kelebihan maksimum "
        f"{kb.get('_kelebihan_maksimum')} pada "
        f"{kb.get('_kelompok_paling_sering_ditandai')} "
        f"lulus {kb.get('_lulus_batas_dua_kali')}"
    )
    print(f"  antrean              : {catatan['antrean']}")
    print(f"\nditulis ke {keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
