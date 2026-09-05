"""Pengelompokan kasus dan tabel tarif bergaya INA-CBG.

PENTING. Ini pendekatan, bukan replika. Grouper INA-CBG resmi memakai logika
yang jauh lebih rinci dan tabel tarif resmi ada di lampiran Permenkes 3/2023.
Yang kami tiru adalah aturan pokoknya:

  1. Kasus dipetakan ke satu Casemix Main Group menurut sistem organ.
  2. Jenis kasus dibedakan antara ada prosedur atau tidak, rawat inap atau jalan.
  3. Tingkat keparahan naik karena diagnosis sekunder, bukan karena biaya.
  4. Tarif adalah satu paket, tidak bergantung pada biaya sebenarnya.

Yang penting untuk model kami bukan angkanya persis, tapi bahwa menambah satu
diagnosis sekunder yang berat memindahkan kelompok tarif dan menaikkan bayaran.
Struktur itulah yang membuat upcoding punya arti, dan struktur itu yang ditiru.

Begitu tabel tarif resmi berhasil diekstraksi dari lampiran Permenkes, berkas
ini diganti pemetaannya, bukan ditulis ulang. Antarmukanya sengaja dijaga.
"""

from __future__ import annotations

from dataclasses import dataclass

from .katalog import KOMORBID_BY_ICD, KONDISI_BY_ICD

# --- Casemix Main Group -----------------------------------------------------
# Huruf mengikuti konvensi INA-CBG yang beredar umum. Pemetaan kondisi ke huruf
# adalah keputusan kami.

CMG = {
    "A": "Sistem Saraf",
    "B": "Mata dan Adneksa",
    "C": "Sistem THT dan Mulut",
    "D": "Sistem Pernapasan",
    "E": "Sistem Kardiovaskular",
    "F": "Sistem Pencernaan",
    "G": "Sistem Hepatobilier dan Pankreas",
    "H": "Sistem Muskuloskeletal dan Jaringan Ikat",
    "I": "Sistem Integumen dan Payudara",
    "J": "Sistem Endokrin, Nutrisi dan Metabolik",
    "K": "Sistem Nefro-urinari",
    "L": "Sistem Reproduksi Pria",
    "M": "Sistem Reproduksi Wanita",
    "N": "Kehamilan dan Persalinan",
    "O": "Bayi Baru Lahir dan Neonatal",
    "P": "Sistem Darah dan Imun",
    "Q": "Neoplasma dan Mieloproliferatif",
    "R": "Infeksi dan Parasit",
    "S": "Kesehatan Jiwa dan Perilaku",
    "U": "Cedera dan Keracunan",
    "Z": "Prosedur dan Faktor Lain",
}

# jenis kasus, mengikuti penomoran INA-CBG
TIPE_PROSEDUR_RI = 1
TIPE_PROSEDUR_BESAR_RJ = 2
TIPE_PROSEDUR_SIGNIFIKAN_RJ = 3
TIPE_RI_BUKAN_PROSEDUR = 4
TIPE_RJ_BUKAN_PROSEDUR = 5

# --- pemetaan kondisi ke CMG, nomor kelompok, dan tarif dasar ---------------
# tarif_ri  : tarif rawat inap, tingkat keparahan I, kelas rawat 3,
#             rumah sakit kelas C, regional 1, dalam rupiah
# tarif_rj  : tarif rawat jalan tanpa prosedur besar
#
# Angka disusun agar peringkat biaya antar-kelompok mendekati gambaran nyata.
# Seluruhnya berstatus asumsi sampai tabel resmi masuk.

PETA_KONDISI = {
    "I10":   ("E", 8, 2_800_000, 190_000),
    "E11":   ("J", 12, 3_600_000, 230_000),
    "E78":   ("J", 15, 2_400_000, 180_000),
    "I50":   ("E", 5, 6_400_000, 320_000),
    "I21":   ("E", 2, 14_500_000, 480_000),
    "I20":   ("E", 4, 5_600_000, 300_000),
    "I48":   ("E", 6, 5_200_000, 290_000),
    "I63":   ("A", 3, 7_400_000, 340_000),
    "I61":   ("A", 2, 11_800_000, 380_000),
    "G45":   ("A", 5, 5_000_000, 280_000),
    "N18":   ("K", 4, 6_800_000, 330_000),
    "Z49":   ("Z", 3, 1_050_000, 980_000),
    "N20":   ("K", 8, 4_400_000, 250_000),
    "N39.0": ("K", 12, 3_200_000, 200_000),
    "N40":   ("L", 3, 4_800_000, 260_000),
    "A15":   ("R", 4, 5_400_000, 260_000),
    "J18":   ("D", 6, 4_600_000, 240_000),
    "A91":   ("R", 6, 4_000_000, 230_000),
    "A01.0": ("R", 8, 3_400_000, 210_000),
    "A09":   ("F", 14, 2_600_000, 180_000),
    "A41":   ("R", 2, 12_600_000, 420_000),
    "B20":   ("R", 10, 6_200_000, 300_000),
    "B18":   ("G", 6, 5_400_000, 290_000),
    "B54":   ("R", 12, 3_200_000, 200_000),
    "L03":   ("I", 8, 3_800_000, 220_000),
    "J44":   ("D", 4, 5_600_000, 280_000),
    "J45":   ("D", 8, 3_400_000, 200_000),
    "J06":   ("D", 14, 1_900_000, 150_000),
    "K29":   ("F", 12, 2_800_000, 190_000),
    "K35":   ("F", 3, 7_600_000, 340_000),
    "K80":   ("G", 3, 8_200_000, 330_000),
    "K92":   ("F", 5, 7_000_000, 330_000),
    "C50":   ("Q", 4, 8_400_000, 420_000),
    "C53":   ("Q", 6, 8_000_000, 410_000),
    "C34":   ("Q", 5, 8_800_000, 430_000),
    "C18":   ("Q", 7, 9_200_000, 430_000),
    "C11":   ("Q", 8, 7_800_000, 400_000),
    "C22":   ("Q", 9, 8_600_000, 420_000),
    "C92":   ("Q", 2, 14_000_000, 520_000),
    "D56":   ("P", 3, 4_200_000, 1_150_000),
    "D66":   ("P", 2, 7_600_000, 2_400_000),
    "D50":   ("P", 8, 2_600_000, 180_000),
    "H25":   ("B", 3, 4_600_000, 260_000),
    "H40":   ("B", 6, 3_400_000, 230_000),
    "O80":   ("N", 6, 2_400_000, 210_000),
    "O82":   ("N", 2, 6_200_000, 320_000),
    "O14":   ("N", 4, 5_400_000, 300_000),
    "D25":   ("M", 4, 6_400_000, 290_000),
    "P07":   ("O", 2, 9_600_000, 340_000),
    "P59":   ("O", 5, 4_200_000, 230_000),
    "S72":   ("U", 2, 11_200_000, 380_000),
    "S52":   ("U", 5, 5_200_000, 260_000),
    "S06":   ("U", 3, 8_400_000, 330_000),
    "M17":   ("H", 8, 4_800_000, 250_000),
    "M54":   ("H", 12, 2_400_000, 170_000),
    "G40":   ("A", 8, 4_600_000, 250_000),
    "F20":   ("S", 3, 6_800_000, 240_000),
    "E05":   ("J", 8, 3_800_000, 220_000),
    "J00":   ("D", 15, 1_600_000, 140_000),
    "K30":   ("F", 16, 1_900_000, 150_000),
    "R51":   ("A", 14, 1_800_000, 150_000),
    "L30":   ("I", 12, 1_700_000, 150_000),
    "H10":   ("B", 12, 1_600_000, 140_000),
    "M79":   ("H", 14, 1_800_000, 150_000),
    "K02":   ("C", 10, 1_500_000, 145_000),
    "R50":   ("Z", 12, 2_200_000, 160_000),
}

# Prosedur yang memindahkan kasus ke jenis prosedur, beserta tambahan tarif.
# Tambahan dinyatakan sebagai pengali terhadap tarif dasar, karena INA-CBG
# membayar paket, bukan menjumlahkan komponen.
PROSEDUR_BESAR = {
    "36.06": 4.20,   # pemasangan stent koroner
    "01.24": 3.40,   # kraniotomi
    "81.54": 3.20,   # penggantian lutut total
    "79.35": 1.75,   # reduksi terbuka fiksasi interna femur
    "78.55": 1.45,
    "79.32": 1.35,
    "74.1": 1.55,    # seksio sesarea
    "68.4": 1.70,    # histerektomi abdominal total
    "68.29": 1.35,
    "51.23": 1.85,   # kolesistektomi laparoskopik
    "51.22": 1.70,
    "47.01": 1.30,   # apendektomi laparoskopik
    "47.09": 1.20,   # apendektomi
    "13.41": 1.55,   # fakoemulsifikasi
    "13.59": 1.35,
    "12.64": 1.40,
    "60.29": 1.80,   # prostatektomi transuretral
    "45.73": 2.40,
    "85.41": 1.90,   # mastektomi
    "56.0": 1.45,
    "96.71": 1.90,   # ventilasi mekanik
    "41.31": 1.60,
    "39.95": 1.00,   # hemodialisis, sudah jadi kelompok tersendiri
    "92.24": 1.45,   # radioterapi
    "99.25": 1.35,   # kemoterapi
}

# prosedur signifikan rawat jalan
PROSEDUR_SIGNIFIKAN_RJ = {"39.95", "99.25", "92.24", "99.04", "99.06", "45.13",
                          "45.23", "13.41", "95.02"}

# --- pengali ----------------------------------------------------------------

PENGALI_KEPARAHAN = {1: 1.00, 2: 1.42, 3: 2.05}
PENGALI_KELAS_RAWAT = {3: 1.00, 2: 1.20, 1: 1.44}
PENGALI_KELAS_RS = {"D": 0.85, "C": 1.00, "B": 1.15, "A": 1.32, "FKTP": 0.70}
PENGALI_REGIONAL = {0: 1.00, 1: 1.03, 2: 1.06, 3: 1.09, 4: 1.13}


@dataclass(frozen=True)
class Kelompok:
    """Hasil pengelompokan satu episode."""

    kode: str          # misalnya E-4-08-II
    cmg: str
    tipe: int
    nomor: int
    keparahan: int     # 1, 2, 3 untuk rawat inap, 0 untuk rawat jalan
    rawat_inap: bool


def _berat(icd: str) -> bool:
    """Apakah diagnosis ini menaikkan tingkat keparahan."""
    if icd in KOMORBID_BY_ICD:
        return bool(KOMORBID_BY_ICD[icd]["berat"])
    if icd in KONDISI_BY_ICD:
        return bool(KONDISI_BY_ICD[icd]["berat"])
    return False


def hitung_keparahan(dxs: list[str], los: int, rawat_inap: bool) -> int:
    """Tingkat keparahan dari diagnosis sekunder.

    Aturan yang kami pakai, menghormati semangat INA-CBG bahwa keparahan
    ditentukan komorbiditas dan komplikasi, bukan biaya:

      III  dua atau lebih diagnosis sekunder berat,
           atau satu berat dengan lama rawat panjang
      II   satu diagnosis sekunder berat, atau tiga atau lebih ringan
      I    selain itu
    """
    if not rawat_inap:
        return 0
    n_berat = sum(1 for d in dxs if _berat(d))
    n_ringan = len(dxs) - n_berat
    if n_berat >= 2 or (n_berat >= 1 and los >= 10):
        return 3
    if n_berat >= 1 or n_ringan >= 3:
        return 2
    return 1


def kelompokkan(dxp: str, dxs: list[str], prc: list[str], los: int,
                rawat_inap: bool) -> Kelompok:
    """Petakan satu episode ke satu kelompok tarif."""
    cmg, nomor, _, _ = (*PETA_KONDISI.get(dxp, ("Z", 99, 2_000_000, 160_000)),)[:4]

    prc_besar = [p for p in prc if p in PROSEDUR_BESAR]
    if rawat_inap:
        tipe = TIPE_PROSEDUR_RI if prc_besar else TIPE_RI_BUKAN_PROSEDUR
    else:
        if prc_besar:
            tipe = TIPE_PROSEDUR_BESAR_RJ
        elif any(p in PROSEDUR_SIGNIFIKAN_RJ for p in prc):
            tipe = TIPE_PROSEDUR_SIGNIFIKAN_RJ
        else:
            tipe = TIPE_RJ_BUKAN_PROSEDUR

    keparahan = hitung_keparahan(dxs, los, rawat_inap)
    romawi = {0: "0", 1: "I", 2: "II", 3: "III"}[keparahan]
    kode = f"{cmg}-{tipe}-{nomor:02d}-{romawi}"
    return Kelompok(kode, cmg, tipe, nomor, keparahan, rawat_inap)


def tarif(kel: Kelompok, dxp: str, prc: list[str], kelas_rawat: int,
          kelas_rs: str, regional: int) -> int:
    """Tarif paket untuk satu kelompok, dalam rupiah."""
    _, _, dasar_ri, dasar_rj = PETA_KONDISI.get(
        dxp, ("Z", 99, 2_000_000, 160_000))
    nilai = dasar_ri if kel.rawat_inap else dasar_rj

    pengali_prc = 1.0
    for p in prc:
        if p in PROSEDUR_BESAR:
            pengali_prc = max(pengali_prc, PROSEDUR_BESAR[p])
    nilai *= pengali_prc

    if kel.rawat_inap:
        nilai *= PENGALI_KEPARAHAN[kel.keparahan]
        nilai *= PENGALI_KELAS_RAWAT[kelas_rawat]
    nilai *= PENGALI_KELAS_RS[kelas_rs]
    nilai *= PENGALI_REGIONAL[regional]
    return int(round(nilai / 1000.0) * 1000)


def daftar_kelompok() -> list[str]:
    """Seluruh kode kelompok yang mungkin dihasilkan pemetaan ini.

    Dipakai untuk membangun kamus token bidang TRF dan untuk kepala K2, yang
    mengeluarkan sebaran peluang atas seluruh kelompok.
    """
    kode = []
    for dxp, (cmg, nomor, _, _) in PETA_KONDISI.items():
        for tipe in (TIPE_PROSEDUR_RI, TIPE_RI_BUKAN_PROSEDUR):
            for rom in ("I", "II", "III"):
                kode.append(f"{cmg}-{tipe}-{nomor:02d}-{rom}")
        for tipe in (TIPE_PROSEDUR_BESAR_RJ, TIPE_PROSEDUR_SIGNIFIKAN_RJ,
                     TIPE_RJ_BUKAN_PROSEDUR):
            kode.append(f"{cmg}-{tipe}-{nomor:02d}-0")
    return sorted(set(kode))
