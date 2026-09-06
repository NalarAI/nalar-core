"""Agen Penyelia: anggaran, batas giliran, dan pemutus rantai.

Dibangun bersama tahap dua, bukan sesudahnya, dan alasannya sederhana. Agen
yang tidak punya pemutus rantai akan memanggil alat sampai ada yang
menghentikannya dari luar, dan yang menghentikannya dari luar biasanya
tagihan atau orang yang menunggu.

Tiga batas yang dijaga, dan ketiganya alasan berhenti yang sah, bukan
kegagalan.

Giliran. Berkas perkara yang sehat selesai dalam beberapa pemanggilan alat.
Model yang masih memanggil pada giliran kesepuluh sedang tersesat, bukan
sedang teliti.

Biaya. Target A7 mengikat di bawah Rp 500 per berkas, dibanding ongkos
periksa manual Rp 750 ribu. Perhitungan yang sama dipakai daftar verifikasi
untuk menolak berkas bernilai kecil: kalau memeriksanya lebih mahal daripada
yang bisa diselamatkan, memeriksanya bukan penghematan.

Pengulangan. Alat yang dipanggil dua kali dengan argumen yang sama tidak
akan memberi jawaban berbeda. Kalau itu terjadi, model sedang berputar, dan
memutus rantainya lebih murah daripada menunggu ia sadar sendiri.

Yang terjadi sesudah rantai diputus bukan kegagalan yang dilempar ke atas.
Yang keluar tetap berkas perkara, hanya versi aturan. Faskes tidak pernah
tahu bahwa ada agen yang menyerah, dan memang tidak perlu tahu.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .alat import GalatAlat, Perkakas
from .penutur import Balasan


class RantaiDiputus(Exception):
    """Penyelia menghentikan agen. Bukan galat, melainkan putusan."""

    def __init__(self, sebab: str, tahap: str = ""):
        super().__init__(sebab)
        self.sebab = sebab
        self.tahap = tahap


@dataclass
class Anggaran:
    """Batas yang dipegang penyelia untuk satu berkas perkara."""

    giliran: int = 8
    panggilan: int = 12
    rp: float = 500.0
    detik: float = 90.0
    ulang: int = 2


@dataclass
class Penyelia:
    """Pengatur giliran satu perkara. Satu penyelia untuk satu berkas."""

    perkakas: Perkakas
    anggaran: Anggaran = field(default_factory=Anggaran)
    n_giliran: int = 0
    n_panggilan: int = 0
    rp: float = 0.0
    token_masuk: int = 0
    token_keluar: int = 0
    riwayat: list[tuple[str, str]] = field(default_factory=list)
    sebab_putus: str = ""

    # -- giliran model ------------------------------------------------------

    def catat_balasan(self, b: Balasan) -> None:
        self.n_giliran += 1
        self.token_masuk += b.token_masuk
        self.token_keluar += b.token_keluar
        self.rp += b.biaya_rp()
        if self.n_giliran > self.anggaran.giliran:
            self._putus(f"giliran melewati {self.anggaran.giliran}")
        if self.rp > self.anggaran.rp:
            self._putus(f"biaya melewati Rp {self.anggaran.rp:.0f}")

    # -- pemanggilan alat ---------------------------------------------------

    def panggil(self, nama: str, **arg):
        """Panggil alat lewat penyelia, sehingga terhitung dan terbatasi."""
        if self.n_panggilan >= self.anggaran.panggilan:
            self._putus(f"pemanggilan alat melewati {self.anggaran.panggilan}")

        # Sidik pemanggilan, bukan hasilnya. Argumen yang sama pada alat yang
        # sama tidak akan memberi jawaban berbeda, jadi mengulangnya tanda
        # model sedang berputar, bukan sedang memeriksa ulang.
        sidik = (nama, repr(sorted(arg.items())))
        if self.riwayat.count(sidik) >= self.anggaran.ulang:
            self._putus(f"alat {nama} dipanggil berulang dengan argumen yang sama")
        self.riwayat.append(sidik)

        self.n_panggilan += 1
        return self.perkakas.panggil(nama, **arg)

    def panggil_lunak(self, nama: str, **arg):
        """Sama, tapi penolakan alat dikembalikan sebagai keterangan.

        Dipakai ketika yang memanggil model bahasa. Penolakan alat adalah
        keterangan yang berguna bagi model, bukan alasan menghentikan
        gilirannya. Yang bukan penolakan alat tetap naik ke atas.
        """
        try:
            return {"berhasil": True, "hasil": self.panggil(nama, **arg)}
        except GalatAlat as e:
            return {"berhasil": False, "tolakan": str(e)}

    # -- laporan ------------------------------------------------------------

    def _putus(self, sebab: str) -> None:
        self.sebab_putus = sebab
        raise RantaiDiputus(sebab)

    def ringkas(self) -> dict:
        return {
            "giliran": self.n_giliran,
            "panggilan_alat": self.n_panggilan,
            "token_masuk": self.token_masuk,
            "token_keluar": self.token_keluar,
            "biaya_rp": round(self.rp, 3),
            "dalam_anggaran": not self.sebab_putus,
            "sebab_putus": self.sebab_putus,
        }
