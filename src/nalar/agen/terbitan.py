"""Agen Aturan: menua bersama peraturan, bukan menua sendirian.

Tarif INA-CBG akan berubah. Ketika itu terjadi, sistem yang tidak tahu akan
terus menilai memakai tabel lama, dan seluruh penilaiannya diam diam memakai
angka yang salah. Bukan salah kutip di satu kalimat, melainkan salah di
seluruh keluaran, tanpa satu pun pesan galat.

Survei tujuh dimensi atas agen kesehatan mencatat sekitar 98 persen sistem
yang ditinjau tidak punya mekanisme memperbarui dan melupakan pengetahuan
lama. Agen ini mengisi lubang itu, dan mengisinya dengan tiga hal yang bisa
diperiksa, bukan dengan janji.

Pertama, membandingkan tabel lama dan baru, lalu menyebut kode mana yang
bergerak dan berapa besarnya.

Kedua, menjalankan ulang penilaian pada periode berjalan dan menyebut berkas
mana yang berubah putusan. Ini yang paling penting bagi verifikator: bukan
"tarif berubah", melainkan "dua belas berkas yang kemarin bersih hari ini
tertandai, dan ini nomornya".

Ketiga, menandai pengetahuan lama kedaluwarsa. Entri aturan yang menyebut
peraturan yang sudah dicabut tidak dibiarkan hidup berdampingan dengan yang
baru, karena agen yang mengutip keduanya akan terdengar sama yakinnya pada
dua hal yang bertentangan.

Yang tidak dikerjakan agen ini: memutuskan tabel mana yang benar. Ia
menerima tabel baru dari yang berwenang, dan melaporkan akibatnya. Memilih
peraturan bukan pekerjaan mesin.
"""

from __future__ import annotations

import re
import time

import numpy as np

from .jejak import Jejak


def _bersihkan_singgahan(tr) -> None:
    """Kosongkan seluruh singgahan pada modul tarif.

    Fungsi mana yang disinggahi bukan urusan agen ini, dan pernah berubah
    sekali. Jadi yang dicari fungsi yang punya cache_clear, bukan nama yang
    ditulis tangan. Menuliskan namanya berarti tambalan yang diam diam
    berhenti bekerja ketika modulnya dirapikan.
    """
    for nama in dir(tr):
        bersihkan = getattr(getattr(tr, nama), "cache_clear", None)
        if callable(bersihkan):
            bersihkan()


def bandingkan_tarif(lama: dict, baru: dict) -> dict:
    """Kode yang bergerak antara dua tabel tarif, beserta besarnya.

    Kedua tabel berbentuk peta (kode, regional, kelas_rs, kepemilikan) ke
    tiga tarif kelas rawat, yaitu bentuk yang dipakai tarif_resmi.
    """
    kunci_lama, kunci_baru = set(lama), set(baru)
    naik, turun, berubah = [], [], 0
    for k in kunci_lama & kunci_baru:
        a, b = lama[k], baru[k]
        if a == b:
            continue
        berubah += 1
        d = sum(b) - sum(a)
        (naik if d > 0 else turun).append((abs(d) / 3.0, k))
    naik.sort(reverse=True)
    turun.sort(reverse=True)
    return {
        "n_baris_lama": len(kunci_lama),
        "n_baris_baru": len(kunci_baru),
        "n_baris_berubah": berubah,
        "n_kode_hilang": len(kunci_lama - kunci_baru),
        "n_kode_baru": len(kunci_baru - kunci_lama),
        "naik_terbesar": [
            {"kode": k[0], "regional": k[1], "kelas_rs": k[2], "rata_naik_rp": round(d)}
            for d, k in naik[:5]
        ],
        "turun_terbesar": [
            {
                "kode": k[0],
                "regional": k[1],
                "kelas_rs": k[2],
                "rata_turun_rp": round(d),
            }
            for d, k in turun[:5]
        ],
    }


def putusan_yang_berubah(sebelum, sesudah, id_klaim) -> dict:
    """Berkas yang berpindah sisi, dari bersih ke tertandai atau sebaliknya.

    Yang dilaporkan nomornya, bukan cuma cacahnya. Verifikator tidak bisa
    mengerjakan apa pun dengan kalimat "dua belas berkas berubah".
    """
    a = np.asarray(sebelum, dtype=bool)
    b = np.asarray(sesudah, dtype=bool)
    jadi_tertandai = np.flatnonzero(~a & b)
    jadi_bersih = np.flatnonzero(a & ~b)
    return {
        "n_diperiksa": int(a.size),
        "n_jadi_tertandai": int(jadi_tertandai.size),
        "n_jadi_bersih": int(jadi_bersih.size),
        "jadi_tertandai": [id_klaim(int(i)) for i in jadi_tertandai[:20]],
        "jadi_bersih": [id_klaim(int(i)) for i in jadi_bersih[:20]],
        "porsi_berpindah": round(
            float((jadi_tertandai.size + jadi_bersih.size) / max(a.size, 1)), 5
        ),
    }


_NOMOR = re.compile(r"(\d+)\s*(?:tahun|/)\s*(\d{4})", re.I)


def kenali_peraturan(teks: str) -> dict | None:
    """Ubah sebutan peraturan jadi nomor dan tahun.

    Ada karena versi pertama mencocokkan ejaan. Pustaka menulis "Peraturan
    Menteri Kesehatan Nomor 3 Tahun 2023", yang mencabut menulis "Permenkes 3
    Tahun 2023", dan tidak ada yang tertandai kedaluwarsa. Yang paling buruk
    dari kegagalan itu bukan besarnya, melainkan diamnya: seluruh uji lain
    lulus, dan pustakanya tetap mengutip peraturan yang sudah dicabut.

    Peraturan dikenali dari nomor dan tahunnya, bukan dari cara orang
    menyebutnya.
    """
    m = _NOMOR.search(teks or "")
    if not m:
        return None
    return {"nomor": int(m.group(1)), "tahun": int(m.group(2))}


def kedaluwarsakan(pustaka, dicabut: str) -> list[dict]:
    """Tandai entri aturan yang menyebut peraturan yang sudah dicabut.

    Yang ditandai bukan dihapus. Berkas perkara yang sudah terlanjur dikirim
    mengutip peraturan itu, dan verifikator yang membukanya setahun lagi
    berhak tahu bahwa yang dikutip sudah tidak berlaku, bukan menemukan
    kutipannya lenyap.
    """
    sasaran = kenali_peraturan(dicabut)
    kena = []
    for e in pustaka.DASAR:
        pu = e.get("peraturan")
        cocok = bool(
            sasaran
            and pu
            and int(pu.get("nomor", -1)) == sasaran["nomor"]
            and int(pu.get("tahun", -1)) == sasaran["tahun"]
        )
        if not cocok:
            continue
        e["kedaluwarsa"] = dicabut
        kena.append({"kode": e["kode"], "judul": e["judul"], "peraturan": pu})
    return kena


def jalankan(keadaan, tabel_baru: dict, dicabut: str = "") -> dict:
    """Laporkan akibat sebuah tabel tarif baru pada periode berjalan.

    Yang dikembalikan laporan, bukan perubahan. Tidak ada satu pun tabel
    penilaian yang ditulis dari sini. Tabel barunya dipasang orang yang
    berwenang, sesudah membaca laporan ini.
    """
    from .. import tarif_resmi as tr
    from . import aturan as pustaka

    jejak = Jejak(perkara="terbitan")
    t0 = time.time()

    lama = tr._muat()
    beda = bandingkan_tarif(lama, tabel_baru)
    jejak.tambah("bandingkan_tarif", {"n_baris_baru": len(tabel_baru)}, beda, 0.0)

    sebelum = np.asarray(keadaan.detektor.tandai(keadaan.episodes), dtype=bool)

    # Tabel diganti sementara, lalu dikembalikan apa pun yang terjadi. Tanpa
    # blok akhirnya, satu galat di tengah meninggalkan seluruh proses memakai
    # tabel yang belum disahkan siapa pun.
    asli_muat = tr._muat
    try:
        tr._muat = lambda: tabel_baru  # noqa: E731
        _bersihkan_singgahan(tr)
        sesudah = np.asarray(keadaan.detektor.tandai(keadaan.episodes), dtype=bool)
    finally:
        tr._muat = asli_muat
        _bersihkan_singgahan(tr)

    putusan = putusan_yang_berubah(sebelum, sesudah, keadaan.id_klaim)
    jejak.tambah("putusan_yang_berubah", {"dicabut": dicabut}, putusan, 0.0)

    usang = kedaluwarsakan(pustaka, dicabut) if dicabut else []
    if dicabut:
        jejak.tambah("kedaluwarsakan", {"dicabut": dicabut}, usang, 0.0)

    return {
        "tarif": beda,
        "putusan": putusan,
        "aturan_kedaluwarsa": usang,
        "detik": round(time.time() - t0, 2),
        "jejak": jejak,
        "ringkas_jejak": jejak.ringkas(),
    }
