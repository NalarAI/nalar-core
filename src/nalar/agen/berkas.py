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
from .dalam import IKATAN, kumpulkan_fakta, periksa_cepat, periksa_dalam
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

Isian yang tersedia. Tiap nama medan pada balasan alat boleh dipakai apa
adanya, jadi kalau balasan alat menulis "selisih_rp": "{selisih_rp}", kamu
tinggal menyalin {selisih_rp} ke dalam kalimatmu.

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
  Minta paling banyak tiga entri, dan sebut yang paling dekat saja.

Tulis ringkas. Jangan menambah kalimat penutup yang tidak berisi keterangan."""


# Isian yang seharusnya berdiri sesudah tiap sebutan. Diambil dari tabel
# yang sama yang dipakai memeriksanya, jadi keterangan cacat dan pemeriksaan
# cacat tidak bisa berbeda pendapat.
_ISIAN_BENAR = {frasa: medan[0] for frasa, medan in IKATAN}

# Medan yang benar benar punya nama isian sendiri. Yang di luar daftar ini
# muncul di dalam daftar butir, dan menampilkan namanya di sana akan
# mengundang model menulis {ubah_selisih_rp}, isian yang tidak pernah ada.
MEDAN_ISIAN = {
    "tarif_ditagihkan_rp",
    "tarif_didukung_bukti_rp",
    "barang_ditagihkan_rp",
    "barang_wajar_rp",
    "total_diajukan_rp",
    "total_didukung_bukti_rp",
    "selisih_tarif_rp",
    "selisih_barang_rp",
    "selisih_rp",
    "selisih_mentah_rp",
    "tagihan_barang_rp",
    "tarif_rp",
}


def sebut_cacat(cacat: list[dict]) -> str:
    """Ubah daftar cacat jadi kalimat yang bisa ditindaklanjuti model.

    Menyodorkan bentuk mentahnya tidak menolong. Model 4B membaca
    {"jenis": "ikatan", "nama": "selisih", "disebut": 489690.0} lalu menulis
    ulang seluruh berkas dari awal, bukan memperbaiki yang satu itu. Yang
    menolong kalimat yang menyebut apa yang salah dan apa yang seharusnya
    ditulis sebagai gantinya.
    """
    baris = []
    for c in cacat[:6]:
        j = c.get("jenis")
        if j == "a1":
            baris.append(
                "Kamu mengetik angka sendiri: "
                + ", ".join(
                    f"{x:,.0f}".replace(",", ".") for x in c.get("angka", [])[:4]
                )
                + ". Jangan ketik angka. Pakai nama isian di dalam kurung kurawal."
            )
        elif j == "ikatan":
            benar = _ISIAN_BENAR.get(c["nama"])
            baris.append(
                f"Sesudah kata '{c['nama']}' kamu menulis angka, dan angka itu "
                "bukan miliknya." + (f" Ganti dengan {{{benar}}}." if benar else "")
            )
        elif j == "arah":
            baris.append(
                f"Kode {c['kode']} kamu daftarkan sebagai penurun selisih, "
                "padahal ia menaikkan. Buang dari daftar itu."
            )
        elif j == "bagian":
            baris.append(f"Bagian '{c['nama']}' belum ada di berkas perkara.")
        elif j == "kutipan":
            baris.append(
                f"Kamu mengutip {c['sebut']} padahal alat tidak pernah "
                "mengembalikannya. Buang kutipan itu."
            )
        elif j == "kode":
            baris.append(f"Kode {c['kode']} tidak ada pada hasil alat mana pun. Buang.")
        elif j == "banding":
            baris.append(
                f"Perbandingan '{c['kata']}' pada kalimat ini urutannya terbalik: "
                f"{c['kalimat']}"
            )
    return "\n".join(f"- {b}" for b in baris)


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
        "content": json.dumps(_tanpa_rupiah(hasil), ensure_ascii=False, default=str),
    }


def _tanpa_rupiah(hasil):
    """Ganti tiap besaran rupiah dengan nama isiannya sebelum model melihatnya.

    Selama angkanya berdiri di dalam balasan alat, model akan menyalinnya,
    dan penjaga A1 memang mengizinkannya karena angka itu berasal dari alat.
    Yang tidak diizinkan siapa pun terjadi sesudahnya: angka yang sah itu
    dilekatkan pada nama yang salah, dan sebelas dari empat belas berkas
    susunan agen jatuh persis di situ.

    Maka angkanya tidak ditunjukkan sama sekali. Yang ditunjukkan namanya,
    di tempat angkanya, jadi menyalin yang terlihat justru menghasilkan
    kalimat yang benar. Besaran per butir bukti dibiarkan apa adanya, karena
    dari situ model memilih bukti mana yang pantas disebut.
    """
    if isinstance(hasil, list):
        return [_tanpa_rupiah(x) for x in hasil]
    if not isinstance(hasil, dict):
        return hasil
    keluar = {}
    for k, v in hasil.items():
        besaran = k.endswith("_rp") and isinstance(v, (int, float))
        if besaran and not isinstance(v, bool):
            # Besaran per butir tidak punya nama isian sendiri, dan memang
            # tidak perlu punya. Yang dipakai menyebutnya {bukti_menolong},
            # dan yang ditinggalkan di sini cuma arahnya, karena dari arah
            # itulah model memilih butir mana yang pantas disebut.
            keluar[k] = f"{{{k}}}" if k in MEDAN_ISIAN else _arah(v)
        else:
            keluar[k] = _tanpa_rupiah(v)
    return keluar


def _arah(v) -> str:
    return "menurunkan selisih" if v > 0 else "menaikkan selisih"


def jalankan(
    keadaan,
    id_berkas: str,
    penutur: Penutur | None = None,
    anggaran: Anggaran | None = None,
    gerbang: Gerbang | None = None,
    dalam: bool = False,
    n_perbaikan: int = 1,
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
    n_diperbaiki = 0
    pesan: list[dict] = []

    if not penutur.hidup():
        sebab_mundur = "tidak ada model bahasa yang menyala"
    else:
        pesan[:] = [
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

    # Satu kesempatan memperbaiki, dan cuma satu. Model yang tidak bisa
    # memperbaiki dengan cacatnya disebutkan tidak akan bisa pada kesempatan
    # ketiga, dan tiap kesempatan tambahan berharga satu giliran penuh.
    #
    # Yang diberikan bukan bentuk mentah cacatnya melainkan kalimat yang
    # menyebut apa yang salah, karena bentuk mentah membuat model menulis
    # ulang seluruh berkas alih alih memperbaiki satu tempat.
    if teks and not sebab_mundur and n_perbaikan > 0:
        for _ in range(n_perbaikan):
            tersedia = susun_isian(hasil_per_alat)
            jadi, hilang = isi_lubang(teks, tersedia)
            if hilang:
                masalah = (
                    "Isian yang kamu pakai tidak ada: "
                    + ", ".join(sorted(set(hilang)))
                    + ". Yang ada cuma ini, pakai salah satunya: "
                    + " ".join("{" + n + "}" for n in sorted(tersedia))
                )
            else:
                h = periksa_dalam(jadi, jejak, fakta, hasil_alat)
                if h["lulus"]:
                    break
                masalah = sebut_cacat(h["cacat"])
            try:
                pesan.append({"role": "assistant", "content": teks})
                pesan.append(
                    {
                        "role": "user",
                        "content": (
                            "Berkas perkaranya belum bisa dikirim. Yang salah:\n"
                            + masalah
                            + "\n\nTulis ulang berkas perkaranya dengan itu "
                            "diperbaiki. Jangan ubah yang lain."
                        ),
                    }
                )
                b = penutur.balas(pesan, p.perkakas.skema())
                p.catat_balasan(b)
                if b.teks:
                    teks = b.teks
                    n_diperbaiki += 1
            except (RantaiDiputus, GalatPenutur):
                break

    if teks and not sebab_mundur:
        # Angkanya dipasang di sini, bukan diketik model. Alasannya panjang
        # dan ada di isian.py: percobaan pertama dengan model sungguhan
        # jatuh di penjaga A1 karena model menghitung sendiri selisihnya.
        teks, hilang = isi_lubang(teks, susun_isian(hasil_per_alat))
        if hilang:
            sebab_mundur = f"isian yang tidak ada dipakai agen: {sorted(set(hilang))}"
        else:
            # Kedua pemeriksaan jalan di sini, bukan cuma yang cepat. Yang
            # dalam berharga satu milidetik, dan tanpa ia sebelas dari empat
            # belas berkas lolos membawa angka yang sah pada nama yang salah.
            cepat = periksa_cepat(teks, jejak, fakta)
            saring = periksa_dalam(teks, jejak, fakta, hasil_alat)
            if not saring["lulus"]:
                jenis = sorted({c["jenis"] for c in saring["cacat"]})
                sebab_mundur = f"berkas susunan agen jatuh di saringan: {jenis}"
                cepat = {**cepat, "cacat": saring["cacat"]}
    elif not sebab_mundur:
        sebab_mundur = "agen berhenti tanpa menulis apa pun"

    if sebab_mundur:
        keluar = {
            "id": id_berkas,
            "teks": dasar["teks"],
            "sumber": "aturan",
            "sebab_mundur": sebab_mundur,
            "cacat": cepat["cacat"],
            "n_diperbaiki": n_diperbaiki,
            # A1 atas naskah yang benar benar keluar, bukan atas naskah yang
            # ditolak. Yang keluar di sini versi aturan, dan A1 versi aturan
            # itu yang berlaku. Tanpa medan ini yang memanggil harus menebak,
            # dan tebakannya akan menyebut berkas bersih sebagai bercacat.
            "a1": dasar["a1"],
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
        "n_diperbaiki": n_diperbaiki,
        "a1": cepat["a1"],
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
