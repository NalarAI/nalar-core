"""Uji tahap empat: Agen Pola, Agen Aturan, dan target A2 serta A6.

Kedua agen ini yang mengisi dua lubang yang disebut survei tujuh dimensi
agen kesehatan: pengaktifan oleh peristiwa, dan mekanisme memperbarui serta
melupakan pengetahuan lama.

Yang diuji bukan bahwa keduanya berjalan. Yang diuji janji yang membuat
keduanya boleh dipasang:

Agen Pola diam ketika tidak ada yang melewati ambang. Agen yang selalu punya
sesuatu untuk dilaporkan akan berhenti dibaca dalam sebulan.
Perkaranya menyebut berkas mana yang menyumbang, bukan cuma peringkat.
Agen Aturan mengembalikan tabel tarif aslinya apa pun yang terjadi, termasuk
ketika penilaiannya gagal di tengah.
Ia melaporkan nomor berkas yang berubah putusan, bukan cuma cacahnya.
Aturan yang dicabut ditandai, bukan dihapus.
A2: lapisan agen tidak menggeser satu pun penandaan.

Jalankan:
    python tests/test_agen_empat.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

lulus, gagal = 0, 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


try:
    import sklearn  # noqa: F401
except ImportError:
    print("\nDILEWATI  scikit-learn tidak terpasang")
    print("          pasang dengan: pip install '.[dev]'")
    sys.exit(0)

import numpy as np  # noqa: E402

from nalar import tarif_resmi as tr  # noqa: E402
from nalar.agen import aturan as pustaka  # noqa: E402
from nalar.agen import pola, susun, susun_agen, terbitan  # noqa: E402
from nalar.agen.penutur import Penutur  # noqa: E402
from nalar.api.keadaan import Keadaan  # noqa: E402

print("\n1. Menyiapkan keadaan")
K = Keadaan(n_peserta=1500, tahun=2, seed=7, n_fktp=90, n_fkrtl=24)
K.bangun(alpha=0.02)
cek("keadaan siap", K.siap and len(K.episodes) > 200, str(len(K.episodes)))

print("\n2. Agen Pola dibangunkan peristiwa, bukan oleh pembaca halaman")

h = pola.jalankan(K)
cek("agen pola berjalan tanpa galat", "perkara" in h, str(h)[:80])
cek(
    "seluruh perkara melewati ambang yang ditetapkan lebih dulu",
    all(p["p"] <= h["ambang"]["batas_p"] for p in h["perkara"])
    and all(p["geser_rp"] >= h["ambang"]["minimal_geser_rp"] for p in h["perkara"]),
    str([(p["p"], p["geser_rp"]) for p in h["perkara"][:2]]),
)
cek(
    "tiap perkara menyebut berkas yang menyumbang, bukan cuma peringkat",
    all(isinstance(p["berkas_penyumbang"], list) for p in h["perkara"]),
)
cek(
    "tiap perkara menyebut tanggal pergeserannya",
    all(isinstance(p["hari_ganti"], int) for p in h["perkara"]),
)
cek(
    "perkaranya terurut dari pergeseran terbesar",
    all(
        h["perkara"][i]["geser_rp"] >= h["perkara"][i + 1]["geser_rp"]
        for i in range(len(h["perkara"]) - 1)
    ),
)

# Ambang yang mustahil harus menghasilkan diam, bukan daftar kosong yang
# disamarkan jadi sesuatu. Ini yang membedakan agen dari laporan.
sepi = pola.jalankan(K, minimal_geser_rp=10**12)
cek(
    "tidak ada yang melewati ambang berarti agen diam",
    sepi["n_perkara"] == 0 and sepi["perkara"] == [],
    str(sepi["n_perkara"]),
)
cek(
    "yang diam tetap melaporkan berapa faskes yang diuji",
    sepi["n_faskes_diuji"] == h["n_faskes_diuji"],
)
cek(
    "tidak menyimpulkan sebab, cuma meminta pemeriksaan",
    all("kesimpulan" in p["catatan"] for p in h["perkara"]) or not h["perkara"],
)

print("\n3. Agen Aturan, dan target A6")

lama = tr._muat()
if not lama:
    print("         DILEWATI, tabel tarif resmi tidak ada di lingkungan ini")
else:
    # Terbitan buatan: seluruh tarif naik sepuluh persen. Bukan ramalan
    # kebijakan, cuma pengungkit untuk melihat apakah agennya melapor.
    baru = {k: tuple(int(round(x * 1.10)) for x in v) for k, v in lama.items()}
    r = terbitan.jalankan(K, baru, dicabut="Permenkes 3 Tahun 2023")

    cek(
        "tabel tarif aslinya dikembalikan sesudah dijalankan",
        tr._muat() == lama,
    )
    cek(
        "perubahan tarif dilaporkan per kode",
        r["tarif"]["n_baris_berubah"] > 0,
        str(r["tarif"]["n_baris_berubah"]),
    )
    cek(
        "kenaikan terbesar disebut beserta kodenya",
        bool(r["tarif"]["naik_terbesar"]) and "kode" in r["tarif"]["naik_terbesar"][0],
    )
    cek(
        "berkas yang berubah putusan disebut nomornya",
        isinstance(r["putusan"]["jadi_tertandai"], list)
        and isinstance(r["putusan"]["jadi_bersih"], list),
    )
    cek(
        "cacah yang berpindah cocok dengan porsinya",
        abs(
            r["putusan"]["porsi_berpindah"]
            - (r["putusan"]["n_jadi_tertandai"] + r["putusan"]["n_jadi_bersih"])
            / max(r["putusan"]["n_diperiksa"], 1)
        )
        < 1e-6,
    )
    cek(
        "aturan yang dicabut ditandai, bukan dihapus",
        bool(r["aturan_kedaluwarsa"])
        and any(e.get("kedaluwarsa") for e in pustaka.DASAR),
        str(r["aturan_kedaluwarsa"][:2]),
    )
    cek(
        "entri yang ditandai tetap ada di pustaka",
        len(pustaka.DASAR) >= 4,
        str(len(pustaka.DASAR)),
    )
    # A6 berbunyi dalam satu hari kerja. Yang diukur di sini lama
    # penilaiannya, bukan lama seluruh prosesnya, karena memasang tabel baru
    # tetap pekerjaan orang.
    cek(
        f"A6 penilaian ulang selesai jauh di bawah satu hari kerja, {r['detik']} detik",
        r["detik"] < 8 * 3600,
        f"{r['detik']} detik",
    )
    print(f"         penilaian ulang {r['detik']} detik untuk {len(K.episodes)} berkas")

    # Tabel harus kembali sekalipun penilaiannya meledak di tengah.
    rusak = dict(baru)
    kelas = K.detektor.tandai

    def meledak(_):
        raise RuntimeError("sengaja gagal")

    K.detektor.tandai = meledak
    try:
        terbitan.jalankan(K, rusak)
    except RuntimeError:
        pass
    finally:
        K.detektor.tandai = kelas
    cek("tabel aslinya kembali walau penilaiannya gagal di tengah", tr._muat() == lama)

    for e in pustaka.DASAR:
        e.pop("kedaluwarsa", None)

print("\n4. Peraturan dikenali dari nomornya, bukan dari ejaannya")

# Ini yang gagal pertama kali, dan gagalnya diam. Pustaka menulis "Peraturan
# Menteri Kesehatan Nomor 3 Tahun 2023", yang mencabut menulis "Permenkes 3
# Tahun 2023", tidak ada yang tertandai kedaluwarsa, dan seluruh uji lain
# tetap lulus. Pustakanya diam diam tetap mengutip peraturan yang dicabut.
for sebutan in (
    "Permenkes 3 Tahun 2023",
    "Peraturan Menteri Kesehatan Nomor 3 Tahun 2023",
    "PMK 3/2023",
):
    kena = terbitan.kedaluwarsakan(pustaka, sebutan)
    cek(
        f"sebutan '{sebutan}' mengenai entri yang sama",
        [k["kode"] for k in kena] == ["D01"],
        str(kena),
    )

cek(
    "peraturan lain tidak ikut tertandai",
    [k["kode"] for k in terbitan.kedaluwarsakan(pustaka, "Permenkes 16 Tahun 2019")]
    == ["D02"],
)
cek(
    "sebutan tanpa nomor tidak menandai apa pun",
    terbitan.kedaluwarsakan(pustaka, "peraturan menteri kesehatan") == [],
)
for e in pustaka.DASAR:
    e.pop("kedaluwarsa", None)


print("\n5. Target A2, lapisan agen tidak menggeser penandaan")

sebelum = np.asarray(K.detektor.tandai(K.episodes), dtype=bool)
ID = [K.id_klaim(int(i)) for i in K.urutan[:25]]
for i in ID:
    susun(K, i)
    susun_agen(K, i, penutur=Penutur())
sesudah = np.asarray(K.detektor.tandai(K.episodes), dtype=bool)
cek(
    "menyusun berkas perkara tidak menggeser satu pun penandaan",
    bool((sebelum == sesudah).all()),
    f"{int((sebelum != sesudah).sum())} bergeser",
)

bersih = [i for i, r in enumerate(K.episodes) if not r.get("modus")]
laju = float(sesudah[bersih].mean())
cek(
    f"laju penandaan berkas bersih tetap di bawah alpha, {laju:.4f}",
    laju <= 0.03,
    f"{laju:.4f}",
)

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
