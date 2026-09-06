"""Agen Lawan: model bahasa merancang siasat penghindaran, bukan menebak anomali.

Ini yang menyerang kegagalan T6. Target itu berbunyi keuntungan maksimum
pelaku yang beradaptasi harus turun setengah, dan pada detektor yang benar
benar dikirim ia turun 25,6 persen. Lebih buruk lagi, pelaku yang menyebar
serangannya meloloskan lebih banyak uang daripada yang serakah. Sistem kami
membuat menyebar lebih menguntungkan, dan itu kebalikan dari yang seharusnya
dilakukan pengawasan.

Ketiga pelaku yang dipakai mengukur itu kami tulis sendiri, dan ketiganya
memakai satu modus saja. Yang tidak bisa dijawab pengujian seperti itu satu
pertanyaan: apakah ada siasat yang tidak terpikir oleh kami. Menjawabnya
dengan menulis pelaku keempat buatan sendiri hanya memindahkan batasnya.

Yang dipinjam dari LLM-DAS: peran model bahasa diputar dari pengolah data
menjadi perancang algoritma. Model membaca uraian cara kerja detektor,
menunjuk kelemahan logikanya, lalu menyusun siasat yang mengeksploitasi
kelemahan itu. Yang diperlihatkan ke model hanya rancangan, tidak satu pun
angka dari berkas, jadi kerahasiaan berkas tetap terjaga sekalipun model
berjalan di mesin yang berbeda.

Dua penjagaan yang tidak boleh dilepas.

Model tidak menjalankan kode. Ia menyusun siasat sebagai data, dan yang
menjalankan juru baca deterministik di siasat.py. Alasannya ada di sana.

Siasat baru harus menang pada himpunan yang tidak dipakai menemukannya.
Ruang siasatnya kecil, dan mencari di ruang kecil sampai menemukan yang
menang di tempat yang sama dengan tempat mencarinya bukan penemuan, itu
pencocokan berlebihan yang diberi nama bagus.

Keluarannya bukan keputusan, melainkan kasus uji. Tidak ada satu pun jalur di
sini yang menyentuh penilaian berkas sungguhan.
"""

from __future__ import annotations

import itertools
import json

from .alat import Alat, GalatAlat, Perkakas
from .arena import BAKU, garis_dasar
from .arena import jalankan as adu
from .jejak import Jejak
from .penutur import GalatPenutur, Penutur, penutur_baku
from .penyelia import Anggaran, Penyelia, RantaiDiputus
from .siasat import GalatSiasat, perbendaharaan, periksa

URAIAN = """Cara kerja detektor yang kamu hadapi, apa adanya.

Detektor tidak pernah melihat satu pun contoh kecurangan berlabel. Ia menebak
berapa tarif yang wajar bagi sebuah berkas, lalu menyebut selisih antara yang
ditagihkan dan tebakannya sebagai temuan.

Penciri yang dipakai menebak: diagnosis utama, prosedur, obat, pemeriksaan
penunjang, bahan habis pakai, lama rawat, kelas rawat, kelas fasilitas
kesehatan, wilayah, dan status daerah tertinggal.

Diagnosis sekunder sengaja dibuang dari penciri. Itu keputusan sadar:
menambah diagnosis sekunder menaikkan kelompok tarif, dan kalau ia ikut jadi
penciri maka tebakannya ikut naik dan selisihnya menghilang.

Akibat yang tidak sengaja dari daftar itu: lama rawat, kelas rawat, dan
pemeriksaan penunjang ikut jadi penciri. Menaikkan ketiganya menaikkan pula
tarif yang dianggap wajar.

Ambang penandaan dikalibrasi terpisah untuk tiap kelompok sebaya, memakai
kalibrasi konformal terbelah, dengan janji bahwa paling banyak alpha bagian
dari berkas yang sebenarnya wajar boleh ikut tertandai. Kelompok yang
pembandingnya kurang dari tiga tidak diberi ambang sama sekali. Sistem
menahan diri di sana, dan tidak menandai apa pun.

Berkas yang tertandai belum tentu diperiksa. Antrean pemeriksaan menolak
berkas yang selisihnya lebih kecil daripada ongkos memeriksanya, karena
memeriksanya bukan penghematan.

Tugasmu menyusun siasat yang mengeluarkan uang sebanyak banyaknya tanpa
tertangkap. Yang dinilai bukan berapa yang kamu ambil, melainkan berapa yang
lolos."""

ARAHAN = """Kamu perancang serangan untuk menguji ketahanan detektor klaim.

Ini pengujian ketahanan atas sistem kami sendiri, pada data buatan. Yang kamu
temukan jadi kasus uji untuk menambal detektornya, bukan nasihat untuk siapa
pun.

Kamu tidak menulis program. Kamu menyusun siasat sebagai satu obyek JSON,
memakai perbendaharaan yang diberikan. Siasat di luar perbendaharaan ditolak.

Bentuk siasat:

  {"nama": "...",
   "sasaran": {"jenis": "...", ...parameter},
   "gerakan": [{"jenis": "...", ...parameter}],
   "pilihan": {"jenis": "...", ...parameter}}

Parameter gerakan yang tidak kamu sebut dibiarkan terbuka, dan pelaku akan
mencoba seluruh rentangnya lalu memilih yang terbaik menurut cara memilih
yang kamu tetapkan. Menyebutnya berarti mengunci.

Panggil coba_siasat untuk menguji satu siasat. Hasil yang sudah ada dan
garis dasarnya diberikan kepadamu tiap giliran, jadi tidak perlu diminta.

Bacalah uraian detektor, tunjuk satu kelemahan logikanya, lalu susun siasat
yang mengeksploitasi kelemahan itu. Satu siasat tiap giliran. Jangan
mengulang siasat yang sudah dicoba."""


def tanda_tangan(s: dict) -> str:
    """Sidik siasat, supaya yang sama tidak dihitung dua kali."""
    return json.dumps(
        {
            "sasaran": s.get("sasaran") or {"jenis": "semua_rawat_inap"},
            "gerakan": s.get("gerakan"),
            "pilihan": s.get("pilihan") or {"jenis": "paling_untung"},
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def _nilai(h: dict, dasar: dict) -> None:
    """Tandai apakah satu siasat mengalahkan garis dasar, pada dua ukuran.

    Ukuran pertama uang yang lolos seluruhnya. Ukuran kedua yang terbesar di
    antara yang lolos, dan itu ukuran T6 yang sebenarnya: berapa besar
    keuntungan yang masih bisa diambil pelaku tanpa tertangkap.

    Dua ukuran, bukan satu, karena siasat yang menyasar sebagian kecil berkas
    tidak akan pernah menang pada jumlah. Menuntutnya menang pada jumlah
    berarti menutup mata terhadap lubang yang kecil tapi dalam, dan lubang
    yang kecil tapi dalam persis yang dicari pelaku yang sabar.
    """
    h["lebih_jumlah_rp"] = h.get("lolos_rp", 0) - dasar["lolos_terbaik_rp"]
    h["lebih_maks_rp"] = h.get("maks_lolos_rp", 0) - dasar["maks_lolos_terbaik_rp"]
    h["menang_jumlah"] = bool(h.get("lolos_rp", 0) > 0 and h["lebih_jumlah_rp"] > 0)
    h["menang_maks"] = bool(h.get("lolos_rp", 0) > 0 and h["lebih_maks_rp"] > 0)
    h["mengalahkan_garis_dasar"] = h["menang_jumlah"] or h["menang_maks"]


class Gelanggang:
    """Himpunan berkas, detektor, dan papan skornya. Dipakai bersama."""

    def __init__(self, episodes, idx_temu, idx_sahih, penskor, ambang, tahan, **kw):
        self.episodes = episodes
        self.idx_temu = idx_temu
        self.idx_sahih = idx_sahih
        self.penskor = penskor
        self.ambang = ambang
        self.tahan = tahan
        self.kw = kw
        self.papan: list[dict] = []
        self.terlihat: set[str] = {tanda_tangan(s) for s in BAKU}

        self.dasar_temu = garis_dasar(episodes, idx_temu, penskor, ambang, tahan, **kw)
        self.dasar_sahih = garis_dasar(
            episodes, idx_sahih, penskor, ambang, tahan, **kw
        )

    def coba(self, siasat: dict, catat: bool = True) -> dict:
        """Jalankan satu siasat pada himpunan penemuan."""
        periksa(siasat)
        h = adu(
            self.episodes,
            self.idx_temu,
            self.penskor,
            self.ambang,
            self.tahan,
            siasat,
            **self.kw,
        )
        _nilai(h, self.dasar_temu)
        if catat:
            self.papan.append({"siasat": siasat, "temu": h})
            self.terlihat.add(tanda_tangan(siasat))
        return h

    def sahihkan(self, siasat: dict) -> dict:
        """Jalankan ulang pada himpunan yang tidak dipakai menemukannya."""
        h = adu(
            self.episodes,
            self.idx_sahih,
            self.penskor,
            self.ambang,
            self.tahan,
            siasat,
            **self.kw,
        )
        _nilai(h, self.dasar_sahih)
        return h

    def ringkas_papan(self, atas: int = 8) -> dict:
        urut = sorted(self.papan, key=lambda b: -b["temu"].get("lolos_rp", 0))[:atas]
        return {
            "garis_dasar_terbaik": {
                "nama": self.dasar_temu["nama_terbaik"],
                "lolos_rp": self.dasar_temu["lolos_terbaik_rp"],
            },
            "sudah_dicoba": [
                {
                    "nama": b["siasat"]["nama"],
                    "lolos_rp": b["temu"].get("lolos_rp", 0),
                    "diserang": b["temu"].get("n_diserang", 0),
                    "tertangkap": b["temu"].get("porsi_tertangkap"),
                }
                for b in urut
            ],
        }


# -- pencarian menyeluruh, garis dasar yang harus dikalahkan agen -----------

# Gabungan gerakan yang ditelusuri pencarian. Dibatasi dua gerakan, karena
# tiga gerakan membuat ruangnya membesar tanpa menambah bentuk serangan yang
# benar benar berbeda.
_GERAK_TUNGGAL = [
    [{"jenis": "tambah_diagnosis"}],
    [{"jenis": "perpanjang_rawat"}],
    [{"jenis": "naikkan_kelas"}],
    [{"jenis": "tambah_prosedur"}],
    [{"jenis": "gelembungkan_barang"}],
]
_GERAK_GANDA = [
    [{"jenis": "tambah_diagnosis"}, {"jenis": "lampirkan_lab", "n": 3}],
    [{"jenis": "tambah_diagnosis"}, {"jenis": "gelembungkan_barang", "persen": 30}],
    [{"jenis": "perpanjang_rawat"}, {"jenis": "lampirkan_lab", "n": 2}],
]
_SASARAN = [
    {"jenis": "semua_rawat_inap"},
    {"jenis": "kelompok_menahan_diri"},
    {"jenis": "selisih_awal_kecil", "batas_rp": 1_000_000},
]
_PILIHAN = [
    {"jenis": "paling_untung"},
    {"jenis": "aman_di_bawah_ambang"},
    {"jenis": "kenaikan_skor_terkecil"},
    {"jenis": "untung_di_bawah_porsi_ambang", "porsi": 0.7},
    {"jenis": "untung_dibatasi", "batas_rp": 700_000},
]


def cari_menyeluruh(g: Gelanggang, batas: int = 60) -> list[dict]:
    """Telusuri ruang siasat tanpa model bahasa. Ini garis dasarnya.

    Agen yang tidak mengalahkan pencarian ini tidak sedang merancang apa pun,
    ia hanya menebak lebih lambat. Ruangnya memang kecil dan bisa ditelusuri
    habis, dan itu justru yang membuat perbandingannya jujur.
    """
    keluar = []
    ruang = itertools.product(_SASARAN, _GERAK_TUNGGAL + _GERAK_GANDA, _PILIHAN)
    for k, (s, gerak, p) in enumerate(ruang):
        if k >= batas:
            break
        siasat = {
            "nama": f"cari-{k:02d}",
            "sasaran": s,
            "gerakan": gerak,
            "pilihan": p,
        }
        if tanda_tangan(siasat) in {tanda_tangan(x) for x in BAKU}:
            continue
        keluar.append({"siasat": siasat, "temu": g.coba(siasat, catat=False)})
    return sorted(keluar, key=lambda b: -b["temu"].get("lolos_rp", 0))


# -- agen ------------------------------------------------------------------


class PerkakasLawan(Perkakas):
    """Satu alat saja. Ia membaca dan mengukur, dan tidak mengubah penilaian.

    Versi pertama punya alat kedua untuk membaca papan skor, dan alat itu
    menjatuhkan agennya sendiri. Papan skor sudah diberikan tiap giliran,
    jadi memanggilnya adalah hal pertama yang masuk akal dilakukan model,
    dan karena tiap giliran disusun ulang dari nol ia tidak ingat sudah
    memanggilnya. Penyelia melihat alat yang sama dipanggil berulang dengan
    argumen yang sama, lalu memutus rantainya sebelum satu siasat pun dicoba.
    Yang salah bukan penyelianya, melainkan menyediakan alat untuk keterangan
    yang sudah diberikan.
    """

    def __init__(self, gelanggang: Gelanggang, jejak: Jejak):
        self.g = gelanggang
        super().__init__(None, jejak)

    def _coba_siasat(self, siasat: dict) -> dict:
        try:
            if tanda_tangan(siasat) in self.g.terlihat:
                raise GalatAlat("siasat itu sudah pernah dicoba, susun yang berbeda")
            return self.g.coba(siasat)
        except GalatSiasat as e:
            raise GalatAlat(str(e)) from None

    def _bangun(self) -> list[Alat]:
        return [
            Alat(
                nama="coba_siasat",
                keterangan=(
                    "Jalankan satu siasat pada himpunan penemuan, lalu "
                    "kembalikan berapa yang diambil, berapa yang lolos, dan "
                    "berapa bagian yang tertangkap."
                ),
                parameter={"siasat": {"type": "object"}},
                wajib=("siasat",),
                jalankan=self._coba_siasat,
            ),
        ]


def jalankan(
    gelanggang: Gelanggang,
    penutur: Penutur | None = None,
    anggaran: Anggaran | None = None,
    n_giliran: int = 12,
) -> dict:
    """Suruh model bahasa merancang siasat, lalu ukur yang ditemukannya.

    Yang dikembalikan siasat yang mengalahkan garis dasar pada himpunan
    penemuan sekaligus pada himpunan yang tidak dipakai menemukannya.
    """
    penutur = penutur if penutur is not None else penutur_baku()
    jejak = Jejak(perkara="lawan")
    p = Penyelia(
        PerkakasLawan(gelanggang, jejak),
        anggaran or Anggaran(giliran=n_giliran, panggilan=n_giliran * 2, rp=5000.0),
    )

    if not penutur.hidup():
        return {
            "sumber": "tidak ada model bahasa yang menyala",
            "temuan": [],
            "penyelia": p.ringkas(),
        }

    # Percakapannya tidak ditumpuk. Tiap giliran disusun ulang dari nol:
    # arahan, perbendaharaan, dan papan skor terbaru. Ingatan agen ada di
    # papan skor, bukan di riwayat percakapan.
    #
    # Versi pertama menumpuk seluruh giliran, dan itu salah dua kali. Jendela
    # nalar dua belas ribu token terlampaui di tengah jalan, lalu peladen
    # mengolah ulang seluruh awalan tiap giliran dan satu giliran memakan
    # menit alih alih detik. Dan ingatan yang berupa riwayat tidak bisa
    # diperiksa siapa pun, sedangkan papan skor bisa dicetak dan dibantah.
    sebab = ""
    try:
        while True:
            pesan = [
                {"role": "system", "content": ARAHAN + "\n\n" + URAIAN},
                {
                    "role": "user",
                    "content": (
                        "Perbendaharaan yang tersedia:\n"
                        + json.dumps(perbendaharaan(), ensure_ascii=False)
                        + "\n\nHasil sejauh ini:\n"
                        + json.dumps(gelanggang.ringkas_papan(), ensure_ascii=False)
                        + "\n\nSusun satu siasat yang belum pernah dicoba, "
                        "lalu ujilah dengan coba_siasat."
                    ),
                },
            ]
            b = penutur.balas(pesan, p.perkakas.skema())
            p.catat_balasan(b)
            for c in b.panggilan:
                p.panggil_lunak(c["nama"], **c["argumen"])
    except RantaiDiputus as e:
        sebab = e.sebab
    except GalatPenutur as e:
        sebab = f"model bahasa tidak menjawab: {e}"

    return {
        "sumber": "agen",
        "sebab_berhenti": sebab,
        "dicoba": len(gelanggang.papan),
        "temuan": kumpulkan(gelanggang),
        "penyelia": p.ringkas(),
        "ringkas_jejak": jejak.ringkas(),
    }


def bertahan(temu: dict, sahih: dict) -> bool:
    """Meloloskan lebih banyak uang daripada garis dasar, di kedua himpunan.

    Satu ukuran saja, ditetapkan lebih dulu, dan ukuran itu uang yang lolos.
    Versi pertama menerima dua ukuran, uang yang lolos atau yang terbesar di
    antara yang lolos, dan mana pun yang menang dihitung. Itu memilih ukuran
    sesudah melihat hasilnya, dan dengan cara itu hampir seluruh siasat bisa
    disebut menang pada salah satu ukuran.

    Yang terbesar di antara yang lolos tetap dilaporkan, karena itu ukuran T6
    yang sebenarnya. Ia hanya tidak dipakai menentukan siasat mana yang
    dihitung sebagai temuan.
    """
    return bool(temu.get("menang_jumlah") and sahih.get("menang_jumlah"))


def tak_pernah_tertangkap(temu: dict, sahih: dict) -> bool:
    """Mengambil uang tanpa satu berkas pun tertangkap, di kedua himpunan.

    Ini dilaporkan terpisah, dan tidak dihitung sebagai temuan A4. Siasat
    seperti ini biasanya mengambil lebih sedikit daripada garis dasar, jadi
    ia kalah pada ukuran uang yang lolos. Tapi ia menunjukkan lubang yang
    bentuknya lain: bukan lubang yang dalam, melainkan tempat berteduh yang
    sistemnya sendiri sediakan.
    """
    return bool(
        temu.get("porsi_tertangkap") == 0
        and sahih.get("porsi_tertangkap") == 0
        and temu.get("lolos_rp", 0) > 0
        and sahih.get("lolos_rp", 0) > 0
    )


def sidik_hasil(b: dict) -> tuple:
    """Sidik akibat, bukan sidik tulisan.

    Dua siasat yang tulisannya berbeda tapi akibatnya sama persis adalah satu
    siasat dalam dua pakaian. Yang paling sering terjadi begini: ketika
    sasarannya kelompok yang menahan diri, tidak ada satu pun berkas yang
    bisa tertangkap, sehingga seluruh cara memilih memberi hasil yang sama.
    Menghitungnya tiga akan melaporkan tiga temuan padahal cuma ada satu.
    """
    return (
        b["temu"].get("n_diserang"),
        b["temu"].get("lolos_rp"),
        b["temu"].get("maks_lolos_rp"),
        b["sahih"].get("lolos_rp"),
        b["sahih"].get("maks_lolos_rp"),
    )


def kumpulkan(g: Gelanggang) -> list[dict]:
    """Siasat yang menang di dua himpunan sekaligus, terurut dari yang terbaik.

    Menang di himpunan penemuan saja tidak dihitung. Ruang siasatnya kecil,
    dan mencoba puluhan siasat lalu memilih yang terbaik di tempat yang sama
    dengan tempat mencarinya akan selalu menghasilkan pemenang, termasuk
    ketika tidak ada satu pun siasat yang benar benar lebih baik.
    """
    keluar = []
    for b in g.papan:
        if not b["temu"].get("mengalahkan_garis_dasar"):
            continue
        sahih = g.sahihkan(b["siasat"])
        satu = {"siasat": b["siasat"], "temu": b["temu"], "sahih": sahih}
        if bertahan(b["temu"], sahih):
            keluar.append(satu)
    return sisakan_yang_berbeda(keluar)


def sisakan_yang_berbeda(daftar: list[dict]) -> list[dict]:
    """Buang siasat yang akibatnya sama persis dengan yang sudah ada."""
    keluar, terlihat = [], set()
    for b in sorted(daftar, key=lambda x: -x["sahih"].get("lolos_rp", 0)):
        sidik = sidik_hasil(b)
        if sidik in terlihat:
            continue
        terlihat.add(sidik)
        keluar.append(b)
    return keluar
