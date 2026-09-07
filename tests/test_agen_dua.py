"""Uji lapisan agen tahap dua: penyelia, gerbang tera, Agen Berkas, Agen Sanggah.

Yang diperiksa di sini bukan bahwa agennya menghasilkan kalimat yang enak
dibaca. Yang diperiksa lima janji yang jadi alasan lapisan ini boleh
menyentuh faskes sama sekali:

Penyelia benar benar memutus rantai, pada giliran, biaya, dan pengulangan.
Agen yang mengarang angka tidak pernah lolos, dan yang keluar versi aturan.
Angka yang benar tapi dilekatkan pada nama yang salah tetap tertangkap,
sekalipun penjaga A1 meloloskannya.
Gerbang layak kirim menjaga laju cacat di bawah delta, dan jaminannya diuji
pada tarikan yang tidak dipakai menera.
Agen Sanggah tidak pernah menyebut kode pemeriksaan di luar katalog.

Penutur yang dipakai bukan model sungguhan, melainkan penutur bernaskah yang
membaca hasil alat dari percakapannya sendiri. Itu disengaja: yang diuji
lingkaran, penyelia, dan penjaganya, dan ketiganya harus benar sebelum satu
bobot pun dipasang. Pengukuran dengan model sungguhan ada di
scripts/ukur_agen.py.

Jalankan:
    python tests/test_agen_dua.py
"""

from __future__ import annotations

import json
import os
import random
import re
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

from nalar.agen import (  # noqa: E402
    Anggaran,
    Balasan,
    Gerbang,
    Penutur,
    PenuturTiruan,
    Penyelia,
    Perkakas,
    RantaiDiputus,
    baca_sanggahan,
    periksa_dalam,
    petakan_bukti,
    susun,
    susun_agen,
    tera,
)
from nalar.agen.alat_db import (  # noqa: E402
    PerkakasBasisData,
    SumberBasisData,
)
from nalar.agen.berkas import ANGKA_MINIMAL  # noqa: E402
from nalar.agen.dalam import ikatan_salah, kumpulkan_fakta  # noqa: E402
from nalar.agen.jejak import Jejak  # noqa: E402
from nalar.agen.penutur import (  # noqa: E402
    GalatPenutur,
    _panggilan_tertolak,
)
from nalar.agen.sanggah import petakan_bukti_model  # noqa: E402
from nalar.api.keadaan import Keadaan  # noqa: E402
from nalar.katalog import PEMERIKSAAN  # noqa: E402


def rupiah(n) -> str:
    return "Rp " + f"{int(round(n)):,}".replace(",", ".")


# --------------------------------------------------------------------------
# Penutur bernaskah. Membaca hasil alat dari percakapannya sendiri, jadi
# angkanya benar benar berasal dari alat, bukan dari uji ini.
# --------------------------------------------------------------------------


class PenuturPatuh(Penutur):
    """Menyusun berkas perkara persis seperti yang diminta arahan."""

    nama = "patuh"
    rusak = ""

    def hidup(self) -> bool:
        return True

    def _hasil(self, pesan):
        keluar = {}
        for p in pesan:
            if p.get("role") == "tool":
                keluar[p["name"]] = json.loads(p["content"])
        return keluar

    def balas(self, pesan, alat) -> Balasan:
        h = self._hasil(pesan)
        if "ambil_berkas" not in h:
            nomor = re.search(r"K\d+", pesan[-1]["content"]).group(0)
            return Balasan(
                panggilan=[
                    {"nama": "ambil_berkas", "argumen": {"id": nomor}, "id": "a1"},
                    {
                        "nama": "hitung_pengandaian",
                        "argumen": {"id": nomor},
                        "id": "a2",
                    },
                ],
                token_masuk=900,
                token_keluar=60,
            )
        if "cari_aturan" not in h:
            return Balasan(
                panggilan=[
                    {
                        "nama": "cari_aturan",
                        "argumen": {
                            "pertanyaan": "tarif dinaikkan tanpa bukti",
                            "atas": 2,
                        },
                        "id": "a3",
                    }
                ],
                token_masuk=1400,
                token_keluar=40,
            )
        return Balasan(teks=self.tulis(h), token_masuk=2100, token_keluar=260)

    def tulis(self, h) -> str:
        b, g, a = h["ambil_berkas"], h["hitung_pengandaian"], h["cari_aturan"]
        # Nama isian, bukan angka. Balasan alat memang tidak lagi membawa
        # rupiah, jadi penutur ini menulis persis seperti model sungguhan.
        diajukan, didukung = "{total_diajukan_rp}", "{total_didukung_bukti_rp}"
        if self.rusak == "tukar":
            diajukan, didukung = didukung, diajukan
        if self.rusak == "karang":
            diajukan = "Rp 987.654.321"
        # Balasan alat cuma membawa arahnya, bukan besarannya, jadi penutur
        # ini memilih butir dengan cara yang sama seperti model sungguhan.
        menolong = [
            x for x in g["bukti"] if x["ubah_selisih_rp"] == "menurunkan selisih"
        ]
        if self.rusak == "arah":
            menolong = g["bukti"]
        baris = [
            f"Berkas {b['id']} pada {b['faskes']}, kelompok tarif "
            f"{b['kelompok_tarif']}, lama rawat {b['lama_rawat']} hari.",
            "",
            f"Diajukan {diajukan}, didukung bukti {didukung}, selisih {{selisih_rp}}.",
            "",
            "Bukti yang bila dilampirkan menurunkan selisih:",
        ]
        for x in menolong:
            baris.append(f"  {x['kode']}, {x['ubah_selisih_rp']}")
        if not menolong:
            baris.append("  tidak ada butir tunggal yang menurunkan selisih.")
        baris.append("")
        baris.append("Modus yang paling dekat dengan bentuk selisih ini:")
        for e in a["entri"]:
            baris.append(f"  {e['kode']} {e['judul']}, jangkauan {e['jangkauan']}.")
        return "\n".join(baris)


class PenuturBerputar(Penutur):
    """Memanggil alat yang sama dengan argumen yang sama, terus menerus."""

    nama = "berputar"

    def hidup(self) -> bool:
        return True

    def balas(self, pesan, alat) -> Balasan:
        nomor = re.search(r"K\d+", pesan[1]["content"]).group(0)
        return Balasan(
            panggilan=[{"nama": "ambil_berkas", "argumen": {"id": nomor}, "id": "x"}],
            token_masuk=800,
            token_keluar=30,
        )


class PenuturBoros(Penutur):
    """Menghabiskan anggaran token tanpa pernah selesai."""

    nama = "boros"

    def hidup(self) -> bool:
        return True

    def balas(self, pesan, alat) -> Balasan:
        return Balasan(teks="", token_masuk=200000, token_keluar=200000)


print("\n1. Menyiapkan keadaan")
K = Keadaan(n_peserta=1500, tahun=2, seed=7, n_fktp=90, n_fkrtl=24)
K.bangun(alpha=0.02)
ID = [K.id_klaim(int(i)) for i in K.urutan[:80]]
cek("keadaan siap", K.siap and len(ID) == 80, str(len(ID)))


print("\n2. Penyelia memutus rantai")

hasil = susun_agen(K, ID[0], penutur=PenuturBerputar(), anggaran=Anggaran(ulang=2))
cek(
    "alat yang dipanggil berulang menghentikan agen",
    hasil["sumber"] == "aturan" and "berulang" in hasil["sebab_mundur"],
    hasil["sebab_mundur"],
)

hasil = susun_agen(K, ID[0], penutur=PenuturBoros(), anggaran=Anggaran(rp=500.0))
cek(
    "biaya melewati anggaran menghentikan agen",
    hasil["sumber"] == "aturan" and "biaya" in hasil["sebab_mundur"],
    hasil["sebab_mundur"],
)

naskah = [Balasan(teks="") for _ in range(20)]
hasil = susun_agen(
    K, ID[0], penutur=PenuturTiruan(naskah), anggaran=Anggaran(giliran=3)
)
cek(
    "agen yang tidak menulis apa pun jatuh ke versi aturan",
    hasil["sumber"] == "aturan",
    hasil["sebab_mundur"],
)

hasil = susun_agen(K, ID[0], penutur=Penutur())
cek(
    "tanpa model bahasa yang menyala, keluarannya versi aturan",
    hasil["sumber"] == "aturan" and "tidak ada model" in hasil["sebab_mundur"],
    hasil["sebab_mundur"],
)

p = Penyelia(Perkakas(K, Jejak(perkara="uji")), Anggaran())
jawab = p.panggil_lunak(
    "cari_tarif", kode="TIDAK-ADA", kelas_rawat=1, kelas_rs="A", regional=1
)
cek(
    "penolakan alat dikembalikan sebagai keterangan, bukan galat",
    jawab["berhasil"] is False and "tidak ada" in jawab["tolakan"],
    str(jawab),
)
cek("penolakan alat ikut tercatat di jejak", p.perkakas.jejak.ringkas()["n_galat"] == 1)

try:
    Penyelia(Perkakas(K, Jejak(perkara="uji")), Anggaran(panggilan=0)).panggil(
        "ambil_berkas", id=ID[0]
    )
    putus = False
except RantaiDiputus:
    putus = True
cek("batas pemanggilan alat benar benar mengikat", putus)


print("\n3. Agen Berkas yang patuh")

agen = susun_agen(K, ID[0], penutur=PenuturPatuh(), dalam=True)
cek(
    "berkas susunan agen dipakai ketika lolos saringan",
    agen["sumber"] == "agen",
    agen["sebab_mundur"],
)
cek(
    "seluruh angkanya berasal dari alat",
    agen["dalam"]["lulus"],
    str(agen["dalam"]["cacat"][:2]),
)
cek(
    "agen memanggil sekurangnya tiga alat",
    agen["penyelia"]["panggilan_alat"] >= 3,
    str(agen["penyelia"]),
)
cek(
    "biaya satu berkas di bawah Rp 500",
    agen["penyelia"]["biaya_rp"] < 500,
    str(agen["penyelia"]["biaya_rp"]),
)


print("\n4. Agen yang mengarang tidak pernah lolos")

pk = PenuturPatuh()
pk.rusak = "karang"
hasil = susun_agen(K, ID[0], penutur=pk)
cek(
    "angka karangan membuat berkas jatuh ke versi aturan",
    hasil["sumber"] == "aturan" and any(c["jenis"] == "a1" for c in hasil["cacat"]),
    str(hasil["cacat"][:2]),
)

# Berkas yang dipakai harus punya butir bertanda negatif, kalau tidak
# kerusakannya tidak merusak apa pun dan ujinya lolos tanpa menguji.
pp = Perkakas(K, Jejak(perkara="pilih"))
ID_NEG = next(
    i
    for i in ID
    if any(
        b["ubah_selisih_rp"] < 0
        for b in pp.panggil("hitung_pengandaian", id=i)["bukti"]
    )
)
pa = PenuturPatuh()
pa.rusak = "arah"
hasil = susun_agen(K, ID_NEG, penutur=pa)
cek(
    "butir yang justru menaikkan selisih tertangkap saringan cepat",
    hasil["sumber"] == "aturan" and any(c["jenis"] == "arah" for c in hasil["cacat"]),
    str(hasil["cacat"][:2]),
)


print("\n5. Angka benar pada nama yang salah")

pt = PenuturPatuh()
pt.rusak = "tukar"
tukar = susun_agen(K, ID[0], penutur=pt, dalam=True)
# Dua nilai yang tertukar lolos penjaga A1 seluruhnya, karena keduanya
# memang keluar dari alat. Dulu ia lolos ke keluaran dan baru tertangkap
# pemeriksaan dalam yang cuma jalan saat kalibrasi. Sekarang yang dalam ikut
# jalan tiap berkas, jadi ia tertangkap sebelum keluar.
cek(
    "nilai yang tertukar tidak lagi lolos ke keluaran",
    tukar["sumber"] == "aturan",
    tukar["sebab_mundur"],
)
cek(
    "yang menangkapnya pemeriksaan ikatan, bukan penjaga angka",
    any(c["jenis"] == "ikatan" for c in tukar["cacat"])
    and not any(c["jenis"] == "a1" for c in tukar["cacat"]),
    str(tukar["cacat"][:2]),
)

dasar = susun(K, ID[1])
palsu = dasar["teks"] + "\nDasarnya Permenkes 99 Tahun 2099."
cek(
    "peraturan yang tidak pernah diambil alat tertangkap",
    any(
        c["jenis"] == "kutipan"
        for c in periksa_dalam(palsu, dasar["jejak"], dasar["fakta"], dasar["hasil"])[
            "cacat"
        ]
    ),
)

f = kumpulkan_fakta([{"selisih_rp": 1_000_000, "total_diajukan_rp": 9_000_000}])
cek(
    "nama yang diikuti angka milik nama lain tertangkap",
    len(ikatan_salah("Selisih Rp 9.000.000 pada berkas ini.", f)) == 1,
)
cek(
    "nama yang diikuti angkanya sendiri tidak dituduh",
    ikatan_salah("Selisih Rp 1.000.000 pada berkas ini.", f) == [],
)


# Pemeriksa yang menuduh berkas benar lebih berbahaya daripada pemeriksa
# yang meloloskan berkas cacat, karena yang salah menuduh berhenti dibaca.
# Keempat kalimat di bawah diambil dari berkas susunan model sungguhan, dan
# dua di antaranya sempat dituduh cacat padahal benar.
FAKTA_UJI = {
    "nilai": {"total_diajukan_rp": {20107500.0}, "selisih_rp": {6371692.0}},
    "daftar": {},
}

cek(
    "titik dua di depan besarannya tetap terbaca",
    ikatan_salah("Diajukan: Rp 20.107.500.", FAKTA_UJI) == [],
)
cek(
    "titik dua yang membuka daftar tidak dibaca sebagai besaran",
    ikatan_salah("Bukti yang menurunkan selisih: HB Rp 489.690.", FAKTA_UJI) == [],
)
cek(
    "angka di dalam kode bukan besaran",
    ikatan_salah("Modus terdekat dengan selisih ini: M02.", FAKTA_UJI) == [],
)
cek(
    "besaran yang memang salah tetap tertangkap",
    [c["jenis"] for c in ikatan_salah("Diajukan: Rp 999.000.", FAKTA_UJI)]
    == ["ikatan"],
)


print("\n6. Berkas perkara versi aturan tetap bersih")

kotor = 0
for i in ID[:40]:
    d = susun(K, i)
    h = periksa_dalam(d["teks"], d["jejak"], d["fakta"], d["hasil"])
    if not h["lulus"]:
        kotor += 1
        if kotor == 1:
            print(f"         contoh cacat: {h['cacat'][:2]}")
cek("garis dasar lolos pemeriksaan dalam pada 40 berkas", kotor == 0, f"{kotor} kotor")


print("\n7. Gerbang layak kirim yang ditera")

acak = random.Random(11)
skor = [round(acak.random(), 4) for _ in range(400)]
# Cacat dibuat lebih sering pada keyakinan rendah, seperti yang diandaikan
# gerbangnya. Kalau kaitannya tidak ada, gerbang yang benar akan menutup
# hampir seluruhnya, dan itu ikut diuji di bawah.
cacat = [acak.random() > (0.15 + 0.85 * s) for s in skor]
t = tera(skor, cacat, delta=0.05)
cek(
    "laju cacat terkirim di bawah delta pada himpunan tera",
    t["risiko"] <= 0.05,
    str(t["risiko"]),
)
cek("gerbangnya tidak menutup semuanya", t["terkirim"] > 0.1, str(t["terkirim"]))
cek(
    "batasnya lebih ketat daripada delta dikali n, karena memakai keyakinan",
    t["batas_cacat"] < 0.05 * t["n"],
    f"{t['batas_cacat']} vs {0.05 * t['n']}",
)

longgar = tera(skor, cacat, delta=0.20)
cek(
    "delta yang lebih longgar mengirim lebih banyak",
    longgar["terkirim"] >= t["terkirim"] and longgar["ambang"] <= t["ambang"],
    f"{longgar['terkirim']} vs {t['terkirim']}",
)

kosong = tera([], [], delta=0.05)
cek("tanpa himpunan tera, gerbangnya menutup", kosong["ambang"] == 1.0)

# Kalau seluruh berkas kalibrasi cacat, yang boleh lolos hanya sisa jatah
# yang dijanjikan delta, bukan nol. Menuntut nol berarti menuntut jaminan
# yang lebih keras daripada yang tertulis, dan yang tertulis itu yang
# dipertanggungjawabkan.
buruk = tera(skor, [True] * len(skor), delta=0.05)
cek(
    "kalau semuanya cacat, yang lolos tidak melewati jatah delta",
    buruk["risiko"] <= 0.05 and buruk["terkirim"] <= 0.05,
    str(buruk["terkirim"]),
)


# Jaminannya diuji pada tarikan yang tidak dipakai menera. Ini yang
# membedakan kalibrasi konformal dari ambang yang dicocokkan ke data: yang
# dijanjikan berlaku pada berkas yang belum pernah dilihat.
#
# Yang dihitung dua hal berbeda, dan bedanya penting. Berapa banyak putaran
# yang laju cacatnya di bawah delta, dan berapa rata ratanya. Kalibrasi yang
# hanya menjanjikan rata rata akan lolos ukuran kedua sambil jatuh di ukuran
# pertama sekitar separuh waktu, dan itu persis yang tidak kami mau.
#
# Risikonya dihitung tertutup, bukan diukur pada contoh uji. Keyakinan yang
# dijanjikan berlaku atas laju sebenarnya, dan laju yang diukur pada tiga
# ratus contoh punya deraunya sendiri sekitar 0,017. Mengukur lewat contoh
# uji berarti menguji jaminan ditambah derau, lalu menyalahkan jaminannya.
# Pada sebaran buatan ini laju sebenarnya di atas ambang lam bisa
# diintegralkan langsung: 0,425 dikali kuadrat satu dikurang lam.
def risiko_sebenarnya(lam: float) -> float:
    return 0.425 * (1 - min(1.0, max(0.0, lam))) ** 2


lewat, laju = 0, []
for putaran in range(200):
    r = random.Random(1000 + putaran)
    s_kal = [r.random() for _ in range(300)]
    c_kal = [r.random() > (0.15 + 0.85 * x) for x in s_kal]
    amb = tera(s_kal, c_kal, delta=0.10)["ambang"]
    risiko = risiko_sebenarnya(amb)
    laju.append(risiko)
    if risiko <= 0.10:
        lewat += 1
cek(
    "laju sebenarnya di bawah delta pada sekurangnya 190 dari 200 tera",
    lewat >= 190,
    f"{lewat}/200",
)
cek(
    "gerbangnya tidak menutup berlebihan, laju rata ratanya mendekati delta",
    0.03 <= sum(laju) / len(laju) <= 0.10,
    f"{sum(laju) / len(laju):.4f}",
)
print(f"         {lewat}/200 tera di bawah delta, laju rata rata {sum(laju) / 200:.4f}")

g = Gerbang(ambang=t["ambang"], delta=0.05, n_kalibrasi=t["n"])
cek(
    "gerbang menahan berkas berkeyakinan rendah",
    g.putuskan(0.0) == "perlu_dibaca_manusia" and g.putuskan(1.0) == "layak_kirim",
)


print("\n8. Agen Sanggah")

surat = (
    "Dengan hormat, bersama ini kami lampirkan hasil pemeriksaan hemoglobin "
    "dan trombosit atas nama pasien tersebut. Mohon berkas ditinjau ulang."
)
peta = petakan_bukti(surat)
kode = {b["kode"] for b in peta}
cek("surat biasa terbaca jadi kode pemeriksaan", {"HB", "TROMB"} <= kode, str(kode))
cek("tiap pemetaan menyertakan alasannya", all(b["alasan"] for b in peta))

cek(
    "kode yang sudah ada pada berkas tidak dipetakan ulang",
    "HB" not in {b["kode"] for b in petakan_bukti(surat, {"HB"})},
)

cek(
    "surat yang tidak menyebut pemeriksaan apa pun tidak memaksakan kode",
    petakan_bukti("Kami keberatan atas hasil verifikasi ini.") == [],
)

# Sanggahan yang isinya acak tidak boleh melahirkan kode di luar katalog.
kata = [
    "pasien",
    "rawat",
    "dokter",
    "berkas",
    "hemoglobin",
    "operasi",
    "tagihan",
    "kreatinin",
    "keberatan",
    "lampiran",
    "rontgen",
    "trombosit",
    "biaya",
]
liar = 0
for putaran in range(300):
    r = random.Random(putaran)
    isi = " ".join(r.choice(kata) for _ in range(30))
    for b in petakan_bukti(isi):
        if b["kode"] not in PEMERIKSAAN:
            liar += 1
cek("tidak pernah menyebut kode di luar katalog, 300 surat acak", liar == 0, str(liar))

s = baca_sanggahan(K, ID[0], surat)
if s["hasil"]:
    h = s["hasil"]
    cek(
        "selisih baru dihitung penebak, bukan dijanjikan agen",
        h["selisih_semula_rp"] - h["selisih_sesudah_rp"] == h["turun_rp"],
        str(h),
    )
else:
    cek("sanggahan dijawab meski tidak mengubah apa pun", bool(s["keterangan"]))

kosong = baca_sanggahan(K, ID[0], "Kami keberatan.")
cek(
    "surat yang tidak dikenali tetap dijawab apa adanya",
    kosong["hasil"] is None and "tidak" in kosong["keterangan"].lower(),
    kosong["keterangan"][:60],
)


# Jalur model bahasanya diuji dengan penutur bernaskah, jadi yang diuji
# penjaganya bukan modelnya. Penjaga di sini satu kalimat: kode boleh masuk
# kalau potongan kalimat yang disebut model benar benar ada di surat.


def _catat(butir):
    return Balasan(
        panggilan=[
            {"nama": "catat_pemeriksaan", "argumen": {"pemeriksaan": butir}, "id": "s1"}
        ],
        token_masuk=700,
        token_keluar=40,
    )


surat_lab = (
    "Bersama ini kami lampirkan hasil pemeriksaan hemoglobin pasien "
    "dengan nilai 8,2 g/dL."
)

peta, buang = petakan_bukti_model(
    surat_lab,
    PenuturTiruan(
        [_catat([{"kode": "HB", "kutipan": "hasil pemeriksaan hemoglobin"}])]
    ),
)
cek(
    "kutipan yang ada di surat diterima",
    [b["kode"] for b in peta] == ["HB"] and not buang,
    str(peta),
)
cek("alasannya memuat kutipannya", "hemoglobin" in peta[0]["alasan"])

peta, buang = petakan_bukti_model(
    surat_lab,
    PenuturTiruan([_catat([{"kode": "KREA", "kutipan": "hasil kreatinin terlampir"}])]),
)
cek(
    "kutipan yang tidak ada di surat membuang kodenya",
    peta == [] and buang and buang[0]["kode"] == "KREA",
    str(buang),
)

peta, buang = petakan_bukti_model(
    surat_lab,
    PenuturTiruan([_catat([{"kode": "XYZ", "kutipan": "hemoglobin"}])]),
)
cek(
    "kode di luar katalog dibuang",
    peta == [] and buang and buang[0]["sebab"] == "kode di luar katalog",
    str(buang),
)

peta, _ = petakan_bukti_model(
    surat_lab,
    PenuturTiruan([_catat([{"kode": "HB", "kutipan": "hemoglobin"}])]),
    {"HB"},
)
cek("kode yang sudah ada pada berkas tidak dipetakan ulang model", peta == [])


class PenuturBisu(Penutur):
    """Model yang menyala tapi tidak pernah menjawab."""

    nama = "bisu"

    def hidup(self) -> bool:
        return True

    def balas(self, pesan, alat) -> Balasan:
        raise GalatPenutur("peladen model tidak menjawab")


s_bisu = baca_sanggahan(K, ID[0], surat, penutur=PenuturBisu())
cek(
    "model yang tidak menjawab jatuh ke pencocokan kata",
    s_bisu["cara"] == "kata"
    and s_bisu["dipetakan"] == petakan_bukti(surat, set(s_bisu["sudah_ada"])),
    str(s_bisu["cara"]),
)


print("\n9. A1 pada seluruh jalur tahap dua")

n_agen, n_lolos, biaya = 0, 0, []
for i in ID[:40]:
    h = susun_agen(K, i, penutur=PenuturPatuh(), dalam=True)
    if h["sumber"] == "agen":
        n_agen += 1
        biaya.append(h["penyelia"]["biaya_rp"])
        if h["dalam"]["lulus"]:
            n_lolos += 1
cek("agen menyusun sendiri sebagian besar berkas", n_agen >= 35, str(n_agen))
cek(
    "nol pelanggaran pada seluruh berkas susunan agen",
    n_lolos == n_agen,
    f"{n_lolos}/{n_agen}",
)
rata = sum(biaya) / max(1, len(biaya))
cek("biaya rata rata per berkas di bawah Rp 500", rata < 500, f"Rp {rata:.2f}")
print(f"         biaya rata rata Rp {rata:.2f} per berkas")


print("\n9. Nama alat yang ditolak penyedia kembali jadi giliran biasa")
# Isi penolakan di bawah disusun dari bagian bagian penolakan yang benar
# benar diterima dari Groq pada 7 September 2026, bukan bentuk karangan.
# Modelnya memanggil hitungan_pengandaian, dan nama itu tidak ada.
#
# Yang dijaga satu hal: satu huruf yang salah pada nama alat tidak boleh
# membatalkan seluruh berkas. Penyelia sudah tahu cara menolak alat yang
# tidak ada, jadi penolakan penyedia diterjemahkan balik supaya sampai ke
# sana, dan model membetulkan namanya sendiri pada giliran berikutnya.
TERTOLAK = json.dumps(
    {
        "error": {
            "message": (
                "Tool call validation failed: attempted to call tool "
                "'hitungan_pengandaian' which was not in request.tools"
            ),
            "type": "invalid_request_error",
            "code": "tool_use_failed",
            "failed_generation": (
                '{"name": "hitungan_pengandaian", "arguments": {"id": "K00000000"}}'
            ),
        }
    }
)
POTONG = json.dumps(
    {"error": {"code": "tool_use_failed", "failed_generation": '{"name": '}}
)

d = _panggilan_tertolak(TERTOLAK)
cek(
    "nama alat yang salah terbaca dari penolakan",
    d == [{"nama": "hitungan_pengandaian", "argumen": {"id": "K00000000"}}],
    str(d),
)
cek(
    "penolakan karena sebab lain tidak ikut diterjemahkan",
    _panggilan_tertolak(json.dumps({"error": {"code": "rate_limit_exceeded"}})) is None,
)
cek(
    "badan yang bukan JSON tidak menjatuhkan penerjemahnya",
    _panggilan_tertolak("Bad Request") is None,
)
cek(
    "naskah yang terpotong tidak jadi panggilan setengah jadi",
    _panggilan_tertolak(POTONG) is None,
)

# Terjemahan di atas baru ada gunanya kalau ujungnya memang menolak dengan
# keterangan. Itu yang diperiksa di sini, pada penyelia yang sungguhan.
pn = Penyelia(Perkakas(K, Jejak(perkara="uji-tertolak")), Anggaran())
jawab = pn.panggil_lunak("hitungan_pengandaian", id=ID[0])
cek(
    "penyelia menolak alat yang tidak ada, dengan keterangan",
    not jawab["berhasil"] and bool(jawab["tolakan"]),
    str(jawab)[:90],
)


print("\n10. Berkas perkara yang tidak menyebut angka ditolak")


class PenuturKosong(Penutur):
    """Memanggil satu alat, lalu menulis kalimat tanpa satu angka pun.

    Bukan naskah karangan. Ini persis yang terjadi pada berkas K00001283 di
    situs yang sudah terpasang: modelnya gagal memanggil alat yang
    menghitung, lalu menulis bahwa tiap besaran tidak tersedia. Berkas itu
    lolos A1, lolos pemeriksaan dalam, dan terkirim.
    """

    nama = "kosong"

    def hidup(self) -> bool:
        return True

    def balas(self, pesan, alat) -> Balasan:
        sudah = any(p.get("role") == "tool" for p in pesan)
        if not sudah:
            nomor = re.search(r"K\d+", pesan[-1]["content"]).group(0)
            return Balasan(
                panggilan=[
                    {"nama": "ambil_berkas", "argumen": {"id": nomor}, "id": "k1"}
                ],
                token_masuk=900,
                token_keluar=40,
            )
        return Balasan(
            teks=(
                "Nilai yang diajukan tidak tersedia, nilai yang didukung bukti "
                "tidak tersedia, selisih tidak tersedia. Bukti yang bila "
                "dilampirkan menurunkan selisih tidak tersedia. Modus yang "
                "paling dekat dengan bentuk selisih ini tidak tersedia."
            ),
            token_masuk=1200,
            token_keluar=60,
        )


kosong = susun_agen(K, ID[0], penutur=PenuturKosong(), n_perbaikan=0)
cek(
    "berkas tanpa angka mundur ke versi aturan",
    kosong["sumber"] == "aturan",
    kosong["sumber"],
)
cek(
    "sebabnya menyebut angka, bukan saringan",
    "angka" in kosong["sebab_mundur"],
    kosong["sebab_mundur"],
)
cek(
    "yang keluar tetap berkas perkara yang menyebut besaran",
    kosong["a1"]["n_angka_diperiksa"] >= ANGKA_MINIMAL,
    str(kosong["a1"]["n_angka_diperiksa"]),
)

# Yang dijaga bukan cuma penolakannya. Berkas yang memang menyebut angka
# harus tetap lewat, kalau tidak aturan baru ini menolak semuanya dan tidak
# ada yang tahu.
utuh = susun_agen(K, ID[0], penutur=PenuturPatuh())
cek(
    "berkas yang menyebut angka tetap lewat",
    utuh["sumber"] == "agen",
    utuh.get("sebab_mundur", ""),
)

# Alat yang tidak bisa dilayani jalur basis data tidak ditawarkan ke model.
# Menawarkannya membuat model memanggilnya, dan giliran yang habis untuk satu
# penolakan itu yang membuat berkas kosong di atas terjadi.
pd = PerkakasBasisData(
    SumberBasisData("http://tidak-dipakai", "x"), Jejak(perkara="uji")
)
nama_alat = [a["name"] for a in pd.skema()]
cek(
    "skor_ulang tidak ditawarkan ke model",
    "skor_ulang" not in nama_alat,
    str(nama_alat),
)
cek("alat yang menghitung tetap ditawarkan", "hitung_pengandaian" in nama_alat)
# Tidak ditawarkan bukan berarti hilang. Yang memanggilnya langsung tetap
# mendapat keterangan kenapa, bukan pesan "alat tidak dikenal" yang tidak
# memberitahu apa apa.
try:
    pd.panggil("skor_ulang", id=ID[0], bukti_tambahan=["HB"])
    cek("skor_ulang tetap menerangkan sebabnya", False, "justru menjawab")
except Exception as e:  # noqa: BLE001
    cek("skor_ulang tetap menerangkan sebabnya", "penebak tarif" in str(e), str(e)[:70])

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
