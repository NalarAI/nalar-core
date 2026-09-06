"""Keadaan yang dibangun sekali lalu dipakai berulang.

Melatih penebak normatif memakan waktu, dan website tidak boleh menunggu itu
pada setiap permintaan. Jadi seluruhnya dibangun sekali saat peladen menyala:
data dibangkitkan, detektor dilatih dan dikalibrasi, lalu skornya disimpan.

Yang berubah ketika pemakai menggeser pengaturan di layar hanyalah ambang dan
antreannya. Model tidak dilatih ulang, karena menggeser alpha memang tidak
mengubah apa yang wajar bagi sebuah klaim. Ia hanya mengubah seberapa berani
kita menandainya. Membedakan dua hal itu penting, dan antarmuka harus
mencerminkannya.

Data yang dipakai seluruhnya buatan. Tidak ada satu pun klaim peserta JKN yang
sungguhan, sesuai ketentuan lomba dan sesuai akal sehat.
"""

from __future__ import annotations

import threading

import numpy as np

from ..dataset import bangun_meta, pisah_menurut_entitas
from ..detektor import Detektor
from ..generator import Pembangkit
from ..katalog import PEMERIKSAAN

NAMA_BUKTI = {
    "HB": "hemoglobin",
    "KREA": "kreatinin",
    "LEUKO": "leukosit",
    "ALB": "albumin",
    "NA": "natrium",
    "TROMB": "trombosit",
}

PERINGATAN_RUPIAH = (
    "Angka rupiah bergeser sekitar empat puluh persen antar benih acak, jadi "
    "jangan dikutip sendirian. Yang stabil adalah porsi batas atas."
)


class Keadaan:
    """Satu berkas data buatan beserta detektor yang sudah terlatih di atasnya."""

    def __init__(self, n_peserta=8000, tahun=3, seed=7, n_fktp=400, n_fkrtl=80):
        self.kunci = threading.Lock()
        self.siap = False
        self.pengaturan = {"n_peserta": n_peserta, "tahun": tahun, "seed": seed}
        self._n_peserta = n_peserta
        self._tahun = tahun
        self._seed = seed
        self._n_fktp = n_fktp
        self._n_fkrtl = n_fkrtl

    def bangun(self, alpha: float = 0.02) -> None:
        """Bangkitkan, latih, kalibrasi, dan skor. Dipanggil sekali."""
        g = Pembangkit(
            n_peserta=self._n_peserta,
            tahun=self._tahun,
            seed=self._seed,
            n_fktp=self._n_fktp,
            n_fkrtl=self._n_fkrtl,
        )
        eps = g.jalankan()
        meta = bangun_meta(eps)
        m_tr, _ = pisah_menurut_entitas(meta, frac_uji=0.25, seed=self._seed)
        itr = np.flatnonzero(m_tr)
        ite = np.flatnonzero(~m_tr)
        rng = np.random.default_rng(self._seed)
        rng.shuffle(itr)
        nk = max(300, min(20000, len(itr) // 3))

        self._kal = [eps[i] for i in itr[:nk]]
        det = Detektor(alpha=alpha, seed=self._seed)
        det.latih([eps[i] for i in itr[nk:]])
        det.kalibrasi(self._kal)

        self.n_hari = g.n_hari
        self.detektor = det
        self.episodes = [eps[i] for i in ite]
        self._hitung_ulang()
        self.siap = True

    def _hitung_ulang(self) -> None:
        """Skor dan ambang, dihitung ulang setiap alpha berubah."""
        d = self.detektor.skor(self.episodes)
        self.skor = d
        self.selisih = d["selisih"]
        amb, tahan = self.detektor.ambang_untuk(self.episodes)
        self.ambang = amb
        self.tahan = tahan
        self.tanda = self.detektor.tandai(self.episodes)
        self.posisi = self.detektor.posisi(self.episodes)
        self.urutan = np.argsort(-self.selisih)

    def set_alpha(self, alpha: float) -> None:
        """Ubah alpha tanpa melatih ulang.

        Melatih ulang tidak diperlukan karena alpha tidak mengubah tarif yang
        wajar bagi sebuah klaim. Yang diubah hanya seberapa jauh sebuah klaim
        boleh menyimpang sebelum ditandai. Kalibrasi ulang memang perlu, dan
        itu murah.
        """
        with self.kunci:
            if abs(alpha - self.detektor.alpha) < 1e-9:
                return
            self.detektor.alpha = alpha
            self.detektor.kalibrasi(self._episodes_kalibrasi())
            self._hitung_ulang()

    def _episodes_kalibrasi(self):
        # Kalibrasi memakai himpunan latih, bukan himpunan uji, supaya ambang
        # tidak pernah dilihat dari data yang dinilainya.
        return self._kal

    # -- pembantu ----------------------------------------------------------

    def id_klaim(self, i: int) -> str:
        return f"K{self.episodes[i]['eps_id']:08d}"

    def indeks_dari_id(self, kid: str) -> int:
        if not hasattr(self, "_peta_id"):
            self._peta_id = {self.id_klaim(i): i for i in range(len(self.episodes))}
        if kid not in self._peta_id:
            raise KeyError(kid)
        return self._peta_id[kid]

    def nama_faskes(self, r) -> str:
        jenis = "RS" if r["f_jenis"] else "FKTP"
        return f"{jenis}-{int(r['faskes']):04d}"

    def nama_bukti(self, kode: str) -> str:
        if kode in NAMA_BUKTI:
            return NAMA_BUKTI[kode]
        p = PEMERIKSAAN.get(kode)
        return p[0] if p else kode


# Satu keadaan bersama untuk seluruh peladen. Peladen ini melayani peraga,
# bukan beban produksi, jadi satu salinan sudah cukup dan jauh lebih sederhana
# daripada menyimpan per sesi.
KEADAAN = Keadaan()
