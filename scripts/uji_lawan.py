"""Menguji detektor yang benar benar dikirim terhadap pelaku yang beradaptasi.

Ada lubang yang harus ditutup sebelum apa pun dikirim. Target T6 pada
rancangan dinyatakan tercapai, dan angkanya diukur pada transformer. Sejak
percobaan kedua belas, yang kami usulkan bukan transformer lagi melainkan
pohon berpenguat. Jadi klaim terkuat pada dokumen kami diukur pada model yang
sudah tidak kami kirim. Itu harus diperbaiki, bukan didiamkan.

Tiga pelaku diadu, sesuai rancangan:

    serakah     ambil keuntungan terbesar, tidak peduli tertangkap
    hati hati   hanya ambil yang skornya tetap di bawah ambang
    menyebar    ambil yang kenaikan skornya paling kecil

Pelaku hati hati dan menyebar diberi akses penuh ke skor detektor. Itu
asumsi terburuk dan disengaja. Rumah sakit yang benar benar ingin menghindari
sistem akan mencoba coba sampai tahu apa yang lolos, dan mengukur seolah
mereka buta akan memberi angka yang terlalu bagus.

Jalankan:
    python scripts/uji_lawan.py
"""

from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar import adversarial  # noqa: E402
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402
from nalar.pembanding import mesin_aturan  # noqa: E402


def utama(n_peserta=20000, tahun=3, seed=7, keluaran="runs/lawan.json"):
    catatan = {}
    print("[1] membangkitkan data dan melatih detektor yang dikirim")
    g = Pembangkit(n_peserta=n_peserta, tahun=tahun, seed=seed, n_fktp=900, n_fkrtl=150)
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=seed)
    itr, ite = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(seed)
    rng.shuffle(itr)
    nk = min(20000, len(itr) // 3)
    det = Detektor(alpha=0.02, seed=seed)
    det.latih([eps[i] for i in itr[nk:]]).kalibrasi([eps[i] for i in itr[:nk]])
    print(f"    {len(eps)} episode, {len(ite)} masuk uji")

    # Ambangnya berbeda beda menurut kelompok, sedangkan pengukur pelaku
    # menerima satu ambang saja. Jadi skornya digeser: yang dikembalikan
    # selisih dikurangi ambang klaim itu sendiri, sehingga ambang berlakunya
    # nol untuk semua. Klaim yang kelompoknya menahan diri diberi skor sangat
    # kecil, karena ia memang tidak akan pernah ditandai otomatis.
    def penskor_detektor(daftar):
        s = det.skor(daftar)["selisih"]
        amb, tahan = det.ambang_untuk(daftar)
        keluar = s - amb
        keluar[tahan] = -1e18
        return keluar

    def penskor_aturan(daftar):
        return mesin_aturan(daftar)[0]

    print("[2] detektor yang dikirim melawan tiga pelaku")
    hasil_det = adversarial.bandingkan(eps, ite, penskor_detektor, 0.0, seed=seed)
    for j in ("serakah", "hati_hati", "menyebar"):
        h = hasil_det[j]
        print(
            f"    {j:10s} diambil Rp {h['total_diambil_rp'] / 1e6:8.1f} jt "
            f"dari {h['klaim_yang_diserang']:3d} klaim, "
            f"maks per klaim Rp {h['maks_per_klaim_rp'] / 1e6:6.2f} jt, "
            f"tertangkap {h['porsi_tertangkap']}"
        )
    catatan["detektor"] = hasil_det

    print("[3] mesin aturan melawan pelaku yang sama, sebagai pembanding")
    # Tanpa baris ini, penurunan keuntungan tidak bisa dibaca. Aturan tetap
    # pun akan menurunkan keuntungan pelaku serakah, jadi pertanyaannya bukan
    # apakah turun, melainkan apakah turun lebih banyak daripada aturan.
    amb_aturan = float(np.percentile(mesin_aturan([eps[i] for i in itr[:nk]])[0], 98))
    hasil_atr = adversarial.bandingkan(eps, ite, penskor_aturan, amb_aturan, seed=seed)
    for j in ("serakah", "hati_hati", "menyebar"):
        h = hasil_atr[j]
        print(
            f"    {j:10s} diambil Rp {h['total_diambil_rp'] / 1e6:8.1f} jt, "
            f"maks per klaim Rp {h['maks_per_klaim_rp'] / 1e6:6.2f} jt, "
            f"tertangkap {h['porsi_tertangkap']}"
        )
    catatan["mesin_aturan"] = hasil_atr

    print("[4] menilai target T6")
    turun_det = hasil_det.get("_penurunan_keuntungan_maksimum")
    turun_atr = hasil_atr.get("_penurunan_keuntungan_maksimum")
    catatan["penilaian_T6"] = {
        "penurunan_keuntungan_maksimum_detektor": turun_det,
        "penurunan_keuntungan_maksimum_mesin_aturan": turun_atr,
        "batas": 0.5,
        "lulus": bool(turun_det is not None and turun_det >= 0.5),
        "lebih_baik_dari_aturan": bool(
            turun_det is not None and turun_atr is not None and turun_det > turun_atr
        ),
    }
    print(f"    detektor turun {turun_det}, mesin aturan turun {turun_atr}")
    print(f"    {catatan['penilaian_T6']}")

    print("[5] pelaku menyebar, yang seharusnya lolos deteksi per klaim")
    # Pelaku menyebar sengaja mengambil sedikit dari banyak klaim supaya tidak
    # ada satu klaim pun yang menonjol. Kalau ia lolos, yang seharusnya
    # menangkapnya bukan skor per klaim melainkan profil faskes. Jadi profil
    # dijalankan pada klaim yang sudah diserang, dan diperiksa apakah faskes
    # penyerang naik peringkat.
    from nalar.profil import peringkat_faskes, profil_faskes

    e_te = [eps[i] for i in ite]
    s_bersih = det.skor(e_te)["selisih"]
    prof_awal = profil_faskes(e_te, s_bersih, minimal_klaim=20)
    urut_awal = [k for k, _ in peringkat_faskes(prof_awal)]
    peta_awal = {k: i for i, k in enumerate(urut_awal)}

    # satu faskes dipilih, lalu seluruh klaim rawat inapnya diserang pelan
    per_faskes = {}
    for i, r in enumerate(e_te):
        if r["rawat_inap"] and not r["modus"]:
            per_faskes.setdefault((int(r["f_jenis"]), int(r["faskes"])), []).append(i)
    korban = [
        k
        for k, v in per_faskes.items()
        if len(v) >= 20 and peta_awal.get(k, 0) > len(urut_awal) // 2
    ]
    if korban:
        target = korban[0]
        e_serang = [dict(r) for r in e_te]
        naik = 0
        for i in per_faskes[target]:
            gerak = adversarial.kandidat_gerakan(e_te[i])
            if not gerak:
                continue
            varian = [adversarial._terapkan_upcode(e_te[i], gg) for gg in gerak]
            sv = penskor_detektor(varian)
            aman = np.flatnonzero(sv <= 0)
            if aman.size == 0:
                continue
            untung = np.array([v["tarif"] - e_te[i]["tarif"] for v in varian])
            pilih = int(aman[np.argmax(untung[aman])])
            if untung[pilih] > 0:
                e_serang[i] = varian[pilih]
                naik += 1
        s_serang = det.skor(e_serang)["selisih"]
        prof_akhir = profil_faskes(e_serang, s_serang, minimal_klaim=20)
        urut_akhir = [k for k, _ in peringkat_faskes(prof_akhir)]
        peta_akhir = {k: i for i, k in enumerate(urut_akhir)}
        catatan["menyebar_terlihat_profil"] = {
            "faskes": f"{target[0]}:{target[1]}",
            "klaim_diserang": naik,
            "peringkat_sebelum": peta_awal.get(target),
            "peringkat_sesudah": peta_akhir.get(target),
            "dari_total_faskes": len(urut_akhir),
            "naik_ke_25_teratas": bool(peta_akhir.get(target, 999) < 25),
        }
        print(f"    {catatan['menyebar_terlihat_profil']}")

    os.makedirs(os.path.dirname(keluaran), exist_ok=True)
    with open(keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)
    print(f"\nditulis ke {keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
