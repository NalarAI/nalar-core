"""Penjaga arus acak pembangkit, supaya penataan gaya tidak menggeser dunia.

Sebuah baris di fraud.py pernah diubah urutannya saat gaya kode
diseragamkan. Yang lama memanggil pengacak lebih dulu lalu memeriksa lama
rawat, yang baru sebaliknya:

    if rec["rawat_inap"] and rng.random() < _peluang(kode, "M12"):
        if los < 10:

    if rec["rawat_inap"] and los < 10 and rng.random() < _peluang(kode, "M12"):

Keduanya menghasilkan keputusan yang sama untuk berkas itu. Yang berbeda
berapa kali pengacak dipanggil, dan itu menggeser seluruh undian sesudahnya.
Dunianya jadi dunia lain: 8.758 episode jadi 8.582, tarif totalnya bergeser
tujuh persen.

Akibatnya baru ketahuan berbulan kemudian. Angka ketahanan T6 yang kami
laporkan berubah dari 0,256 jadi 0,550 tanpa satu baris pun menyentuh
detektor, dan sempat terbaca sebagai perbaikan. Ia bukan perbaikan, ia
undian yang berbeda.

Uji ini memakukan sidik dunia pada benih tetap. Ia tidak menilai apakah
dunianya bagus. Ia cuma memastikan tidak ada yang menggesernya tanpa sadar,
dan kalau memang sengaja digeser, angkanya di sini harus ikut diperbarui
dalam commit yang sama sehingga perubahannya terlihat di riwayat.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar.generator import Pembangkit  # noqa: E402

lulus = gagal = 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


# Dunia kecil, supaya ujinya selesai dalam hitungan detik pada integrasi
# berkelanjutan. Kecil pun cukup: satu panggilan pengacak yang bergeser
# sudah mengubah seluruh angka di bawah.
SIDIK = {
    "n_episode": 665,
    "tarif_total": 593509034,
    "n_curang": 127,
    "los_total": 143,
    "dxs_total": 246,
}

print("\n1. Sidik dunia pada benih tetap")
g = Pembangkit(n_peserta=400, tahun=1, seed=7, n_fktp=60, n_fkrtl=12)
eps = g.jalankan()
punya = {
    "n_episode": len(eps),
    "tarif_total": sum(int(r["tarif"]) for r in eps),
    "n_curang": sum(1 for r in eps if r.get("modus")),
    "los_total": sum(int(r["los"]) for r in eps),
    "dxs_total": sum(len(r["dxs"]) for r in eps),
}
for k, v in SIDIK.items():
    cek(f"{k} tetap", punya[k] == v, f"{punya[k]} bukan {v}")

print("\n2. Dua panggilan dengan benih sama memberi dunia sama")
g2 = Pembangkit(n_peserta=400, tahun=1, seed=7, n_fktp=60, n_fkrtl=12)
eps2 = g2.jalankan()
cek(
    "cacah episodenya sama",
    len(eps2) == len(eps),
    f"{len(eps2)} bukan {len(eps)}",
)
cek(
    "tarif totalnya sama",
    sum(int(r["tarif"]) for r in eps2) == punya["tarif_total"],
)

print("\n3. Benih berbeda memberi dunia berbeda")
g3 = Pembangkit(n_peserta=400, tahun=1, seed=8, n_fktp=60, n_fkrtl=12)
eps3 = g3.jalankan()
cek(
    "benih lain menggeser tarif totalnya",
    sum(int(r["tarif"]) for r in eps3) != punya["tarif_total"],
)

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
