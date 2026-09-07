"""Isian: model menulis kalimatnya, sistem yang menaruh angkanya.

Ini keputusan rancangan yang lahir dari pengukuran, bukan dari perkiraan.
Percobaan pertama dengan Qwen3 4B jatuh di penjaga A1 pada berkas pertama,
dan sebabnya selalu sama. Model menerima nilai diajukan dan nilai yang
didukung bukti dari alat, lalu menghitung sendiri selisihnya, dan
menuliskannya. Angkanya bahkan aritmetikanya benar. Yang salah asalnya: ia
tidak berasal dari alat mana pun, jadi tidak ada yang bisa ditunjukkan
ketika rumah sakit membantahnya. Pada satu berkas ia bahkan membalik
arahnya, menulis nilai yang didukung bukti lebih besar daripada yang
diajukan, dan surat seperti itu menuduh rumah sakit menagih kurang.

Menambah larangan pada arahan tidak menyelesaikan apa pun. Model bahasa
memang begitu, dan menuntutnya berhenti berhitung sama saja menuntutnya jadi
mesin lain.

Maka pembagiannya digeser. Model menulis kalimat memakai nama isian di dalam
kurung kurawal, dan sistem yang menggantinya dengan angka dari hasil alat.
Yang tersisa buat model justru yang memang bisa dikerjakannya: memilih alat,
memilih bukti mana yang pantas disebut, menyusun urutan, dan memilih kata.
Aritmetika bukan salah satunya.

Penjaga A1 tidak dicabut sesudah ini, dan itu penting. Model yang tetap
mengetik angka tetap tertangkap, dan pemeriksaan dalam tetap menangkap isian
yang benar tapi dilekatkan pada nama yang salah, misalnya "diajukan
{selisih}". Yang berubah bukan penjagaannya, melainkan berapa sering model
punya kesempatan melanggarnya.
"""

from __future__ import annotations

import re

LUBANG = re.compile(r"\{([a-z_]+)(?:\.([a-z_0-9]+))?\}")


class GalatIsian(Exception):
    """Model memakai nama isian yang tidak ada, atau yang alatnya belum dipanggil."""


def rupiah(n) -> str:
    return "Rp " + f"{int(round(float(n))):,}".replace(",", ".")


def _bukti_menolong(g: dict) -> str:
    menolong = [b for b in g.get("bukti", []) if b.get("ubah_selisih_rp", 0) > 0]
    if not menolong:
        return (
            "tidak ada pemeriksaan tunggal yang menurunkan selisih berkas ini, "
            "yang dibutuhkan keterangan klinis"
        )
    return "; ".join(
        f"{b['kode']} turun {rupiah(b['ubah_selisih_rp'])}" for b in menolong
    )


def _modus(a: dict) -> str:
    """Daftar modus, dan sejauh mana NALAR menjangkau tiap modus.

    Entri dasar hukum tidak punya jangkauan, dan dulu nilai kosongnya ikut
    tercetak apa adanya sehingga sebuah surat ke rumah sakit memuat kalimat
    "jangkauan NALAR None". Yang tidak punya jangkauan sekarang disebut apa
    adanya, sebagai dasar hukum.
    """
    bagian = []
    for e in a.get("entri", []):
        j = e.get("jangkauan")
        bagian.append(
            f"{e['kode']} {e['judul']}, "
            + (f"jangkauan NALAR {j}" if j else "dasar hukum")
        )
    return "; ".join(bagian)


def susun_isian(hasil: dict[str, dict]) -> dict[str, str]:
    """Nama isian yang boleh dipakai, beserta isinya, dari hasil alat.

    Hanya alat yang benar benar dipanggil yang menyumbang isian. Isian yang
    alatnya belum dipanggil tidak diisi kosong, melainkan tidak ada sama
    sekali, sehingga memakainya jadi penolakan yang terlihat. Isian kosong
    akan menghasilkan kalimat yang terbaca lengkap padahal keterangannya
    tidak pernah diambil.
    """
    isi: dict[str, str] = {}

    b = hasil.get("ambil_berkas")
    if b:
        isi.update(
            {
                "berkas": str(b["id"]),
                "faskes": str(b["faskes"]),
                "cbg": str(b["kelompok_tarif"]),
                "kelas_rawat": str(b["kelas_rawat"]),
                "lama_rawat": f"{b['lama_rawat']} hari",
                "diagnosis_utama": str(b["diagnosis_utama"]),
            }
        )

    g = hasil.get("hitung_pengandaian")
    if g:
        isi.update(
            {
                "diajukan": rupiah(g["total_diajukan_rp"]),
                "didukung": rupiah(g["total_didukung_bukti_rp"]),
                "selisih": rupiah(g["selisih_rp"]),
                "selisih_tarif": rupiah(
                    g["tarif_ditagihkan_rp"] - g["tarif_didukung_bukti_rp"]
                ),
                "selisih_barang": rupiah(
                    g["barang_ditagihkan_rp"] - g["barang_wajar_rp"]
                ),
                "bukti_menolong": _bukti_menolong(g),
            }
        )

    t = hasil.get("cari_tarif")
    if t:
        isi["tarif_resmi"] = rupiah(t["tarif_rp"])
        isi["sumber_tarif"] = str(t["sumber"])

    a = hasil.get("cari_aturan")
    if a:
        isi["modus"] = _modus(a)

    _medan_alat(isi, hasil)
    return isi


# Urutan ini menentukan siapa yang menang ketika dua alat mengembalikan nama
# yang sama. Yang menghitung menang atas yang mengambil, karena empat besaran
# di dalamnya sudah dibulatkan bersama sehingga selisihnya bisa dikurangkan.
URUT_ALAT = ("hitung_pengandaian", "cari_tarif", "ambil_berkas", "skor_ulang")


def _medan_alat(isi: dict[str, str], hasil: dict[str, dict]) -> None:
    """Tiap medan tunggal yang dikembalikan alat jadi nama isian juga.

    Ini bukan kenyamanan, ini perbaikan atas cacat yang terukur. Nama pendek
    seperti {diajukan} cuma ada di arahan, sedangkan nama panjang seperti
    total_diajukan_rp berdiri di dalam balasan alat, tepat di depan mata
    model, dengan angkanya menempel. Model 4B menyalin yang dilihatnya, dan
    yang dilihatnya nama medan. Maka dari empat puluh berkas, dua belas
    memakai nama isian yang tidak ada dan semuanya nama medan alat.

    Melarangnya tidak menolong. Yang menolong membuat yang disalinnya benar.
    """
    for nama_alat in URUT_ALAT:
        h = hasil.get(nama_alat)
        if not h:
            continue
        for k, v in h.items():
            if k in isi or isinstance(v, (bool, list, dict)):
                continue
            isi[k] = rupiah(v) if k.endswith("_rp") else str(v)


def isi_lubang(teks: str, isi: dict[str, str]) -> tuple[str, list[str]]:
    """Ganti tiap nama isian dengan isinya. Yang tidak dikenal ikut dilaporkan.

    Yang tidak dikenal tidak dibuang diam diam. Kalimat yang kehilangan
    isiannya terbaca seolah lengkap, dan verifikator tidak punya cara tahu
    ada keterangan yang hilang. Maka namanya dibiarkan berdiri, dan
    daftarnya dikembalikan supaya berkasnya bisa ditolak.
    """
    hilang: list[str] = []

    def ganti(m):
        nama = m.group(1) if m.group(2) is None else f"{m.group(1)}.{m.group(2)}"
        if nama in isi:
            return isi[nama]
        hilang.append(nama)
        return m.group(0)

    return LUBANG.sub(ganti, teks), hilang
