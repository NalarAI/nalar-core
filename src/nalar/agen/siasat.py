"""Bahasa siasat penghindaran, beserta juru bacanya.

Ini bagian yang paling mudah dikerjakan dengan cara yang salah, jadi
alasannya ditulis panjang.

Cara yang salah: model bahasa menulis program Python, lalu programnya
dijalankan. Itu memang yang paling luwes, dan itu juga berarti memasang
penjalan kode sembarang di dalam repositori sistem klaim. Tidak ada penilai
lomba, apalagi tim keamanan BPJS, yang pantas diminta mempercayai itu.

Cara yang dipakai: siasat ditulis sebagai bentuk data, dan yang menjalankan
juru baca deterministik buatan kami sendiri. Model bahasa merancang, bukan
mengeksekusi. Perbendaharaan gerakannya tetap dan bisa dibaca siapa saja,
tiap siasat bisa disimpan sebagai satu baris JSON, dan menjalankannya ulang
memberi hasil yang sama persis. Sebuah siasat yang ditemukan hari ini masih
bisa dijalankan setahun lagi untuk memeriksa apakah tambalannya bertahan.

Yang hilang dari cara ini kebebasan menemukan gerakan yang belum kami
bayangkan. Itu batasan yang nyata dan ditulis apa adanya di TEMUAN. Yang
didapat sebagai gantinya: seluruh ruang siasat bisa ditelusuri habis oleh
pencarian biasa, jadi ada garis dasar yang harus dikalahkan agen, sama
seperti berkas perkara punya garis dasar berbasis aturan.

Perbendaharaannya bukan daftar sembarang. Tiap gerakan menyentuh satu
penciri yang benar benar dipakai penebak, dan tiga di antaranya sengaja
menyentuh titik buta yang sudah kami tulis sendiri di pustaka aturan: lama
rawat, kelas rawat, dan bukti penyerta ikut menaikkan tarif yang dianggap
wajar, jadi menaikkannya justru mengecilkan selisih.
"""

from __future__ import annotations

import copy

from ..fraud import KODE_PENAIK
from ..katalog import PEMERIKSAAN
from ..tarif import kelompokkan, tarif

# Prosedur murah yang lazim ditambahkan pada berkas rawat inap. Dipakai
# gerakan tambah_prosedur, dan sengaja pendek: yang diuji apakah menambah
# prosedur menggeser penilaian, bukan seberapa kreatif daftarnya.
KODE_PROSEDUR = ["93.94", "96.6", "99.04", "38.93", "89.52"]

GERAKAN = {
    "tambah_diagnosis": {
        "keterangan": (
            "Tambahkan diagnosis sekunder yang menaikkan tingkat keparahan, "
            "sehingga kelompok tarifnya naik. Ini modus M04, upcoding. "
            "Parameter mulai memilih kode mana yang dipakai dari daftar "
            "penaik keparahan, sehingga pelaku bisa memilih kode yang paling "
            "sedikit menggeser skor, bukan hanya yang paling menaikkan tarif."
        ),
        "parameter": {
            "n": {"jenis": "bilangan", "min": 1, "maks": 2},
            "mulai": {"jenis": "bilangan", "min": 0, "maks": 5},
        },
    },
    "perpanjang_rawat": {
        "keterangan": (
            "Tambahkan hari rawat. Menaikkan tarif lewat tingkat keparahan, "
            "tapi lama rawat juga penciri penebak, jadi tarif yang dianggap "
            "wajar ikut naik. Ini modus M12."
        ),
        "parameter": {"hari": {"jenis": "bilangan", "min": 1, "maks": 4}},
    },
    "naikkan_kelas": {
        "keterangan": (
            "Naikkan kelas rawat satu tingkat. Kelas rawat juga penciri "
            "penebak. Ini modus M13."
        ),
        "parameter": {},
    },
    "tambah_prosedur": {
        "keterangan": "Tambahkan prosedur yang tidak dilakukan. Ini modus M14.",
        "parameter": {"n": {"jenis": "bilangan", "min": 1, "maks": 3}},
    },
    "lampirkan_lab": {
        "keterangan": (
            "Lampirkan hasil pemeriksaan penunjang. Tidak menaikkan tarif "
            "yang ditagihkan sama sekali, tapi menaikkan tarif yang dianggap "
            "wajar oleh penebak, sehingga selisihnya mengecil."
        ),
        "parameter": {"n": {"jenis": "bilangan", "min": 1, "maks": 4}},
    },
    "lampirkan_lab_terbaik": {
        "keterangan": (
            "Lampirkan pemeriksaan penunjang yang paling menurunkan selisih, "
            "bukan yang mana saja. Ini persis daftar yang portal fasilitas "
            "kesehatan tampilkan hari ini, lengkap dengan besar penurunan "
            "tiap butirnya."
        ),
        "parameter": {"n": {"jenis": "bilangan", "min": 1, "maks": 4}},
    },
    "gelembungkan_barang": {
        "keterangan": (
            "Naikkan tagihan bahan habis pakai sekian persen. Ini modus M07."
        ),
        "parameter": {"persen": {"jenis": "bilangan", "min": 5, "maks": 60}},
    },
}

SASARAN = {
    "semua_rawat_inap": {"keterangan": "Seluruh berkas rawat inap.", "parameter": {}},
    "kelompok_menahan_diri": {
        "keterangan": (
            "Hanya berkas yang kelompok sebayanya menahan diri, yaitu yang "
            "pembandingnya kurang dari tiga sehingga sistem tidak menandai "
            "apa pun di sana."
        ),
        "parameter": {},
    },
    "selisih_awal_kecil": {
        "keterangan": (
            "Hanya berkas yang selisih awalnya di bawah batas tertentu, "
            "sehingga tetap jauh dari perhatian meski diserang."
        ),
        "parameter": {"batas_rp": {"jenis": "bilangan", "min": 0, "maks": 20_000_000}},
    },
    "kelas_faskes": {
        "keterangan": "Hanya faskes berkelas tertentu.",
        "parameter": {"kelas": {"jenis": "pilihan", "pilihan": ["A", "B", "C", "D"]}},
    },
}

PILIHAN = {
    "paling_untung": {
        "keterangan": "Ambil kenaikan tarif terbesar, tidak peduli tertandai."
    },
    "aman_di_bawah_ambang": {
        "keterangan": (
            "Hanya ambil varian yang skornya tetap di bawah ambang penandaan."
        )
    },
    "kenaikan_skor_terkecil": {
        "keterangan": "Ambil varian yang paling sedikit menaikkan skor."
    },
    "untung_di_bawah_porsi_ambang": {
        "keterangan": (
            "Ambil untung terbesar di antara varian yang skornya di bawah "
            "sekian bagian dari ambang. Porsi 0,7 berarti berhenti jauh "
            "sebelum garis, bukan menempel di garis."
        ),
        "parameter": {
            "porsi": {"jenis": "pecahan", "min": 0.1, "maks": 1.0},
        },
    },
    "untung_dibatasi": {
        "keterangan": (
            "Ambil untung terbesar yang masih di bawah batas rupiah. Dipakai "
            "untuk tetap berada di bawah lantai biaya pemeriksaan, sehingga "
            "berkasnya tidak pernah masuk antrean sekalipun tertandai."
        ),
        "parameter": {
            "batas_rp": {"jenis": "bilangan", "min": 50_000, "maks": 5_000_000}
        },
    },
}


class GalatSiasat(Exception):
    """Siasat tidak bisa dibaca, atau memakai gerakan yang tidak ada."""


def perbendaharaan() -> dict:
    """Seluruh gerakan, sasaran, dan cara memilih yang tersedia.

    Dikirim ke model bahasa apa adanya. Yang tidak dikirim satu pun angka
    dari berkas, karena yang dirancang siasatnya, bukan datanya.
    """
    return {"sasaran": SASARAN, "gerakan": GERAKAN, "pilihan": PILIHAN}


def periksa(siasat: dict) -> None:
    """Tolak siasat yang bentuknya salah, sebelum satu berkas pun disentuh."""
    if not isinstance(siasat, dict):
        raise GalatSiasat("siasat harus berupa obyek")

    nama = siasat.get("nama")
    if not isinstance(nama, str) or not nama.strip():
        raise GalatSiasat("siasat harus punya nama")

    s = siasat.get("sasaran") or {"jenis": "semua_rawat_inap"}
    if s.get("jenis") not in SASARAN:
        raise GalatSiasat(f"sasaran {s.get('jenis')} tidak ada")

    gerak = siasat.get("gerakan")
    if not isinstance(gerak, list) or not gerak:
        raise GalatSiasat("gerakan harus daftar berisi sekurangnya satu gerakan")
    if len(gerak) > 3:
        raise GalatSiasat("paling banyak tiga gerakan digabung")
    for g in gerak:
        if not isinstance(g, dict) or g.get("jenis") not in GERAKAN:
            raise GalatSiasat(f"gerakan {g} tidak ada pada perbendaharaan")

    p = siasat.get("pilihan") or {"jenis": "paling_untung"}
    if p.get("jenis") not in PILIHAN:
        raise GalatSiasat(f"cara memilih {p.get('jenis')} tidak ada")


# -- gerakan ---------------------------------------------------------------


def _hitung_ulang_tarif(d: dict) -> None:
    kel = kelompokkan(d["dxp"], d["dxs"], d["prc"], d["los"], d["rawat_inap"])
    d["cbg"], d["keparahan"] = kel.kode, kel.keparahan
    d["tarif"] = tarif(
        kel, d["dxp"], d["prc"], d["kelas_rawat"], d["f_kelas"], d["f_reg"]
    )


def _tambah_diagnosis(d: dict, n: int = 1, mulai: int = 0) -> None:
    kandidat = [c for c in KODE_PENAIK if c not in d["dxs"]]
    if not kandidat:
        return
    a = int(mulai) % len(kandidat)
    ambil = (kandidat + kandidat)[a : a + max(1, int(n))]
    d["dxs"] = list(d["dxs"]) + [c for c in ambil if c not in d["dxs"]]
    _hitung_ulang_tarif(d)


def _perpanjang_rawat(d: dict, hari: int = 1) -> None:
    d["los"] = int(d["los"]) + max(1, int(hari))
    _hitung_ulang_tarif(d)


def _naikkan_kelas(d: dict) -> None:
    d["kelas_rawat"] = max(1, int(d["kelas_rawat"]) - 1)
    _hitung_ulang_tarif(d)


def _tambah_prosedur(d: dict, n: int = 1) -> None:
    kandidat = [c for c in KODE_PROSEDUR if c not in d["prc"]]
    d["prc"] = list(d["prc"]) + kandidat[: max(1, int(n))]
    _hitung_ulang_tarif(d)


def urutan_pengandaian(r: dict, penskor) -> list[str]:
    """Kode pemeriksaan, terurut dari yang paling menurunkan selisih.

    Ini persis daftar yang portal fasilitas kesehatan tampilkan hari ini,
    lengkap dengan besar penurunan tiap butirnya, seluruhnya sekaligus,
    dalam satu jawaban.

    Daftar itu inti janji kami kepada faskes. Tanpa daftar itu, penandaan
    cuma tuduhan yang tidak bisa dibantah, dan faskes yang buktinya sah tetap
    kalah karena tidak tahu bukti mana yang diminta. Dengan daftar itu, ia
    tahu persis apa yang perlu dikirim.

    Dan daftar yang sama adalah peta bagi yang ingin menghindar. Fungsi ini
    ada supaya harga peta itu bisa diukur, bukan diperkirakan.

    Dihitung sekali dari berkas apa adanya, bukan dari tiap varian. Itu bukan
    penghematan, itu yang benar: faskes membaca daftar untuk berkas yang ia
    ajukan, bukan untuk berkas yang belum pernah ada.
    """
    ada = {k for k, _ in r["lab"]}
    kandidat = [k for k in PEMERIKSAAN if k not in ada]
    if not kandidat:
        return []
    tiruan = []
    for k in kandidat:
        t = copy.deepcopy(r)
        t["lab"] = list(r["lab"]) + [(k, 1.0)]
        tiruan.append(t)
    skor = penskor([r] + tiruan)
    dasar = float(skor[0])
    turun = [(dasar - float(x), k) for x, k in zip(skor[1:], kandidat)]
    turun.sort(reverse=True)
    return [k for t, k in turun if t > 0]


def _lampirkan_lab_terbaik(d: dict, n: int = 1, urutan: list | None = None) -> None:
    """Lampirkan pemeriksaan teratas pada daftar pengandaian berkas ini."""
    if not urutan:
        return _lampirkan_lab(d, n)
    ada = {k for k, _ in d["lab"]}
    pilih = [k for k in urutan if k not in ada][: max(1, int(n))]
    d["lab"] = list(d["lab"]) + [(k, 1.0) for k in pilih]


def _lampirkan_lab(d: dict, n: int = 1) -> None:
    ada = {k for k, _ in d["lab"]}
    kandidat = [k for k in PEMERIKSAAN if k not in ada]
    d["lab"] = list(d["lab"]) + [(k, 1.0) for k in kandidat[: max(1, int(n))]]


def _gelembungkan_barang(d: dict, persen: int = 20) -> None:
    d["tagih_bhp"] = int(round(float(d.get("tagih_bhp", 0)) * (1 + persen / 100.0)))


_TERAP = {
    "tambah_diagnosis": _tambah_diagnosis,
    "perpanjang_rawat": _perpanjang_rawat,
    "naikkan_kelas": _naikkan_kelas,
    "tambah_prosedur": _tambah_prosedur,
    "lampirkan_lab": _lampirkan_lab,
    "lampirkan_lab_terbaik": _lampirkan_lab_terbaik,
    "gelembungkan_barang": _gelembungkan_barang,
}


# Sebanyak banyaknya varian yang dibangkitkan satu berkas. Ruang parameter
# bisa membesar cepat kalau tiga gerakan digabung dan ketiganya dibiarkan
# terbuka, dan yang menanggung biayanya penebak, satu panggilan per varian.
BATAS_VARIAN = 12


def _nilai_parameter(jenis: str, g: dict) -> list[dict]:
    """Susunan parameter yang dicoba untuk satu gerakan.

    Parameter yang disebut siasat dipakai apa adanya. Parameter yang tidak
    disebut dibiarkan terbuka, dan seluruh rentangnya dicoba. Itu yang
    membuat cara memilih punya arti: tanpa pilihan, serakah dan hati hati
    akan mengambil varian yang sama karena cuma ada satu.
    """
    param = GERAKAN[jenis]["parameter"]
    if not param:
        return [{}]
    susunan: list[dict] = [{}]
    for nama, batas in param.items():
        baru: list[dict] = []
        nilai = (
            [g[nama]]
            if nama in g
            else list(range(int(batas["min"]), int(batas["maks"]) + 1))
        )
        for a in susunan:
            for v in nilai:
                baru.append({**a, nama: v})
        susunan = baru
    return susunan


# Gerakan yang perlu tahu skor berkasnya untuk memilih. Dipisah supaya
# gerakan lain tetap bisa dijalankan tanpa penebak sama sekali.
BUTUH_PENSKOR = {"lampirkan_lab_terbaik"}


def varian(r: dict, gerakan: list[dict], penskor=None) -> list[dict]:
    """Seluruh berkas yang mungkin sesudah gerakan diterapkan.

    Yang dikembalikan salinan. Berkas aslinya tidak pernah disentuh, dan itu
    bukan soal kerapian: himpunan uji yang sama dipakai ulang untuk tiap
    siasat, dan satu siasat yang mengubahnya akan mencemari seluruh
    pengukuran sesudahnya tanpa satu pun tanda.
    """
    # Daftar pengandaian dihitung sekali untuk berkas ini, bukan sekali per
    # varian. Kalau tidak, satu siasat memakan ratusan ribu penskoran dan
    # pengukurannya tidak pernah selesai.
    urutan = None
    if penskor is not None and any(g["jenis"] in BUTUH_PENSKOR for g in gerakan):
        urutan = urutan_pengandaian(r, penskor)

    susunan: list[list[dict]] = [[]]
    for g in gerakan:
        jenis = g["jenis"]
        baru: list[list[dict]] = []
        for a in susunan:
            for nilai in _nilai_parameter(jenis, g):
                baru.append([*a, {"jenis": jenis, **nilai}])
        susunan = baru[:BATAS_VARIAN]

    keluar = []
    for langkah in susunan:
        d = copy.deepcopy(r)
        for g in langkah:
            arg = {k: v for k, v in g.items() if k != "jenis"}
            if g["jenis"] in BUTUH_PENSKOR:
                arg["urutan"] = urutan
            _TERAP[g["jenis"]](d, **arg)
        keluar.append(d)
    return keluar


# -- sasaran ---------------------------------------------------------------


def cocok_sasaran(r: dict, sasaran: dict, tahan: bool, selisih_awal: float) -> bool:
    jenis = sasaran.get("jenis", "semua_rawat_inap")
    if not r["rawat_inap"]:
        return False
    if jenis == "semua_rawat_inap":
        return True
    if jenis == "kelompok_menahan_diri":
        return bool(tahan)
    if jenis == "selisih_awal_kecil":
        return float(selisih_awal) <= float(sasaran.get("batas_rp", 0))
    if jenis == "kelas_faskes":
        return r["f_kelas"] == sasaran.get("kelas")
    return False


# -- cara memilih ----------------------------------------------------------


def pilih(
    pilihan: dict,
    untung,
    skor,
    skor_awal: float,
    ambang: float,
) -> int | None:
    """Nomor varian yang diambil pelaku, atau tidak ada yang diambil."""
    import numpy as np

    jenis = pilihan.get("jenis", "paling_untung")
    untung = np.asarray(untung, dtype=np.float64)
    skor = np.asarray(skor, dtype=np.float64)
    if untung.size == 0 or (untung <= 0).all():
        return None

    if jenis == "paling_untung":
        return int(np.argmax(untung))

    if jenis == "aman_di_bawah_ambang":
        aman = np.flatnonzero((skor <= ambang) & (untung > 0))
        return int(aman[np.argmax(untung[aman])]) if aman.size else None

    if jenis == "kenaikan_skor_terkecil":
        boleh = np.flatnonzero(untung > 0)
        return int(boleh[np.argmin(skor[boleh] - skor_awal)])

    if jenis == "untung_di_bawah_porsi_ambang":
        porsi = float(pilihan.get("porsi", 0.7))
        aman = np.flatnonzero((skor <= ambang * porsi) & (untung > 0))
        return int(aman[np.argmax(untung[aman])]) if aman.size else None

    if jenis == "untung_dibatasi":
        batas = float(pilihan.get("batas_rp", 500_000))
        boleh = np.flatnonzero((untung > 0) & (untung <= batas))
        return int(boleh[np.argmax(untung[boleh])]) if boleh.size else None

    return None
