"""Menjalankan keenam agen sekali jalan, lalu melaporkan lulus atau gagal.

Tiap agen sudah punya ujinya sendiri, dan tiap uji lulus. Yang tidak pernah
ada satu jalan yang membuktikan keenamnya bekerja bersama pada satu keadaan
yang sama, dengan model bahasa yang benar benar menyala.

Perbedaannya bukan soal kerapian. Uji memakai penutur bernaskah, dan penutur
bernaskah membuktikan penjaganya benar tanpa membuktikan modelnya patuh.
Berkas ini memakai model sungguhan, dan tiap agen harus menyerahkan bukti
yang bisa dilihat: nomor berkas, kode pemeriksaan, cacah perkara, sebab
rantai diputus.

Keadaannya sengaja kecil supaya muat di mesin pengembangan yang memorinya
terbatas. Yang diperiksa di sini apakah agennya bekerja, bukan seberapa baik
angkanya. Angka mutunya diukur skrip lain pada data penuh.

Jalankan:
    python scripts/periksa_agen.py
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import time

import numpy as np

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar import tarif_resmi as tr  # noqa: E402
from nalar.agen import (  # noqa: E402  # noqa: E402
    Anggaran,
    PenuturSetempat,
    awasi_pola,
    baca_sanggahan,
    lawan,
    susun_agen,
    terbitan,
)
from nalar.api.keadaan import Keadaan  # noqa: E402
from nalar.katalog import PEMERIKSAAN  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def lapor(agen: str, lulus: bool, bukti: str) -> None:
    hasil.append((agen, lulus, bukti))
    tanda = "LULUS" if lulus else "GAGAL"
    print(f"  {tanda}  {agen:16s} {bukti}")


def _bersih(t: str) -> str:
    return " ".join(
        "".join(c if c.isalnum() or c == " " else " " for c in t.lower()).split()
    )


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=700)
    p.add_argument("--tahun", type=int, default=2)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--model", default=os.environ.get("NALAR_MODEL", "nalar-qwen3-4b"))
    a = p.parse_args()

    penutur = PenuturSetempat(model=a.model)
    hidup = penutur.hidup()
    print(f"Model {penutur.model} di {penutur.alamat}, menyala: {hidup}")
    if not hidup:
        print(
            "Tiga agen yang memakai model bahasa akan dilewati, bukan dianggap lulus."
        )

    print("\n[0] menyiapkan keadaan")
    t = time.time()
    K = Keadaan(n_peserta=a.peserta, tahun=a.tahun, seed=a.benih, n_fktp=40, n_fkrtl=10)
    K.bangun(alpha=0.02)
    kid = K.id_klaim(int(K.urutan[0]))
    print(
        f"    {len(K.episodes)} klaim, siap dalam {time.time() - t:.0f} detik, "
        f"berkas contoh {kid}"
    )

    print("\n[1] Agen Penyelia, memutus rantai yang melewati anggaran")
    h = susun_agen(K, kid, penutur=penutur, anggaran=Anggaran(giliran=1))
    lapor(
        "Penyelia",
        h["sumber"] == "aturan" and bool(h["sebab_mundur"]),
        h["sebab_mundur"][:60] or "rantai tidak diputus",
    )

    print("\n[2] Agen Berkas, menyusun berkas perkara")
    if not hidup:
        lapor("Berkas", False, "DILEWATI, tidak ada model bahasa")
    else:
        h = susun_agen(K, kid, penutur=penutur, dalam=True)
        d = h.get("dalam") or {"cacat": []}
        bersih = h["sumber"] == "agen" and not d["cacat"]
        lapor(
            "Berkas",
            bersih,
            f"sumber {h['sumber']}, {len(d['cacat'])} cacat, "
            f"{len(h['ringkas_jejak']['alat'])} panggilan alat, "
            f"sidik {h['ringkas_jejak']['sidik_akhir'][:8]}",
        )
        if bersih:
            print(f"         {h['teks'][:150]}")

    print("\n[3] Agen Sanggah, membaca surat balasan faskes")
    surat = (
        "Bersama ini kami lampirkan hasil pemeriksaan hemoglobin dan trombosit "
        "atas nama pasien tersebut. Pemeriksaan kreatinin tidak dilakukan."
    )
    if not hidup:
        lapor("Sanggah", False, "DILEWATI, tidak ada model bahasa")
    else:
        s = baca_sanggahan(K, kid, surat, penutur=penutur)
        semua = s["dipetakan"] + s["sudah_terbaca"]
        kode_sah = all(b["kode"] in PEMERIKSAAN for b in semua)
        # Tiap kode harus membawa alasan yang katanya benar benar ada di surat.
        teks = _bersih(surat)
        berakar = all(
            all(k in teks.split() for k in _bersih(b["alasan"]).split()[-3:])
            or b["kode"].lower() in teks
            or _bersih(b["nama"]) in teks
            for b in semua
        )
        punya = {b["kode"] for b in semua}
        # Suratnya menyebut dua pemeriksaan yang dilampirkan dan satu yang
        # justru disebut tidak dikerjakan. Menerima "ada yang terbaca" saja
        # akan meloloskan agen yang cuma menemukan separuhnya, dan itulah
        # yang terjadi pada jalan pertama pemeriksaan ini.
        harus = {"HB", "TROMB"}
        lapor(
            "Sanggah",
            harus <= punya
            and "KREA" not in punya
            and kode_sah
            and berakar
            and s["cara"] == "model",
            f"cara {s['cara']}, terbaca {sorted(punya)}, harus memuat "
            f"{sorted(harus)}, kreatinin ditolak {'KREA' not in punya}, "
            f"kode sah {kode_sah}, berakar {berakar}",
        )

    print("\n[4] Agen Pola, mengawasi pergeseran faskes")
    hp = awasi_pola(K)
    lapor(
        "Pola",
        "n_faskes_diuji" in hp and "perkara" in hp and "ambang" in hp,
        f"{hp['n_faskes_diuji']} faskes diuji, {hp['n_lolos_tanpa_koreksi']} lolos "
        f"tanpa koreksi, {hp['n_perkara']} perkara dibuka pada fdr "
        f"{hp['ambang']['fdr']}",
    )

    print("\n[5] Agen Aturan, menanggapi tabel tarif baru")
    lama = tr._muat()
    if not lama:
        lapor("Aturan", False, "DILEWATI, tabel tarif resmi tidak ada")
    else:
        baru = {k: tuple(int(round(x * 1.10)) for x in v) for k, v in lama.items()}
        r = terbitan.jalankan(K, baru, dicabut="Permenkes 3 Tahun 2023")
        pulih = tr._muat() == lama
        pu = r["putusan"]
        berubah = pu["n_jadi_tertandai"] + pu["n_jadi_bersih"]
        lapor(
            "Aturan",
            pulih and pu["n_diperiksa"] > 0 and bool(r["aturan_kedaluwarsa"]),
            f"{pu['n_diperiksa']} berkas dinilai ulang, {berubah} berubah putusan, "
            f"{len(r['aturan_kedaluwarsa'])} aturan kedaluwarsa, {r['detik']} detik, "
            f"tabel aslinya pulih {pulih}",
        )

    print("\n[6] Agen Lawan, merancang siasat penghindaran")
    if not hidup:
        lapor("Lawan", False, "DILEWATI, tidak ada model bahasa")
    else:
        idx = np.array([int(i) for i in K.urutan[:80]])
        temu, sahih = idx[::2], idx[1::2]

        def penskor(daftar):
            return K.detektor.skor(daftar)["selisih"]

        amb = np.full(len(K.episodes), np.inf)
        tahan = np.ones(len(K.episodes), dtype=bool)
        av, tv = K.detektor.ambang_untuk([K.episodes[i] for i in idx])
        amb[idx] = av
        tahan[idx] = tv
        g = lawan.Gelanggang(
            K.episodes, temu, sahih, penskor, amb, tahan, maks_klaim=30
        )
        hl = lawan.jalankan(g, penutur=penutur, anggaran=Anggaran(giliran=6, rp=2000.0))
        temuan = hl.get("temuan") or []
        lapor(
            "Lawan",
            hl["sumber"] == "agen" and hl["dicoba"] > 0,
            f"{hl['dicoba']} siasat dicoba, {len(temuan)} mengalahkan garis dasar, "
            f"berhenti karena {hl['sebab_berhenti'] or 'model selesai sendiri'}",
        )

    print("\n" + "=" * 68)
    n_lulus = sum(1 for _, ok, _ in hasil if ok)
    print(
        f"{n_lulus} dari {len(hasil)} agen terbukti bekerja pada satu jalan yang sama"
    )
    print("=" * 68)
    for nama, ok, bukti in hasil:
        if not ok:
            print(f"  belum terbukti: {nama}, {bukti}")
    return 0 if n_lulus == len(hasil) else 1


if __name__ == "__main__":
    raise SystemExit(utama())
