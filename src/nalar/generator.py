"""SIMJKN, pembangkit episode klaim sintetis.

Tujuh tahap, sesuai rancangan bagian 12. Keluarannya bukan hanya klaim yang
diajukan, tapi juga versi jujurnya dan selisih rupiahnya. Pasangan itu yang
membuat evaluasi punya kebenaran dasar yang tepat.

Yang harus benar di sini bukan angkanya, tapi strukturnya:

  - Komorbiditas punya rantai, tidak muncul acak.
  - Bukti klinis berkorelasi dengan diagnosis, tidak ditabur bebas.
  - Ketiadaan laboratorium mengikuti kelas faskes dan wilayah, bukan acak.
  - Kesalahan pengkodean yang jujur tetap ada, supaya penyimpangan tidak
    otomatis berarti curang.
  - Kecurangan melekat pada kebijakan faskes, tidak ditabur per klaim.

Tanpa lima hal itu, soalnya jadi terlalu mudah dan model akan terlihat jauh
lebih baik daripada kenyataan.
"""

from __future__ import annotations

import numpy as np

from . import katalog as K
from . import fraud as F
from .tarif import kelompokkan, tarif
from .wilayah import BOBOT_PROV, IS_DTPK, N_PROV, REGIONAL_PROV, Jaringan

# porsi segmen kepesertaan. Disusun mendekati komposisi JKN, dengan PBI
# sebagai segmen terbesar.
SEBARAN_SEGMEN = np.array([0.52, 0.27, 0.14, 0.07])   # PBI, PPU, PBPU, BP

# hak kelas rawat menurut segmen
HAK_KELAS_SEGMEN = {
    0: np.array([0.00, 0.02, 0.98]),   # PBI hampir seluruhnya kelas 3
    1: np.array([0.22, 0.42, 0.36]),   # PPU
    2: np.array([0.18, 0.32, 0.50]),   # PBPU
    3: np.array([0.20, 0.36, 0.44]),   # BP
}

# sebaran umur penduduk Indonesia yang masih muda, dipakai sebagai bobot
# untuk sepuluh pita umur
SEBARAN_UMUR = np.array([0.085, 0.165, 0.170, 0.165, 0.140,
                         0.115, 0.085, 0.048, 0.021, 0.006])

HARI_PER_TAHUN = 365

# Nilai bawaan kedua tombol penyetel. Diisi oleh modul kalibrasi dan ditulis
# ulang ke sini setelah penyetelan, supaya pembangkit bisa dipakai langsung
# tanpa menyetel ulang tiap kali.
# Hasil penyetelan pada 5 September 2026, 1.200 peserta selama tiga tahun.
# Seluruh sasaran agregat lolos di bawah toleransi lima belas persen.
PENGALI_UTILISASI = 2.4165
TILT_TEMPAT = {"tilt_fktp": 4.0, "skala_inap": 0.0746}


class Pembangkit:
    def __init__(self, n_peserta: int = 40_000, tahun: int = 3,
                 seed: int = 7, prevalensi_faskes_nakal: float = 0.22,
                 pengali_utilisasi: float | None = None,
                 tilt_tempat: dict | None = None,
                 n_fktp: int | None = None, n_fkrtl: int | None = None,
                 porsi_faskes_berubah: float = 0.0):
        self.rng = np.random.default_rng(seed)
        self.n_peserta = n_peserta
        self.tahun = tahun
        # dua tombol penyetel, nilainya dari modul kalibrasi
        self.pengali_utilisasi = (PENGALI_UTILISASI if pengali_utilisasi is None
                                  else float(pengali_utilisasi))
        t = TILT_TEMPAT if tilt_tempat is None else tilt_tempat
        self.tilt_fktp = float(t.get("tilt_fktp", 1.0))
        self.skala_inap = float(t.get("skala_inap", 1.0))
        self.n_hari = tahun * HARI_PER_TAHUN
        self.jaringan = Jaringan(n_peserta, self.rng, n_fktp, n_fkrtl)
        self.kebijakan = F.tetapkan_kebijakan(
            self.jaringan, self.rng, prevalensi_faskes_nakal,
            porsi_berubah=porsi_faskes_berubah, total_hari=self.n_hari)
        self._siapkan_populasi()
        self._siapkan_tabel_kondisi()

    # -- tahap 1: populasi --------------------------------------------------

    def _siapkan_populasi(self) -> None:
        rng, n = self.rng, self.n_peserta
        self.prov = rng.choice(N_PROV, size=n, p=BOBOT_PROV)
        self.umur_pita = rng.choice(K.N_AGE, size=n, p=SEBARAN_UMUR)
        self.sex = rng.integers(0, 2, size=n)          # 0 laki laki, 1 perempuan
        self.segmen = rng.choice(4, size=n, p=SEBARAN_SEGMEN)
        self.hak_kelas = np.empty(n, dtype=np.int64)
        for s in range(4):
            m = self.segmen == s
            if m.any():
                self.hak_kelas[m] = rng.choice(
                    [1, 2, 3], size=int(m.sum()), p=HAK_KELAS_SEGMEN[s])
        self.dtpk = IS_DTPK[self.prov]
        self.regional = REGIONAL_PROV[self.prov]
        # FKTP tempat peserta terdaftar
        self.fktp = np.array([self.jaringan.pilih_fktp(int(p), rng)
                              for p in self.prov])

    # -- tabel kondisi ------------------------------------------------------

    def _siapkan_tabel_kondisi(self) -> None:
        """Matriks insidens kondisi kali pita umur, dipisah menurut jenis kelamin."""
        n_k = len(K.KONDISI)
        self.inc = np.zeros((n_k, K.N_AGE))
        self.sex_kondisi = np.zeros(n_k, dtype=np.int64)
        for i, k in enumerate(K.KONDISI):
            self.inc[i] = k["inc"]
            self.sex_kondisi[i] = k["sex"]
        # insidens diberikan per seribu orang per tahun
        for i, k in enumerate(K.KONDISI):
            self.inc[i] *= K.KOREKSI_INSIDENS.get(k["icd"], 1.0)
        self.inc = self.inc / 1000.0 * self.pengali_utilisasi

    # -- tahap 2 dan 3: morbiditas dan pencarian layanan --------------------

    def _kondisi_peserta(self, umur: int, sex: int, dtpk: int):
        """Kondisi yang dialami satu peserta selama satu tahun.

        Mengembalikan daftar indeks kondisi. Peserta di daerah tertinggal
        lebih jarang berobat untuk keluhan yang sama, jadi peluangnya ditekan.
        Ketimpangan akses ini harus ada di data, kalau tidak model akan
        menganggap rendahnya pemanfaatan di timur sebagai anomali.
        """
        rng = self.rng
        p = self.inc[:, umur].copy()
        # jenis kelamin: 1 laki laki saja, 2 perempuan saja
        p[(self.sex_kondisi == 1) & (sex == 1)] = 0.0
        p[(self.sex_kondisi == 2) & (sex == 0)] = 0.0
        if dtpk:
            p = p * 0.62
        kena = np.flatnonzero(rng.random(len(p)) < p)
        return kena

    # -- tahap 5: isi klinis satu episode -----------------------------------

    def _isi_klinis(self, kond: dict, umur: int, punya_lab: bool,
                    rawat_inap: bool, kelas_rs: str):
        rng = self.rng

        # prosedur
        prc = [c for c, pr in kond["prc"] if rng.random() < pr]

        # obat
        obt = [c for c, pr in kond["obt"] if rng.random() < pr]

        # lama rawat
        if rawat_inap:
            mu, sd = kond["los"]
            los = int(max(1, round(rng.lognormal(np.log(max(mu, 1.0)), 0.42))))
            los = min(los, 60)
        else:
            los = 0

        # diagnosis sekunder yang sah, dari rantai komorbiditas
        dxs = []
        for c in kond["komorbid"]:
            if rng.random() < (0.34 if rawat_inap else 0.20):
                dxs.append(c)
        # komorbiditas akut yang muncul saat dirawat
        if rawat_inap:
            for kk in K.KOMORBID_TAMBAHAN:
                if rng.random() < (0.055 if kk["berat"] else 0.085):
                    dxs.append(kk["icd"])
        dxs = list(dict.fromkeys(dxs))[:9]

        # pemeriksaan penunjang. Tidak semua faskes bisa memeriksa.
        lab = []
        if punya_lab:
            for kode, pr, arah in kond["lab"]:
                if rng.random() < pr:
                    lab.append((kode, self._nilai_lab(kode, arah)))
            # bukti yang menyertai diagnosis sekunder yang sah
            for d in dxs:
                kk = K.KOMORBID_BY_ICD.get(d)
                if not kk:
                    continue
                for kode, arah in kk["bukti_lab"]:
                    if rng.random() < 0.82:
                        lab.append((kode, self._nilai_lab(kode, arah)))
                for o in kk["bukti_obt"]:
                    if rng.random() < 0.78 and o not in obt:
                        obt.append(o)
        else:
            # tanpa laboratorium, obat pendukung tetap diberikan
            for d in dxs:
                kk = K.KOMORBID_BY_ICD.get(d)
                if kk and rng.random() < 0.55:
                    obt.extend(o for o in kk["bukti_obt"] if o not in obt)
        # buang pemeriksaan ganda, ambil yang terakhir
        lab = list({k: v for k, v in lab}.items())

        # bahan habis pakai, mengikuti prosedur
        bhp = self._bhp_dari_prosedur(prc, rawat_inap, los)

        return dxs, prc, obt, lab, bhp, los

    def _nilai_lab(self, kode: str, arah: int) -> float:
        """Nilai pemeriksaan, digeser sesuai arah kelainan yang diharapkan."""
        rng = self.rng
        lo, hi = K.PEMERIKSAAN[kode][1], K.PEMERIKSAAN[kode][2]
        lebar = max(hi - lo, 1e-9)
        if arah == 0:
            z = rng.normal(0.5, 0.30)
        elif arah > 0:
            z = 1.0 + abs(rng.lognormal(-0.5, 0.75))
        else:
            z = -abs(rng.lognormal(-0.9, 0.70))
        return float(lo + z * lebar)

    def _bhp_dari_prosedur(self, prc, rawat_inap, los):
        rng = self.rng
        peta = {
            "39.95": [("ALK003", 1), ("ALK004", 1)],
            "13.41": [("ALK005", 1), ("ALK008", 1)],
            "36.06": [("ALK007", 1), ("ALK011", 4)],
            "79.35": [("ALK006", 1), ("ALK015", 1), ("ALK008", 2)],
            "78.55": [("ALK006", 1)],
            "74.1": [("ALK008", 3), ("ALK001", 1)],
            "68.4": [("ALK008", 3)],
            "51.23": [("ALK008", 2)],
            "47.09": [("ALK008", 2)],
            "47.01": [("ALK008", 2)],
            "96.71": [("ALK013", 1), ("ALK010", 2)],
            "99.04": [("ALK009", 2), ("ALK002", 1)],
            "99.06": [("ALK009", 1)],
            "57.94": [("ALK001", 1)],
        }
        bhp = {}
        for p in prc:
            for kode, jml in peta.get(p, []):
                bhp[kode] = bhp.get(kode, 0) + jml
        if rawat_inap:
            bhp["ALK002"] = bhp.get("ALK002", 0) + max(1, los // 3)
            bhp["ALK011"] = bhp.get("ALK011", 0) + max(2, los)
            if rng.random() < 0.45:
                bhp["ALK012"] = bhp.get("ALK012", 0) + max(1, los // 2)
        return sorted(bhp.items())

    # -- tahap 6: pengkodean dan tarif --------------------------------------

    def _kesalahan_jujur(self, dxs, prc):
        """Kesalahan pengkodean yang tidak disengaja.

        Penelitian di Indonesia melaporkan ketidaktepatan kode diagnosis pada
        kisaran tiga puluh persen berkas, dari satu penelitian pada 87 dokumen
        di satu rumah sakit. Sampel sekecil itu tidak bisa dipakai sebagai
        angka pasti, jadi laju di bawah adalah titik tengah dengan rentang
        lebar, dan analisis kepekaan dijalankan terpisah.
        """
        rng = self.rng
        if rng.random() < 0.18 and dxs:
            # satu diagnosis sekunder terlewat dicatat
            dxs = dxs[:-1]
        if rng.random() < 0.09 and prc:
            prc = prc[:-1]
        return dxs, prc

    # -- pembangkitan utama -------------------------------------------------

    def jalankan(self):
        """Hasilkan seluruh episode. Mengembalikan daftar dict."""
        rng = self.rng
        J = self.jaringan
        keluar = []
        eps_id = 0

        for pid in range(self.n_peserta):
            umur = int(self.umur_pita[pid])
            sex = int(self.sex[pid])
            prov = int(self.prov[pid])
            dtpk = int(self.dtpk[pid])
            kronis_aktif: list[int] = []
            hari_terakhir = -1
            n_eps_tahun_ini = 0

            for th in range(self.tahun):
                baru = self._kondisi_peserta(umur, sex, dtpk)
                aktif = sorted(set(list(baru) + kronis_aktif))
                for ki in aktif:
                    kond = K.KONDISI[ki]
                    if kond["kronis"] and ki not in kronis_aktif:
                        kronis_aktif.append(ki)

                    # kondisi kronis menghasilkan beberapa kunjungan setahun
                    if kond["kronis"]:
                        # Frekuensi kunjungan kronis adalah pola layanan,
                        # bukan turunan insidens. Tombol utilisasi tidak boleh
                        # menyentuhnya, kalau tidak ia terhitung dua kali.
                        dasar = K.KUNJUNGAN_KRONIS_PER_TAHUN.get(
                            kond["icd"], K.KUNJUNGAN_KRONIS_BAWAAN)
                        n_kunjungan = max(1, rng.poisson(dasar))
                        n_kunjungan = min(n_kunjungan, 130)
                    else:
                        n_kunjungan = 1

                    for _ in range(int(n_kunjungan)):
                        hari = th * HARI_PER_TAHUN + int(rng.integers(HARI_PER_TAHUN))
                        rec = self._satu_episode(
                            eps_id, pid, kond, umur, sex, prov, hari,
                            hari_terakhir, len(kronis_aktif), n_eps_tahun_ini)
                        if rec is None:
                            continue
                        keluar.append(rec)
                        eps_id += 1
                        hari_terakhir = hari
                        n_eps_tahun_ini += 1
                n_eps_tahun_ini = 0

        keluar.sort(key=lambda r: (r["peserta_id"], r["hari"]))
        # tahap tujuh lanjutan: modus yang butuh lebih dari satu klaim
        keluar = F.pasca(keluar, self.kebijakan, J, rng)
        return keluar

    def _satu_episode(self, eps_id, pid, kond, umur, sex, prov, hari,
                      hari_terakhir, n_kronis, n_eps):
        rng = self.rng
        J = self.jaringan

        # Tempat layanan diputuskan dua langkah, bukan satu undian tiga arah.
        # Langkah pertama, apakah kasus ini selesai di FKTP atau naik ke FKRTL.
        # Langkah kedua, kalau naik, apakah dirawat inap. Pemisahan ini penting
        # karena penyetel agregat hanya boleh menyentuh langkah pertama. Kalau
        # ia boleh menyentuh langkah kedua, ia akan memindahkan infark miokard
        # akut ke rawat jalan demi mengejar sasaran nasional.
        tp = kond["tempat"]
        p_fktp = tp.get(K.FKTP_ONLY, 0.0)
        p_rjtl = tp.get(K.RJTL, 0.0)
        p_ritl = tp.get(K.RITL, 0.0)
        sisa = p_rjtl + p_ritl
        total = p_fktp + sisa
        p_fktp = p_fktp / total if total > 0 else 0.0
        p_inap = (p_ritl / sisa) if sisa > 0 else 0.0

        # langkah satu, dengan penyetel
        odds = (p_fktp / max(1.0 - p_fktp, 1e-9)) * self.tilt_fktp
        p_fktp_efektif = odds / (1.0 + odds)
        naik = rng.random() >= p_fktp_efektif

        # langkah dua, tanpa penyetel untuk kondisi yang wajib dirawat
        if kond["icd"] in K.WAJIB_INAP:
            p_inap_efektif = p_inap
        else:
            p_inap_efektif = min(p_inap * self.skala_inap, 1.0)

        if not naik:
            t = K.FKTP_ONLY
        else:
            t = K.RITL if rng.random() < p_inap_efektif else K.RJTL

        rawat_inap = t == K.RITL
        if t == K.FKTP_ONLY:
            faskes = int(self.fktp[pid])
            jenis = 0
            kelas_rs = "FKTP"
            punya_lab = bool(J.fktp_punya_lab[faskes])
            regional = int(J.fktp_regional[faskes])
            f_tt = 0
            dpjp = -1
            rujuk = 0
            perujuk = -1
        else:
            butuh_tinggi = kond["icd"] in ("I21", "C92", "I61", "C50", "C34")
            faskes = J.pilih_rs(prov, rng, butuh_tinggi)
            jenis = 1
            kelas_rs = ("A", "B", "C", "D")[int(J.rs_kelas[faskes])]
            punya_lab = True
            regional = int(J.rs_regional[faskes])
            f_tt = int(J.rs_tt[faskes])
            dpjp = J.dpjp(faskes, rng)
            # rujukan berjenjang, kecuali gawat darurat
            gawat = kond["icd"] in ("I21", "I61", "S06", "S72", "A41", "K35")
            if gawat and rng.random() < 0.72:
                rujuk, perujuk = 2, -1
            else:
                rujuk, perujuk = 1, int(self.fktp[pid])

        dxs, prc, obt, lab, bhp, los = self._isi_klinis(
            kond, umur, punya_lab, rawat_inap, kelas_rs)

        # kelas rawat: umumnya sesuai hak, kadang naik karena kelas penuh
        hak = int(self.hak_kelas[pid])
        kelas_rawat = hak
        if rawat_inap and rng.random() < 0.06 and hak > 1:
            kelas_rawat = hak - 1

        dxs_j, prc_j = self._kesalahan_jujur(dxs, prc)
        kel_j = kelompokkan(kond["icd"], dxs_j, prc_j, los, rawat_inap)
        tarif_j = tarif(kel_j, kond["icd"], prc_j, kelas_rawat, kelas_rs, regional)

        rec = dict(
            eps_id=eps_id, peserta_id=pid, hari=hari, d_prev=-1,
            umur=umur, sex=sex, segmen=int(self.segmen[pid]),
            hak_kelas=hak, prov=prov,
            n_kronis=min(n_kronis, 5), n_eps=min(n_eps, 5),
            faskes=faskes, f_jenis=jenis, f_kelas=kelas_rs,
            f_milik=int(J.rs_milik[faskes]) if jenis else 0,
            f_tt=f_tt, f_reg=regional,
            f_dtpk=int(J.rs_dtpk[faskes]) if jenis else int(J.fktp_dtpk[faskes]),
            dpjp=dpjp, punya_lab=punya_lab,
            bulan=(hari % HARI_PER_TAHUN) // 30, dow=hari % 7,
            libur=1 if hari % 7 in (5, 6) else 0,
            rujuk=rujuk, perujuk=perujuk,
            rawat_inap=rawat_inap,
            # versi jujur
            dxp=kond["icd"], dxs_j=dxs_j, prc_j=prc_j, obt_j=obt,
            lab_j=lab, bhp_j=bhp, los_j=los,
            kelas_rawat_j=kelas_rawat, cbg_j=kel_j.kode,
            keparahan_j=kel_j.keparahan, tarif_j=tarif_j,
        )

        # tahap 7: kebijakan faskes dan injeksi
        F.terapkan(rec, self.kebijakan, J, self.rng)
        return rec
