"""Pemetaan kondisi katalog ke kelompok INA-CBG resmi.

Dibuat setelah tabel tarif resmi berhasil diekstraksi dari lampiran
Permenkes 3/2023. Sebelum ini, kode kelompok tarif di tarif.py dikarang
sendiri, dan ternyata hanya sepuluh persen di antaranya benar benar ada di
peraturan. Huruf CMG-nya pun banyak yang meleset, misalnya stroke ternyata
masuk G bukan A, dan pneumonia masuk J bukan D.

Tiap entri menyimpan kelompok untuk rawat inap dan untuk rawat jalan, karena
keduanya kelompok yang berbeda di INA-CBG, bukan tarif yang sama dengan
pengali. Kolom cocok menyatakan seberapa yakin pemetaannya:

  tepat    deskripsi resminya menyebut kondisi ini secara langsung
  dekat    kelompok terdekat yang masuk akal secara klinis
  payung   kelompok umum yang menampung banyak kondisi sekaligus

Yang bertanda payung perlu diperiksa lagi kalau ekstraksi tabel diperbaiki.
Ekstraksi sekarang menangkap 885 dari sekitar 1.077 kelompok, jadi sebagian
kelompok yang lebih tepat mungkin memang belum terbaca.
"""

from __future__ import annotations

# (kelompok rawat inap tanpa keparahan, kelompok rawat jalan, tingkat cocok)
PETA = {
    # kardiovaskular dan metabolik
    "I10": ("I-4-17", "I-4-17", "tepat"),      # hipertensi
    "E11": ("E-4-10", "E-4-10", "tepat"),      # penyakit kencing manis
    "E78": ("E-4-10", "E-4-10", "dekat"),      # gangguan metabolik
    "I50": ("I-4-12", "I-4-12", "tepat"),      # kegagalan jantung
    "I21": ("I-4-11", "I-4-11", "dekat"),      # infark miokard
    "I20": ("I-4-20", "I-4-20", "tepat"),      # angina pektoris
    "I48": ("I-4-19", "I-4-19", "tepat"),      # aritmia
    # serebrovaskular
    "I63": ("G-4-14", "G-4-14", "tepat"),      # infark serebral
    "I61": ("G-4-13", "G-4-13", "tepat"),      # perdarahan intrakranial
    "G45": ("G-4-16", "G-4-16", "tepat"),      # iskemik transien
    # ginjal dan urin
    "N18": ("N-4-10", "N-4-10", "dekat"),      # kegagalan ginjal
    "Z49": ("N-1-12", "N-3-12", "dekat"),      # dialisis
    "N20": ("N-4-13", "N-4-13", "tepat"),      # batu urin
    "N39.0": ("N-4-12", "N-4-12", "dekat"),    # infeksi saluran kemih
    "N40": ("V-1-10", "V-1-10", "tepat"),      # prostat
    # infeksi
    "A15": ("A-4-13", "A-4-13", "dekat"),      # tuberkulosis
    "J18": ("J-4-16", "J-4-16", "tepat"),      # pneumonia
    "A91": ("A-4-12", "A-4-12", "payung"),     # demam berdarah
    "A01.0": ("A-4-14", "A-4-14", "payung"),   # tifoid
    "A09": ("K-4-17", "K-4-17", "tepat"),      # gastroenteritis
    "A41": ("A-4-11", "A-4-11", "dekat"),      # sepsis
    "B20": ("A-4-15", "A-4-15", "tepat"),      # HIV
    "B18": ("B-4-10", "B-4-10", "tepat"),      # hepatitis
    "B54": ("A-4-14", "A-4-14", "payung"),     # malaria
    "L03": ("L-4-10", "L-4-10", "dekat"),      # selulitis
    # pernapasan
    "J44": ("J-4-17", "J-4-17", "tepat"),      # PPOK
    "J45": ("J-4-18", "J-4-18", "tepat"),      # asma
    "J06": ("U-4-16", "U-4-16", "dekat"),      # ISPA
    "J00": ("U-4-16", "U-4-16", "dekat"),      # nasofaringitis
    # pencernaan
    "K29": ("K-4-11", "K-4-11", "tepat"),      # gastritis
    "K30": ("K-4-11", "K-4-11", "dekat"),      # dispepsia
    "K35": ("K-1-12", "K-1-12", "dekat"),      # apendisitis
    "K80": ("B-1-11", "B-1-11", "tepat"),      # kolelitiasis
    "K92": ("K-4-13", "K-4-13", "dekat"),      # perdarahan cerna
    # kanker
    "C50": ("C-4-13", "C-3-13", "tepat"),      # payudara
    "C53": ("C-4-13", "C-3-14", "dekat"),      # serviks
    "C34": ("C-4-13", "C-3-11", "tepat"),      # paru
    "C18": ("C-4-13", "C-3-12", "tepat"),      # kolon
    "C11": ("C-4-13", "C-3-17", "dekat"),      # nasofaring
    "C22": ("C-4-13", "C-3-16", "dekat"),      # hati
    "C92": ("C-4-10", "C-3-18", "tepat"),      # leukemia
    # darah
    "D56": ("D-4-13", "D-3-10", "dekat"),      # talasemia
    "D66": ("D-4-14", "D-3-10", "dekat"),      # hemofilia
    "D50": ("D-4-12", "D-4-12", "dekat"),      # anemia
    # mata
    "H25": ("H-1-30", "H-2-36", "tepat"),      # katarak
    "H40": ("H-1-31", "H-2-30", "dekat"),      # glaukoma
    "H10": ("H-4-10", "H-4-10", "dekat"),      # konjungtivitis
    # obstetri dan ginekologi
    "O80": ("O-6-11", "O-6-11", "tepat"),      # persalinan vaginal
    "O82": ("O-6-10", "O-6-10", "tepat"),      # seksio sesarea
    "O14": ("O-6-13", "O-6-13", "dekat"),      # preeklampsia
    "D25": ("W-1-11", "W-1-11", "dekat"),      # mioma uteri
    # neonatal
    "P07": ("P-8-02", "P-8-02", "tepat"),      # berat lahir rendah
    "P59": ("P-8-04", "P-8-04", "dekat"),      # ikterus neonatorum
    # muskuloskeletal dan cedera
    "S72": ("M-4-10", "M-4-10", "tepat"),      # fraktur femur
    "S52": ("M-4-11", "M-4-11", "dekat"),      # fraktur lengan
    "S06": ("G-4-11", "G-4-11", "dekat"),      # cedera intrakranial
    "M17": ("M-4-16", "M-4-16", "dekat"),      # gonartrosis
    "M54": ("M-4-17", "M-4-17", "tepat"),      # dorsalgia
    "M79": ("M-4-17", "M-4-17", "dekat"),      # mialgia
    # saraf dan jiwa
    "G40": ("G-4-22", "G-4-22", "tepat"),      # epilepsi
    "F20": ("F-4-10", "F-5-13", "dekat"),      # skizofrenia
    "E05": ("E-1-20", "E-1-20", "tepat"),      # tirotoksikosis
    # keluhan ringan
    "R51": ("G-4-23", "G-4-23", "tepat"),      # nyeri kepala
    "L30": ("L-4-11", "L-4-11", "dekat"),      # dermatitis
    "K02": ("U-1-10", "U-3-10", "dekat"),      # karies gigi
    "R50": ("A-4-12", "A-4-12", "tepat"),      # demam tidak ditentukan
}

ROMAWI = {1: "I", 2: "II", 3: "III"}


def kode_cbg(dxp: str, keparahan: int, rawat_inap: bool) -> str | None:
    """Kode INA-CBG lengkap untuk satu diagnosis primer.

    Rawat inap memakai keparahan I, II, atau III. Rawat jalan memakai 0.
    """
    entri = PETA.get(dxp)
    if not entri:
        return None
    dasar = entri[0] if rawat_inap else entri[1]
    if rawat_inap:
        return f"{dasar}-{ROMAWI.get(int(keparahan), 'I')}"
    return f"{dasar}-0"


def ringkas_cocok() -> dict:
    from collections import Counter
    c = Counter(v[2] for v in PETA.values())
    return dict(c) | {"total": len(PETA)}
