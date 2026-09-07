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
from .penutur import GalatPenutur, Penutur

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


ARAHAN_SURAT = """Kamu membaca surat balasan dari fasilitas kesehatan kepada
BPJS Kesehatan. Tugasmu satu, dan cuma satu: menyebut pemeriksaan penunjang
mana yang menurut surat ini benar benar sudah dikerjakan atau dilampirkan.

Kamu tidak menilai apa pun. Kamu tidak menghitung apa pun. Yang menghitung
ulang selisihnya penebak tarif, sesudah kamu selesai.

Aturan yang tidak boleh dilanggar:

1. Cuma kode dari daftar di bawah. Kode di luar daftar dibuang sistem.
2. Pemeriksaan yang surat sebut tidak dilakukan, belum dikerjakan, ditolak,
   atau baru direncanakan, jangan disebut. Surat yang bilang "trombosit
   tidak diperiksa" tidak sedang melampirkan trombosit.
3. Untuk tiap kode, salin potongan kalimat dari suratnya, apa adanya,
   sebagai dasar. Potongan yang tidak ada di surat membuat kodenya dibuang.
4. Kalau surat tidak menyebut satu pun, panggil alat dengan daftar kosong.

Daftar kode dan namanya:

{daftar}"""


def _daftar_kode() -> str:
    return "\n".join(f"  {k}  {n}" for k, (n, *_) in PEMERIKSAAN.items())


def skema_surat() -> list[dict]:
    """Satu alat, dan kodenya dijepit daftar katalog di dalam skemanya.

    Menjepitnya di skema tidak menggantikan pemeriksaan sesudahnya, dan
    memang tidak boleh menggantikan. Peladen yang tidak menegakkan enum
    tetap ada, dan kode di luar katalog tetap dibuang oleh yang memanggil.
    """
    return [
        {
            "name": "catat_pemeriksaan",
            "description": (
                "Daftar pemeriksaan yang menurut surat sudah dikerjakan "
                "atau dilampirkan, beserta potongan kalimat dasarnya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pemeriksaan": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "kode": {
                                    "type": "string",
                                    "enum": sorted(PEMERIKSAAN),
                                },
                                "kutipan": {
                                    "type": "string",
                                    "description": (
                                        "Potongan kalimat dari surat, "
                                        "disalin apa adanya."
                                    ),
                                },
                            },
                            "required": ["kode", "kutipan"],
                        },
                    }
                },
                "required": ["pemeriksaan"],
            },
        }
    ]


def berakar(kutipan: str, kata_surat: set[str]) -> bool:
    """Tiap kata pada kutipan ada di surat, dan sekurangnya satu berarti.

    Versi pertama menuntut kutipannya utuh, potongan huruf demi huruf dari
    suratnya. Tuntutan itu terlalu keras, dan kerasnya terukur: dari dua
    puluh empat surat, lima pemetaan yang benar dibuang karenanya. Sebabnya
    selalu sama. Surat menulis "kami lampirkan hasil prokalsitonin dan
    laktat", model mengutipnya sebagai "kami lampirkan hasil laktat", dan
    itu penyingkatan yang wajar, bukan karangan.

    Yang dituntut sekarang lebih longgar dan lebih tepat sasaran: tiap kata
    pada kutipan harus ada di surat. Model yang memetakan kreatinin pada
    surat yang tidak pernah menyebutnya tetap harus mengarang kata itu, dan
    kata karangan tetap tidak akan ketemu.

    Yang tidak dibuktikannya, dan penting ditulis di sini, ikatan antara
    kodenya dan suratnya. Kutipan yang seluruhnya kata umum bisa menemani
    kode apa pun, dan itu sebabnya sekurangnya satu kata harus di luar
    daftar kata umum. Bahkan begitu, pemetaan yang salah masih mungkin, dan
    yang menahannya bukan penjaga ini melainkan dua hal lain: alasannya ikut
    tercetak supaya bisa dibantah, dan yang menghitung ulang selisihnya
    penebak tarif, bukan agen.
    """
    kata = [k for k in _bersih(kutipan).split() if k]
    if len(kata) < 2 or not all(k in kata_surat for k in kata):
        return False
    return any(k not in UMUM for k in kata)


def petakan_bukti_model(
    surat: str,
    penutur: Penutur,
    kode_sudah_ada: set[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Pemetaan susunan model, beserta daftar yang dibuang penjaganya.

    Penjaganya satu kalimat: kode boleh masuk kalau potongan kalimat yang
    disebut model benar benar ada di dalam surat. Model yang memetakan
    kreatinin pada surat yang tidak pernah menyebutnya harus mengarang
    potongan itu lebih dulu, dan potongan karangan tidak akan ketemu.

    Ini penjaga yang sama dengan A1 pada Agen Berkas, dipindah ke bahan yang
    berbeda. Di sana angka harus berasal dari alat. Di sini kode harus
    berasal dari kalimat yang bisa ditunjuk.
    """
    ada = kode_sudah_ada or set()
    kata_surat = set(_bersih(surat).split())
    pesan = [
        {
            "role": "system",
            "content": ARAHAN_SURAT.format(daftar=_daftar_kode()),
        },
        {"role": "user", "content": surat},
    ]
    b = penutur.balas(pesan, skema_surat())

    butir = []
    for c in b.panggilan:
        if c.get("nama") != "catat_pemeriksaan":
            continue
        isi = (c.get("argumen") or {}).get("pemeriksaan") or []
        if isinstance(isi, list):
            butir.extend(x for x in isi if isinstance(x, dict))

    keluar: list[dict] = []
    dibuang: list[dict] = []
    sudah_disebut: set[str] = set()
    for x in butir:
        kode = str(x.get("kode", "")).strip().upper()
        kutipan = str(x.get("kutipan", "")).strip()
        if kode not in PEMERIKSAAN:
            dibuang.append({"kode": kode, "sebab": "kode di luar katalog"})
            continue
        if kode in ada or kode in sudah_disebut:
            continue
        if not berakar(kutipan, kata_surat):
            dibuang.append({"kode": kode, "sebab": "kutipannya tidak ada di surat"})
            continue
        sudah_disebut.add(kode)
        keluar.append(
            {
                "kode": kode,
                "nama": PEMERIKSAAN[kode][0],
                "alasan": f'surat menyebut "{kutipan}"',
            }
        )
    return keluar, dibuang


def jalankan(
    keadaan, id_berkas: str, surat: str, penutur: Penutur | None = None
) -> dict:
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

    # Model bahasa dipakai kalau ada, pencocokan kata kalau tidak. Model
    # yang gagal menjawab tidak menghentikan sanggahan, karena garis
    # dasarnya tetap berdiri sendiri tanpa satu bobot pun terpasang.
    cara, dibuang = "kata", []
    peta = []
    if penutur is not None and penutur.hidup():
        try:
            peta, dibuang = petakan_bukti_model(surat, penutur, sudah)
            cara = "model"
        except GalatPenutur:
            cara = "kata"
    if cara == "kata":
        peta = petakan_bukti(surat, sudah)
    kode = [b["kode"] for b in peta]

    if not kode:
        return {
            "id": id_berkas,
            "dipetakan": [],
            "cara": cara,
            "dibuang": dibuang,
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
        "cara": cara,
        "dibuang": dibuang,
        "sudah_ada": sorted(sudah),
        "hasil": hasil,
        "keterangan": tolak,
        "jejak": jejak,
        "ringkas_jejak": jejak.ringkas(),
    }
