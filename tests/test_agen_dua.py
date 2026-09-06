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
from nalar.agen.dalam import ikatan_salah, kumpulkan_fakta  # noqa: E402
from nalar.agen.jejak import Jejak  # noqa: E402
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
        diajukan, didukung = g["total_diajukan_rp"], g["total_didukung_bukti_rp"]
        if self.rusak == "tukar":
            diajukan, didukung = didukung, diajukan
        if self.rusak == "karang":
            diajukan = diajukan + 777
        menolong = [x for x in g["bukti"] if x["ubah_selisih_rp"] > 0]
        if self.rusak == "arah":
            menolong = g["bukti"]
        baris = [
            f"Berkas {b['id']} pada {b['faskes']}, kelompok tarif "
            f"{b['kelompok_tarif']}, lama rawat {b['lama_rawat']} hari.",
            "",
            f"Diajukan {rupiah(diajukan)}, didukung bukti {rupiah(didukung)}, "
            f"selisih {rupiah(g['selisih_rp'])}.",
            "",
            "Bukti yang bila dilampirkan menurunkan selisih:",
        ]
        for x in menolong:
            baris.append(f"  {x['kode']}, turun {rupiah(abs(x['ubah_selisih_rp']))}")
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
cek(
    "nilai diajukan dan didukung bukti yang tertukar lolos penjaga A1",
    tukar["sumber"] == "agen",
    tukar["sebab_mundur"],
)
cek(
    "tapi tertangkap pemeriksaan dalam",
    any(c["jenis"] == "ikatan" for c in tukar["dalam"]["cacat"]),
    str(tukar["dalam"]["cacat"][:2]),
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

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
