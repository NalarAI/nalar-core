"""Uji lapisan agen tahap satu: alat, jejak audit, dan penjaga A1.

Yang diperiksa bukan sekadar fungsinya berjalan. Yang diperiksa empat janji
yang jadi alasan lapisan ini boleh dipasang sama sekali:

Alat menolak argumen yang salah, dan penolakannya ikut tercatat.
Jejaknya tidak bisa disunting tanpa merusak rantai sidiknya.
Tidak ada alat yang bisa mengubah penilaian.
Tidak ada angka pada berkas perkara yang tidak berasal dari pemanggilan alat.

Yang terakhir adalah target A1, dan angkanya diukur di sini pada banyak
berkas sekaligus, bukan pada satu contoh yang dipilih.

Jalankan:
    python tests/test_agen.py
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

from nalar.agen import GalatAlat, Jejak, Perkakas, periksa_a1, susun  # noqa: E402
from nalar.agen import aturan as pustaka  # noqa: E402
from nalar.agen.periksa import angka_pada  # noqa: E402
from nalar.api.keadaan import Keadaan  # noqa: E402

print("\n1. Menyiapkan keadaan")
K = Keadaan(n_peserta=1500, tahun=2, seed=7, n_fktp=90, n_fkrtl=24)
K.bangun(alpha=0.02)
cek("keadaan siap", K.siap, "")
cek("ada berkas untuk diperiksa", len(K.episodes) > 200, str(len(K.episodes)))

ID = [K.id_klaim(int(i)) for i in K.urutan[:60]]

print("\n2. Pustaka aturan")
j = pustaka.jangkauan()
cek(
    "dua puluh modus terdaftar",
    sum(j.values()) == 20,
    str(j),
)
cek(
    "jangkauan tiap modus ditulis apa adanya, termasuk yang belum tersentuh",
    j["belum"] > 0 and j["penuh"] > 0,
    str(j),
)
cek(
    "pencarian menemukan modus upcoding",
    any(e["kode"] == "M04" for e in pustaka.cari("upcoding diagnosis dinaikkan")),
)
cek(
    "titik buta lama rawat ditulis, bukan disembunyikan",
    any("titik buta" in (m["sebab"] or "").lower() for m in pustaka.MODUS),
)

print("\n3. Alat menolak yang tidak sah, dan penolakannya tercatat")
jej = Jejak(perkara="uji")
p = Perkakas(K, jej)

cek("lima alat terdaftar", len(p.daftar) == 5, str(sorted(p.daftar)))
cek(
    "skema alat bisa diberikan ke pemanggilan fungsi",
    all("name" in s and "parameters" in s for s in p.skema()),
)

for nama, arg, sebab in [
    ("ambil_berkas", {}, "argumen wajib hilang"),
    ("ambil_berkas", {"id": "KTIDAKADA"}, "berkas tidak ada"),
    ("ambil_berkas", {"id": ID[0], "lebih": 1}, "argumen tidak dikenal"),
    (
        "cari_tarif",
        {"kode": "X", "kelas_rawat": 9, "kelas_rs": "A", "regional": 1},
        "kelas rawat di luar rentang",
    ),
    (
        "cari_tarif",
        {"kode": "X", "kelas_rawat": 3, "kelas_rs": "Z", "regional": 1},
        "kelas rs tidak dikenal",
    ),
]:
    n = len(jej.catatan)
    try:
        p.panggil(nama, **arg)
        ditolak = False
    except GalatAlat:
        ditolak = True
    cek(f"ditolak: {sebab}", ditolak)
    cek(f"penolakan tercatat: {sebab}", len(jej.catatan) == n + 1)

try:
    p.panggil("hapus_semua", id="x")
    ada = True
except GalatAlat:
    ada = False
cek("alat di luar daftar tidak bisa dipanggil", not ada)

print("\n4. Jejak tidak bisa disunting diam diam")
utuh, sebab = jej.periksa_rantai()
cek("rantai sidik utuh", utuh, sebab)
salinan = Jejak(perkara="uji", catatan=list(jej.catatan))
salinan.catatan[1].argumen = {"id": "KDIUBAH"}
rusak, di_mana = salinan.periksa_rantai()
cek("satu argumen diubah membuat rantainya ketahuan", not rusak, di_mana)

print("\n5. Alat tidak mengubah penilaian")
sebelum = float(K.selisih[K.urutan[0]])
p2 = Perkakas(K, Jejak(perkara="uji2"))
for i in ID[:5]:
    p2.panggil("ambil_berkas", id=i)
    p2.panggil("hitung_pengandaian", id=i)
sesudah = float(K.selisih[K.urutan[0]])
cek("selisih tidak bergeser sesudah alat dipanggil", abs(sebelum - sesudah) < 1e-9)

print("\n6. Skor ulang mengikuti penebak, bukan janji agen")
uji_id = None
for i in ID:
    h = Perkakas(K, Jejak(perkara="cari")).panggil("hitung_pengandaian", id=i)
    menolong = [b for b in h["bukti"] if b["ubah_selisih_rp"] > 0]
    if menolong:
        uji_id, butir = i, menolong[0]
        break

if uji_id is None:
    cek(
        "ada berkas dengan bukti yang menolong", False, "tidak ada di 60 berkas teratas"
    )
else:
    r = Perkakas(K, Jejak(perkara="ulang")).panggil(
        "skor_ulang", id=uji_id, bukti_tambahan=[butir["kode"]]
    )
    cek("mencentang bukti yang menolong menurunkan selisih", r["turun_rp"] > 0, str(r))
    cek(
        "besar penurunannya sama dengan yang dijanjikan pengandaian",
        abs(r["turun_rp"] - butir["ubah_selisih_rp"]) <= 1,
        f"{r['turun_rp']} lawan {butir['ubah_selisih_rp']}",
    )

print("\n7. Target A1 pada berkas perkara berbasis aturan")
n_perkara, n_langgar, contoh = 0, 0, []
# Kosakata menuduh diperiksa di sini, bukan hanya di uji ujung ke ujung.
# Pustaka aturan memuat judul peraturan yang menyebut kecurangan, dan
# pencariannya bisa memunculkannya kalau pertanyaannya bergeser sedikit.
# Yang dijaga bukan kata pada pustakanya, melainkan kata yang benar benar
# keluar ke berkas perkara.
DILARANG = ("curang", "fraud", "kecurangan", "penipuan")
n_menuduh, contoh_kata = 0, []
for i in ID:
    hasil = susun(K, i)
    n_perkara += 1
    if not hasil["a1"]["lulus"]:
        n_langgar += 1
        if len(contoh) < 3:
            contoh.append((i, hasil["a1"]["angka_tak_bersumber"]))
    rendah = hasil["teks"].lower()
    ada = [k for k in DILARANG if k in rendah]
    if ada:
        n_menuduh += 1
        if len(contoh_kata) < 3:
            contoh_kata.append((i, ada))

cek(
    f"tidak ada kosakata menuduh pada {n_perkara} berkas perkara",
    n_menuduh == 0,
    f"{n_menuduh} berkas, contoh {contoh_kata}",
)
cek(
    f"tidak ada angka tak bersumber pada {n_perkara} berkas perkara",
    n_langgar == 0,
    str(contoh),
)

satu = susun(K, ID[0])
cek("berkas perkara memuat angka", satu["a1"]["n_angka_diperiksa"] > 5)
cek("rantai jejaknya utuh", satu["a1"]["rantai_utuh"])
cek(
    "tiap berkas perkara memanggil sekurangnya empat alat",
    satu["ringkas_jejak"]["n_panggilan"] >= 4,
    str(satu["ringkas_jejak"]),
)

print("\n8. Penjaga A1 memang menangkap angka karangan")
palsu = satu["teks"] + "\nPotensi pemulihan tahun ini Rp 4.812.335.117."
putusan = periksa_a1(palsu, satu["jejak"])
cek("angka yang tidak pernah dikembalikan alat ketahuan", not putusan["lulus"])
cek(
    "angka pada teks berformat Indonesia terbaca benar",
    angka_pada("Rp 40.704.807 dan 37,59 kali") == [40704807.0, 37.59],
    str(angka_pada("Rp 40.704.807 dan 37,59 kali")),
)

print(f"\n{lulus} lulus, {gagal} gagal")
if __name__ == "__main__":
    raise SystemExit(1 if gagal else 0)
