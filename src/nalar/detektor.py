"""Detektor NALAR, konfigurasi yang benar benar diusulkan.

Berkas ini lahir dari kesimpulan percobaan 11 dan 12, bukan dari rancangan
awal. Rancangan mengusulkan transformer sebagai penebak normatif. Pengujian
menunjukkan pohon berpenguat mengerjakan pekerjaan yang sama lebih baik,
0,721 melawan 0,649 porsi batas atas, tanpa memakai satu pun label. Jadi yang
dikemas di sini adalah yang menang, bukan yang dirancang.

Yang tetap dipakai dari rancangan, karena tidak bergantung pada model:

  pemodelan kewajaran tanpa label    tesis pokoknya, dan tesisnya bertahan
  kalibrasi konformal per kelompok   yang mengubah rasio ketimpangan 105 ke 1,8
  keluaran berdenominasi rupiah      supaya bisa ditagih dan bisa dibantah
  penjelasan berbasis pengandaian    supaya faskes punya jalan membantah
  peringkat menurut nilai bersih     bukan menurut peluang

Apa yang model ini tidak lakukan, dan disengaja. Ia tidak memutuskan sebuah
klaim curang. Ia melaporkan selisih antara yang ditagihkan dan yang didukung
bukti, beserta bukti mana yang kurang. Kata curang tidak pernah muncul di
keluarannya.
"""

from __future__ import annotations

import json
import os

import numpy as np

from .konformal import Kalibrator
from .pembanding import fitur_bukti
from .vocab import HARGA_ACUAN


class Detektor:
    """Penebak normatif berbasis pohon, plus seluruh perkakas di sekitarnya."""

    def __init__(self, alpha: float = 0.02, seed: int = 0,
                 biaya_audit_rp: int = 750_000,
                 z_saring: float | None = 1.0,
                 sadar_faskes: bool = False):
        self.alpha = alpha
        self.seed = seed
        # Biaya rata rata satu pemeriksaan berkas. Dipakai memotong antrean
        # pada titik ketika memeriksa tidak lagi sepadan. Angkanya parameter
        # kebijakan, bukan parameter model, dan harus diisi BPJS.
        self.biaya_audit_rp = biaya_audit_rp
        self.m_tarif = None
        self.m_bhp = None
        self.kal = None
        self.ambang_tingkat: dict = {}
        self.ambang_umum = float("inf")
        # Berapa contoh kalibrasi minimum sebelum sebuah kelompok boleh punya
        # ambangnya sendiri. Di bawah ini, kuantilnya terlalu berisik untuk
        # dijadikan dasar mempersoalkan faskis mana pun.
        self.minimal_kalibrasi = 300
        # Kelompok yang dikecualikan dari penandaan otomatis. Ini saklar
        # kebijakan, bukan perbaikan teknis, dan alasannya ditulis terbuka.
        #
        # Setelah tiga kali percobaan perbaikan, faskes di daerah tertinggal
        # tetap ditandai sekitar 2,5 persen sedangkan yang bukan 0,7 persen,
        # padahal alpha dua persen. Menambah dimensi kelompok menurunkannya
        # dari 5,3 ke 3,6 lalu mentok. Menambah syarat jumlah faskes justru
        # membuat kelompok lain menahan diri tanpa menolong yang ini.
        #
        # Sebabnya kami duga keterpertukaran yang bocor di tingkat faskes,
        # bukan di tingkat klaim, dan itu tidak bisa diperbaiki dengan
        # kalibrasi. Jadi selama belum ada bukti sebaliknya, faskes di daerah
        # tertinggal tidak ditandai otomatis. Mereka tetap masuk lewat porsi
        # sampel acak, jadi umpan baliknya tidak hilang, tapi tidak ada
        # puskesmas yang dipersoalkan berdasarkan ambang yang kami sendiri
        # tidak bisa jamin berlaku untuknya.
        #
        # Ini pilihan yang bisa dibalik BPJS. Kosongkan daftarnya, dan
        # penandaan otomatis berlaku untuk semua, dengan ketimpangan yang
        # sudah diukur dan tertulis di atas.
        self.kecualikan_dtpk = True
        # Berapa faskes berbeda minimum sebelum sebuah kelompok boleh punya
        # ambangnya sendiri. Tanpa syarat ini, kelompok yang klaimnya banyak
        # tapi faskesnya sedikit akan mendapat ambang yang tidak berlaku di
        # luar faskes yang itu itu saja.
        self.minimal_faskes = 3
        # Batas skor baku di atas mana sebuah faskes dikeluarkan dari
        # himpunan kalibrasi. None berarti tidak menyaring, yaitu perilaku
        # lama, dan tetap bisa dipilih supaya perbandingannya bisa diulang.
        self.z_saring = z_saring
        # Ambang yang memperhitungkan sedikitnya jumlah faskes dalam satu
        # kelompok, lewat mengeluarkan satu faskes bergantian lalu mengambil
        # ambang terbesar. Matikan secara bawaan, karena diukur dan ternyata
        # tidak menggerakkan apa apa: laju penandaan daerah tertinggal tetap
        # 2,53 persen persis dengan dan tanpa. Sebabnya mengeluarkan satu dari
        # tiga puluh faskes hanya membuang dua setengah persen klaim, dan
        # persentil sembilan puluh delapan nyaris tidak bergeser sebanyak itu.
        # Kodenya ditinggalkan supaya hasil negatifnya bisa diulang, bukan
        # supaya dipakai.
        self.sadar_faskes = sadar_faskes
        self.n_faskes_dibuang = 0
        self.porsi_klaim_dibuang = 0.0
        self._terlatih = False
        self._terkalibrasi = False

    # -- pelatihan ----------------------------------------------------------

    def latih(self, episodes) -> "Detektor":
        """Pelajari tarif dan nilai tagihan yang wajar dari bukti.

        Tidak memakai satu pun label kecurangan. Dilatih pada seluruh klaim,
        termasuk yang curang, karena di dunia nyata kita memang tidak tahu
        mana yang jujur. Sebagian besar klaim jujur, jadi yang dipelajari
        adalah pemetaan yang wajar, dan klaim curang menjadi pencilan.
        """
        from sklearn.ensemble import HistGradientBoostingRegressor

        X = fitur_bukti(episodes)
        tarif = np.array([r["tarif"] for r in episodes], dtype=np.float64)
        bhp = np.array([r.get("tagih_bhp", 0) for r in episodes],
                       dtype=np.float64)

        def buat():
            return HistGradientBoostingRegressor(
                max_iter=300, learning_rate=0.08, max_leaf_nodes=63,
                l2_regularization=1.0, random_state=self.seed)

        # dilatih pada skala logaritma karena biaya klaim berekor sangat panjang
        self.m_tarif = buat().fit(X, np.log1p(tarif))
        self.m_bhp = buat().fit(X, np.log1p(bhp))
        self._terlatih = True
        return self

    # -- penskoran ----------------------------------------------------------

    def skor(self, episodes) -> dict:
        """Selisih rupiah per klaim, beserta uraiannya.

        Mengembalikan tiga hal yang berbeda arti:
          selisih_tarif    tarif ditagih dikurangi tarif yang didukung bukti
          selisih_tagihan  nilai barang ditagih dikurangi yang wajar
          selisih          jumlah keduanya, dibatasi tidak negatif
        """
        if not self._terlatih:
            raise RuntimeError("panggil latih dulu")
        X = fitur_bukti(episodes)
        tarif = np.array([r["tarif"] for r in episodes], dtype=np.float64)
        bhp = np.array([r.get("tagih_bhp", 0) for r in episodes],
                       dtype=np.float64)
        harap_tarif = np.expm1(self.m_tarif.predict(X))
        harap_bhp = np.expm1(self.m_bhp.predict(X))
        s_tarif = tarif - harap_tarif
        s_bhp = bhp - harap_bhp
        return {
            "selisih_tarif": s_tarif,
            "selisih_tagihan": s_bhp,
            "harapan_tarif": harap_tarif,
            "harapan_tagihan": harap_bhp,
            "selisih": np.clip(s_tarif + s_bhp, 0, None),
        }

    def posisi(self, episodes) -> np.ndarray:
        """Seberapa dekat tagihan sebuah klaim ke garis penandaannya.

        Nol berarti persis sebesar yang didukung bukti. Satu berarti persis di
        ambang. Negatif berarti menagih di bawah yang wajar.

        Ini bukan hiasan atas selisih rupiah, ini menjawab serangan yang tidak
        bisa dilihat selisih rupiah. Pelaku yang beradaptasi menagih tepat di
        bawah garis, tidak pernah melewatinya, jadi tidak ada satu klaim pun
        yang ditandai. Terukurnya begini. Satu rumah sakit mengambil Rp 36,4
        juta, sepuluh persen dari seluruh tagihannya, dengan cara itu. Rata
        rata selisih rupiahnya bergeser 0,156 juta, sedangkan lantai deteksi
        pada 233 klaim adalah 0,189 juta. Serangannya memang berada di bawah
        derau, jadi tidak ada penaksir rata rata rupiah yang bisa melihatnya.

        Pada ukuran posisi, serangan yang sama bergeser 3,6 simpangan baku.
        Sebabnya pembaginya ambang kelompok, sehingga ragam antar klaim yang
        besarnya berbeda beda ikut terbagi habis, dan yang tersisa tinggal
        perilaku menagihnya.

        Klaim yang kelompoknya menahan diri diberi nol, bukan dibuang, supaya
        rata rata faskes tidak berubah arti hanya karena sebagian klaimnya
        tidak bisa dinilai.
        """
        d = self.skor(episodes)
        s = d["selisih_tarif"] + d["selisih_tagihan"]
        amb, _ = self.ambang_untuk(episodes)
        sah = np.isfinite(amb) & (amb > 0)
        keluar = np.zeros(len(s), dtype=np.float64)
        keluar[sah] = np.clip(s[sah] / amb[sah], -1.0, 1.0)
        return keluar

    # -- kalibrasi ----------------------------------------------------------

    @staticmethod
    def kunci_bertingkat(r) -> list:
        """Tiga tingkat kunci kelompok, dari paling halus ke paling kasar.

        Dipakai untuk mundur bertahap. Kalau kelompok terhalus tidak punya
        cukup data kalibrasi, turun ke yang lebih kasar. Kalau yang paling
        kasar pun tidak cukup, sistem menahan diri dan tidak menandai apa pun
        di sana.
        """
        kelas, dtpk, ada_lab = r["f_kelas"], int(r["f_dtpk"]), 1 if r["lab"] else 0
        return [f"{kelas}|{dtpk}|{ada_lab}", f"{kelas}|{dtpk}", f"{kelas}"]

    @staticmethod
    def kelompok_kalibrasi(episodes) -> np.ndarray:
        """Kunci kelompok untuk kalibrasi konformal.

        Kelas fasilitas kesehatan saja tidak cukup, dan itu terukur. Dengan
        kelas saja, faskes di daerah tertinggal ditandai 3,2 persen sedangkan
        yang bukan 0,6 persen, lima kali lebih sering, pada klaim yang sama
        sama bersih.

        Sebabnya bukan kecurangan. Faskes di daerah tertinggal jarang punya
        laboratorium, jadi klaimnya membawa bukti lebih tipis, dan penebak
        normatif memperkirakan tarif yang lebih rendah untuk bukti yang lebih
        tipis. Selisihnya jadi tampak besar padahal yang kurang alatnya, bukan
        kejujurannya.

        Karena itu kelompok kalibrasi harus memuat tiga hal sekaligus: kelas
        faskes, status daerah tertinggal, dan ada tidaknya pemeriksaan
        penunjang pada klaim itu. Dengan begitu satu klaim dibandingkan hanya
        dengan klaim yang punya keterbatasan serupa.

        Ini melemahkan jaminan menjadi jaminan bersyarat kelompok, dan itu
        justru yang diinginkan. Jaminan bersyarat kelompok berarti puskesmas
        tanpa laboratorium tidak ditandai lebih sering daripada rumah sakit
        kelas A yang punya segalanya.
        """
        return np.array([
            f"{r['f_kelas']}|{int(r['f_dtpk'])}|{1 if r['lab'] else 0}"
            for r in episodes])

    def kalibrasi(self, episodes_bersih) -> "Detektor":
        """Tetapkan ambang penandaan dengan jaminan bebas distribusi.

        Kalibrasi dijalankan per kelas fasilitas kesehatan. Tanpa itu, sistem
        yang diurutkan menurut rupiah tidak pernah menandai FKTP dan menandai
        rumah sakit kelas B seratus kali lebih sering, pada klaim yang sama
        sama bersih. Angka itu diukur, bukan dikhawatirkan: rasio 105 dengan
        ambang tunggal, 1,8 dengan ambang per kelas.
        """
        from .konformal import ambang as ambang_konformal
        from .konformal import ambang_sadar_faskes

        s = self.skor(episodes_bersih)["selisih"]

        # Penyaringan kontaminasi.
        #
        # Nama parameternya berbunyi bersih, tapi di dunia nyata tidak ada
        # tumpukan klaim yang sudah dipastikan bersih. Yang dipakai adalah
        # klaim apa adanya, dan sebagiannya curang. Akibatnya terukur, dan
        # jauh lebih besar daripada yang kami kira.
        #
        # Persentil 98 selisih klaim bersih FKTP adalah 7.415 rupiah, tapi
        # ambang yang terhitung 18.719. Dua setengah kali lipat, terangkat
        # oleh klaim curang yang ikut masuk himpunan kalibrasi. Pada rumah
        # sakit kelas B pengangkatannya hanya 1,3 kali. Bukan karena kelas B
        # lebih jujur, melainkan karena sebaran selisih klaim bersihnya sudah
        # lebar sejak awal sehingga tambahan dari klaim curang tidak banyak
        # menggeser ujung atasnya. Sebaran FKTP rapat, enam puluh persen
        # selisihnya nol persis, jadi sedikit klaim curang langsung mengangkat
        # ujungnya.
        #
        # Itulah sebab ketimpangan yang selama empat percobaan kami kejar di
        # tempat yang salah. Bukan model yang berat sebelah terhadap rumah
        # sakit besar, melainkan FKTP yang ditandai jauh di bawah jatah yang
        # dijanjikan alpha, sehingga laju keseluruhan tertarik ke bawah dan
        # semua kelas rumah sakit terlihat berlebih.
        #
        # Saringannya memakai profil faskes, yaitu kepala K4. Faskes yang
        # selisih rata ratanya menonjol terhadap kelompok sebayanya
        # dikeluarkan dari himpunan kalibrasi. Tidak ada label yang dipakai.
        # Risikonya jelas dan kami tuliskan: model ikut memilih data yang
        # mengkalibrasi dirinya sendiri. Karena itu batas pemotongannya
        # disapu, dan hasilnya dilaporkan pada beberapa nilai, bukan hanya
        # pada yang paling menguntungkan.
        if self.z_saring is not None:
            from .profil import profil_faskes
            prof = profil_faskes(episodes_bersih, s, minimal_klaim=20,
                                 minimal_sebaya=3)
            buang = {k for k, v in prof.items() if v["z"] > self.z_saring}
            simpan = np.array([
                (int(r["f_jenis"]), int(r["faskes"])) not in buang
                for r in episodes_bersih])
            self.n_faskes_dibuang = len(buang)
            self.porsi_klaim_dibuang = round(float(1 - simpan.mean()), 4)
            if simpan.sum() >= self.minimal_kalibrasi:
                episodes_bersih = [r for r, m in zip(episodes_bersih, simpan)
                                   if m]
                s = s[simpan]

        # Kalibrasi bertingkat. Kelompok terhalus dipakai bila datanya cukup.
        # Kalau tidak, mundur ke yang lebih kasar. Kalau yang paling kasar pun
        # tidak cukup, kelompok itu masuk daftar tahan diri.
        #
        # Perlunya ini terukur, bukan diduga. Dengan satu tingkat saja, FKTP
        # di daerah tertinggal tanpa laboratorium ditandai 3,14 persen padahal
        # alpha dua persen, sedangkan FKTP biasa yang berlaboratorium 0,24
        # persen. Tiga belas kali lipat, dan jaminannya bocor justru pada
        # kelompok yang paling sedikit datanya dan paling rentan dipersoalkan.
        per_kunci: dict = {}
        faskes_kunci: dict = {}
        asal_faskes: dict = {}
        for r, nilai in zip(episodes_bersih, s):
            fid = f"{r['f_jenis']}:{r['faskes']}"
            for k in self.kunci_bertingkat(r):
                per_kunci.setdefault(k, []).append(nilai)
                asal_faskes.setdefault(k, []).append(fid)
                faskes_kunci.setdefault(k, set()).add(
                    (r["faskes"], r["f_jenis"]))

        # Syarat kedua: jumlah faskes, bukan hanya jumlah klaim.
        #
        # Ini yang tidak terpikir sampai diukur. Kelompok faskes di daerah
        # tertinggal punya ribuan klaim kalibrasi, jadi lolos syarat jumlah
        # klaim, tapi klaim itu berasal dari segelintir faskes saja. Akibatnya
        # keterpertukaran bocor di tingkat faskes: faskes kalibrasi dan faskes
        # uji berbeda karakternya, dan ambang yang dihitung dari yang satu
        # tidak berlaku untuk yang lain.
        #
        # Terukurnya begini. Dengan syarat jumlah klaim saja, faskes daerah
        # tertinggal ditandai 2,53 persen padahal alpha dua persen, sedangkan
        # yang bukan 0,70 persen.
        # Kunci yang ditolak khusus karena faskesnya kurang, bukan karena
        # klaimnya kurang. Perbedaannya penting dan sempat kami lewatkan.
        #
        # Kalau kelompok terhalus milik sebuah klaim ditolak lalu klaim itu
        # dibiarkan turun ke kelompok yang lebih kasar, yang terjadi bukan
        # berhati hati melainkan sebaliknya: ia menerima ambang yang dihitung
        # dari faskes yang tidak menyerupainya. Terukurnya begini. Dengan
        # syarat empat puluh faskes, klaim di daerah tertinggal jatuh ke
        # ambang FKTP umum dan laju penandaannya melonjak dari 2,5 persen ke
        # 9,4 persen. Penjaganya bekerja terbalik.
        #
        # Jadi penolakan karena kurang faskes berarti menahan diri, titik.
        # Kami tidak menyatakan faskes itu bersih. Kami menyatakan belum
        # cukup tahu untuk berjanji apa apa tentang mereka, dan mereka tetap
        # masuk pemeriksaan lewat porsi sampel acak.
        self.kunci_kurang_faskes = set()
        self.ambang_tingkat = {}
        for k, v in per_kunci.items():
            if (len(v) >= self.minimal_kalibrasi
                    and len(faskes_kunci[k]) < self.minimal_faskes):
                self.kunci_kurang_faskes.add(k)
        for k, v in per_kunci.items():
            if (len(v) >= self.minimal_kalibrasi
                    and len(faskes_kunci[k]) >= self.minimal_faskes):
                self.ambang_tingkat[k] = (
                    ambang_sadar_faskes(v, asal_faskes[k], self.alpha)
                    if self.sadar_faskes
                    else ambang_konformal(np.asarray(v), self.alpha))
        self.ambang_umum = ambang_konformal(s, self.alpha)
        self._terkalibrasi = True
        return self

    def ambang_untuk(self, episodes):
        """Ambang tiap klaim, plus penanda apakah sistem menahan diri.

        Menahan diri berarti klaim itu tidak pernah ditandai otomatis. Ia
        tetap bisa terpilih lewat porsi sampel acak, jadi umpan baliknya tidak
        hilang, tapi tidak ada faskes yang dipersoalkan berdasarkan ambang
        yang dihitung dari data yang terlalu sedikit.
        """
        amb, tahan = [], []
        for r in episodes:
            if self.kecualikan_dtpk and int(r["f_dtpk"]) == 1:
                amb.append(float("inf"))
                tahan.append(True)
                continue
            tingkat = self.kunci_bertingkat(r)
            if tingkat and tingkat[0] in self.kunci_kurang_faskes:
                amb.append(float("inf"))
                tahan.append(True)
                continue
            ketemu = None
            for k in tingkat:
                if k in self.ambang_tingkat:
                    ketemu = self.ambang_tingkat[k]
                    break
            if ketemu is None:
                amb.append(float("inf"))
                tahan.append(True)
            else:
                amb.append(ketemu)
                tahan.append(False)
        return np.array(amb), np.array(tahan)

    def tandai(self, episodes) -> np.ndarray:
        if not self._terkalibrasi:
            raise RuntimeError("panggil kalibrasi dulu")
        s = self.skor(episodes)["selisih"]
        amb, _ = self.ambang_untuk(episodes)
        return s > amb

    # -- peringkat audit ----------------------------------------------------

    def antrean_audit(self, episodes, kapasitas: int = 1000,
                      batas_per_faskes: int | None = None,
                      porsi_acak: float = 0.05) -> list[int]:
        """Antrean pemeriksaan, diurutkan menurut nilai bersih yang diharapkan.

        Tiga hal yang membedakannya dari sekadar mengurutkan skor:

        Biaya audit dikurangkan, sehingga klaim yang selisihnya lebih kecil
        daripada biaya memeriksanya tidak pernah masuk antrean.

        Ada batas per faskes, supaya seluruh kuota tidak habis di satu rumah
        sakit dan cakupannya menyebar.

        Ada porsi kecil sampel acak. Ini terasa sia sia dan memang mahal, tapi
        tanpa itu kita hanya akan pernah tahu kebenaran tentang klaim yang
        sudah kita curigai, dan sistem mengunci diri pada keyakinan awalnya.
        """
        rng = np.random.default_rng(self.seed)
        s = self.skor(episodes)["selisih"]
        bersih = s - self.biaya_audit_rp
        layak = np.flatnonzero(bersih > 0)
        urut = layak[np.argsort(-bersih[layak])]

        n_acak = int(round(kapasitas * porsi_acak))
        n_skor = kapasitas - n_acak

        terpilih: list[int] = []
        hitung: dict = {}
        for i in urut:
            if len(terpilih) >= n_skor:
                break
            f = (episodes[i]["faskes"], episodes[i]["f_jenis"])
            if batas_per_faskes and hitung.get(f, 0) >= batas_per_faskes:
                continue
            hitung[f] = hitung.get(f, 0) + 1
            terpilih.append(int(i))

        sisa = np.setdiff1d(np.arange(len(episodes)), np.array(terpilih or [0]))
        if n_acak > 0 and len(sisa) > 0:
            terpilih += [int(x) for x in
                         rng.choice(sisa, size=min(n_acak, len(sisa)),
                                    replace=False)]
        return terpilih

    # -- penjelasan ---------------------------------------------------------

    def profil_ganda(self, episodes, atas=25):
        """Dua daftar faskes yang saling melengkapi, bukan saling mengganti.

        Yang pertama diurut menurut kelebihan rupiah. Ia menangkap kecurangan
        biasa dengan presisi satu pada dua puluh lima teratas, dan ia buta
        total terhadap faskes yang menagih tepat di bawah garis.

        Yang kedua diurut menurut posisi terhadap garis. Kebalikannya persis.
        Presisinya pada tugas biasa hanya 0,24, jadi ia tidak boleh
        menggantikan yang pertama. Tapi pada serangan yang tidak terlihat
        sama sekali oleh daftar pertama, ia menggerakkan faskes penyerang dari
        peringkat 222 ke 90 dari 238.

        Dua daftar ini menjawab dua pertanyaan berbeda, dan menggabungkannya
        jadi satu skor akan merusak keduanya. Yang pertama bertanya siapa
        menagih lebih daripada yang didukung bukti. Yang kedua bertanya siapa
        menagih terus menerus persis sebanyak yang masih diizinkan.
        """
        from .profil import peringkat_faskes, profil_faskes

        rp = profil_faskes(episodes, self.skor(episodes)["selisih"],
                           minimal_klaim=20)
        ps = profil_faskes(episodes, self.posisi(episodes), minimal_klaim=20)
        return {
            "antrean_rupiah": [
                {"faskes": f"{k[0]}:{k[1]}", "n": v["n"],
                 "kelebihan_rp": v["kelebihan_rp"], "z": v["z"]}
                for k, v in peringkat_faskes(rp, atas=atas)],
            "daftar_pantau_posisi": [
                {"faskes": f"{k[0]}:{k[1]}", "n": v["n"],
                 "posisi_susut": v["rata_susut"],
                 "posisi_sebaya": v["rata_sebaya"],
                 "z": v["z"]}
                for k, v in peringkat_faskes(ps, atas=atas)],
            "catatan": (
                "Daftar kedua bukan tuduhan. Ia menandai faskes yang pola "
                "penagihannya menempel pada batas, yang bisa berarti "
                "pengodean yang rapi dan bisa berarti sesuatu yang lain. "
                "Yang dituntut darinya penjelasan, bukan pengembalian."),
        }

    def jelaskan(self, episodes, i: int) -> dict:
        """Alasan penandaan, dalam bentuk yang bisa dibantah faskes.

        Tiga lapis, sesuai rancangan bagian penjelasan.

        Lapis angka menyatakan berapa yang ditagihkan, berapa yang didukung
        bukti, dan berapa selisihnya.

        Lapis bukti yang hilang menyebut bukti apa yang biasanya menyertai
        kombinasi seperti ini tapi tidak ada di klaim ini, diurutkan menurut
        seberapa besar pengaruhnya terhadap perkiraan. Dihitung dengan
        pengandaian, bukan dengan bobot: untuk tiap bukti yang tidak ada,
        perkiraan dihitung ulang seandainya bukti itu ada.

        Ini bentuk yang bisa dijawab. Kalau kreatininnya sebenarnya ada tapi
        tidak terkirim, rumah sakit tinggal mengirimnya dan penandaan gugur.
        Itu hasil yang baik, bukan kegagalan sistem.
        """
        r = episodes[i]
        s = self.skor([r])
        acuan_bhp = sum(HARGA_ACUAN.get(k, 0) * n for k, n in r["bhp"])

        # pengandaian: bukti apa yang paling mengubah perkiraan bila ada
        pengandaian = []
        for kode in ("HB", "KREA", "LEUKO", "ALB", "NA", "TROMB"):
            if any(k == kode for k, _ in r["lab"]):
                continue
            tiruan = dict(r)
            tiruan["lab"] = list(r["lab"]) + [(kode, 1.0)]
            baru = self.skor([tiruan])["selisih"][0]
            ubah = float(s["selisih"][0] - baru)
            if abs(ubah) > 1000:
                pengandaian.append({"bukti": kode,
                                    "perubahan_selisih_rp": round(ubah)})
        pengandaian.sort(key=lambda x: -abs(x["perubahan_selisih_rp"]))

        return {
            "status": "ketidaksesuaian yang perlu dikonfirmasi",
            "angka": {
                "tarif_ditagihkan": int(r["tarif"]),
                "tarif_didukung_bukti": round(float(s["harapan_tarif"][0])),
                "tagihan_barang_ditagihkan": int(r.get("tagih_bhp", 0)),
                "tagihan_barang_wajar": round(float(s["harapan_tagihan"][0])),
                "nilai_barang_menurut_harga_acuan": int(acuan_bhp),
                "selisih_rp": round(float(s["selisih"][0])),
            },
            "bukti_yang_bila_ada_akan_mengubah_penilaian": pengandaian[:5],
            "konteks": {
                "kelompok_tarif_ditagihkan": r["cbg"],
                "kelas_rawat": r["kelas_rawat"],
                "lama_rawat": r["los"],
                "jumlah_diagnosis_sekunder": len(r["dxs"]),
                "jumlah_pemeriksaan": len(r["lab"]),
                "jumlah_obat": len(r["obt"]),
            },
            "catatan": (
                "Angka di atas bukan tuduhan. Ia menyatakan bahwa tarif yang "
                "ditagihkan lebih besar daripada yang dapat dijelaskan bukti "
                "yang menyertai klaim ini. Fasilitas kesehatan berhak "
                "melengkapi bukti sebelum ada konsekuensi apa pun."),
        }

    # -- simpan dan muat ----------------------------------------------------

    def simpan(self, jalur: str) -> None:
        import pickle
        os.makedirs(os.path.dirname(jalur) or ".", exist_ok=True)
        with open(jalur, "wb") as f:
            pickle.dump({"m_tarif": self.m_tarif, "m_bhp": self.m_bhp,
                         "ambang_tingkat": self.ambang_tingkat,
                         "ambang_umum": self.ambang_umum,
                         "minimal_kalibrasi": self.minimal_kalibrasi,
                         "minimal_faskes": self.minimal_faskes,
                         "kecualikan_dtpk": self.kecualikan_dtpk,
                         "alpha": self.alpha, "seed": self.seed,
                         "biaya_audit_rp": self.biaya_audit_rp}, f)

    @classmethod
    def muat(cls, jalur: str) -> "Detektor":
        import pickle
        with open(jalur, "rb") as f:
            d = pickle.load(f)
        o = cls(alpha=d["alpha"], seed=d["seed"],
                biaya_audit_rp=d["biaya_audit_rp"])
        o.m_tarif, o.m_bhp = d["m_tarif"], d["m_bhp"]
        o.ambang_tingkat = d["ambang_tingkat"]
        o.ambang_umum = d["ambang_umum"]
        o.minimal_kalibrasi = d["minimal_kalibrasi"]
        o.minimal_faskes = d.get("minimal_faskes", 3)
        o.kecualikan_dtpk = d.get("kecualikan_dtpk", True)
        o._terlatih = o._terkalibrasi = True
        return o
