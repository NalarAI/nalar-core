"""Penyusun berkas perkara berbasis aturan. Garis dasar tahap satu.

Tidak ada model bahasa di sini, dan itu inti tahap satu. Yang dibangun lebih
dulu lapisan alat, jejak auditnya, dan penyusun yang memakai keduanya secara
deterministik. Hasilnya jadi garis dasar: agen mana pun yang dipasang nanti
harus mengalahkan berkas perkara ini, dan kalau tidak, agennya yang dicabut.

Bentuk keluarannya sengaja dibuat sama dengan yang nanti diminta dari agen,
sampai ke urutan bagiannya, supaya perbandingannya lurus.
"""

from __future__ import annotations

from .alat import GalatAlat, Perkakas
from .dalam import kumpulkan_fakta
from .jejak import Jejak
from .periksa import periksa_a1


def _rp(n) -> str:
    return "Rp " + f"{int(round(n)):,}".replace(",", ".")


def susun(keadaan, id_berkas: str) -> dict:
    """Berkas perkara untuk satu nomor berkas, beserta jejak dan putusan A1."""
    jejak = Jejak(perkara=id_berkas)
    p = Perkakas(keadaan, jejak)

    berkas = p.panggil("ambil_berkas", id=id_berkas)
    hitung = p.panggil("hitung_pengandaian", id=id_berkas)

    # Tarif resmi dicari sebagai pembanding kedua, di luar tebakan model.
    # Kalau kodenya tidak ada di peraturan, itu dicatat sebagai penolakan
    # alat, bukan dilewati diam diam.
    try:
        tarif = p.panggil(
            "cari_tarif",
            kode=berkas["kelompok_tarif"],
            kelas_rawat=berkas["kelas_rawat"],
            kelas_rs=berkas["kelas_faskes"]
            if berkas["kelas_faskes"] != "FKTP"
            else "D",
            regional=berkas["regional"],
        )
    except GalatAlat:
        tarif = None

    modus = p.panggil(
        "cari_aturan",
        pertanyaan="tarif diagnosis tindakan dinaikkan tanpa bukti pada berkas",
        atas=2,
    )
    batas = p.panggil(
        "cari_aturan", pertanyaan="batas keputusan sistem verifikator", atas=1
    )

    menolong = [b for b in hitung["bukti"] if b["ubah_selisih_rp"] > 0]

    baris = [
        f"Berkas {berkas['id']} pada {berkas['faskes']}, kelompok tarif "
        f"{berkas['kelompok_tarif']}, kelas rawat {berkas['kelas_rawat']}, "
        f"lama rawat {berkas['lama_rawat']} hari.",
        "",
        f"Diajukan {_rp(hitung['total_diajukan_rp'])}, "
        f"didukung bukti {_rp(hitung['total_didukung_bukti_rp'])}, "
        f"selisih {_rp(hitung['selisih_rp'])}.",
    ]

    if tarif is not None:
        baris.append(
            f"Tarif resmi kelompok ini pada konteks tersebut {_rp(tarif['tarif_rp'])}, "
            f"menurut {tarif['sumber']}."
        )

    if menolong:
        baris.append("")
        baris.append("Bukti yang bila dilampirkan menurunkan selisih:")
        for b in menolong:
            baris.append(f"  {b['kode']}, turun {_rp(b['ubah_selisih_rp'])}")
    else:
        baris.append("")
        baris.append(
            "Tidak ada pemeriksaan tunggal yang menurunkan selisih berkas ini. "
            "Yang dibutuhkan keterangan klinis."
        )

    baris.append("")
    baris.append("Modus yang paling dekat dengan bentuk selisih ini:")
    for e in modus["entri"]:
        baris.append(f"  {e['kode']} {e['judul']}, jangkauan NALAR {e['jangkauan']}.")

    baris.append("")
    baris.append(batas["entri"][0]["isi"])

    teks = "\n".join(baris)
    # Hasil alatnya ikut dikembalikan, bukan dibuang sesudah dipakai. Berkas
    # perkara ini garis dasar yang harus dikalahkan agen, jadi ia harus bisa
    # diperiksa dengan pemeriksaan yang sama, dan pemeriksaan dalam menuntut
    # fakta alatnya, bukan sekadar himpunan angkanya.
    hasil = [x for x in (berkas, hitung, tarif, modus, batas) if x is not None]
    return {
        "id": id_berkas,
        "teks": teks,
        "jejak": jejak,
        "a1": periksa_a1(teks, jejak),
        "ringkas_jejak": jejak.ringkas(),
        "hasil": hasil,
        "fakta": kumpulkan_fakta(hasil),
    }
