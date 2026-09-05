"""Kebijakan faskes dan injeksi modus kecurangan.

Gagasan kuncinya, kecurangan tidak ditaburkan acak per klaim. Ia melekat pada
perilaku faskes. Kalau ditaburkan acak, tidak ada faskes yang lebih curang dari
faskes lain, seluruh keluarga C mati, dan hasil evaluasinya menyesatkan karena
di dunia nyata kecurangan memang mengelompok.

Tiap injeksi mengembalikan tiga hal: klaim yang diubah, klaim aslinya, dan
selisih rupiahnya. Selisih itu kebenaran dasar yang dipakai seluruh evaluasi.

Modus yang tidak diinjeksikan: M15 tindakan tidak sesuai indikasi dan M18
pengurangan jumlah obat. Keduanya tidak meninggalkan jejak pada data yang
kami bangkitkan. Menginjeksikannya lalu mengaku mendeteksinya akan menjadi
pembuktian yang kosong.
"""

from __future__ import annotations

import numpy as np

from . import katalog as K
from .tarif import hitung_keparahan, kelompokkan, tarif
from .vocab import HARGA_ACUAN

# --- kebijakan --------------------------------------------------------------

JUJUR = 0
OPORTUNIS = 1
SISTEMATIS = 2
EKSTREM = 3
NAMA_KEBIJAKAN = ("jujur", "oportunis", "sistematis", "ekstrem")

# porsi tiap kebijakan bila prevalensi faskes nakal ditetapkan 0.22
PORSI_NAKAL = np.array([0.636, 0.273, 0.091])  # oportunis, sistematis, ekstrem

# Modus yang dipakai tiap kebijakan, beserta peluangnya per klaim yang
# memenuhi syarat. Angka angka ini asumsi, dan analisis kepekaan dijalankan
# pada tiga tingkat prevalensi.
INTENSITAS = {
    OPORTUNIS: dict(M04=0.30, M12=0.10, M13=0.08, M07=0.12, M17=0.06,
                    M20=0.08, M09=0.06, M11=0.02, M08=0.05, M03=0.05),
    SISTEMATIS: dict(M04=0.62, M12=0.24, M13=0.22, M07=0.30, M17=0.20,
                     M20=0.22, M09=0.18, M11=0.06, M08=0.16, M03=0.16),
    EKSTREM: dict(M04=0.80, M12=0.34, M13=0.32, M07=0.48, M17=0.45,
                  M20=0.34, M09=0.28, M11=0.14, M08=0.26, M03=0.26,
                  M06=0.35, M05=0.30),
}

# Diagnosis sekunder berat yang paling sering dipakai menaikkan keparahan.
# Kalau bukti pendukungnya tidak ikut ditambahkan, inilah yang seharusnya
# terlihat oleh kepala K1.
KODE_PENAIK = ["N17", "E87.6", "E87.1", "J96", "E43", "R57.2", "D65", "K72"]


class Kebijakan:
    """Kebijakan per faskes, plus keadaan yang perlu diingat."""

    def __init__(self, n_fkrtl: int, n_fktp: int):
        self.rs = np.zeros(n_fkrtl, dtype=np.int64)
        self.fktp = np.zeros(n_fktp, dtype=np.int64)
        # faskes rujukan favorit, dipakai modus M10
        self.rs_favorit = np.full(n_fktp, -1, dtype=np.int64)


def tetapkan_kebijakan(jaringan, rng: np.random.Generator,
                       prevalensi: float = 0.22,
                       minimal_per_jenis: int = 3) -> Kebijakan:
    """Tetapkan kebijakan per faskes, berstrata.

    Undian bebas menghasilkan masalah pada jaringan kecil. Dengan dua puluh
    rumah sakit dan porsi ekstrem dua persen, jumlah yang diharapkan kurang
    dari satu, jadi sering tidak ada satu pun faskes ekstrem dan kepala K4
    serta K5 tidak punya apa apa untuk ditemukan. Evaluasinya lalu terlihat
    seolah kepala itu gagal, padahal soalnya memang kosong.

    Penetapan berstrata menjamin tiap jenis kebijakan punya wakil minimal.
    Porsi keseluruhan tetap dijaga sedekat mungkin dengan yang diminta, dan
    penyimpangannya dicatat supaya bisa diperiksa.
    """
    keb = Kebijakan(jaringan.n_fkrtl, jaringan.n_fktp)
    for arr, n in ((keb.rs, jaringan.n_fkrtl), (keb.fktp, jaringan.n_fktp)):
        target = np.maximum(
            np.round(n * prevalensi * PORSI_NAKAL).astype(int),
            min(minimal_per_jenis, max(n // 8, 1)))
        total = int(target.sum())
        if total > n:
            target = np.floor(target * n / total).astype(int)
            total = int(target.sum())
        pilih = rng.permutation(n)[:total]
        ofs = 0
        for jenis, jml in zip((OPORTUNIS, SISTEMATIS, EKSTREM), target):
            arr[pilih[ofs:ofs + jml]] = jenis
            ofs += jml
    # sebagian FKTP nakal punya rumah sakit favorit
    for i in np.flatnonzero(keb.fktp > 0):
        if rng.random() < 0.55:
            keb.rs_favorit[i] = int(rng.integers(jaringan.n_fkrtl))
    return keb


def _peluang(keb_kode: int, modus: str) -> float:
    if keb_kode == JUJUR:
        return 0.0
    return INTENSITAS[keb_kode].get(modus, 0.0)


# --- injeksi per episode ----------------------------------------------------

def terapkan(rec: dict, keb: Kebijakan, jaringan, rng: np.random.Generator) -> None:
    """Ubah satu klaim menurut kebijakan faskesnya.

    Menulis bidang yang diamati, daftar modus, dan selisih rupiah.
    """
    kode = int(keb.rs[rec["faskes"]] if rec["f_jenis"] else keb.fktp[rec["faskes"]])

    dxs = list(rec["dxs_j"])
    prc = list(rec["prc_j"])
    obt = list(rec["obt_j"])
    lab = [list(x) for x in rec["lab_j"]]
    bhp = [list(x) for x in rec["bhp_j"]]
    los = rec["los_j"]
    kelas_rawat = rec["kelas_rawat_j"]
    modus: list[str] = []
    selisih_bhp = 0

    # --- M04 upcoding ------------------------------------------------------
    # Menambah diagnosis sekunder berat tanpa menambah buktinya. Varian sulit
    # ikut memalsukan bukti, dan varian itu hampir tidak bisa dilihat dari satu
    # klaim. Sengaja dimasukkan supaya hasil evaluasi tidak terlalu optimistis.
    # Hanya dilakukan bila masih ada ruang untuk naik. Klaim yang sudah
    # keparahan III tidak bisa dinaikkan lagi, jadi menambah kode di situ
    # tidak menghasilkan rupiah apa pun. Menandainya sebagai kecurangan akan
    # memasukkan kasus bernilai nol ke dalam kebenaran dasar, dan model jadi
    # dihukum karena tidak menemukan uang yang memang tidak ada.
    ada_ruang = hitung_keparahan(dxs, los, rec["rawat_inap"]) < 3
    if rec["rawat_inap"] and ada_ruang and rng.random() < _peluang(kode, "M04"):
        kandidat = [c for c in KODE_PENAIK if c not in dxs]
        if kandidat:
            n = 1 if rng.random() < 0.7 else 2
            tambah = list(rng.choice(kandidat, size=min(n, len(kandidat)),
                                     replace=False))
            dxs.extend(tambah)
            modus.append("M04")
            # varian yang ikut memalsukan bukti
            if rng.random() < 0.28:
                for d in tambah:
                    kk = K.KOMORBID_BY_ICD.get(d)
                    if not kk:
                        continue
                    for kd, arah in kk["bukti_lab"]:
                        lab = [x for x in lab if x[0] != kd]
                        lo, hi = K.PEMERIKSAAN[kd][1], K.PEMERIKSAAN[kd][2]
                        lebar = hi - lo
                        nilai = lo + (1.6 if arah > 0 else -0.4) * lebar
                        lab.append([kd, float(nilai)])
                modus.append("M04b")

    # --- M12 perpanjangan lama rawat --------------------------------------
    if rec["rawat_inap"] and rng.random() < _peluang(kode, "M12"):
        # perpanjang sampai melewati ambang sepuluh hari, yang pada aturan
        # keparahan kami memindahkan kelompok bila ada satu diagnosis berat
        if los < 10:
            los = int(rng.integers(10, 14))
            modus.append("M12")

    # --- M13 manipulasi kelas perawatan ------------------------------------
    if rec["rawat_inap"] and kelas_rawat > 1 and rng.random() < _peluang(kode, "M13"):
        kelas_rawat -= 1
        modus.append("M13")

    # --- M17 dan M14 tindakan atau barang fiktif ---------------------------
    if rng.random() < _peluang(kode, "M17"):
        pilih = rng.choice(["ALK009", "ALK002", "ALK011", "ALK012", "ALK001"])
        ada = [b for b in bhp if b[0] == pilih]
        if ada:
            ada[0][1] += int(rng.integers(2, 8))
        else:
            bhp.append([str(pilih), int(rng.integers(2, 6))])
        modus.append("M17")

    # --- M07 penggelembungan harga -----------------------------------------
    if bhp and rng.random() < _peluang(kode, "M07"):
        pengali = float(rng.uniform(1.25, 2.10))
        rec["pengali_harga"] = pengali
        modus.append("M07")
    else:
        rec["pengali_harga"] = 1.0

    # --- M20 manipulasi hasil pemeriksaan ----------------------------------
    # Nilai digeser sampai tepat melewati ambang penagihan. Sebaran yang wajar
    # tidak menumpuk di ambang, sebaran yang dimanipulasi menumpuk. Ini uji
    # yang sangat kuat dan sangat murah, asal nilainya ada di data.
    if lab and rng.random() < _peluang(kode, "M20"):
        bisa = [x for x in lab if x[0] in K.AMBANG_PENAGIHAN]
        if bisa:
            x = bisa[int(rng.integers(len(bisa)))]
            ambang = K.AMBANG_PENAGIHAN[x[0]]
            lo, hi = K.PEMERIKSAAN[x[0]][1], K.PEMERIKSAAN[x[0]][2]
            arah_bawah = ambang <= lo
            geser = abs(rng.normal(0, 0.02)) * max(abs(ambang), 1.0)
            x[1] = float(ambang - geser) if arah_bawah else float(ambang + geser)
            modus.append("M20")

    # --- M09 fragmentasi tindakan ------------------------------------------
    PASANGAN = {"47.01": "47.09", "51.23": "51.22", "79.35": "78.55"}
    if rng.random() < _peluang(kode, "M09"):
        for a, b in PASANGAN.items():
            if a in prc and b not in prc:
                prc.append(b)
                modus.append("M09")
                break

    # --- M03 rujukan tidak sesuai ------------------------------------------
    if rec["f_jenis"] == 0 and rng.random() < _peluang(kode, "M03"):
        modus.append("M03")

    # --- hitung ulang kelompok dan tarif ------------------------------------
    kel = kelompokkan(rec["dxp"], dxs, prc, los, rec["rawat_inap"])
    trf = tarif(kel, rec["dxp"], prc, kelas_rawat, rec["f_kelas"], rec["f_reg"])

    # tagihan bahan habis pakai, di luar paket
    tagih_bhp_j = sum(HARGA_ACUAN.get(k, 0) * n for k, n in rec["bhp_j"])
    tagih_bhp = int(sum(HARGA_ACUAN.get(k, 0) * n for k, n in bhp)
                    * rec["pengali_harga"])
    selisih_bhp = tagih_bhp - tagih_bhp_j

    # Jaring pengaman. Kalau seluruh perubahan ternyata tidak menghasilkan
    # rupiah, klaim ini tidak dicatat sebagai terpengaruh. Kebenaran dasar
    # harus menyatakan uang, bukan niat.
    selisih_total = int(trf - rec["tarif_j"] + selisih_bhp)
    if selisih_total <= 0:
        modus = []

    rec.update(
        dxs=dxs, prc=prc, obt=obt,
        lab=[(k, float(v)) for k, v in lab],
        bhp=[(k, int(n)) for k, n in bhp],
        los=los, kelas_rawat=kelas_rawat,
        cbg=kel.kode, keparahan=kel.keparahan, tarif=trf,
        tagih_bhp=tagih_bhp, tagih_bhp_j=tagih_bhp_j,
        kebijakan=kode, modus=modus,
        selisih_rp=max(selisih_total, 0),
    )


# --- injeksi lintas episode -------------------------------------------------

def pasca(episodes: list[dict], keb: Kebijakan, jaringan,
          rng: np.random.Generator) -> list[dict]:
    """Modus yang hanya bisa dilakukan dengan melihat lebih dari satu klaim.

    M11 penagihan berulang, M08 dan M16 pemecahan episode, M05 penjiplakan,
    M06 klaim atas layanan yang tidak pernah diberikan.
    """
    tambahan: list[dict] = []
    per_faskes: dict[int, list[int]] = {}
    for i, r in enumerate(episodes):
        per_faskes.setdefault(r["faskes"] if r["f_jenis"] else -1, []).append(i)

    next_id = max(r["eps_id"] for r in episodes) + 1 if episodes else 0

    for r in episodes:
        kode = int(keb.rs[r["faskes"]] if r["f_jenis"]
                   else keb.fktp[r["faskes"]])
        if kode == JUJUR:
            continue

        # --- M11 penagihan berulang ---------------------------------------
        # Duplikat sempurna akan tertangkap indeks unik. Yang menarik adalah
        # duplikat yang sengaja dirusak sedikit di satu kolom, karena itu lolos
        # pemeriksaan kunci dan hanya terlihat sebagai kemiripan berlebih.
        if rng.random() < _peluang(kode, "M11"):
            d = dict(r)
            d["eps_id"] = next_id
            next_id += 1
            d["hari"] = r["hari"] + int(rng.integers(1, 4))
            d["modus"] = list(r["modus"]) + ["M11"]
            d["selisih_rp"] = int(r["tarif"] + r["tagih_bhp"])
            d["duplikat_dari"] = r["eps_id"]
            tambahan.append(d)

        # --- M08 dan M16 pemecahan episode --------------------------------
        if r["rawat_inap"] and r["los"] >= 5 and rng.random() < _peluang(kode, "M08"):
            los_a = max(1, r["los"] // 2)
            los_b = max(1, r["los"] - los_a)
            prc = list(r["prc"])
            prc_a = prc[: max(1, len(prc) // 2)] if prc else []
            prc_b = prc[len(prc_a):]

            a = dict(r)
            a["los"] = los_a
            a["prc"] = prc_a
            kel_a = kelompokkan(a["dxp"], a["dxs"], prc_a, los_a, True)
            a["cbg"], a["keparahan"] = kel_a.kode, kel_a.keparahan
            a["tarif"] = tarif(kel_a, a["dxp"], prc_a, a["kelas_rawat"],
                               a["f_kelas"], a["f_reg"])

            b = dict(r)
            b["eps_id"] = next_id
            next_id += 1
            b["hari"] = r["hari"] + los_a + int(rng.integers(0, 3))
            b["los"] = los_b
            b["prc"] = prc_b
            kel_b = kelompokkan(b["dxp"], b["dxs"], prc_b, los_b, True)
            b["cbg"], b["keparahan"] = kel_b.kode, kel_b.keparahan
            b["tarif"] = tarif(kel_b, b["dxp"], prc_b, b["kelas_rawat"],
                               b["f_kelas"], b["f_reg"])
            b["tagih_bhp"] = 0

            selisih = a["tarif"] + b["tarif"] - r["tarif"]
            a["modus"] = list(r["modus"]) + ["M08"]
            b["modus"] = list(r["modus"]) + ["M08"]
            a["selisih_rp"] = r["selisih_rp"] + selisih // 2
            b["selisih_rp"] = selisih - selisih // 2
            b["pecahan_dari"] = r["eps_id"]
            r.update(a)
            tambahan.append(b)

    # --- M05 penjiplakan ---------------------------------------------------
    for faskes, idxs in per_faskes.items():
        if faskes < 0 or len(idxs) < 6:
            continue
        kode = int(keb.rs[faskes])
        if kode == JUJUR or rng.random() >= _peluang(kode, "M05"):
            continue
        # ambil satu klaim sumber, salin isinya ke beberapa klaim lain milik
        # pasien berbeda. Yang membedakan penjiplakan dari protokol klinis
        # adalah kesamaan pada variabel yang seharusnya bervariasi, yaitu
        # nilai pemeriksaan dan lama rawat.
        sumber = episodes[int(rng.choice(idxs))]
        n_salin = int(rng.integers(3, 9))
        sasaran = rng.choice(idxs, size=min(n_salin, len(idxs)), replace=False)
        for j in sasaran:
            t = episodes[int(j)]
            if t["eps_id"] == sumber["eps_id"]:
                continue
            asal_tarif = t["tarif"]
            t["dxs"] = list(sumber["dxs"])
            t["prc"] = list(sumber["prc"])
            t["obt"] = list(sumber["obt"])
            t["lab"] = list(sumber["lab"])
            t["los"] = sumber["los"]
            kel = kelompokkan(t["dxp"], t["dxs"], t["prc"], t["los"],
                              t["rawat_inap"])
            t["cbg"], t["keparahan"] = kel.kode, kel.keparahan
            t["tarif"] = tarif(kel, t["dxp"], t["prc"], t["kelas_rawat"],
                               t["f_kelas"], t["f_reg"])
            t["modus"] = list(t["modus"]) + ["M05"]
            t["selisih_rp"] = t["selisih_rp"] + (t["tarif"] - asal_tarif)

    # --- M06 klaim atas layanan yang tidak pernah diberikan ---------------
    # Ditempelkan pada peserta nyata yang memang terdaftar, sesuai pola kasus
    # 2024. Bedanya dari klaim jujur, tidak ada obat dan tidak ada pemeriksaan.
    for faskes, idxs in per_faskes.items():
        if faskes < 0 or not idxs:
            continue
        kode = int(keb.rs[faskes])
        if kode != EKSTREM:
            continue
        n_palsu = int(len(idxs) * float(rng.uniform(0.10, 0.30)))
        for _ in range(n_palsu):
            asal = episodes[int(rng.choice(idxs))]
            d = dict(asal)
            d["eps_id"] = next_id
            next_id += 1
            d["hari"] = int(rng.integers(0, max(asal["hari"] + 1, 2)))
            d["obt"] = []
            d["lab"] = []
            d["bhp"] = []
            d["tagih_bhp"] = 0
            d["modus"] = ["M06"]
            d["selisih_rp"] = int(d["tarif"])
            d["fiktif"] = True
            tambahan.append(d)

    episodes.extend(tambahan)
    episodes.sort(key=lambda r: (r["peserta_id"], r["hari"], r["eps_id"]))
    prev: dict[int, int] = {}
    for r in episodes:
        p = r["peserta_id"]
        r["d_prev"] = r["hari"] - prev[p] if p in prev else -1
        prev[p] = r["hari"]
    return episodes
