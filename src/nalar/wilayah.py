"""Provinsi, jaringan fasilitas kesehatan, dan regional tarif.

Jumlah faskes disetel ke angka terbitan BPJS Kesehatan untuk 2025:
23.770 FKTP, 3.194 FKRTL, 6.190 faskes penunjang. Sebarannya antar-provinsi
mengikuti bobot penduduk, karena registri Kemenkes belum diunduh.

Begitu registri rumah sakit Kemenkes masuk, fungsi bangun_faskes diganti
supaya memakai daftar nyata beserta kelas, kepemilikan, dan jumlah tempat
tidurnya. Antarmukanya sengaja dijaga agar penggantian itu tidak menyentuh
bagian lain.
"""

from __future__ import annotations

import numpy as np

# (nama, bobot penduduk kasar dalam juta, regional tarif 0-4)
# Regional tarif INA-CBG membagi wilayah menjadi lima. Pembagian di bawah ini
# pendekatan kami: Jawa dan Bali regional 1, Sumatera regional 2, dan makin
# jauh ke timur regional makin tinggi.
PROVINSI = [
    ("Aceh", 5.4, 1), ("Sumatera Utara", 15.6, 1), ("Sumatera Barat", 5.7, 1),
    ("Riau", 6.6, 1), ("Jambi", 3.7, 1), ("Sumatera Selatan", 8.7, 1),
    ("Bengkulu", 2.1, 1), ("Lampung", 9.2, 1), ("Kepulauan Bangka Belitung", 1.5, 1),
    ("Kepulauan Riau", 2.1, 1), ("DKI Jakarta", 10.7, 0), ("Jawa Barat", 49.9, 0),
    ("Jawa Tengah", 37.5, 0), ("DI Yogyakarta", 3.7, 0), ("Jawa Timur", 41.1, 0),
    ("Banten", 12.3, 0), ("Bali", 4.3, 0), ("Nusa Tenggara Barat", 5.5, 2),
    ("Nusa Tenggara Timur", 5.5, 2), ("Kalimantan Barat", 5.5, 2),
    ("Kalimantan Tengah", 2.7, 2), ("Kalimantan Selatan", 4.2, 2),
    ("Kalimantan Timur", 3.9, 2), ("Kalimantan Utara", 0.7, 3),
    ("Sulawesi Utara", 2.6, 2), ("Sulawesi Tengah", 3.1, 2),
    ("Sulawesi Selatan", 9.2, 2), ("Sulawesi Tenggara", 2.7, 2),
    ("Gorontalo", 1.2, 2), ("Sulawesi Barat", 1.4, 2),
    ("Maluku", 1.9, 3), ("Maluku Utara", 1.3, 3),
    ("Papua Barat", 0.6, 4), ("Papua Barat Daya", 0.6, 4),
    ("Papua", 1.0, 4), ("Papua Selatan", 0.5, 4),
    ("Papua Tengah", 1.3, 4), ("Papua Pegunungan", 1.4, 4),
]
N_PROV = len(PROVINSI)
BOBOT_PROV = np.array([p[1] for p in PROVINSI], dtype=np.float64)
BOBOT_PROV = BOBOT_PROV / BOBOT_PROV.sum()
REGIONAL_PROV = np.array([p[2] for p in PROVINSI], dtype=np.int64)

# provinsi yang banyak memuat daerah tertinggal, terdepan, terluar
DTPK = {"Nusa Tenggara Timur", "Maluku", "Maluku Utara", "Papua Barat",
        "Papua Barat Daya", "Papua", "Papua Selatan", "Papua Tengah",
        "Papua Pegunungan", "Kalimantan Utara", "Sulawesi Barat"}
IS_DTPK = np.array([1 if p[0] in DTPK else 0 for p in PROVINSI], dtype=np.int64)

# angka terbitan BPJS Kesehatan untuk 2025
N_FKTP_NASIONAL = 23_770
N_FKRTL_NASIONAL = 3_194

# sebaran kelas rumah sakit. Kelas A paling sedikit, kelas C dan D terbanyak.
SEBARAN_KELAS_RS = np.array([0.02, 0.13, 0.47, 0.38])  # A, B, C, D
KELAS_HURUF = ("A", "B", "C", "D")

# jumlah tempat tidur menurut kelas, dipakai untuk batas fisik kelas rawat
TT_MEAN = {"A": 620, "B": 300, "C": 140, "D": 60}

SEBARAN_KEPEMILIKAN = np.array([0.04, 0.34, 0.05, 0.51, 0.06])


class Jaringan:
    """Jaringan faskes sintetis, berskala terhadap jumlah peserta."""

    def __init__(self, n_peserta: int, rng: np.random.Generator,
                 n_fktp: int | None = None, n_fkrtl: int | None = None,
                 skala_nasional: int = 282_700_000):
        """Jaringan faskes.

        Ada satu ketegangan yang tidak bisa dihindari pada simulasi kecil.
        Secara nasional ada satu FKRTL untuk sekitar 88.500 peserta. Kalau
        rasio itu dipertahankan pada simulasi enam puluh ribu peserta, kita
        hanya punya satu rumah sakit, dan kepala kelompok sebaya tidak punya
        apa apa untuk dibandingkan. Kalau jumlah faskes dinaikkan, rasionya
        jadi jauh lebih padat daripada kenyataan.

        Kami memilih mempertahankan volume klaim per faskes, dan menerima
        rasio peserta per faskes yang termampatkan. Alasannya, yang dipelajari
        kepala K4 dan K5 adalah sebaran klaim di dalam satu faskes, bukan
        jumlah peserta yang terdaftar padanya.

        Akibatnya harus ditulis, bukan disembunyikan. Deteksi tingkat entitas
        pada data ini lebih mudah daripada di dunia nyata, karena tiap faskes
        di sini melayani populasi yang jauh lebih kecil sehingga polanya lebih
        bersih. Angka faktor_kompresi merekam seberapa besar penyimpangannya.
        """
        f = max(n_peserta / skala_nasional, 1e-9)
        self.n_fktp = n_fktp if n_fktp else max(int(round(N_FKTP_NASIONAL * f)), 30)
        self.n_fkrtl = n_fkrtl if n_fkrtl else max(int(round(N_FKRTL_NASIONAL * f)), 12)
        rasio_nyata = skala_nasional / N_FKRTL_NASIONAL
        rasio_simulasi = n_peserta / max(self.n_fkrtl, 1)
        self.faktor_kompresi = round(rasio_nyata / max(rasio_simulasi, 1e-9), 1)
        self._bangun(rng)

    def _bangun(self, rng: np.random.Generator) -> None:
        # FKRTL
        self.rs_prov = rng.choice(N_PROV, size=self.n_fkrtl, p=BOBOT_PROV)
        self.rs_kelas = rng.choice(4, size=self.n_fkrtl, p=SEBARAN_KELAS_RS)
        self.rs_milik = rng.choice(5, size=self.n_fkrtl, p=SEBARAN_KEPEMILIKAN)
        tt_mean = np.array([TT_MEAN[KELAS_HURUF[k]] for k in self.rs_kelas])
        self.rs_tt = np.maximum(
            rng.lognormal(np.log(tt_mean), 0.32).astype(int), 20)
        # kapasitas tempat tidur per kelas rawat, dipakai modus M13.
        # Sebagian besar tempat tidur JKN ada di kelas 3.
        self.rs_tt_kelas = np.stack([
            (self.rs_tt * 0.14).astype(int) + 2,   # kelas 1
            (self.rs_tt * 0.24).astype(int) + 3,   # kelas 2
            (self.rs_tt * 0.62).astype(int) + 5,   # kelas 3
        ], axis=1)
        self.rs_regional = REGIONAL_PROV[self.rs_prov]
        self.rs_dtpk = IS_DTPK[self.rs_prov]
        # jumlah dokter penanggung jawab per rumah sakit, kasar dari tempat tidur
        self.rs_n_dpjp = np.maximum((self.rs_tt / 12).astype(int), 3)
        self.rs_dpjp_ofs = np.concatenate([[0], np.cumsum(self.rs_n_dpjp)])
        self.n_dpjp = int(self.rs_dpjp_ofs[-1])

        # FKTP
        self.fktp_prov = rng.choice(N_PROV, size=self.n_fktp, p=BOBOT_PROV)
        self.fktp_regional = REGIONAL_PROV[self.fktp_prov]
        self.fktp_dtpk = IS_DTPK[self.fktp_prov]
        # apakah FKTP punya laboratorium. Di daerah tertinggal jauh lebih jarang.
        p_lab = np.where(self.fktp_dtpk == 1, 0.22, 0.58)
        self.fktp_punya_lab = rng.random(self.n_fktp) < p_lab

        # indeks faskes per provinsi, supaya penugasan bisa cepat
        self.fktp_per_prov = [np.flatnonzero(self.fktp_prov == p)
                              for p in range(N_PROV)]
        self.rs_per_prov = [np.flatnonzero(self.rs_prov == p)
                            for p in range(N_PROV)]
        # provinsi tanpa rumah sakit dirujuk ke provinsi terdekat yang punya.
        # Pendekatan sederhana: pakai kumpulan nasional sebagai cadangan.
        self.rs_semua = np.arange(self.n_fkrtl)

    def pilih_fktp(self, prov: int, rng: np.random.Generator) -> int:
        kandidat = self.fktp_per_prov[prov]
        if len(kandidat) == 0:
            return int(rng.integers(self.n_fktp))
        return int(rng.choice(kandidat))

    def pilih_rs(self, prov: int, rng: np.random.Generator,
                 butuh_kelas_tinggi: bool = False) -> int:
        kandidat = self.rs_per_prov[prov]
        if len(kandidat) == 0:
            kandidat = self.rs_semua
        if butuh_kelas_tinggi:
            tinggi = kandidat[self.rs_kelas[kandidat] <= 1]
            if len(tinggi) > 0:
                kandidat = tinggi
        return int(rng.choice(kandidat))

    def dpjp(self, rs: int, rng: np.random.Generator) -> int:
        lo = int(self.rs_dpjp_ofs[rs])
        return lo + int(rng.integers(self.rs_n_dpjp[rs]))
