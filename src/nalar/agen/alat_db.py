"""Alat yang sama, tapi isinya dibaca dari basis data bukan dari memori.

Alat agen membaca keadaan data di dalam memori: seluruh episode ditambah
penebak terlatih. Itu menuntut proses Python besar, dan proses sebesar itu
tidak muat di fungsi tanpa peladen. Akibatnya Agen Berkas cuma bisa jalan di
mesin yang menyalakan peladen sendiri.

Berkas ini melepaskan ikatan itu untuk empat dari lima alat. Yang diwarisi
seluruh kerangkanya: skema alat, pemeriksaan argumen, pencatatan jejak,
penolakan yang terekam. Yang diganti cuma dari mana angkanya diambil.

Satu alat tidak bisa ikut, dan itu ditulis apa adanya. `skor_ulang`
menghitung ulang selisih seandainya bukti tambahan ada, dan yang
menghitungnya penebak tarif. Penebak tidak muat di sini, jadi alatnya
menolak dengan keterangan, bukan menjawab angka karangan. Agen Berkas tidak
pernah memanggilnya, jadi penolakan itu tidak menghalangi apa pun.

Yang perlu dijaga di sini satu hal, dan ia halus. Jawaban tiap alat harus
sama persis dengan jawaban versi memori, sampai ke medan yang tidak dipakai
model sekalipun. Begitu jawabannya berbeda, yang dilihat model berbeda, dan
seluruh angka yang sudah diukur pada lima ratus berkas tidak berlaku lagi.
Itu sebabnya tabelnya menyimpan keluaran alat apa adanya, bukan bentuk yang
lebih rapi.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from ..pembulatan import bulat_berkas
from .alat import GalatAlat, Perkakas


class SumberBasisData:
    """Pembaca tabel lewat PostgREST, memakai pustaka bawaan saja.

    Tanpa ketergantungan tambahan supaya bisa dipakai di fungsi tanpa
    peladen, tempat tiap megabita paket menambah lama pemanggilan dingin.
    """

    def __init__(self, url: str, kunci: str, skema: str = "nalar"):
        self.url = url.rstrip("/")
        self.kunci = kunci
        self.skema = skema

    def baca(self, jalur: str) -> list[dict]:
        r = urllib.request.Request(
            f"{self.url}/rest/v1/{jalur}",
            headers={
                "apikey": self.kunci,
                "Authorization": f"Bearer {self.kunci}",
                "Accept-Profile": self.skema,
                "User-Agent": "nalar/1.0",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(r, timeout=15) as h:
                return json.loads(h.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise GalatAlat(f"basis data tidak menjawab: {e}") from None

    def satu(self, jalur: str) -> dict | None:
        d = self.baca(jalur)
        return d[0] if d else None


class PerkakasBasisData(Perkakas):
    """Perkakas yang sama, dengan empat alat dialihkan ke basis data."""

    # Alat yang pasti ditolak jalur ini tidak ditawarkan ke model. Ia tetap
    # ada dan tetap menolak dengan keterangan, karena yang memanggilnya
    # langsung berhak tahu sebabnya. Yang berubah cuma daftar yang dilihat
    # model.
    #
    # Sebabnya diukur, bukan dikira. Pada berkas K00001283 di situs yang
    # sudah terpasang, model memanggil skor_ulang, penolakannya memakan satu
    # giliran, lalu model menulis berkas yang seluruh angkanya "tidak
    # tersedia" karena hitung_pengandaian tidak pernah ia panggil. Alat yang
    # ditawarkan tapi tidak bisa dilayani menyesatkan, bukan sekadar sia sia.
    TAK_DITAWARKAN = ("skor_ulang",)

    def __init__(self, sumber: SumberBasisData, jejak):
        self.sumber = sumber
        super().__init__(None, jejak)

    def skema(self) -> list[dict]:
        return [
            a.skema() for n, a in self.daftar.items() if n not in self.TAK_DITAWARKAN
        ]

    # -- alat yang dialihkan ------------------------------------------------

    def _ambil_berkas(self, id: str) -> dict:
        # Tabelnya menyimpan keluaran alat ini apa adanya, jadi yang perlu
        # dikerjakan cuma membuang medan waktu tulis yang bukan bagian
        # jawabannya.
        r = self.sumber.satu(f"berkas?id=eq.{urllib.parse.quote(id)}&select=*")
        if not r:
            raise GalatAlat(f"berkas {id} tidak ada")
        return {k: v for k, v in r.items() if k != "dibuat_pada"}

    def _hitung_pengandaian(self, id: str) -> dict:
        k = self.sumber.satu(
            f"klaim?id=eq.{urllib.parse.quote(id)}"
            "&select=tarif_ditagihkan_rp,tarif_didukung_bukti_rp,"
            "barang_ditagihkan_rp,barang_wajar_rp"
        )
        if not k:
            raise GalatAlat(f"berkas {id} tidak ada")
        # Empat angka di tabel sudah hasil pembulatan bersama, dan
        # membulatkannya lagi tidak menggesernya. Yang dipanggil tetap fungsi
        # yang sama supaya medan turunannya disusun dengan aturan yang sama,
        # bukan dihitung ulang di sini dengan aturan yang mirip.
        n = bulat_berkas(
            k["tarif_ditagihkan_rp"],
            k["tarif_didukung_bukti_rp"],
            k["barang_ditagihkan_rp"],
            k["barang_wajar_rp"],
        )
        bukti = self.sumber.baca(
            f"pengandaian?klaim_id=eq.{urllib.parse.quote(id)}"
            "&select=kode,ubah_selisih_rp&order=urutan"
        )
        return {
            "id": id,
            **n,
            "bukti": [
                {"kode": b["kode"], "ubah_selisih_rp": int(b["ubah_selisih_rp"])}
                for b in bukti
            ],
        }

    def _cari_tarif(
        self,
        kode: str,
        kelas_rawat: int,
        kelas_rs: str,
        regional: int,
        kepemilikan: str = "PEMERINTAH",
    ) -> dict:
        r = self.sumber.satu(
            f"tarif?kode=eq.{urllib.parse.quote(kode)}&regional=eq.{int(regional)}"
            f"&kelas_rs=eq.{urllib.parse.quote(kelas_rs)}"
            f"&kepemilikan=eq.{urllib.parse.quote(kepemilikan)}"
            "&select=tarif_kelas1,tarif_kelas2,tarif_kelas3"
        )
        if not r:
            raise GalatAlat(f"kode {kode} tidak ada pada tabel tarif resmi")
        kolom = {1: "tarif_kelas1", 2: "tarif_kelas2", 3: "tarif_kelas3"}
        n = r.get(kolom.get(int(kelas_rawat), ""))
        if n is None:
            raise GalatAlat(f"kelas rawat {kelas_rawat} tidak dikenal")
        return {
            "kode": kode,
            "kelas_rawat": kelas_rawat,
            "kelas_rs": kelas_rs,
            "regional": regional,
            "kepemilikan": kepemilikan,
            "tarif_rp": int(n),
            "sumber": "Lampiran Permenkes 3 Tahun 2023",
        }

    def _skor_ulang(self, id: str, bukti_tambahan: list) -> dict:
        raise GalatAlat(
            "penilaian ulang menuntut penebak tarif, dan penebak itu tidak "
            "tersedia pada jalur ini. Pakai daftar pengandaian yang sudah "
            "dihitung, atau jalankan lewat peladen."
        )
