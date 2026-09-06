"""Penyetelan pembangkit terhadap angka terbitan.

Uji kecocokan agregat dari rancangan bagian 12.6, dikerjakan sebagai penyetel,
bukan sebagai laporan. Ada dua tombol saja, dan keduanya punya sasaran yang
berasal dari angka terbitan BPJS Kesehatan dan DJSN.

  pengali_utilisasi   menaikkan atau menurunkan jumlah kunjungan
  tilt_tempat         menggeser bauran FKTP, rawat jalan lanjut, rawat inap

Sasaran:

  kunjungan per peserta per tahun
      725,3 juta kunjungan dibagi 282,7 juta peserta pada 2025, hasilnya 2,57.
      Sumber: Public Expose BPJS Kesehatan 2025.

  bauran tempat layanan
      Laporan bulanan DJSN mencatat 318,4 juta kunjungan RJTP sampai 31 Juli
      2025. Disetahunkan, itu sekitar tiga perempat seluruh kunjungan. Sisanya
      dibagi rawat jalan tingkat lanjut dan rawat inap, dengan rawat inap
      porsinya kecil. Angka 0,75, 0,23, dan 0,02 adalah pembacaan kami atas
      dua sumber itu, dan berstatus asumsi sampai laporan DJSN diunduh penuh
      dan dibaca langsung.

Kalau sasaran berubah karena kami membaca angka yang lebih baik, yang berubah
hanya berkas ini. Pembangkitnya tidak disentuh.
"""

from __future__ import annotations

import numpy as np

SASARAN_KUNJUNGAN_PER_ORANG_TAHUN = 2.57
SASARAN_BAURAN = {"FKTP": 0.75, "RJTL": 0.23, "RITL": 0.02}

# Toleransi lulus untuk uji kecocokan agregat. Rancangan menuliskan selisih
# relatif di bawah lima belas persen untuk sepuluh besaran teratas.
TOLERANSI_RELATIF = 0.15


def bauran(episodes) -> dict[str, float]:
    n = len(episodes)
    if n == 0:
        return {"FKTP": 0.0, "RJTL": 0.0, "RITL": 0.0}
    c = {"FKTP": 0, "RJTL": 0, "RITL": 0}
    for r in episodes:
        if not r["f_jenis"]:
            c["FKTP"] += 1
        elif r["rawat_inap"]:
            c["RITL"] += 1
        else:
            c["RJTL"] += 1
    return {k: v / n for k, v in c.items()}


def kunjungan_per_orang_tahun(episodes, n_peserta: int, tahun: int) -> float:
    return len(episodes) / max(n_peserta * tahun, 1)


def laporan(episodes, n_peserta: int, tahun: int) -> dict:
    """Uji kecocokan agregat. Mengembalikan hasil beserta lulus atau tidak."""
    b = bauran(episodes)
    kpot = kunjungan_per_orang_tahun(episodes, n_peserta, tahun)
    hasil = {
        "kunjungan_per_orang_tahun": {
            "terukur": round(kpot, 3),
            "sasaran": SASARAN_KUNJUNGAN_PER_ORANG_TAHUN,
            "selisih_relatif": round(
                abs(kpot - SASARAN_KUNJUNGAN_PER_ORANG_TAHUN)
                / SASARAN_KUNJUNGAN_PER_ORANG_TAHUN,
                3,
            ),
        }
    }
    for k, sas in SASARAN_BAURAN.items():
        hasil[f"porsi_{k}"] = {
            "terukur": round(b[k], 4),
            "sasaran": sas,
            "selisih_relatif": round(abs(b[k] - sas) / sas, 3),
        }
    hasil["lulus"] = all(
        v["selisih_relatif"] <= TOLERANSI_RELATIF
        for v in hasil.values()
        if isinstance(v, dict)
    )
    return hasil


def setel(
    n_peserta: int = 4000,
    tahun: int = 3,
    seed: int = 11,
    putaran: int = 14,
    verbose: bool = True,
) -> dict:
    """Cari nilai kedua tombol dengan iterasi sederhana.

    Bukan pengoptimal canggih. Dua tombol, sasaran monoton, jadi pembaruan
    proporsional sudah cukup dan bisa diperiksa orang lain dengan mata.
    """
    from .generator import Pembangkit

    pengali = 1.0
    tilt = {"tilt_fktp": 1.0, "skala_inap": 1.0}

    for i in range(putaran):
        g = Pembangkit(
            n_peserta=n_peserta,
            tahun=tahun,
            seed=seed,
            prevalensi_faskes_nakal=0.0,
            pengali_utilisasi=pengali,
            tilt_tempat=dict(tilt),
        )
        eps = g.jalankan()
        b = bauran(eps)
        kpot = kunjungan_per_orang_tahun(eps, n_peserta, tahun)

        if verbose:
            print(
                f"  putaran {i:2d}  kunjungan/orang/tahun {kpot:.3f}  "
                f"FKTP {b['FKTP']:.3f}  RJTL {b['RJTL']:.3f}  "
                f"RITL {b['RITL']:.3f}"
            )

        cukup_volume = (
            abs(kpot - SASARAN_KUNJUNGAN_PER_ORANG_TAHUN)
            / SASARAN_KUNJUNGAN_PER_ORANG_TAHUN
            <= 0.06
        )
        cukup_bauran = all(abs(b[k] - s) / s <= 0.10 for k, s in SASARAN_BAURAN.items())
        if cukup_volume and cukup_bauran:
            break

        # perbarui tombol volume
        if kpot > 1e-9:
            pengali *= (SASARAN_KUNJUNGAN_PER_ORANG_TAHUN / kpot) ** 0.65
        pengali = float(np.clip(pengali, 0.05, 60.0))

        # perbarui tombol bauran. Dua tombol, dua sasaran.
        if b["FKTP"] > 1e-6:
            tilt["tilt_fktp"] *= (SASARAN_BAURAN["FKTP"] / b["FKTP"]) ** 0.75 * (
                (1 - SASARAN_BAURAN["FKTP"]) / max(1 - b["FKTP"], 1e-6)
            ) ** -0.75
        if b["RITL"] > 1e-6:
            tilt["skala_inap"] *= (SASARAN_BAURAN["RITL"] / b["RITL"]) ** 0.65
        else:
            tilt["skala_inap"] *= 1.6
        # Batas sengaja diketatkan. Penyetel boleh menggeser bauran, tidak boleh
        # memindahkan kasus ke tempat yang salah secara klinis. Kalau sasaran
        # agregat tidak tercapai di dalam batas ini, yang dilaporkan adalah
        # kegagalannya, bukan batas yang dilonggarkan.
        tilt["tilt_fktp"] = float(np.clip(tilt["tilt_fktp"], 0.25, 4.0))
        tilt["skala_inap"] = float(np.clip(tilt["skala_inap"], 0.01, 8.0))

    return {
        "pengali_utilisasi": round(pengali, 4),
        "tilt_tempat": {k: round(v, 4) for k, v in tilt.items()},
        "hasil": laporan(eps, n_peserta, tahun),
    }
