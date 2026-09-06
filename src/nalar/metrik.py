"""Metrik operasional.

Yang diukur bukan akurasi. Dengan prevalensi beberapa persen, menebak semuanya
bersih sudah memberi akurasi di atas sembilan puluh persen. Yang diukur adalah
berapa rupiah berlebih yang benar benar ditemukan pada anggaran audit tertentu,
dan berapa lipat itu dibanding cara memilih audit yang dipakai sekarang.
"""

from __future__ import annotations

import numpy as np


def rupiah_pada_k(skor, selisih_benar, k):
    """Jumlah selisih rupiah sebenarnya dari k klaim berperingkat teratas."""
    skor = np.asarray(skor, dtype=np.float64)
    sel = np.asarray(selisih_benar, dtype=np.float64)
    k = min(int(k), len(skor))
    if k <= 0:
        return 0.0
    urut = np.argsort(-skor)[:k]
    return float(np.clip(sel[urut], 0, None).sum())


def presisi_pada_k(skor, curang, k):
    skor = np.asarray(skor, dtype=np.float64)
    c = np.asarray(curang).astype(bool)
    k = min(int(k), len(skor))
    if k <= 0:
        return 0.0
    urut = np.argsort(-skor)[:k]
    return float(c[urut].mean())


def batas_atas(selisih, k):
    """Rupiah yang ditemukan kalau kita tahu jawabannya.

    Ini penskor sempurna: urutkan menurut selisih sebenarnya. Dipakai sebagai
    pembagi, sehingga hasil tiap penskor bisa dinyatakan sebagai porsi dari
    yang mungkin, bukan sebagai kelipatan atas pembanding yang dipilih
    sembarang.

    Metrik kelipatan atas mesin aturan punya cacat yang baru terlihat setelah
    beberapa percobaan: pada anggaran besar, semua penskor mendekati batas
    atas, jadi kelipatannya menyusut walau kinerjanya membaik. Porsi terhadap
    batas atas tidak punya cacat itu.
    """
    sel = np.clip(np.asarray(selisih, dtype=np.float64), 0, None)
    k = min(int(k), len(sel))
    if k <= 0:
        return 0.0
    return float(np.sort(sel)[::-1][:k].sum())


def kurva(skor_dict, selisih, curang, daftar_k):
    """Bandingkan beberapa penskor pada beberapa anggaran audit."""
    atas = {int(k): batas_atas(selisih, k) for k in daftar_k}
    hasil = {"_batas_atas": {k: round(v) for k, v in atas.items()}}
    for nama, s in skor_dict.items():
        rp = {int(k): rupiah_pada_k(s, selisih, k) for k in daftar_k}
        hasil[nama] = {
            "rupiah_pada_k": {k: round(v) for k, v in rp.items()},
            "presisi_pada_k": {
                int(k): round(presisi_pada_k(s, curang, k), 4) for k in daftar_k
            },
            # porsi dari yang mungkin ditemukan pada anggaran itu
            "porsi_batas_atas": {
                k: round(rp[k] / atas[k], 4) if atas[k] > 0 else None for k in rp
            },
        }
    return hasil


def peningkatan_atas(hasil, nama_uji, nama_dasar, daftar_k):
    """Berapa lipat model menemukan rupiah dibanding pembanding."""
    out = {}
    for k in daftar_k:
        a = hasil[nama_uji]["rupiah_pada_k"][int(k)]
        b = hasil[nama_dasar]["rupiah_pada_k"][int(k)]
        out[int(k)] = round(a / b, 3) if b > 0 else None
    return out


def acak_dasar(selisih, k, n_ulang=200, seed=0):
    """Rupiah yang ditemukan kalau audit dipilih acak. Batas bawah."""
    rng = np.random.default_rng(seed)
    sel = np.clip(np.asarray(selisih, dtype=np.float64), 0, None)
    k = min(int(k), len(sel))
    nilai = [
        sel[rng.choice(len(sel), size=k, replace=False)].sum() for _ in range(n_ulang)
    ]
    return float(np.mean(nilai))


def kalibrasi_selisih(perkiraan, benar, n_pita=8):
    """Diagram keandalan untuk perkiraan selisih rupiah.

    Ketika model memperkirakan selisih lima juta, apakah selisih sebenarnya
    rata rata memang lima juta. Kalau tidak terkalibrasi, seluruh peringkat
    audit salah, karena peringkatnya berdasarkan selisih.
    """
    p = np.asarray(perkiraan, dtype=np.float64)
    b = np.asarray(benar, dtype=np.float64)
    if len(p) < n_pita * 5:
        return []
    tepi = np.quantile(p, np.linspace(0, 1, n_pita + 1))
    out = []
    for i in range(n_pita):
        m = (p >= tepi[i]) & (p <= tepi[i + 1] if i == n_pita - 1 else p < tepi[i + 1])
        if m.sum() < 5:
            continue
        out.append(
            dict(
                pita=i,
                n=int(m.sum()),
                perkiraan_rerata=round(float(p[m].mean())),
                benar_rerata=round(float(b[m].mean())),
            )
        )
    return out


def keadilan_kelompok(tanda, kelompok, bersih):
    """Laju penandaan per kelompok, dihitung hanya pada klaim yang bersih.

    Sistem yang secara sistematis menuduh puskesmas di daerah akan dimatikan
    dalam setahun, dan pantas dimatikan. Ini uji T5 pada rancangan.
    """
    tanda = np.asarray(tanda).astype(bool)
    b = np.asarray(bersih).astype(bool)
    kel = np.asarray(kelompok)
    out = {}
    for k in np.unique(kel):
        m = (kel == k) & b
        if m.sum() < 20:
            continue
        out[str(k)] = dict(n=int(m.sum()), laju=round(float(tanda[m].mean()), 5))
    if len(out) >= 2:
        laju = [v["laju"] for v in out.values()]
        lo, hi = min(laju), max(laju)
        out["_rasio_maks_min"] = round(hi / lo, 3) if lo > 0 else None
        out["_lulus_batas_dua_kali"] = bool(lo > 0 and hi / lo <= 2.0)
    return out


def keadilan_pada_anggaran(skor, kelompok, bersih, porsi=0.02):
    """Laju penandaan per kelompok pada anggaran penandaan tetap.

    Dipakai untuk menguraikan ketimpangan per kepala. Ambang konformal
    bergantung pada himpunan kalibrasi tiap kepala, jadi membandingkan kepala
    lewat ambang konformal mencampur dua hal sekaligus. Dengan anggaran tetap,
    misalnya dua persen klaim teratas, yang dibandingkan murni bentuk sebaran
    skornya.

    Seluruh laju dihitung hanya pada klaim yang bersih, karena yang diukur
    adalah gangguan terhadap faskes yang tidak berbuat apa apa.
    """
    skor = np.asarray(skor, dtype=np.float64)
    n_tandai = max(1, int(round(len(skor) * porsi)))
    ambang = np.partition(skor, -n_tandai)[-n_tandai]
    tanda = skor >= ambang
    return keadilan_kelompok(tanda, kelompok, bersih)


def urai_keadilan(skor_dict, kelompok, bersih, porsi=0.02):
    """Bandingkan ketimpangan beberapa penskor pada anggaran yang sama."""
    keluar = {}
    for nama, s in skor_dict.items():
        h = keadilan_pada_anggaran(s, kelompok, bersih, porsi)
        keluar[nama] = {
            "rasio_maks_min": h.get("_rasio_maks_min"),
            "lulus_batas_dua_kali": h.get("_lulus_batas_dua_kali"),
            "laju_per_kelompok": {
                k: v["laju"] for k, v in h.items() if not k.startswith("_")
            },
        }
    return keluar


def keadilan_berarah(tanda, kelompok, bersih):
    """Ketimpangan yang diukur pada arah yang benar benar merugikan.

    Metrik rasio tertinggi terhadap terendah menyamakan dua hal yang sangat
    berbeda. Kelompok yang ditandai lebih sering dirugikan. Kelompok yang
    ditandai lebih jarang tidak dirugikan, ia diuntungkan.

    Kekhawatiran yang ditulis rancangan berbunyi jelas: sistem yang secara
    sistematis menuduh puskesmas di daerah akan dimatikan dalam setahun. Yang
    ditakutkan penandaan berlebih terhadap yang lemah, bukan penandaan kurang.

    Karena itu di sini yang dilaporkan kelebihan terhadap laju keseluruhan,
    dan kelompok yang di bawah laju keseluruhan tidak dihitung sebagai
    pelanggaran. Rasio simetris tetap dilaporkan terpisah, supaya tidak ada
    yang disembunyikan dengan mengganti definisi.
    """
    tanda = np.asarray(tanda).astype(bool)
    b = np.asarray(bersih).astype(bool)
    kel = np.asarray(kelompok)
    laju_umum = float(tanda[b].mean()) if b.any() else 0.0
    out = {"_laju_keseluruhan": round(laju_umum, 5)}
    kelebihan = []
    for k in np.unique(kel):
        m = (kel == k) & b
        if m.sum() < 20:
            continue
        laju = float(tanda[m].mean())
        rasio = laju / laju_umum if laju_umum > 0 else None
        out[str(k)] = {
            "n": int(m.sum()),
            "laju": round(laju, 5),
            "rasio_thd_keseluruhan": round(rasio, 3) if rasio else None,
        }
        if rasio and rasio > 1.0:
            kelebihan.append((rasio, str(k)))
    if kelebihan:
        r, nama = max(kelebihan)
        out["_kelompok_paling_sering_ditandai"] = nama
        out["_kelebihan_maksimum"] = round(r, 3)
        out["_lulus_batas_dua_kali"] = bool(r <= 2.0)
    return out
