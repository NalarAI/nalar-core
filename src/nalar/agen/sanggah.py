"""Agen Sanggah: membaca bukti balasan faskes yang tidak terstruktur.

Portal hari ini hanya bisa menerima centang pada butir yang sudah kami
daftarkan. Kalau rumah sakit mengirim salinan hasil laboratorium atau
catatan operasi, tidak ada yang membacanya, dan faskes yang buktinya sah
tetap kalah karena bentuk kirimannya salah. Itu bukan keadilan, itu
keterbatasan antarmuka.

Yang dikerjakan agen ini satu langkah saja: mengubah kalimat jadi kode
pemeriksaan yang dikenal model. Sesudah itu ia menyerah dan memanggil
skor_ulang. Selisih barunya dihitung penebak, bukan dijanjikan agen, dan
itu batas yang tidak boleh digeser. Agen yang boleh menjanjikan penurunan
adalah agen yang bisa dibujuk menjanjikan penurunan.

Pemetaan berbasis kata dibangun lebih dulu, tanpa model bahasa. Ia yang jadi
garis dasar. Model bahasa dipasang di atasnya, dan kalau ia tidak menang atas
pencocokan kata, ia dicabut. Pencocokan kata punya satu sifat yang tidak
dimiliki model: ia tidak bisa mengarang kode yang tidak ada di katalog,
karena yang dicocokkan justru isi katalognya.
"""

from __future__ import annotations

import re
import unicodedata

from ..katalog import PEMERIKSAAN
from .alat import GalatAlat, Perkakas
from .jejak import Jejak

# Kata yang muncul di hampir semua surat dan tidak membedakan apa pun.
UMUM = {
    "hasil",
    "pemeriksaan",
    "nilai",
    "pasien",
    "dengan",
    "yang",
    "pada",
    "dan",
    "dari",
    "untuk",
    "telah",
    "sudah",
    "kami",
    "lampiran",
    "terlampir",
    "darah",
}

# Sebutan sehari hari yang dipakai orang klaim tapi tidak persis nama
# katalog. Ditulis satu satu, bukan ditebak dengan kemiripan huruf, karena
# kemiripan huruf mencampur kreatinin dengan kreatin kinase.
SEBUTAN = {
    "HB": ("hb", "haemoglobin", "hemoglobine"),
    "LEUKO": ("leukosit", "sel darah putih", "wbc", "angka leukosit"),
    "TROMB": ("trombosit", "platelet", "plt"),
    "GDP": ("gula darah puasa", "glukosa puasa", "gds"),
    "HBA1C": ("hba1c", "hemoglobin terglikasi", "a1c"),
    "KREA": ("kreatinin", "creatinine", "faal ginjal"),
    "LED": ("led", "laju endap"),
    "HT": ("hematokrit", "hct"),
}


def _bersih(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def petakan_bukti(surat: str, kode_sudah_ada: set[str] | None = None) -> list[dict]:
    """Kode pemeriksaan yang disebut pada surat, beserta alasan pemetaannya.

    Alasannya ikut dikembalikan supaya verifikator bisa membantah pemetaan
    tanpa harus membuka kodenya. Pemetaan yang tidak bisa dibantah sama saja
    dengan pemetaan yang tidak bisa diperiksa.
    """
    ada = kode_sudah_ada or set()
    teks = _bersih(surat)
    keluar = []
    for kode, (nama, *_) in PEMERIKSAAN.items():
        if kode in ada:
            continue
        alasan = ""
        for s in SEBUTAN.get(kode, ()):
            if re.search(rf"\b{re.escape(s)}\b", teks):
                alasan = f"surat menyebut {s}"
                break
        if not alasan:
            kata = [k for k in _bersih(nama).split() if k and k not in UMUM]
            if kata and all(re.search(rf"\b{re.escape(k)}\b", teks) for k in kata):
                alasan = f"surat menyebut {nama.lower()}"
        if not alasan and re.search(rf"\b{kode.lower()}\b", teks):
            alasan = f"surat menyebut kode {kode}"
        if alasan:
            keluar.append({"kode": kode, "nama": nama, "alasan": alasan})
    return keluar


def jalankan(keadaan, id_berkas: str, surat: str) -> dict:
    """Baca surat balasan, petakan, lalu minta penebak menghitung ulang.

    Yang dikembalikan selalu memuat kode yang dipetakan beserta alasannya,
    termasuk ketika tidak ada yang terpetakan sama sekali. Surat yang tidak
    mengubah apa pun tetap harus dijawab, dan jawabannya harus menyebut
    bahwa isinya tidak dikenali, bukan didiamkan.
    """
    jejak = Jejak(perkara=f"{id_berkas}/sanggah")
    p = Perkakas(keadaan, jejak)

    berkas = p.panggil("ambil_berkas", id=id_berkas)
    sudah = set(berkas["pemeriksaan_lab"])
    peta = petakan_bukti(surat, sudah)
    kode = [b["kode"] for b in peta]

    if not kode:
        return {
            "id": id_berkas,
            "dipetakan": [],
            "sudah_ada": sorted(sudah),
            "hasil": None,
            "keterangan": (
                "Tidak ada pemeriksaan yang dikenali pada surat ini. "
                "Berkas diteruskan ke verifikator apa adanya."
            ),
            "jejak": jejak,
            "ringkas_jejak": jejak.ringkas(),
        }

    try:
        hasil = p.panggil("skor_ulang", id=id_berkas, bukti_tambahan=kode)
        tolak = ""
    except GalatAlat as e:
        hasil, tolak = None, str(e)

    return {
        "id": id_berkas,
        "dipetakan": peta,
        "sudah_ada": sorted(sudah),
        "hasil": hasil,
        "keterangan": tolak,
        "jejak": jejak,
        "ringkas_jejak": jejak.ringkas(),
    }
