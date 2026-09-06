"""Uji lapisan lawan: bahasa siasat, juru bacanya, dan gelanggangnya.

Yang diuji bukan bahwa serangannya berhasil. Yang diuji enam janji yang
membuat angka T6 boleh dipercaya sama sekali:

Siasat di luar perbendaharaan ditolak, dan model bahasa tidak pernah
menjalankan kode.
Berkas aslinya tidak pernah berubah, berapa kali pun siasat dijalankan.
Gerakan yang menyentuh titik buta memang mengecilkan selisih, bukan
membesarkannya, karena itu inti kenapa titik butanya ada.
Cara memilih benar benar berbeda satu sama lain.
Siasat yang akibatnya sama tidak dihitung dua kali.
Siasat yang menang di satu himpunan saja tidak dihitung sebagai temuan.

Jalankan:
    python tests/test_lawan.py
"""

from __future__ import annotations

import copy
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

from nalar.agen import arena, lawan  # noqa: E402
from nalar.agen.siasat import (  # noqa: E402
    GERAKAN,
    GalatSiasat,
    perbendaharaan,
    periksa,
    pilih,
    varian,
)
from nalar.api.keadaan import Keadaan  # noqa: E402

print("\n1. Menyiapkan keadaan")
K = Keadaan(n_peserta=1500, tahun=2, seed=7, n_fktp=90, n_fkrtl=24)
K.bangun(alpha=0.02)
EPS = K.episodes
INAP = [i for i, r in enumerate(EPS) if r["rawat_inap"]]
cek("ada berkas rawat inap untuk diserang", len(INAP) >= 40, str(len(INAP)))


def penskor(daftar):
    return K.detektor.skor(daftar)["selisih"]


print("\n2. Siasat di luar perbendaharaan ditolak")

tolak = [
    ({"gerakan": [{"jenis": "tambah_diagnosis"}]}, "tanpa nama"),
    ({"nama": "x"}, "tanpa gerakan"),
    ({"nama": "x", "gerakan": []}, "gerakan kosong"),
    ({"nama": "x", "gerakan": [{"jenis": "bakar_berkas"}]}, "gerakan karangan"),
    (
        {
            "nama": "x",
            "gerakan": [{"jenis": "tambah_diagnosis"}],
            "sasaran": {"jenis": "semua"},
        },
        "sasaran karangan",
    ),
    (
        {
            "nama": "x",
            "gerakan": [{"jenis": "tambah_diagnosis"}],
            "pilihan": {"jenis": "curang"},
        },
        "cara memilih karangan",
    ),
    (
        {"nama": "x", "gerakan": [{"jenis": "naikkan_kelas"}] * 4},
        "terlalu banyak gerakan",
    ),
]
n_tolak = 0
for s, sebab in tolak:
    try:
        periksa(s)
    except GalatSiasat:
        n_tolak += 1
    else:
        print(f"         lolos padahal seharusnya ditolak: {sebab}")
cek("seluruh siasat cacat ditolak", n_tolak == len(tolak), f"{n_tolak}/{len(tolak)}")

cek(
    "perbendaharaan tidak memuat satu pun angka dari berkas",
    "berkas" not in str(perbendaharaan()).lower() or "Rp" not in str(perbendaharaan()),
)

print("\n3. Berkas aslinya tidak pernah berubah")

r = EPS[INAP[0]]
sebelum = copy.deepcopy(r)
for _ in range(3):
    varian(r, [{"jenis": "tambah_diagnosis"}, {"jenis": "perpanjang_rawat"}])
cek(
    "menjalankan siasat tidak menyentuh berkas aslinya",
    r["dxs"] == sebelum["dxs"]
    and r["los"] == sebelum["los"]
    and r["tarif"] == sebelum["tarif"],
)

print("\n4. Gerakan bekerja seperti yang dijanjikan uraiannya")

naik = 0
for i in INAP[:60]:
    vs = varian(EPS[i], [{"jenis": "tambah_diagnosis"}])
    if max(v["tarif"] for v in vs) > EPS[i]["tarif"]:
        naik += 1
cek("menambah diagnosis sekunder menaikkan tarif", naik >= 5, f"{naik}/60")

# Titik buta. Melampirkan pemeriksaan penunjang tidak menaikkan tarif yang
# ditagihkan sama sekali, tapi menaikkan tarif yang dianggap wajar, sehingga
# selisihnya mengecil. Ini yang membuat bukti bisa dipakai menutupi, dan
# itulah alasan modus M12, M13, dan M20 ditandai belum tersentuh.
turun = 0
for i in INAP[:40]:
    v = varian(EPS[i], [{"jenis": "lampirkan_lab", "n": 4}])[0]
    if float(penskor([v])[0]) < float(penskor([EPS[i]])[0]):
        turun += 1
cek(
    "melampirkan bukti mengecilkan selisih, bukan membesarkannya",
    turun >= 5,
    f"{turun}/40",
)
sama = all(
    varian(EPS[i], [{"jenis": "lampirkan_lab", "n": 2}])[0]["tarif"] == EPS[i]["tarif"]
    for i in INAP[:20]
)
cek("melampirkan bukti tidak menaikkan tarif yang ditagihkan", sama)

n_var = len(varian(EPS[INAP[0]], [{"jenis": "tambah_diagnosis"}]))
cek(
    "parameter yang tidak disebut dicoba seluruh rentangnya",
    n_var > 1,
    f"{n_var} varian",
)
n_kunci = len(varian(EPS[INAP[0]], [{"jenis": "tambah_diagnosis", "n": 1, "mulai": 0}]))
cek("parameter yang disebut mengunci pilihannya", n_kunci == 1, f"{n_kunci} varian")

print("\n5. Cara memilih benar benar berbeda")

untung = np.array([1_000_000.0, 5_000_000.0, 2_000_000.0])
skor = np.array([100_000.0, 900_000.0, 300_000.0])
ambang = 400_000.0
cek(
    "paling untung mengambil yang terbesar walau melewati ambang",
    pilih({"jenis": "paling_untung"}, untung, skor, 0.0, ambang) == 1,
)
cek(
    "hati hati menolak yang melewati ambang",
    pilih({"jenis": "aman_di_bawah_ambang"}, untung, skor, 0.0, ambang) == 2,
)
cek(
    "menyebar mengambil kenaikan skor terkecil",
    pilih({"jenis": "kenaikan_skor_terkecil"}, untung, skor, 0.0, ambang) == 0,
)
cek(
    "porsi ambang berhenti jauh sebelum garis",
    pilih(
        {"jenis": "untung_di_bawah_porsi_ambang", "porsi": 0.5},
        untung,
        skor,
        0.0,
        ambang,
    )
    == 0,
)
cek(
    "untung dibatasi menolak yang melewati batasnya",
    pilih(
        {"jenis": "untung_dibatasi", "batas_rp": 2_500_000}, untung, skor, 0.0, ambang
    )
    == 2,
)
cek(
    "tidak ada yang diambil kalau semuanya melewati ambang",
    pilih(
        {"jenis": "aman_di_bawah_ambang"},
        np.array([1.0]),
        np.array([9e9]),
        0.0,
        ambang,
    )
    is None,
)

print("\n6. Gelanggang dan garis dasarnya")

amb = np.asarray(K.ambang, dtype=float)
tahan = np.asarray(K.tahan)
temu = INAP[: len(INAP) // 2]
sahih = INAP[len(INAP) // 2 :]
g = lawan.Gelanggang(EPS, temu, sahih, penskor, amb, tahan, maks_klaim=80)

cek("garis dasar memuat ketiga pelaku baku", len(g.dasar_temu["baris"]) == 3)
cek(
    "tiap pelaku baku melaporkan uang yang lolos",
    all("lolos_rp" in b for b in g.dasar_temu["baris"]),
)
cek(
    "uang yang lolos tidak pernah melebihi yang diambil",
    all(b.get("lolos_rp", 0) <= b.get("diambil_rp", 0) for b in g.dasar_temu["baris"]),
)

s1 = {
    "nama": "coba",
    "sasaran": {"jenis": "semua_rawat_inap"},
    "gerakan": [{"jenis": "tambah_diagnosis"}],
    "pilihan": {"jenis": "aman_di_bawah_ambang"},
}
h1 = g.coba(s1)
h2 = g.coba(dict(s1, nama="coba lagi"), catat=False)
cek(
    "menjalankan siasat yang sama dua kali memberi hasil yang sama",
    h1.get("lolos_rp") == h2.get("lolos_rp")
    and h1.get("n_diserang") == h2.get("n_diserang"),
    f"{h1.get('lolos_rp')} lawan {h2.get('lolos_rp')}",
)

kosong = g.coba(
    {
        "nama": "sasaran kosong",
        "sasaran": {"jenis": "selisih_awal_kecil", "batas_rp": -1},
        "gerakan": [{"jenis": "tambah_diagnosis"}],
    },
    catat=False,
)
cek(
    "sasaran yang tidak cocok dengan satu berkas pun dijawab apa adanya",
    kosong.get("n_sasaran") == 0,
    str(kosong)[:80],
)

print("\n7. Yang dihitung sebagai temuan")

menang = {"menang_jumlah": True, "menang_maks": False, "porsi_tertangkap": 0.5}
kalah = {"menang_jumlah": False, "menang_maks": True, "porsi_tertangkap": 0.5}
cek("menang jumlah di dua himpunan dihitung", lawan.bertahan(menang, menang))
cek("menang di satu himpunan saja tidak dihitung", not lawan.bertahan(menang, kalah))
cek(
    "menang pada ukuran yang berbeda di tiap himpunan tidak dihitung",
    not lawan.bertahan(menang, dict(kalah, menang_maks=True)),
)

teduh = {"porsi_tertangkap": 0, "lolos_rp": 1_000_000}
cek(
    "siasat yang tidak pernah tertangkap dikenali terpisah",
    lawan.tak_pernah_tertangkap(teduh, teduh) and not lawan.bertahan(teduh, teduh),
)

kembar = [
    {
        "siasat": {"nama": "a"},
        "temu": {"n_diserang": 5, "lolos_rp": 10, "maks_lolos_rp": 3},
        "sahih": {"lolos_rp": 8, "maks_lolos_rp": 2},
    },
    {
        "siasat": {"nama": "b"},
        "temu": {"n_diserang": 5, "lolos_rp": 10, "maks_lolos_rp": 3},
        "sahih": {"lolos_rp": 8, "maks_lolos_rp": 2},
    },
    {
        "siasat": {"nama": "c"},
        "temu": {"n_diserang": 6, "lolos_rp": 12, "maks_lolos_rp": 3},
        "sahih": {"lolos_rp": 9, "maks_lolos_rp": 2},
    },
]
cek(
    "siasat yang akibatnya sama persis tidak dihitung dua kali",
    len(lawan.sisakan_yang_berbeda(kembar)) == 2,
    str(len(lawan.sisakan_yang_berbeda(kembar))),
)

print("\n8. Apa yang boleh dilihat pelaku")

# Tingkat pengetahuan pelaku ini yang paling menentukan angka T6, jadi
# mekanismenya diuji sendiri. Yang tidak bisa diuji di sini besarnya
# pengaruh: pada keadaan sekecil ini hampir seluruh kelompok menahan diri
# dan tidak ada yang pernah tertangkap, jadi bertanya tidak ada gunanya.
# Angkanya diukur tangan lewat scripts/pengetahuan_pelaku.py.
for tahu in arena.PENGETAHUAN:
    h = arena.jalankan(
        EPS, temu, penskor, amb, tahan, s1, maks_klaim=40, pengetahuan=tahu
    )
    cek(
        f"tingkat pengetahuan {tahu} dilaporkan apa adanya",
        h.get("pengetahuan") == tahu,
    )

try:
    arena.jalankan(EPS, temu, penskor, amb, tahan, s1, pengetahuan="mahatahu")
    ditolak = False
except ValueError:
    ditolak = True
cek("tingkat pengetahuan yang tidak dikenal ditolak", ditolak)

# Pelaku buta tidak bisa memakai cara memilih yang butuh skor, jadi siasat
# apa pun jatuh ke mengambil yang paling menguntungkan.
buta_hati = arena.jalankan(
    EPS, temu, penskor, amb, tahan, s1, maks_klaim=40, pengetahuan="buta"
)
buta_serakah = arena.jalankan(
    EPS, temu, penskor, amb, tahan, arena.BAKU[0], maks_klaim=40, pengetahuan="buta"
)
cek(
    "tanpa skor, cara memilih tidak lagi membedakan apa pun",
    buta_hati.get("lolos_rp") == buta_serakah.get("lolos_rp"),
    f"{buta_hati.get('lolos_rp')} lawan {buta_serakah.get('lolos_rp')}",
)

# Tanpa satu pun berkas untuk diamati, batas yang disimpulkan nol, jadi
# tidak ada yang bisa diambil sama sekali.
tanpa_amat = arena.jalankan(
    EPS,
    temu,
    penskor,
    amb,
    tahan,
    s1,
    maks_klaim=40,
    pengetahuan="belajar",
    n_belajar=0,
)
cek(
    "pelaku yang tidak sempat mengamati tidak mengambil apa apa",
    tanpa_amat.get("n_diserang", 0) == 0,
    str(tanpa_amat.get("n_diserang")),
)

cek(
    "siasat yang ditemukan lapisan lawan ikut disimpan jadi kasus uji",
    len(arena.DITEMUKAN) >= 3 and arena.SELURUH == arena.BAKU + arena.DITEMUKAN,
)


print("\n9. Pencarian menyeluruh tanpa model bahasa")

cari = lawan.cari_menyeluruh(g, batas=12)
cek("pencarian mengembalikan hasil", len(cari) >= 8, str(len(cari)))
cek(
    "hasilnya terurut dari yang paling banyak meloloskan uang",
    all(
        cari[i]["temu"].get("lolos_rp", 0) >= cari[i + 1]["temu"].get("lolos_rp", 0)
        for i in range(len(cari) - 1)
    ),
)
cek(
    "tidak satu pun hasil pencarian sama dengan pelaku baku",
    all(
        lawan.tanda_tangan(b["siasat"])
        not in {lawan.tanda_tangan(x) for x in arena.BAKU}
        for b in cari
    ),
)
cek(
    "seluruh gerakan pada perbendaharaan bisa dijalankan",
    all(varian(EPS[INAP[0]], [{"jenis": j}]) for j in GERAKAN),
)

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
