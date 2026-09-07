"""Pemeriksaan dalam: angka yang benar, tapi dilekatkan pada nama yang salah.

Penjaga A1 memeriksa tiap angka berasal dari alat. Itu perlu, dan itu tidak
cukup. Kalimat "diajukan Rp 14 juta, didukung bukti Rp 19 juta" bisa lolos A1
seluruhnya, karena kedua angkanya memang keluar dari alat, hanya tertukar
tempatnya. Faskes yang membaca kalimat itu akan menyimpulkan bahwa NALAR
menuduhnya menagih kurang.

Cacat seperti itu pernah benar benar lolos ke antarmuka. Daftar bukti
pengandaian mengambil nilai mutlak selisihnya lalu menandai semua butir
sebagai pengurang, padahal pada satu berkas nyata empat dari lima butir
justru menaikkan. Angkanya sah, arahnya terbalik, dan tidak ada penjaga
angka yang bisa menangkapnya.

Keduanya dijalankan pada tiap berkas, sebelum apa pun dikirim.

Versi pertama tidak begitu. Yang dalam disebut terlalu mahal untuk tiap
berkas dan disimpan untuk himpunan kalibrasi saja, dan gerbang layak kirim
dibangun di atas alasan itu. Alasannya tidak pernah diukur.

Sesudah diukur: pemeriksaan cepat 0,44 milidetik per berkas, pemeriksaan
dalam 1,05 milidetik. Menyusun satu berkas perkara memakan 264 milidetik,
dan satu giliran model bahasa sekitar delapan ribu. Jadi yang dalam berharga
empat persepuluh persen dari menyusunnya, dan seperdelapan ribu dari satu
giliran model.

Menyebut sesuatu mahal tanpa menimbangnya adalah cara paling nyaman
membiarkan cacat lewat, dan cacat yang lewat karenanya bukan cacat kecil:
sebelas dari empat belas berkas susunan agen melekatkan angka yang sah pada
nama yang salah. Sekarang keduanya jalan bersama, dan berkas yang jatuh di
salah satunya diganti versi aturan.

Gerbang layak kirim tetap ada, dan alasannya berubah jadi yang sebenarnya.
Bukan karena pemeriksaannya mahal, melainkan karena ada cacat yang tidak
bisa diperiksa mesin sama sekali: apakah modus yang dipilih masuk akal,
apakah kalimatnya terbaca oleh orang klaim. Itu yang ditera, dan itu yang
menahan berkas ragu ke meja manusia.
"""

from __future__ import annotations

import re

from .jejak import Jejak
from .periksa import angka_pada, periksa_a1

# Nama yang dipakai orang klaim, dan medan alat yang seharusnya dirujuknya.
# Frasa panjang ditaruh lebih dulu, karena "selisih tarif" harus menang atas
# "selisih". Satu frasa boleh menunjuk beberapa medan: "ditagihkan" sah untuk
# tarif paketnya saja maupun untuk nilai berkas utuh, dan menuntut satu
# di antaranya saja akan menuduh kalimat yang sebenarnya benar.
IKATAN: list[tuple[str, tuple[str, ...]]] = [
    ("selisih tarif", ("selisih_tarif_rp",)),
    ("selisih barang", ("selisih_barang_rp",)),
    ("tarif resmi", ("tarif_rp",)),
    (
        "didukung bukti",
        ("total_didukung_bukti_rp", "tarif_didukung_bukti_rp", "barang_wajar_rp"),
    ),
    (
        "wajar menurut bukti",
        ("total_didukung_bukti_rp", "tarif_didukung_bukti_rp", "barang_wajar_rp"),
    ),
    ("tarif wajar", ("tarif_didukung_bukti_rp", "total_didukung_bukti_rp")),
    ("diajukan", ("total_diajukan_rp", "tarif_ditagihkan_rp")),
    (
        "ditagihkan",
        ("total_diajukan_rp", "tarif_ditagihkan_rp", "barang_ditagihkan_rp"),
    ),
    ("selisih", ("selisih_rp",)),
    ("lama rawat", ("lama_rawat",)),
    ("kelas rawat", ("kelas_rawat",)),
]

_PERMENKES = re.compile(r"Permenkes\s+(\d+)\s+Tahun\s+(\d{4})", re.I)
_KODE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}\b")

_NAIK = ("lebih besar", "lebih tinggi", "melampaui", "di atas", "melebihi")
_TURUN = ("lebih kecil", "lebih rendah", "di bawah", "kurang dari")

# Angka utuh pertama sesudah sebuah nama. Sisipan seperti "sebesar",
# "senilai", atau "Rp" boleh berada di antaranya, sampai empat puluh huruf.
#
# Yang dilarang di celah itu titik dan ganti baris, dan larangan itu yang
# menahannya berhenti di batas kalimat. Versi pertama memotong teks sepanjang
# huruf tetap lalu mencari angka di dalam potongan, dan potongannya memutus
# angka di tengah: tarif Rp 15.253.100 terbaca 1.525.310, lalu pemeriksaan
# menuduh berkas perkara yang sebenarnya benar. Pemeriksa yang menuduh lebih
# berbahaya daripada pemeriksa yang meloloskan, karena yang salah menuduh
# berhenti dibaca sama sekali.
#
# Dua tuduhan palsu memang terjadi, dan keduanya ditemukan pada berkas
# susunan model sungguhan, bukan pada uji. Titik dua membuat pencarian
# menyeberang ke daftar di belakangnya, sehingga kalimat "menurunkan
# selisih: HB Rp 489.690" dibaca seolah selisihnya Rp 489.690. Dan angka di
# dalam kode, seperti M02, terbaca sebagai besaran bernilai dua.
#
# Membuang titik dua saja tidak cukup, dan sempat salah begitu. "Diajukan:
# Rp 20.107.500" juga memakai titik dua, dan menolak seluruh titik dua
# berarti berhenti memeriksa bentuk penulisan yang paling lazim di berkas
# klaim. Yang membedakan keduanya bukan tanda bacanya melainkan apa yang
# berdiri sesudahnya.
#
# Maka yang boleh berdiri di antara sebutan dan angkanya didaftar satu satu.
# Kata sambung dan satuan boleh, apa pun yang lain menghentikan pembacaan.
# Angka yang menempel pada huruf atau tanda hubung juga tidak dianggap
# besaran, karena M02 bukan angka dua.
# Yang boleh berdiri di antara sebutan dan besarannya, dan cuma ini.
# Daftar putih, bukan jarak sekian huruf: yang tidak terdaftar
# menghentikan pembacaan, sehingga sebuah kode atau kata benda baru
# memutus ikatannya.
_PENGISI = (
    r"(?:\s+|:|,|nya|sebesar|senilai|sejumlah|sebanyak|nilai|total"
    r"|adalah|yaitu|ialah|Rp\.?)"
)
SESUDAH = re.compile(rf"(?:{_PENGISI}){{0,10}}(?<![A-Za-z0-9-])(\d[\d.]*(?:,\d+)?)")


def _besaran(teks: str, mulai: int) -> float | None:
    """Angka utuh pertama sesudah kedudukan mulai, atau tidak ada."""
    m = SESUDAH.match(teks, mulai)
    if not m:
        return None
    try:
        return float(m.group(1).rstrip(".").replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _sama(a: float, b: float) -> bool:
    """Sama sesudah pembulatan yang wajar, termasuk pembulatan ke juta."""
    if abs(a - b) < 0.51:
        return True
    if b and abs(a - b / 1e6) < 0.051:
        return True
    return abs(a - round(b, 2)) < 1e-9


def kumpulkan_fakta(hasil: list[dict]) -> dict:
    """Satukan seluruh hasil alat jadi satu kamus nama ke nilai.

    Nama yang muncul di lebih dari satu hasil disimpan sebagai himpunan
    nilai, bukan ditimpa. Menimpanya akan membuat pemeriksaan menuduh
    kalimat yang merujuk hasil alat yang lebih awal.
    """
    fakta: dict[str, set[float]] = {}
    daftar: dict[str, list] = {}
    for h in hasil:
        if not isinstance(h, dict):
            continue
        for k, v in h.items():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                fakta.setdefault(k, set()).add(float(v))
            elif isinstance(v, list):
                daftar.setdefault(k, []).extend(v)
    return {"nilai": fakta, "daftar": daftar}


def ikatan_salah(teks: str, fakta: dict) -> list[dict]:
    """Nama yang diikuti angka yang bukan miliknya."""
    nilai = fakta["nilai"]
    rusak = []
    rendah = teks.lower()
    for frasa, medan in IKATAN:
        for m in re.finditer(re.escape(frasa), rendah):
            n = _besaran(teks, m.end())
            if n is None:
                continue
            sah = {x for k in medan for x in nilai.get(k, set())}
            if not sah:
                continue
            if not any(_sama(n, s) for s in sah):
                rusak.append(
                    {
                        "jenis": "ikatan",
                        "nama": frasa,
                        "disebut": n,
                        "seharusnya": sorted(sah)[:4],
                    }
                )
    return rusak


def arah_bukti_salah(teks: str, fakta: dict) -> list[dict]:
    """Butir yang disebut menurunkan selisih padahal justru menaikkan."""
    butir = {
        b.get("kode"): b.get("ubah_selisih_rp")
        for b in fakta["daftar"].get("bukti", [])
        if isinstance(b, dict)
    }
    if not butir:
        return []
    rusak = []
    menurunkan = False
    for baris in teks.splitlines():
        r = baris.lower()
        if "menurunkan selisih" in r or "menurunkan sel" in r:
            menurunkan = True
            continue
        if not baris.strip():
            menurunkan = False
            continue
        if not menurunkan:
            continue
        for kode, ubah in butir.items():
            if kode and re.search(rf"\b{re.escape(kode)}\b", baris) and ubah <= 0:
                rusak.append(
                    {
                        "jenis": "arah",
                        "kode": kode,
                        "ubah_selisih_rp": ubah,
                    }
                )
    return rusak


def kutipan_tak_diambil(teks: str, hasil: list[dict]) -> list[dict]:
    """Peraturan yang dikutip tapi tidak pernah dikembalikan alat."""
    sumber = " ".join(
        str(v) for h in hasil if isinstance(h, dict) for v in _semua_teks(h)
    )
    rusak = []
    for m in _PERMENKES.finditer(teks):
        pola = re.compile(rf"Permenkes\s+{m.group(1)}\s+Tahun\s+{m.group(2)}", re.I)
        if not pola.search(sumber):
            rusak.append({"jenis": "kutipan", "sebut": m.group(0)})
    return rusak


def _semua_teks(o) -> list[str]:
    keluar = []
    if isinstance(o, str):
        keluar.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            keluar.extend(_semua_teks(v))
    elif isinstance(o, (list, tuple)):
        for v in o:
            keluar.extend(_semua_teks(v))
    return keluar


def kode_karangan(teks: str, hasil: list[dict]) -> list[dict]:
    """Kode pemeriksaan atau kelompok tarif yang tidak ada pada hasil alat."""
    from ..katalog import PEMERIKSAAN

    dikenal = set(PEMERIKSAAN)
    ada = set()
    for t in _semua_teks(hasil):
        ada.update(_KODE.findall(t))
    rusak = []
    for k in set(_KODE.findall(teks)):
        if k in ada:
            continue
        # Yang dituduh hanya kode yang berbentuk kode pemeriksaan. Kata
        # bercetak besar seperti NALAR atau BPJS bukan kode, dan menuduhnya
        # akan membuat pemeriksaan ini berisik sampai tidak dibaca.
        if k in dikenal:
            rusak.append({"jenis": "kode", "kode": k})
    return rusak


def perbandingan_salah(teks: str) -> list[dict]:
    """Dua angka pada satu kalimat yang urutannya tidak seperti disebut."""
    rusak = []
    for kalimat in re.split(r"[.\n]", teks):
        angka = angka_pada(kalimat)
        if len(angka) < 2:
            continue
        r = kalimat.lower()
        for kata in _NAIK:
            i = r.find(kata)
            if i < 0:
                continue
            kiri = angka_pada(kalimat[:i])
            kanan = angka_pada(kalimat[i:])
            if kiri and kanan and kiri[-1] <= kanan[0]:
                rusak.append(
                    {"jenis": "banding", "kata": kata, "kalimat": kalimat[:80]}
                )
        for kata in _TURUN:
            i = r.find(kata)
            if i < 0:
                continue
            kiri = angka_pada(kalimat[:i])
            kanan = angka_pada(kalimat[i:])
            if kiri and kanan and kiri[-1] >= kanan[0]:
                rusak.append(
                    {"jenis": "banding", "kata": kata, "kalimat": kalimat[:80]}
                )
    return rusak


BAGIAN_WAJIB = ("selisih", "bukti", "modus")


def bagian_kurang(teks: str) -> list[dict]:
    r = teks.lower()
    return [{"jenis": "bagian", "nama": b} for b in BAGIAN_WAJIB if b not in r]


def periksa_cepat(teks: str, jejak: Jejak, fakta: dict) -> dict:
    """Pemeriksaan yang dijalankan tiap berkas sebelum apa pun dikirim."""
    a1 = periksa_a1(teks, jejak)
    cacat: list[dict] = []
    if not a1["lulus"]:
        cacat.append({"jenis": "a1", "angka": a1["angka_tak_bersumber"]})
    cacat += arah_bukti_salah(teks, fakta)
    cacat += bagian_kurang(teks)
    return {"lulus": not cacat, "cacat": cacat, "a1": a1}


def periksa_dalam(teks: str, jejak: Jejak, fakta: dict, hasil: list[dict]) -> dict:
    """Pemeriksaan lengkap. Dijalankan pada tiap berkas, bukan pada sampel.

    Diukur 1,05 milidetik per berkas, melawan 264 milidetik untuk menyusunnya
    dan sekitar delapan ribu untuk satu giliran model bahasa.
    """
    cepat = periksa_cepat(teks, jejak, fakta)
    cacat = list(cepat["cacat"])
    cacat += ikatan_salah(teks, fakta)
    cacat += kutipan_tak_diambil(teks, hasil)
    cacat += kode_karangan(teks, hasil)
    cacat += perbandingan_salah(teks)
    return {"lulus": not cacat, "cacat": cacat, "n_cacat": len(cacat)}
