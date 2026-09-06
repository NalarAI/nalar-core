"""Agen Berkas: menyusun berkas perkara untuk satu nomor klaim.

Pekerjaan yang digantikannya bukan memutuskan, melainkan mengumpulkan.
Verifikator hari ini menerima nomor berkas dan selisih rupiah, lalu harus
sendiri membuka rekam medis, mencari pasal tarif yang berlaku, dan menyusun
kalimat untuk faskes. Yang paling banyak memakan waktunya bagian itu, dan
bagian itu yang tidak menuntut penilaian siapa pun.

Yang tidak dikerjakan agen ini, dan tidak akan pernah: menentukan sebuah
berkas ditandai atau tidak. Itu tetap milik penebak tarif dan ambang
konformal, tetap deterministik, dan tetap bisa dijalankan ulang tanpa model
bahasa sama sekali.

Ada tiga jalan keluar, dan ketiganya sah.

Model menyala, hasilnya lolos saringan, dan keyakinannya di atas ambang
tera: yang keluar berkas perkara susunan agen, berkeadaan layak kirim.

Model menyala, hasilnya lolos saringan, keyakinannya di bawah ambang: yang
keluar berkas perkara susunan agen, berkeadaan perlu dibaca manusia dulu.

Model mati, rantainya diputus penyelia, atau hasilnya jatuh di saringan:
yang keluar berkas perkara versi aturan. Ini bukan kegagalan yang perlu
diberitahukan ke faskes. Berkas perkara versi aturan memang keluaran yang
sah, dan sejak tahap satu ia yang jadi garis dasarnya.
"""

from __future__ import annotations

import json

from .alat import Perkakas
from .dalam import kumpulkan_fakta, periksa_cepat, periksa_dalam
from .gerbang import Gerbang, skor_keyakinan
from .isian import isi_lubang, susun_isian
from .jejak import Jejak
from .penutur import GalatPenutur, Penutur, penutur_baku
from .penyelia import Anggaran, Penyelia, RantaiDiputus
from .perkara import susun

ARAHAN = """Kamu penyusun berkas perkara untuk verifikator klaim BPJS Kesehatan.

Tugasmu mengumpulkan, bukan memutuskan. Kamu tidak boleh menyatakan sebuah
berkas curang, wajar, atau layak dibayar. Yang menilai sudah menilai.

Aturan yang tidak boleh dilanggar:

1. JANGAN MENGETIK ANGKA SAMA SEKALI. Tulis nama isiannya di dalam kurung
   kurawal, dan sistem yang menggantinya dengan angka dari alat. Kamu tidak
   pernah perlu menjumlahkan, mengurangkan, atau membulatkan apa pun.
2. Jangan mengarang kode pemeriksaan, kelompok tarif, atau nomor peraturan.
3. Kalau alat menolak, tulis apa adanya bahwa keterangan itu tidak tersedia.

Isian yang tersedia:

  {berkas} {faskes} {cbg} {kelas_rawat} {lama_rawat}
  {diajukan} {didukung} {selisih}
  {tarif_resmi}      hanya kalau cari_tarif berhasil
  {bukti_menolong}   daftar bukti yang menurunkan selisih, sudah tersusun
  {modus}            daftar modus dari cari_aturan, sudah tersusun

Contoh satu kalimat yang benar:

  Berkas {berkas} pada {faskes} diajukan {diajukan}, didukung bukti
  {didukung}, selisih {selisih}.

Panggil alat sampai kamu punya cukup keterangan, lalu tulis berkas perkara
dalam bahasa Indonesia, dengan bagian berikut dan urutan ini:

- Satu paragraf pembuka: nomor berkas, fasilitas kesehatan, kelompok tarif.
- Nilai yang diajukan, nilai yang didukung bukti, dan selisihnya.
- Bukti yang bila dilampirkan menurunkan selisih, memakai {bukti_menolong}.
- Modus yang paling dekat dengan bentuk selisih ini, memakai {modus}.

Tulis ringkas. Jangan menambah kalimat penutup yang tidak berisi keterangan."""


def _pesan_alat(nama: str, nomor: str, hasil) -> dict:
    """Balasan alat dalam bentuk yang diterima peladen tata cara OpenAI.

    Nomor pemanggilannya ikut dikirim. Peladen menolak balasan alat yang
    tidak bisa dipasangkan ke permintaan mana, dan penolakannya benar: model
    yang tidak tahu jawaban ini milik pertanyaan yang mana akan menjawab
    berdasar hasil alat yang salah.
    """
    return {
        "role": "tool",
        "name": nama,
        "tool_call_id": nomor,
        "content": json.dumps(hasil, ensure_ascii=False, default=str),
    }


def jalankan(
    keadaan,
    id_berkas: str,
    penutur: Penutur | None = None,
    anggaran: Anggaran | None = None,
    gerbang: Gerbang | None = None,
    dalam: bool = False,
) -> dict:
    """Berkas perkara untuk satu nomor, beserta jejak, biaya, dan keadaannya.

    Argumen dalam menyalakan pemeriksaan lengkap. Itu dipakai ketika menera
    gerbang, bukan ketika melayani berkas sungguhan, karena harganya justru
    yang jadi alasan gerbangnya ada.
    """
    dasar = susun(keadaan, id_berkas)
    n_kata_dasar = len(dasar["teks"].split())

    i = keadaan.indeks_dari_id(id_berkas)
    menahan = bool(keadaan.tahan[i])

    penutur = penutur if penutur is not None else penutur_baku()
    jejak = Jejak(perkara=id_berkas)
    p = Penyelia(Perkakas(keadaan, jejak), anggaran or Anggaran())

    hasil_alat: list[dict] = []
    hasil_per_alat: dict[str, dict] = {}
    teks = ""
    sebab_mundur = ""

    if not penutur.hidup():
        sebab_mundur = "tidak ada model bahasa yang menyala"
    else:
        pesan = [
            {"role": "system", "content": ARAHAN},
            {
                "role": "user",
                "content": f"Susun berkas perkara untuk nomor berkas {id_berkas}.",
            },
        ]
        try:
            while True:
                b = penutur.balas(pesan, p.perkakas.skema())
                p.catat_balasan(b)
                if not b.memanggil:
                    teks = b.teks
                    break
                nomor = [
                    c.get("id") or f"p{p.n_panggilan + k}"
                    for k, c in enumerate(b.panggilan)
                ]
                pesan.append(
                    {
                        "role": "assistant",
                        "content": b.teks,
                        "tool_calls": [
                            {
                                "id": nomor[k],
                                "type": "function",
                                "function": {
                                    "name": c["nama"],
                                    "arguments": json.dumps(
                                        c["argumen"], ensure_ascii=False
                                    ),
                                },
                            }
                            for k, c in enumerate(b.panggilan)
                        ],
                    }
                )
                for k, c in enumerate(b.panggilan):
                    jawab = p.panggil_lunak(c["nama"], **c["argumen"])
                    if jawab["berhasil"]:
                        hasil_alat.append(jawab["hasil"])
                        hasil_per_alat[c["nama"]] = jawab["hasil"]
                        pesan.append(_pesan_alat(c["nama"], nomor[k], jawab["hasil"]))
                    else:
                        pesan.append(
                            _pesan_alat(
                                c["nama"], nomor[k], {"ditolak": jawab["tolakan"]}
                            )
                        )
        except RantaiDiputus as e:
            sebab_mundur = f"rantai diputus penyelia: {e.sebab}"
        except GalatPenutur as e:
            sebab_mundur = f"model bahasa tidak menjawab: {e}"

    fakta = kumpulkan_fakta(hasil_alat)
    cepat = {"lulus": False, "cacat": [], "a1": {}}

    if teks and not sebab_mundur:
        # Angkanya dipasang di sini, bukan diketik model. Alasannya panjang
        # dan ada di isian.py: percobaan pertama dengan model sungguhan
        # jatuh di penjaga A1 karena model menghitung sendiri selisihnya.
        teks, hilang = isi_lubang(teks, susun_isian(hasil_per_alat))
        if hilang:
            sebab_mundur = f"isian yang tidak ada dipakai agen: {sorted(set(hilang))}"
        else:
            cepat = periksa_cepat(teks, jejak, fakta)
            if not cepat["lulus"]:
                sebab_mundur = "berkas susunan agen jatuh di saringan"
    elif not sebab_mundur:
        sebab_mundur = "agen berhenti tanpa menulis apa pun"

    if sebab_mundur:
        keluar = {
            "id": id_berkas,
            "teks": dasar["teks"],
            "sumber": "aturan",
            "sebab_mundur": sebab_mundur,
            "cacat": cepat["cacat"],
            "keadaan": "layak_kirim",
            "skor": 1.0,
            "jejak": dasar["jejak"],
            "ringkas_jejak": dasar["ringkas_jejak"],
            "penyelia": p.ringkas(),
        }
        if dalam:
            keluar["dalam"] = periksa_dalam(
                dasar["teks"], dasar["jejak"], fakta_dasar(dasar), hasil_dasar(dasar)
            )
        return keluar

    skor = skor_keyakinan(
        jejak.ringkas(), cepat["a1"], len(teks.split()), n_kata_dasar, menahan
    )
    keluar = {
        "id": id_berkas,
        "teks": teks,
        "sumber": "agen",
        "sebab_mundur": "",
        "cacat": [],
        "keadaan": gerbang.putuskan(skor) if gerbang else "belum_ada_gerbang",
        "skor": round(skor, 4),
        "jejak": jejak,
        "ringkas_jejak": jejak.ringkas(),
        "penyelia": p.ringkas(),
    }
    if dalam:
        keluar["dalam"] = periksa_dalam(teks, jejak, fakta, hasil_alat)
    return keluar


def fakta_dasar(dasar: dict) -> dict:
    """Fakta versi aturan, disusun ulang dari jejaknya sendiri.

    Berkas perkara versi aturan memanggil alatnya lewat jejak terpisah, jadi
    fakta agen tidak berlaku atasnya. Ketika yang diperiksa versi aturan,
    yang dipakai fakta ini.
    """
    return dasar.get("fakta") or {"nilai": {}, "daftar": {}}


def hasil_dasar(dasar: dict) -> list[dict]:
    return dasar.get("hasil") or []
