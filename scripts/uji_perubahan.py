"""Menguji kepala K6, titik perubahan perilaku faskes.

Dua hal diukur, dan yang pertama lebih penting daripada yang kedua.

Kendali positif palsu. Pada data yang tidak memuat satu pun perubahan
perilaku, berapa banyak faskes yang tetap ditandai berubah. Kalau angkanya
jauh di atas lima persen, maka ujinya menemukan pola pada derau, dan angka
berapa pun yang keluar sesudah itu tidak bisa dipercaya. Ini dijalankan lebih
dulu, sebelum melihat apakah kepalanya bisa menemukan apa apa.

Daya temu. Pada data yang sebagian faskes nakalnya baru mulai nakal di tengah
rentang waktu, berapa banyak yang ketemu, dan seberapa dekat tanggal yang
ditebak dengan tanggal yang sebenarnya.

Jalankan:
    python scripts/uji_perubahan.py
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
from nalar.profil import perubahan_faskes  # noqa: E402


def _siapkan(porsi_berubah, n_peserta, tahun, seed):
    g = Pembangkit(
        n_peserta=n_peserta,
        tahun=tahun,
        seed=seed,
        n_fktp=900,
        n_fkrtl=150,
        porsi_faskes_berubah=porsi_berubah,
    )
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=seed)
    itr, ite = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(seed)
    rng.shuffle(itr)
    nk = min(20000, len(itr) // 3)
    det = Detektor(alpha=0.02, seed=seed)
    det.latih([eps[i] for i in itr[nk:]]).kalibrasi([eps[i] for i in itr[:nk]])
    e_te = [eps[i] for i in ite]
    return g, det, e_te, det.skor(e_te)["selisih"]


def utama(n_peserta=20000, tahun=3, seed=7, keluaran="runs/perubahan.json"):
    catatan = {}

    print("[1] kendali positif palsu, data tanpa satu pun perubahan")
    _, _, e0, s0 = _siapkan(0.0, n_peserta, tahun, seed)
    p0 = perubahan_faskes(e0, s0, minimal_klaim=60, n_acak=200, seed=seed)
    nilai_p = np.array([v["p"] for v in p0.values()])
    palsu = {
        "n_faskes_diuji": len(p0),
        "porsi_p_di_bawah_05": round(float(np.mean(nilai_p < 0.05)), 4),
        "porsi_p_di_bawah_01": round(float(np.mean(nilai_p < 0.01)), 4),
        "batas_wajar_05": 0.10,
        "lulus": bool(np.mean(nilai_p < 0.05) <= 0.10),
    }
    catatan["kendali_positif_palsu"] = palsu
    print(
        f"    {palsu['n_faskes_diuji']} faskes diuji, "
        f"p<0,05 pada {palsu['porsi_p_di_bawah_05']:.1%}, "
        f"p<0,01 pada {palsu['porsi_p_di_bawah_01']:.1%}  "
        f"{'lulus' if palsu['lulus'] else 'GAGAL'}"
    )
    if not palsu["lulus"]:
        print(
            "    ujinya menemukan pola pada derau, angka daya temu di "
            "bawah tidak berarti apa apa"
        )

    print("[2] data dengan setengah faskes nakal berubah di tengah jalan")
    g1, _, e1, s1 = _siapkan(0.5, n_peserta, tahun, seed)
    p1 = perubahan_faskes(e1, s1, minimal_klaim=60, n_acak=200, seed=seed)
    keb = g1.kebijakan
    benar = {}
    for r in e1:
        k = (int(r["f_jenis"]), int(r["faskes"]))
        if k in benar:
            continue
        g = keb.ganti_rs[k[1]] if k[0] else keb.ganti_fktp[k[1]]
        benar[k] = int(g)

    berubah = [k for k in p1 if benar.get(k, -1) >= 0]
    tetap = [k for k in p1 if benar.get(k, -1) < 0]
    print(f"    {len(p1)} faskes diuji, {len(berubah)} di antaranya memang berubah")

    hasil = {
        "n_diuji": len(p1),
        "n_benar_berubah": len(berubah),
        "n_tidak_berubah": len(tetap),
    }
    for batas in (0.05, 0.01):
        tt = (
            float(np.mean([p1[k]["p"] < batas for k in berubah]))
            if berubah
            else float("nan")
        )
        sp = (
            float(np.mean([p1[k]["p"] < batas for k in tetap]))
            if tetap
            else float("nan")
        )
        hasil[f"tertangkap_p{batas}"] = round(tt, 4)
        hasil[f"salah_tuduh_p{batas}"] = round(sp, 4)
        print(
            f"    p<{batas}: tertangkap {tt:.1%} dari yang berubah, "
            f"salah tuduh {sp:.1%} dari yang tidak"
        )

    # Seberapa dekat tanggal tebakan dengan tanggal sebenarnya, dihitung
    # hanya pada faskes yang memang berubah dan memang tertangkap. Menghitung
    # jaraknya pada faskes yang tidak berubah tidak ada artinya.
    jarak = [abs(p1[k]["hari_ganti"] - benar[k]) for k in berubah if p1[k]["p"] < 0.05]
    if jarak:
        hasil["jarak_hari_median"] = int(np.median(jarak))
        hasil["jarak_hari_p90"] = int(np.percentile(jarak, 90))
        hasil["rentang_hari"] = tahun * 365
        print(
            f"    tanggal tebakan meleset {np.median(jarak):.0f} hari "
            f"(median) dari {tahun * 365} hari rentang"
        )

    # Dipecah menurut kebijakan yang dituju sesudah berubah. Faskes yang
    # berubah menjadi oportunis hanya menaikkan tarif pada tiga dari sepuluh
    # klaim yang memenuhi syarat, jadi pergeserannya memang kecil. Kalau yang
    # terlewat memang yang seperti itu, kelemahannya bisa dijelaskan. Kalau
    # yang ekstrem pun terlewat, kepalanya memang tidak bekerja.
    nama_keb = ("jujur", "oportunis", "sistematis", "ekstrem")
    # Diambil langsung dari kebijakan faskes, bukan dari bidang kebijakan di
    # rekaman episode. Bidang itu sekarang ikut waktu, jadi episode sebelum
    # titik ganti membawa nilai jujur, dan membacanya dari situ akan
    # melaporkan faskes yang berubah menjadi jujur, yang tidak pernah terjadi.
    tujuan = {}
    for k in berubah + tetap:
        tujuan[k] = int(keb.rs[k[1]] if k[0] else keb.fktp[k[1]])
    per_keb = {}
    for j, nm in enumerate(nama_keb):
        punya = [k for k in berubah if tujuan.get(k) == j]
        if not punya:
            continue
        per_keb[nm] = {
            "ada": len(punya),
            "tertangkap": round(float(np.mean([p1[k]["p"] < 0.05 for k in punya])), 4),
        }
        print(
            f"    berubah jadi {nm:11s} ada {len(punya):2d}, "
            f"tertangkap {per_keb[nm]['tertangkap']:.0%}"
        )
    hasil["tertangkap_per_kebijakan_tujuan"] = per_keb

    # Nilai tambahnya di atas K4 hanya nyata bila ia menemukan faskes yang
    # K4 lewatkan. Kalau tidak, kepala ini boleh dibuang.
    from nalar.profil import peringkat_faskes, profil_faskes

    prof = profil_faskes(e1, s1, minimal_klaim=20, minimal_sebaya=3)
    atas25 = {k for k, _ in peringkat_faskes(prof, atas=25)}
    lewat = [k for k in berubah if k not in atas25 and p1[k]["p"] < 0.05]
    hasil["berubah_yang_dilewatkan_k4_tapi_ditemukan_k6"] = len(lewat)
    hasil["berubah_yang_sudah_ditemukan_k4"] = len([k for k in berubah if k in atas25])
    print(
        f"    dari yang berubah: {hasil['berubah_yang_sudah_ditemukan_k4']} "
        f"sudah tertangkap K4, {len(lewat)} hanya tertangkap K6"
    )

    catatan["daya_temu"] = hasil
    catatan["contoh"] = [
        {"faskes": f"{k[0]}:{k[1]}", "hari_sebenarnya": benar[k], **p1[k]}
        for k in berubah[:5]
    ]

    os.makedirs(os.path.dirname(keluaran), exist_ok=True)
    with open(keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)
    print(f"\nditulis ke {keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
