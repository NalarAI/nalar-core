"""Pengelompokan kasus dan tarif INA-CBG.

Sejak 6 September 2026 berkas ini memakai tabel tarif resmi dari lampiran
Permenkes 3/2023, bukan lagi tabel tebakan. Yang berubah bukan cuma angkanya:

  1. Kode kelompok sekarang kode asli. Tebakan lama cuma sepuluh persen yang
     benar benar ada di peraturan, dan huruf CMG-nya banyak meleset. Stroke
     ternyata masuk G bukan A, pneumonia masuk J bukan D.
  2. Tarif tidak lagi dihitung dari tarif dasar dikali pengali keparahan.
     Tiap kombinasi kode, kelas rawat, kelas rumah sakit, regional, dan
     kepemilikan punya angkanya sendiri.
  3. Kepemilikan rumah sakit memengaruhi tarif. Tabel tebakan tidak memuat
     itu sama sekali.
  4. Rawat inap dan rawat jalan adalah keluarga kelompok yang terpisah,
     bukan tarif yang sama dengan pengali.

Aturan keparahan tetap pendekatan kami sendiri. Grouper resmi memakai logika
yang jauh lebih rinci, dan meniru itu bukan tujuan kami. Yang penting untuk
model adalah menambah satu diagnosis sekunder berat memindahkan kelompok dan
menaikkan bayaran, dan struktur itu benar.

Jalur lama masih ada sebagai cadangan, dipakai hanya bila berkas tarif resmi
belum diekstraksi. Pemakaiannya dicatat supaya tidak diam diam terpakai.
"""

from __future__ import annotations

from dataclasses import dataclass

from .katalog import KOMORBID_BY_ICD, KONDISI_BY_ICD

# --- Casemix Main Group, huruf resmi dari lampiran --------------------------

CMG = {
    "A": "Infeksi dan Parasit",
    "B": "Hepatobilier dan Pankreas",
    "C": "Hematologi dan Onkologi",
    "D": "Darah dan Organ Pembentuk Darah",
    "E": "Endokrin, Nutrisi dan Metabolik",
    "F": "Kesehatan Jiwa dan Perilaku",
    "G": "Sistem Saraf",
    "H": "Mata dan Adneksa",
    "I": "Sistem Kardiovaskular",
    "J": "Sistem Pernapasan",
    "K": "Sistem Pencernaan",
    "L": "Integumen dan Payudara",
    "M": "Muskuloskeletal dan Jaringan Ikat",
    "N": "Nefro-urinari",
    "O": "Kehamilan dan Persalinan",
    "P": "Bayi Baru Lahir dan Neonatal",
    "S": "Kelompok Khusus",
    "T": "Penyalahgunaan Zat",
    "U": "THT dan Mulut",
    "V": "Reproduksi Pria",
    "W": "Reproduksi Wanita",
    "Z": "Faktor Lain",
}

TIPE_PROSEDUR_RI = 1
TIPE_PROSEDUR_BESAR_RJ = 2
TIPE_PROSEDUR_SIGNIFIKAN_RJ = 3
TIPE_RI_BUKAN_PROSEDUR = 4
TIPE_RJ_BUKAN_PROSEDUR = 5

# Prosedur yang menandai kasus sebagai kasus prosedur. Dipakai untuk memilih
# kelompok, bukan lagi untuk mengalikan tarif, karena kelompok prosedur punya
# tarifnya sendiri di peraturan.
PROSEDUR_BESAR = {
    "36.06", "01.24", "81.54", "79.35", "78.55", "79.32", "74.1", "68.4",
    "68.29", "51.23", "51.22", "47.01", "47.09", "13.41", "13.59", "12.64",
    "60.29", "45.73", "85.41", "56.0", "96.71", "41.31", "92.24", "99.25",
}
PROSEDUR_SIGNIFIKAN_RJ = {"39.95", "99.25", "92.24", "99.04", "99.06",
                          "45.13", "45.23", "13.41", "95.02"}

_hitung_jalur = {"resmi": 0, "cadangan": 0}


def statistik_jalur() -> dict:
    """Berapa kali tarif diambil dari peraturan, berapa kali dari cadangan."""
    total = sum(_hitung_jalur.values()) or 1
    return dict(_hitung_jalur) | {
        "porsi_resmi": round(_hitung_jalur["resmi"] / total, 4)}


@dataclass(frozen=True)
class Kelompok:
    kode: str
    cmg: str
    tipe: int
    nomor: int
    keparahan: int
    rawat_inap: bool


def _berat(icd: str) -> bool:
    if icd in KOMORBID_BY_ICD:
        return bool(KOMORBID_BY_ICD[icd]["berat"])
    if icd in KONDISI_BY_ICD:
        return bool(KONDISI_BY_ICD[icd]["berat"])
    return False


def hitung_keparahan(dxs: list[str], los: int, rawat_inap: bool) -> int:
    """Tingkat keparahan dari diagnosis sekunder.

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
    """Petakan satu episode ke satu kelompok tarif resmi."""
    from .peta_cbg import kode_cbg

    keparahan = hitung_keparahan(dxs, los, rawat_inap)
    kode = kode_cbg(dxp, keparahan, rawat_inap)
    if kode is None:
        # kondisi di luar katalog, dipetakan ke kelompok faktor lain
        kode = f"Z-4-99-{'I' if rawat_inap else '0'}"
    bagian = kode.split("-")
    return Kelompok(kode, bagian[0], int(bagian[1]), int(bagian[2]),
                    keparahan, rawat_inap)


def tarif(kel: Kelompok, dxp: str, prc: list[str], kelas_rawat: int,
          kelas_rs: str, regional: int,
          kepemilikan: str = "PEMERINTAH") -> int:
    """Tarif paket dari tabel resmi, dalam rupiah.

    regional pada peraturan bernomor 1 sampai 5. Pembangkit memakai 0 sampai 4,
    jadi digeser satu di sini dan hanya di sini.
    """
    from .tarif_resmi import tarif_resmi, tersedia

    if tersedia():
        v = tarif_resmi(kel.kode, kelas_rawat, kelas_rs,
                        int(regional) + 1, kepemilikan)
        if v:
            _hitung_jalur["resmi"] += 1
            return int(v)

    _hitung_jalur["cadangan"] += 1
    return _tarif_cadangan(kel, dxp, prc, kelas_rawat, kelas_rs, regional)


# --- jalur cadangan ---------------------------------------------------------
# Dipakai hanya bila data/processed/tarif_inacbg.csv belum ada. Angkanya
# pendekatan kami sendiri dan tidak boleh dipakai untuk klaim apa pun.

_DASAR_CADANGAN = 3_000_000
_PENGALI_KEPARAHAN = {0: 0.22, 1: 1.00, 2: 1.42, 3: 2.05}
_PENGALI_KELAS_RAWAT = {3: 1.00, 2: 1.20, 1: 1.44}
_PENGALI_KELAS_RS = {"D": 0.85, "C": 1.00, "B": 1.15, "A": 1.32, "FKTP": 0.70}
_PENGALI_REGIONAL = {0: 1.00, 1: 1.03, 2: 1.06, 3: 1.09, 4: 1.13}


def _tarif_cadangan(kel, dxp, prc, kelas_rawat, kelas_rs, regional) -> int:
    nilai = _DASAR_CADANGAN * _PENGALI_KEPARAHAN.get(kel.keparahan, 1.0)
    if kel.rawat_inap:
        nilai *= _PENGALI_KELAS_RAWAT.get(kelas_rawat, 1.0)
    nilai *= _PENGALI_KELAS_RS.get(kelas_rs, 1.0)
    nilai *= _PENGALI_REGIONAL.get(regional, 1.0)
    return int(round(nilai / 1000.0) * 1000)


def daftar_kelompok() -> list[str]:
    """Seluruh kode kelompok yang mungkin dihasilkan pemetaan katalog.

    Dipakai membangun kamus token bidang TRF dan kepala K2, yang mengeluarkan
    sebaran peluang atas seluruh kelompok.
    """
    from .peta_cbg import PETA

    kode = set()
    for icd in PETA:
        for kep in (1, 2, 3):
            k = kelompokkan(icd, [], [], 3, True).kode
            kode.add(k.rsplit("-", 1)[0] + "-" + {1: "I", 2: "II", 3: "III"}[kep])
        kode.add(kelompokkan(icd, [], [], 0, False).kode)
    kode.add("Z-4-99-I")
    kode.add("Z-4-99-0")
    return sorted(kode)
