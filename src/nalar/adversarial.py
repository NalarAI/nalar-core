"""Pelaku yang beradaptasi terhadap detektor.

Kecurangan bukan proses alam. Ia tanggapan manusia terhadap pengawasan. Begitu
detektor dipasang, pelaku bergeser ke pola yang tidak terdeteksi. Sistem yang
diuji hanya pada pola lama akan terlihat hebat pada tahun pertama dan tidak
berguna pada tahun ketiga.

Sepanjang penelusuran kami, evaluasi deteksi kecurangan kesehatan hampir selalu
dilakukan pada data statis. Pelaku dianggap tidak bergerak. Semua orang di
lapangan tahu asumsi itu salah, tapi datanya statis jadi asumsinya dipakai.

Karena pembangkit datanya kami tulis sendiri, pelaku sintetis bisa diberi
kemampuan melihat skor detektor dan menyesuaikan diri. Ini justru keuntungan
dari tidak punya data asli.

Ukuran keberhasilan yang benar bukan berapa persen pelaku tertangkap, tapi
berapa besar keuntungan maksimum yang masih bisa diambil pelaku terbaik.
Sistem pengawasan yang baik tidak menangkap semua orang, ia membuat kecurangan
tidak sepadan.
"""

from __future__ import annotations

import copy

import numpy as np

from . import katalog as K
from .fraud import KODE_PENAIK
from .tarif import hitung_keparahan, kelompokkan, tarif


def _terapkan_upcode(r: dict, tambah: list[str]) -> dict:
    """Salin klaim lalu tambahkan diagnosis sekunder, hitung ulang tarifnya."""
    d = copy.deepcopy(r)
    d["dxs"] = list(r["dxs"]) + [c for c in tambah if c not in r["dxs"]]
    kel = kelompokkan(d["dxp"], d["dxs"], d["prc"], d["los"], d["rawat_inap"])
    d["cbg"], d["keparahan"] = kel.kode, kel.keparahan
    d["tarif"] = tarif(kel, d["dxp"], d["prc"], d["kelas_rawat"],
                       d["f_kelas"], d["f_reg"])
    return d


def kandidat_gerakan(r: dict, maks: int = 6) -> list[list[str]]:
    """Gerakan yang bisa diambil pelaku pada satu klaim.

    Hanya upcoding lewat diagnosis sekunder. Modus lain bisa ditambahkan
    dengan pola yang sama, tapi satu modus sudah cukup untuk menjawab
    pertanyaan pokoknya, yaitu apakah detektor bisa dihindari.
    """
    if not r["rawat_inap"]:
        return []
    if hitung_keparahan(r["dxs"], r["los"], True) >= 3:
        return []
    kandidat = [c for c in KODE_PENAIK if c not in r["dxs"]]
    gerak = [[c] for c in kandidat[:maks]]
    for i in range(min(3, len(kandidat) - 1)):
        gerak.append([kandidat[i], kandidat[i + 1]])
    return gerak


def jalankan(episodes, idx, penskor, ambang, rng, jenis: str = "hati_hati",
             maks_klaim: int = 400):
    """Jalankan satu jenis pelaku dan ukur berapa yang bisa ia ambil.

    penskor  fungsi yang menerima daftar klaim dan mengembalikan skornya
    ambang   batas penandaan yang sedang berlaku
    jenis    serakah, hati_hati, atau menyebar
    """
    kandidat_idx = [i for i in idx if episodes[i]["rawat_inap"]][:maks_klaim]
    if not kandidat_idx:
        return {"status": "tidak ada klaim rawat inap pada himpunan uji"}

    asli = [episodes[i] for i in kandidat_idx]
    skor_asli = penskor(asli)

    diambil = 0.0
    tertangkap = 0
    dicoba = 0
    per_klaim = []

    for pos, i in enumerate(kandidat_idx):
        r = episodes[i]
        gerak = kandidat_gerakan(r)
        if not gerak:
            continue
        varian = [_terapkan_upcode(r, g) for g in gerak]
        untung = np.array([v["tarif"] - r["tarif"] for v in varian],
                          dtype=np.float64)
        if (untung <= 0).all():
            continue
        dicoba += 1
        skor = penskor(varian)

        if jenis == "serakah":
            # ambil keuntungan terbesar, tidak peduli terdeteksi
            pilih = int(np.argmax(untung))
        elif jenis == "hati_hati":
            # hanya ambil yang skornya tetap di bawah ambang
            aman = np.flatnonzero(skor <= ambang)
            if aman.size == 0:
                continue
            pilih = int(aman[np.argmax(untung[aman])])
        elif jenis == "menyebar":
            # ambil yang paling kecil kenaikan skornya, walau untungnya sedikit
            pilih = int(np.argmin(skor - skor_asli[pos]))
        else:
            raise ValueError(jenis)

        if untung[pilih] <= 0:
            continue
        diambil += float(untung[pilih])
        per_klaim.append(float(untung[pilih]))
        if skor[pilih] > ambang:
            tertangkap += 1

    n = len(per_klaim)
    return {
        "jenis_pelaku": jenis,
        "klaim_yang_bisa_diserang": dicoba,
        "klaim_yang_diserang": n,
        "total_diambil_rp": round(diambil),
        "rerata_per_klaim_rp": round(diambil / n) if n else 0,
        "maks_per_klaim_rp": round(max(per_klaim)) if per_klaim else 0,
        "porsi_tertangkap": round(tertangkap / n, 4) if n else None,
        "diambil_tanpa_tertangkap_rp": round(
            sum(p for p, s in zip(per_klaim, [0] * n)) if False else
            diambil * (1 - (tertangkap / n if n else 0))),
    }


def bandingkan(episodes, idx, penskor, ambang, seed=0):
    """Jalankan ketiga pelaku dan ringkas hasilnya.

    Yang paling penting adalah baris menyebar. Deteksi per klaim akan gagal
    menangkapnya, dan yang seharusnya menangkap adalah kepala kelompok sebaya.
    Kalau kepala itu juga gagal, kami menulis bahwa gagal.
    """
    rng = np.random.default_rng(seed)
    hasil = {}
    for jenis in ("serakah", "hati_hati", "menyebar"):
        hasil[jenis] = jalankan(episodes, idx, penskor, ambang, rng, jenis)

    s = hasil.get("serakah", {})
    h = hasil.get("hati_hati", {})
    if s.get("maks_per_klaim_rp") and h.get("maks_per_klaim_rp") is not None:
        hasil["_penurunan_keuntungan_maksimum"] = round(
            1.0 - h["maks_per_klaim_rp"] / max(s["maks_per_klaim_rp"], 1), 3)
        hasil["_target_T6_turun_setengah"] = bool(
            hasil["_penurunan_keuntungan_maksimum"] >= 0.5)
    return hasil
