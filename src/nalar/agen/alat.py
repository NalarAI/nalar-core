"""Lima alat yang boleh dipanggil agen, beserta pemeriksaan dan pencatatannya.

Tidak ada satu pun di antaranya yang bisa mengubah penilaian. Alat hanya
membaca, menghitung ulang, atau mencari. Penebak tarif, ambang konformal, dan
keputusan menahan diri tetap milik detektor, dan tetap bisa dijalankan tanpa
lapisan ini sama sekali.

Bentuk alat sengaja dibuat lebih dulu daripada agennya. Selama tahap satu,
yang memanggil alat adalah penyusun berkas perkara berbasis aturan, dan
hasilnya jadi garis dasar yang harus dikalahkan agen mana pun nanti.

Argumen diperiksa sendiri, tanpa pustaka tambahan. Skemanya kecil dan
tetap, dan menambah ketergantungan yang harus ikut dipasang di dalam
jaringan BPJS bukan harga yang pantas untuk delapan baris pemeriksaan.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from . import aturan as pustaka_aturan
from .jejak import Jejak


class GalatAlat(Exception):
    """Alat menolak dipanggil. Bukan kesalahan mendadak, melainkan penolakan."""


@dataclass(frozen=True)
class Alat:
    nama: str
    keterangan: str
    parameter: dict[str, dict]
    wajib: tuple[str, ...]
    jalankan: Callable[..., Any]

    def skema(self) -> dict:
        """Bentuk yang bisa diberikan langsung ke pemanggilan fungsi model."""
        return {
            "name": self.nama,
            "description": self.keterangan,
            "parameters": {
                "type": "object",
                "properties": self.parameter,
                "required": list(self.wajib),
            },
        }


def _periksa(alat: Alat, arg: dict) -> None:
    tak_dikenal = set(arg) - set(alat.parameter)
    if tak_dikenal:
        raise GalatAlat(f"argumen tidak dikenal: {sorted(tak_dikenal)}")
    kurang = [k for k in alat.wajib if k not in arg]
    if kurang:
        raise GalatAlat(f"argumen wajib belum ada: {kurang}")
    for k, v in arg.items():
        p = alat.parameter[k]
        jenis = p.get("type")
        if jenis == "string" and not isinstance(v, str):
            raise GalatAlat(f"{k} harus teks")
        if jenis == "integer" and not isinstance(v, int):
            raise GalatAlat(f"{k} harus bilangan bulat")
        if jenis == "number" and not isinstance(v, (int, float)):
            raise GalatAlat(f"{k} harus angka")
        if "enum" in p and v not in p["enum"]:
            raise GalatAlat(f"{k} harus salah satu dari {p['enum']}")
        if "minimum" in p and v < p["minimum"]:
            raise GalatAlat(f"{k} tidak boleh kurang dari {p['minimum']}")
        if "maximum" in p and v > p["maximum"]:
            raise GalatAlat(f"{k} tidak boleh lebih dari {p['maximum']}")


class Perkakas:
    """Kumpulan alat yang terikat pada satu keadaan dan satu jejak.

    Keadaannya obyek apa pun yang menyediakan episodes, detektor, dan cara
    mencari indeks dari nomor berkas. Bentuknya dibuat longgar supaya bisa
    dipakai baik oleh peladen maupun oleh skrip percobaan.
    """

    def __init__(self, keadaan, jejak: Jejak):
        self.k = keadaan
        self.jejak = jejak
        self.daftar: dict[str, Alat] = {a.nama: a for a in self._bangun()}

    # -- pemanggilan --------------------------------------------------------

    def panggil(self, nama: str, **arg) -> Any:
        """Panggil satu alat. Berhasil atau gagal, keduanya tercatat."""
        alat = self.daftar.get(nama)
        if alat is None:
            raise GalatAlat(f"alat {nama} tidak ada")
        t0 = time.perf_counter()
        try:
            _periksa(alat, arg)
            hasil = alat.jalankan(**arg)
        except GalatAlat as e:
            self.jejak.tambah(
                nama, arg, None, (time.perf_counter() - t0) * 1000, str(e)
            )
            raise
        self.jejak.tambah(nama, arg, hasil, (time.perf_counter() - t0) * 1000)
        return hasil

    def skema(self) -> list[dict]:
        return [a.skema() for a in self.daftar.values()]

    # -- isi alat -----------------------------------------------------------

    def _indeks(self, id_berkas: str) -> int:
        try:
            return self.k.indeks_dari_id(id_berkas)
        except KeyError:
            raise GalatAlat(f"berkas {id_berkas} tidak ada") from None

    def _ambil_berkas(self, id: str) -> dict:
        i = self._indeks(id)
        r = self.k.episodes[i]
        return {
            "id": id,
            "faskes": self.k.nama_faskes(r),
            "kelas_faskes": r["f_kelas"],
            "regional": int(r["f_reg"]) + 1,
            "daerah_tertinggal": bool(r["f_dtpk"]),
            "kelompok_tarif": r["cbg"],
            "diagnosis_utama": r["dxp"],
            "n_prosedur": len(r["prc"]),
            "n_obat": len(r["obt"]),
            "pemeriksaan_lab": [k for k, _ in r["lab"]],
            "n_bahan_habis_pakai": len(r["bhp"]),
            "rawat_inap": bool(r["rawat_inap"]),
            "kelas_rawat": int(r["kelas_rawat"]),
            "lama_rawat": int(r["los"]),
            "hari": int(r["hari"]),
            "tarif_ditagihkan_rp": int(r["tarif"]),
            "tagihan_barang_rp": int(r.get("tagih_bhp", 0)),
        }

    def _cari_tarif(
        self,
        kode: str,
        kelas_rawat: int,
        kelas_rs: str,
        regional: int,
        kepemilikan: str = "PEMERINTAH",
    ) -> dict:
        from ..tarif_resmi import tarif_resmi

        n = tarif_resmi(kode, kelas_rawat, kelas_rs, regional, kepemilikan)
        if n is None:
            raise GalatAlat(f"kode {kode} tidak ada pada tabel tarif resmi")
        return {
            "kode": kode,
            "kelas_rawat": kelas_rawat,
            "kelas_rs": kelas_rs,
            "regional": regional,
            "kepemilikan": kepemilikan,
            "tarif_rp": int(n),
            "sumber": "Lampiran Permenkes 3 Tahun 2023",
        }

    def _cari_aturan(self, pertanyaan: str, atas: int = 3) -> dict:
        hasil = pustaka_aturan.cari(pertanyaan, atas=atas)
        if not hasil:
            raise GalatAlat("tidak ada aturan yang cocok dengan pertanyaan itu")
        return {"pertanyaan": pertanyaan, "entri": hasil}

    def _hitung_pengandaian(self, id: str) -> dict:
        i = self._indeks(id)
        j = self.k.detektor.jelaskan(self.k.episodes, i)
        a = j["angka"]
        # Penjumlahan tarif paket dan barang dikerjakan di sini, bukan oleh
        # yang menyusun kalimat. Penjaga A1 menolak angka yang tidak
        # dikembalikan alat, dan penolakannya benar: nilai yang tidak
        # pernah dihitung alat tidak punya jejak yang bisa diaudit.
        return {
            "id": id,
            "tarif_ditagihkan_rp": int(a["tarif_ditagihkan"]),
            "tarif_didukung_bukti_rp": int(a["tarif_didukung_bukti"]),
            "barang_ditagihkan_rp": int(a["tagihan_barang_ditagihkan"]),
            "barang_wajar_rp": int(a["tagihan_barang_wajar"]),
            "total_diajukan_rp": int(a["tarif_ditagihkan"])
            + int(a["tagihan_barang_ditagihkan"]),
            "total_didukung_bukti_rp": int(a["tarif_didukung_bukti"])
            + int(a["tagihan_barang_wajar"]),
            "selisih_rp": int(a["selisih_rp"]),
            "bukti": [
                {
                    "kode": b["bukti"],
                    "ubah_selisih_rp": int(b["perubahan_selisih_rp"]),
                }
                for b in j["bukti_yang_bila_ada_akan_mengubah_penilaian"]
            ],
        }

    def _skor_ulang(self, id: str, bukti_tambahan: list) -> dict:
        """Hitung ulang selisih seandainya bukti berikut ada pada berkas.

        Dipakai portal faskes. Yang menghitung tetap penebak, jadi tidak ada
        agen yang bisa menjanjikan penurunan yang tidak terjadi.
        """
        i = self._indeks(id)
        r = self.k.episodes[i]
        dikenal = {k for k, _ in r["lab"]}
        tambah = [k for k in bukti_tambahan if isinstance(k, str)]
        tak_dikenal = [k for k in tambah if k in dikenal]
        if tak_dikenal:
            raise GalatAlat(f"bukti sudah ada pada berkas: {tak_dikenal}")

        tiruan = dict(r)
        tiruan["lab"] = list(r["lab"]) + [(k, 1.0) for k in tambah]
        semula = float(self.k.detektor.skor([r])["selisih"][0])
        sesudah = float(self.k.detektor.skor([tiruan])["selisih"][0])
        return {
            "id": id,
            "bukti_tambahan": tambah,
            "selisih_semula_rp": int(round(semula)),
            "selisih_sesudah_rp": int(round(sesudah)),
            "turun_rp": int(round(semula - sesudah)),
        }

    def _bangun(self) -> list[Alat]:
        return [
            Alat(
                nama="ambil_berkas",
                keterangan=(
                    "Bukti dan angka pada satu berkas klaim, apa adanya "
                    "dari basis data."
                ),
                parameter={"id": {"type": "string", "description": "Nomor berkas."}},
                wajib=("id",),
                jalankan=self._ambil_berkas,
            ),
            Alat(
                nama="cari_tarif",
                keterangan="Tarif resmi satu kelompok INA-CBG pada satu konteks.",
                parameter={
                    "kode": {"type": "string"},
                    "kelas_rawat": {"type": "integer", "minimum": 1, "maximum": 3},
                    "kelas_rs": {"type": "string", "enum": ["A", "B", "C", "D"]},
                    "regional": {"type": "integer", "minimum": 1, "maximum": 5},
                    "kepemilikan": {
                        "type": "string",
                        "enum": ["PEMERINTAH", "SWASTA"],
                    },
                },
                wajib=("kode", "kelas_rawat", "kelas_rs", "regional"),
                jalankan=self._cari_tarif,
            ),
            Alat(
                nama="cari_aturan",
                keterangan=(
                    "Entri aturan dan modus kecurangan yang paling cocok "
                    "dengan sebuah pertanyaan."
                ),
                parameter={
                    "pertanyaan": {"type": "string"},
                    "atas": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                wajib=("pertanyaan",),
                jalankan=self._cari_aturan,
            ),
            Alat(
                nama="hitung_pengandaian",
                keterangan=(
                    "Selisih satu berkas dan akibat tiap bukti yang belum ada padanya."
                ),
                parameter={"id": {"type": "string"}},
                wajib=("id",),
                jalankan=self._hitung_pengandaian,
            ),
            Alat(
                nama="skor_ulang",
                keterangan="Selisih baru seandainya bukti tambahan ada pada berkas.",
                parameter={
                    "id": {"type": "string"},
                    "bukti_tambahan": {"type": "array"},
                },
                wajib=("id", "bukti_tambahan"),
                jalankan=self._skor_ulang,
            ),
        ]
