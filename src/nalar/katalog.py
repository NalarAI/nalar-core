"""Katalog kondisi klinis, obat, tindakan, dan pemeriksaan.

Ini sumber realisme pembangkit. Kode ICD-10 dan ICD-9-CM nyata. Kode obat
memakai ATC nyata. Kode pemeriksaan memakai singkatan lokal, bukan LOINC,
karena pemetaan LOINC belum dikerjakan dan mengarang nomor LOINC lebih buruk
daripada memakai singkatan yang jujur.

Angka insidens per seribu orang per tahun adalah asumsi kami, disusun agar
peringkat beban penyakit mendekati gambaran Indonesia. Angkanya akan disetel
ulang terhadap Survei Kesehatan Indonesia dan laporan DJSN. Sampai itu terjadi,
seluruh angka di berkas ini berstatus asumsi.
"""

from __future__ import annotations

# pita umur: 0-4, 5-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75-84, 85+
AGE_BANDS = [(0, 4), (5, 14), (15, 24), (25, 34), (35, 44),
             (45, 54), (55, 64), (65, 74), (75, 84), (85, 120)]
N_AGE = len(AGE_BANDS)

# tempat layanan
FKTP_ONLY = "fktp"
RJTL = "rjtl"     # rawat jalan tingkat lanjut
RITL = "ritl"     # rawat inap tingkat lanjut


def _v(*xs):
    """Ringkas penulisan vektor insidens sepanjang sepuluh pita umur."""
    assert len(xs) == N_AGE, len(xs)
    return list(xs)


# Setiap entri:
#   icd        kode ICD-10 utama
#   nama       nama kondisi
#   inc        insidens per 1000 orang per tahun, per pita umur
#   sex        0 semua, 1 laki laki saja, 2 perempuan saja
#   kronis     apakah kondisi menetap dan muncul lagi tiap tahun
#   tempat     daftar tempat layanan yang mungkin, dengan bobot
#   los        (mean, dispersi) lama rawat bila rawat inap
#   prc        daftar (kode ICD-9-CM, peluang)
#   obt        daftar (kode ATC, peluang)
#   lab        daftar (kode pemeriksaan, peluang, arah kelainan)
#              arah: 0 normal, 1 tinggi, -1 rendah
#   komorbid   kondisi yang sering menyertai, dipakai rantai perkembangan
#   berat      apakah kondisi ini menaikkan tingkat keparahan bila jadi sekunder

KONDISI = [
    # --- kardiovaskular dan metabolik ---------------------------------------
    dict(icd="I10", nama="Hipertensi esensial",
         inc=_v(0.0, 0.1, 1.0, 4.0, 14.0, 34.0, 55.0, 68.0, 72.0, 65.0), sex=0,
         kronis=True, tempat={FKTP_ONLY: 0.80, RJTL: 0.19, RITL: 0.01},
         los=(3.0, 1.2),
         prc=[("89.52", 0.30)],
         obt=[("C08CA01", 0.55), ("C09AA02", 0.30), ("C09CA01", 0.25),
              ("C03CA01", 0.15), ("C07AB07", 0.15)],
         lab=[("KOL", 0.35, 1), ("KREA", 0.30, 0), ("GDP", 0.30, 0)],
         komorbid=["E11", "N18", "I50"], berat=False),

    dict(icd="E11", nama="Diabetes melitus tipe 2",
         inc=_v(0.0, 0.05, 0.5, 2.0, 8.0, 20.0, 32.0, 36.0, 30.0, 20.0), sex=0,
         kronis=True, tempat={FKTP_ONLY: 0.60, RJTL: 0.36, RITL: 0.04},
         los=(5.0, 1.5),
         prc=[],
         obt=[("A10BA02", 0.70), ("A10BB12", 0.35), ("A10AB01", 0.20),
              ("C10AA01", 0.25)],
         lab=[("GDP", 0.75, 1), ("HBA1C", 0.45, 1), ("KREA", 0.35, 0)],
         komorbid=["I10", "N18", "H36", "E11.4"], berat=True),

    dict(icd="E78", nama="Gangguan metabolisme lipoprotein",
         inc=_v(0.0, 0.05, 0.4, 1.5, 5.0, 11.0, 15.0, 14.0, 10.0, 6.0), sex=0,
         kronis=True, tempat={FKTP_ONLY: 0.75, RJTL: 0.25},
         los=(2.0, 1.0), prc=[],
         obt=[("C10AA01", 0.55), ("C10AA05", 0.35)],
         lab=[("KOL", 0.80, 1), ("TG", 0.60, 1)],
         komorbid=["I10", "E11"], berat=False),

    dict(icd="I50", nama="Gagal jantung",
         inc=_v(0.02, 0.03, 0.1, 0.3, 1.0, 3.0, 7.0, 13.0, 18.0, 20.0), sex=0,
         kronis=True, tempat={RJTL: 0.45, RITL: 0.55},
         los=(6.5, 1.8),
         prc=[("88.72", 0.55), ("89.52", 0.70), ("87.44", 0.50)],
         obt=[("C03CA01", 0.80), ("C09AA02", 0.45), ("C07AB07", 0.45),
              ("C01AA05", 0.20)],
         lab=[("KREA", 0.70, 1), ("NA", 0.55, -1), ("HB", 0.60, -1),
              ("KAL", 0.55, 0)],
         komorbid=["I10", "N18", "I48"], berat=True),

    dict(icd="I21", nama="Infark miokard akut",
         inc=_v(0.0, 0.0, 0.02, 0.1, 0.5, 1.6, 3.2, 4.5, 4.8, 4.0), sex=0,
         kronis=False, tempat={RITL: 0.95, RJTL: 0.05},
         los=(6.0, 1.6),
         prc=[("89.52", 0.95), ("88.56", 0.40), ("36.06", 0.28),
              ("88.72", 0.55)],
         obt=[("B01AC06", 0.90), ("B01AC04", 0.75), ("C10AA05", 0.70),
              ("C07AB07", 0.55), ("B01AB01", 0.30)],
         lab=[("TROP", 0.90, 1), ("CKMB", 0.60, 1), ("KREA", 0.60, 0),
              ("GDP", 0.45, 0)],
         komorbid=["I10", "E11", "E78"], berat=True),

    dict(icd="I20", nama="Angina pektoris",
         inc=_v(0.0, 0.0, 0.05, 0.2, 1.0, 3.0, 6.0, 8.5, 8.0, 6.0), sex=0,
         kronis=True, tempat={RJTL: 0.70, RITL: 0.30},
         los=(4.0, 1.3),
         prc=[("89.52", 0.85), ("88.56", 0.20)],
         obt=[("B01AC06", 0.80), ("C10AA05", 0.60), ("C01DA02", 0.50)],
         lab=[("TROP", 0.50, 0), ("KOL", 0.45, 1)],
         komorbid=["I10", "E11"], berat=True),

    dict(icd="I48", nama="Fibrilasi dan flutter atrium",
         inc=_v(0.0, 0.0, 0.02, 0.05, 0.2, 0.8, 2.2, 4.5, 6.5, 7.0), sex=0,
         kronis=True, tempat={RJTL: 0.60, RITL: 0.40},
         los=(4.5, 1.4),
         prc=[("89.52", 0.90)],
         obt=[("C01AA05", 0.40), ("B01AA03", 0.35), ("C07AB07", 0.50)],
         lab=[("TSH", 0.30, 0), ("KREA", 0.45, 0)],
         komorbid=["I50", "I10"], berat=True),

    # --- serebrovaskular ----------------------------------------------------
    dict(icd="I63", nama="Infark serebral",
         inc=_v(0.0, 0.01, 0.03, 0.15, 0.6, 2.2, 5.0, 9.0, 12.0, 12.0), sex=0,
         kronis=False, tempat={RITL: 0.92, RJTL: 0.08},
         los=(8.0, 2.0),
         prc=[("88.38", 0.75), ("87.03", 0.60), ("93.11", 0.35)],
         obt=[("B01AC06", 0.80), ("C10AA05", 0.60), ("B01AC04", 0.35),
              ("N07CA01", 0.20)],
         lab=[("GDP", 0.70, 0), ("KOL", 0.55, 1), ("HB", 0.60, 0)],
         komorbid=["I10", "E11", "I48"], berat=True),

    dict(icd="I61", nama="Perdarahan intraserebral",
         inc=_v(0.0, 0.01, 0.03, 0.1, 0.4, 1.2, 2.4, 3.6, 4.0, 3.5), sex=0,
         kronis=False, tempat={RITL: 0.97, RJTL: 0.03},
         los=(10.0, 2.4),
         prc=[("87.03", 0.85), ("01.24", 0.18), ("96.71", 0.25)],
         obt=[("C03CA01", 0.45), ("B05BA03", 0.60), ("N02BE01", 0.40)],
         lab=[("HB", 0.75, 0), ("PT", 0.45, 0), ("KREA", 0.55, 0)],
         komorbid=["I10"], berat=True),

    dict(icd="G45", nama="Serangan iskemik serebral transien",
         inc=_v(0.0, 0.0, 0.02, 0.05, 0.2, 0.7, 1.5, 2.4, 2.8, 2.4), sex=0,
         kronis=False, tempat={RJTL: 0.55, RITL: 0.45},
         los=(4.0, 1.3),
         prc=[("87.03", 0.55), ("88.71", 0.30)],
         obt=[("B01AC06", 0.75), ("C10AA05", 0.50)],
         lab=[("GDP", 0.55, 0), ("KOL", 0.45, 1)],
         komorbid=["I10", "E11"], berat=True),

    # --- ginjal -------------------------------------------------------------
    dict(icd="N18", nama="Penyakit ginjal kronik",
         inc=_v(0.01, 0.02, 0.1, 0.3, 1.0, 3.0, 6.0, 9.0, 10.0, 9.0), sex=0,
         kronis=True, tempat={RJTL: 0.60, RITL: 0.40},
         los=(6.0, 1.7),
         prc=[("39.95", 0.55), ("38.95", 0.30), ("88.75", 0.35)],
         obt=[("B03XA01", 0.45), ("C03CA01", 0.50), ("A11CC04", 0.30),
              ("C08CA01", 0.40)],
         lab=[("KREA", 0.92, 1), ("UR", 0.80, 1), ("HB", 0.80, -1),
              ("KAL", 0.60, 1), ("ALB", 0.40, -1)],
         komorbid=["I10", "E11", "I50"], berat=True),

    dict(icd="Z49", nama="Perawatan dialisis",
         inc=_v(0.0, 0.01, 0.05, 0.2, 0.6, 1.6, 3.0, 4.0, 3.6, 2.4), sex=0,
         kronis=True, tempat={RJTL: 0.95, RITL: 0.05},
         los=(2.0, 1.0),
         prc=[("39.95", 0.98), ("38.95", 0.15)],
         obt=[("B03XA01", 0.70), ("B01AB01", 0.60), ("A11CC04", 0.40)],
         lab=[("KREA", 0.85, 1), ("HB", 0.85, -1), ("KAL", 0.70, 1)],
         komorbid=["N18", "I10", "E11"], berat=True),

    dict(icd="N20", nama="Batu ginjal dan ureter",
         inc=_v(0.02, 0.05, 0.5, 1.4, 2.4, 2.8, 2.6, 2.0, 1.4, 0.8), sex=0,
         kronis=False, tempat={RJTL: 0.55, RITL: 0.45},
         los=(3.5, 1.2),
         prc=[("88.75", 0.70), ("98.51", 0.30), ("56.0", 0.15)],
         obt=[("M01AB05", 0.60), ("J01MA02", 0.35), ("N02BE01", 0.45)],
         lab=[("KREA", 0.60, 0), ("URIN", 0.70, 1)],
         komorbid=[], berat=False),

    dict(icd="N39.0", nama="Infeksi saluran kemih",
         inc=_v(2.0, 1.2, 3.0, 4.0, 4.4, 4.8, 5.4, 6.4, 7.6, 8.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.76, RJTL: 0.18, RITL: 0.06},
         los=(4.0, 1.2),
         prc=[("57.94", 0.25)],
         obt=[("J01MA02", 0.50), ("J01CA04", 0.30), ("J01DD04", 0.25)],
         lab=[("URIN", 0.80, 1), ("LEUKO", 0.55, 1), ("KREA", 0.35, 0)],
         komorbid=["E11"], berat=False),

    dict(icd="N40", nama="Hiperplasia prostat",
         inc=_v(0.0, 0.0, 0.0, 0.05, 0.4, 2.4, 7.0, 12.0, 14.0, 12.0), sex=1,
         kronis=True, tempat={RJTL: 0.65, RITL: 0.35},
         los=(4.0, 1.2),
         prc=[("88.75", 0.60), ("60.29", 0.22), ("57.94", 0.30)],
         obt=[("G04CA02", 0.65), ("G04CB01", 0.30)],
         lab=[("KREA", 0.50, 0), ("PSA", 0.45, 1)],
         komorbid=[], berat=False),

    # --- infeksi ------------------------------------------------------------
    dict(icd="A15", nama="Tuberkulosis paru",
         inc=_v(0.6, 0.5, 2.2, 2.8, 2.6, 2.4, 2.2, 2.0, 1.6, 1.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.74, RJTL: 0.20, RITL: 0.06},
         los=(8.0, 2.2),
         prc=[("87.44", 0.85), ("90.41", 0.60)],
         obt=[("J04AB02", 0.90), ("J04AC01", 0.90), ("J04AK01", 0.80),
              ("J04AK02", 0.75), ("N02BE01", 0.30)],
         lab=[("BTA", 0.80, 1), ("LED", 0.55, 1), ("HB", 0.50, -1),
              ("SGPT", 0.45, 0)],
         komorbid=["B20", "E11"], berat=True),

    dict(icd="J18", nama="Pneumonia",
         inc=_v(14.0, 2.4, 1.2, 1.4, 1.8, 2.6, 4.4, 8.0, 14.0, 20.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.52, RJTL: 0.24, RITL: 0.24},
         los=(6.0, 1.7),
         prc=[("87.44", 0.90), ("93.94", 0.35), ("96.71", 0.08)],
         obt=[("J01DD04", 0.70), ("J01FA09", 0.30), ("N02BE01", 0.60),
              ("R03AC02", 0.30)],
         lab=[("LEUKO", 0.85, 1), ("HB", 0.60, 0), ("CRP", 0.45, 1),
              ("AGD", 0.25, -1)],
         komorbid=["J44", "E11", "I50"], berat=True),

    dict(icd="A91", nama="Demam berdarah dengue",
         inc=_v(3.0, 5.0, 3.4, 2.4, 1.8, 1.4, 1.0, 0.8, 0.6, 0.4), sex=0,
         kronis=False, tempat={RITL: 0.55, RJTL: 0.20, FKTP_ONLY: 0.25},
         los=(4.5, 1.1),
         prc=[("90.59", 0.85), ("99.04", 0.10)],
         obt=[("B05BA03", 0.90), ("N02BE01", 0.85)],
         lab=[("TROMB", 0.95, -1), ("HT", 0.85, 1), ("LEUKO", 0.75, -1),
              ("HB", 0.70, 0)],
         komorbid=[], berat=False),

    dict(icd="A01.0", nama="Demam tifoid",
         inc=_v(2.4, 4.4, 3.0, 2.0, 1.4, 1.0, 0.8, 0.6, 0.4, 0.3), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.62, RJTL: 0.16, RITL: 0.22},
         los=(5.0, 1.3),
         prc=[("90.59", 0.60)],
         obt=[("J01DD04", 0.65), ("J01MA02", 0.30), ("N02BE01", 0.80)],
         lab=[("WIDAL", 0.75, 1), ("LEUKO", 0.60, -1), ("HB", 0.45, 0)],
         komorbid=[], berat=False),

    dict(icd="A09", nama="Diare dan gastroenteritis",
         inc=_v(30.0, 8.0, 5.0, 4.6, 4.2, 4.0, 4.2, 5.0, 6.4, 7.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.88, RJTL: 0.06, RITL: 0.06},
         los=(3.0, 1.0),
         prc=[],
         obt=[("A07CA", 0.70), ("B05BA03", 0.45), ("A07BC05", 0.30),
              ("J01MA02", 0.20)],
         lab=[("LEUKO", 0.35, 0), ("NA", 0.30, -1), ("KAL", 0.30, -1)],
         komorbid=[], berat=False),

    dict(icd="A41", nama="Sepsis",
         inc=_v(1.2, 0.2, 0.15, 0.2, 0.4, 0.9, 1.8, 3.2, 5.0, 6.4), sex=0,
         kronis=False, tempat={RITL: 0.99, RJTL: 0.01},
         los=(9.0, 2.6),
         prc=[("38.93", 0.75), ("96.71", 0.30), ("90.59", 0.85)],
         obt=[("J01DD04", 0.80), ("J01XA01", 0.30), ("C01CA24", 0.35),
              ("B05BA03", 0.90)],
         lab=[("LEUKO", 0.90, 1), ("LAKTAT", 0.55, 1), ("KREA", 0.70, 1),
              ("PCT", 0.40, 1), ("TROMB", 0.60, -1)],
         komorbid=["N18", "E11", "J18"], berat=True),

    dict(icd="B20", nama="Penyakit HIV",
         inc=_v(0.05, 0.02, 0.3, 0.5, 0.4, 0.25, 0.15, 0.08, 0.04, 0.02), sex=0,
         kronis=True, tempat={RJTL: 0.80, RITL: 0.20},
         los=(7.0, 2.0),
         prc=[("87.44", 0.30)],
         obt=[("J05AR", 0.85), ("J05AF05", 0.40), ("J01EE01", 0.25)],
         lab=[("CD4", 0.70, -1), ("HB", 0.55, -1), ("SGPT", 0.40, 0)],
         komorbid=["A15"], berat=True),

    dict(icd="B18", nama="Hepatitis virus kronik",
         inc=_v(0.1, 0.15, 0.5, 0.8, 1.0, 1.2, 1.2, 1.0, 0.7, 0.4), sex=0,
         kronis=True, tempat={RJTL: 0.80, RITL: 0.20},
         los=(6.0, 1.8),
         prc=[("88.76", 0.45)],
         obt=[("J05AF05", 0.50), ("J05AF08", 0.30)],
         lab=[("SGPT", 0.85, 1), ("SGOT", 0.80, 1), ("BIL", 0.50, 1),
              ("ALB", 0.40, -1)],
         komorbid=["C22"], berat=True),

    dict(icd="B54", nama="Malaria",
         inc=_v(1.0, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.78, RITL: 0.16, RJTL: 0.06},
         los=(4.0, 1.2),
         prc=[("90.59", 0.80)],
         obt=[("P01BF01", 0.70), ("P01BA01", 0.25), ("N02BE01", 0.70)],
         lab=[("MALARIA", 0.85, 1), ("HB", 0.70, -1), ("TROMB", 0.55, -1)],
         komorbid=[], berat=False),

    dict(icd="L03", nama="Selulitis",
         inc=_v(1.6, 1.2, 1.4, 1.6, 1.8, 2.2, 2.8, 3.4, 3.8, 3.6), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.68, RJTL: 0.20, RITL: 0.12},
         los=(5.0, 1.4),
         prc=[("86.28", 0.45)],
         obt=[("J01CR02", 0.55), ("J01DD04", 0.35), ("N02BE01", 0.50)],
         lab=[("LEUKO", 0.65, 1), ("GDP", 0.45, 1)],
         komorbid=["E11"], berat=False),

    # --- pernapasan ---------------------------------------------------------
    dict(icd="J44", nama="Penyakit paru obstruktif kronik",
         inc=_v(0.0, 0.05, 0.1, 0.3, 1.0, 3.0, 7.0, 12.0, 15.0, 14.0), sex=0,
         kronis=True, tempat={RJTL: 0.62, RITL: 0.20, FKTP_ONLY: 0.18},
         los=(6.0, 1.7),
         prc=[("87.44", 0.70), ("93.94", 0.50), ("89.37", 0.25)],
         obt=[("R03AC02", 0.80), ("R03BB01", 0.45), ("H02AB06", 0.40),
              ("J01DD04", 0.30)],
         lab=[("AGD", 0.40, -1), ("LEUKO", 0.45, 0), ("HB", 0.40, 0)],
         komorbid=["I50", "J18"], berat=True),

    dict(icd="J45", nama="Asma",
         inc=_v(6.0, 8.0, 4.0, 3.0, 2.8, 2.6, 2.4, 2.2, 1.8, 1.2), sex=0,
         kronis=True, tempat={FKTP_ONLY: 0.60, RJTL: 0.28, RITL: 0.12},
         los=(3.5, 1.1),
         prc=[("93.94", 0.55), ("87.44", 0.30)],
         obt=[("R03AC02", 0.85), ("R03BA02", 0.40), ("H02AB06", 0.30)],
         lab=[("LEUKO", 0.30, 0)],
         komorbid=[], berat=False),

    dict(icd="J06", nama="Infeksi saluran napas atas akut",
         inc=_v(60.0, 30.0, 18.0, 16.0, 15.0, 14.0, 13.0, 12.0, 11.0, 9.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.95, RJTL: 0.05},
         los=(2.0, 0.8),
         prc=[],
         obt=[("N02BE01", 0.70), ("J01CA04", 0.30), ("R05CB", 0.35)],
         lab=[],
         komorbid=[], berat=False),

    # --- pencernaan ---------------------------------------------------------
    dict(icd="K29", nama="Gastritis dan duodenitis",
         inc=_v(1.0, 3.0, 10.0, 12.0, 12.0, 11.0, 10.0, 9.0, 8.0, 6.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.75, RJTL: 0.18, RITL: 0.07},
         los=(3.0, 1.0),
         prc=[("45.13", 0.12)],
         obt=[("A02BC01", 0.70), ("A02BA02", 0.35), ("A03FA01", 0.30)],
         lab=[("HB", 0.30, 0)],
         komorbid=[], berat=False),

    dict(icd="K35", nama="Apendisitis akut",
         inc=_v(0.3, 1.4, 2.0, 1.8, 1.4, 1.1, 0.9, 0.7, 0.5, 0.3), sex=0,
         kronis=False, tempat={RITL: 0.96, RJTL: 0.04},
         los=(4.0, 1.1),
         prc=[("47.09", 0.55), ("47.01", 0.38), ("88.76", 0.55)],
         obt=[("J01DD04", 0.80), ("N02BE01", 0.70), ("M01AB05", 0.35)],
         lab=[("LEUKO", 0.90, 1), ("HB", 0.65, 0)],
         komorbid=[], berat=False),

    dict(icd="K80", nama="Kolelitiasis",
         inc=_v(0.02, 0.1, 0.6, 1.6, 2.6, 3.4, 3.8, 3.4, 2.6, 1.6), sex=0,
         kronis=False, tempat={RJTL: 0.45, RITL: 0.55},
         los=(4.5, 1.3),
         prc=[("88.76", 0.80), ("51.23", 0.35), ("51.22", 0.10)],
         obt=[("M01AB05", 0.50), ("J01DD04", 0.45), ("A03FA01", 0.30)],
         lab=[("BIL", 0.60, 1), ("SGPT", 0.55, 1), ("LEUKO", 0.50, 0)],
         komorbid=[], berat=False),

    dict(icd="K92", nama="Perdarahan saluran cerna",
         inc=_v(0.05, 0.1, 0.3, 0.5, 0.9, 1.6, 2.6, 3.6, 4.4, 4.4), sex=0,
         kronis=False, tempat={RITL: 0.92, RJTL: 0.08},
         los=(6.0, 1.8),
         prc=[("45.13", 0.65), ("99.04", 0.45)],
         obt=[("A02BC02", 0.85), ("B05BA03", 0.70)],
         lab=[("HB", 0.92, -1), ("HT", 0.80, -1), ("TROMB", 0.45, 0)],
         komorbid=["K29", "B18"], berat=True),

    # --- kanker -------------------------------------------------------------
    dict(icd="C50", nama="Neoplasma ganas payudara",
         inc=_v(0.0, 0.0, 0.05, 0.3, 1.2, 2.6, 3.4, 3.2, 2.4, 1.6), sex=2,
         kronis=True, tempat={RJTL: 0.72, RITL: 0.28},
         los=(6.0, 1.8),
         prc=[("99.25", 0.60), ("85.41", 0.20), ("92.24", 0.25),
              ("88.73", 0.35)],
         obt=[("L01CD01", 0.40), ("L01AA01", 0.35), ("L02BG04", 0.25),
              ("N02BE01", 0.45)],
         lab=[("HB", 0.75, -1), ("LEUKO", 0.70, -1), ("TROMB", 0.60, -1),
              ("SGPT", 0.40, 0)],
         komorbid=[], berat=True),

    dict(icd="C53", nama="Neoplasma ganas serviks uteri",
         inc=_v(0.0, 0.0, 0.02, 0.2, 0.9, 1.8, 2.2, 1.8, 1.2, 0.7), sex=2,
         kronis=True, tempat={RJTL: 0.65, RITL: 0.35},
         los=(6.5, 1.9),
         prc=[("99.25", 0.55), ("92.24", 0.40), ("68.4", 0.15)],
         obt=[("L01XA01", 0.50), ("L01CD01", 0.25)],
         lab=[("HB", 0.80, -1), ("LEUKO", 0.65, -1), ("KREA", 0.45, 0)],
         komorbid=[], berat=True),

    dict(icd="C34", nama="Neoplasma ganas bronkus dan paru",
         inc=_v(0.0, 0.0, 0.02, 0.08, 0.4, 1.4, 3.0, 4.4, 4.4, 3.2), sex=0,
         kronis=True, tempat={RJTL: 0.55, RITL: 0.45},
         los=(7.0, 2.1),
         prc=[("87.44", 0.75), ("99.25", 0.50), ("88.38", 0.40)],
         obt=[("L01XA01", 0.45), ("L01CD01", 0.30), ("N02AA01", 0.30)],
         lab=[("HB", 0.75, -1), ("LEUKO", 0.60, 0), ("NA", 0.40, -1)],
         komorbid=["J44"], berat=True),

    dict(icd="C18", nama="Neoplasma ganas kolon",
         inc=_v(0.0, 0.0, 0.03, 0.1, 0.4, 1.2, 2.4, 3.4, 3.6, 2.8), sex=0,
         kronis=True, tempat={RJTL: 0.58, RITL: 0.42},
         los=(7.5, 2.2),
         prc=[("45.23", 0.55), ("99.25", 0.50), ("45.73", 0.18)],
         obt=[("L01BC02", 0.55), ("L01XA01", 0.30)],
         lab=[("HB", 0.80, -1), ("ALB", 0.45, -1), ("SGPT", 0.35, 0)],
         komorbid=[], berat=True),

    dict(icd="C11", nama="Neoplasma ganas nasofaring",
         inc=_v(0.0, 0.02, 0.1, 0.3, 0.7, 1.1, 1.2, 0.9, 0.6, 0.3), sex=0,
         kronis=True, tempat={RJTL: 0.70, RITL: 0.30},
         los=(6.0, 1.8),
         prc=[("92.24", 0.60), ("99.25", 0.50), ("88.38", 0.35)],
         obt=[("L01XA01", 0.55), ("L01BC02", 0.30)],
         lab=[("HB", 0.70, -1), ("LEUKO", 0.60, -1)],
         komorbid=[], berat=True),

    dict(icd="C22", nama="Neoplasma ganas hati",
         inc=_v(0.0, 0.0, 0.02, 0.08, 0.3, 0.9, 1.8, 2.4, 2.2, 1.4), sex=0,
         kronis=True, tempat={RJTL: 0.50, RITL: 0.50},
         los=(7.0, 2.0),
         prc=[("88.76", 0.75), ("99.25", 0.30)],
         obt=[("L01XE16", 0.25), ("N02AA01", 0.35)],
         lab=[("SGPT", 0.80, 1), ("BIL", 0.70, 1), ("ALB", 0.60, -1),
              ("AFP", 0.45, 1)],
         komorbid=["B18"], berat=True),

    dict(icd="C92", nama="Leukemia mieloid",
         inc=_v(0.15, 0.2, 0.15, 0.15, 0.2, 0.3, 0.5, 0.7, 0.8, 0.6), sex=0,
         kronis=True, tempat={RJTL: 0.45, RITL: 0.55},
         los=(11.0, 3.0),
         prc=[("99.25", 0.70), ("41.31", 0.30), ("99.04", 0.65)],
         obt=[("L01BB04", 0.40), ("L01XE01", 0.30), ("J01DD04", 0.45)],
         lab=[("HB", 0.92, -1), ("LEUKO", 0.85, 1), ("TROMB", 0.85, -1)],
         komorbid=[], berat=True),

    # --- darah --------------------------------------------------------------
    dict(icd="D56", nama="Talasemia",
         inc=_v(0.5, 0.6, 0.35, 0.25, 0.15, 0.1, 0.06, 0.03, 0.02, 0.01), sex=0,
         kronis=True, tempat={RJTL: 0.85, RITL: 0.15},
         los=(3.0, 1.0),
         prc=[("99.04", 0.95), ("88.76", 0.20)],
         obt=[("V03AC01", 0.65), ("B03BB01", 0.30)],
         lab=[("HB", 0.98, -1), ("FERITIN", 0.55, 1), ("HT", 0.80, -1)],
         komorbid=[], berat=True),

    dict(icd="D66", nama="Defisiensi faktor VIII herediter",
         inc=_v(0.05, 0.06, 0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005, 0.003),
         sex=1, kronis=True, tempat={RJTL: 0.80, RITL: 0.20},
         los=(4.0, 1.3),
         prc=[("99.06", 0.85)],
         obt=[("B02BD02", 0.90)],
         lab=[("APTT", 0.85, 1), ("HB", 0.55, -1)],
         komorbid=[], berat=True),

    dict(icd="D50", nama="Anemia defisiensi besi",
         inc=_v(6.0, 4.0, 6.0, 6.5, 5.0, 4.4, 4.4, 5.0, 5.6, 5.6), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.60, RJTL: 0.30, RITL: 0.10},
         los=(3.0, 1.0),
         prc=[("99.04", 0.15)],
         obt=[("B03AA07", 0.80), ("B03BB01", 0.35)],
         lab=[("HB", 0.95, -1), ("FERITIN", 0.40, -1), ("HT", 0.70, -1)],
         komorbid=["N18", "C18"], berat=False),

    # --- mata ---------------------------------------------------------------
    dict(icd="H25", nama="Katarak senilis",
         inc=_v(0.0, 0.0, 0.02, 0.05, 0.3, 2.0, 8.0, 20.0, 30.0, 28.0), sex=0,
         kronis=False, tempat={RJTL: 0.75, RITL: 0.25},
         los=(2.0, 0.7),
         prc=[("13.41", 0.70), ("13.59", 0.12), ("95.02", 0.85)],
         obt=[("S01AA13", 0.60), ("S01BA01", 0.45)],
         lab=[("GDP", 0.45, 0)],
         komorbid=["E11"], berat=False),

    dict(icd="H40", nama="Glaukoma",
         inc=_v(0.0, 0.01, 0.05, 0.15, 0.5, 1.4, 2.8, 4.0, 4.4, 3.6), sex=0,
         kronis=True, tempat={RJTL: 0.88, RITL: 0.12},
         los=(2.5, 0.8),
         prc=[("95.02", 0.80), ("12.64", 0.10)],
         obt=[("S01ED01", 0.65), ("S01EE01", 0.40)],
         lab=[],
         komorbid=["E11"], berat=False),

    # --- obstetri -----------------------------------------------------------
    dict(icd="O80", nama="Persalinan tunggal spontan",
         inc=_v(0.0, 0.0, 22.0, 30.0, 10.0, 0.6, 0.0, 0.0, 0.0, 0.0), sex=2,
         kronis=False, tempat={FKTP_ONLY: 0.45, RITL: 0.55},
         los=(2.5, 0.7),
         prc=[("73.59", 0.85), ("75.69", 0.25)],
         obt=[("N02BE01", 0.65), ("B03AA07", 0.55), ("H01BB02", 0.40)],
         lab=[("HB", 0.75, 0)],
         komorbid=[], berat=False),

    dict(icd="O82", nama="Persalinan tunggal dengan seksio sesarea",
         inc=_v(0.0, 0.0, 9.0, 15.0, 6.0, 0.4, 0.0, 0.0, 0.0, 0.0), sex=2,
         kronis=False, tempat={RITL: 0.99, RJTL: 0.01},
         los=(4.0, 1.0),
         prc=[("74.1", 0.92), ("88.78", 0.55)],
         obt=[("J01DD04", 0.80), ("N02BE01", 0.75), ("B03AA07", 0.60),
              ("H01BB02", 0.45)],
         lab=[("HB", 0.90, 0), ("LEUKO", 0.55, 0)],
         komorbid=["O14"], berat=False),

    dict(icd="O14", nama="Preeklampsia",
         inc=_v(0.0, 0.0, 2.2, 3.0, 1.6, 0.1, 0.0, 0.0, 0.0, 0.0), sex=2,
         kronis=False, tempat={RITL: 0.90, RJTL: 0.10},
         los=(5.0, 1.4),
         prc=[("88.78", 0.65), ("74.1", 0.45)],
         obt=[("C08CA01", 0.55), ("A12CC02", 0.70), ("H01BB02", 0.30)],
         lab=[("URIN", 0.85, 1), ("KREA", 0.60, 1), ("TROMB", 0.50, -1),
              ("SGPT", 0.45, 1)],
         komorbid=["I10"], berat=True),

    dict(icd="D25", nama="Leiomioma uteri",
         inc=_v(0.0, 0.0, 0.4, 1.8, 4.0, 4.4, 2.2, 0.8, 0.3, 0.1), sex=2,
         kronis=False, tempat={RJTL: 0.55, RITL: 0.45},
         los=(4.5, 1.2),
         prc=[("88.78", 0.70), ("68.4", 0.28), ("68.29", 0.12)],
         obt=[("B03AA07", 0.55), ("N02BE01", 0.50)],
         lab=[("HB", 0.80, -1)],
         komorbid=["D50"], berat=False),

    # --- neonatal -----------------------------------------------------------
    dict(icd="P07", nama="Bayi berat lahir rendah dan prematur",
         inc=_v(9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), sex=0,
         kronis=False, tempat={RITL: 0.95, RJTL: 0.05},
         los=(9.0, 2.6),
         prc=[("93.90", 0.45), ("99.83", 0.35), ("38.93", 0.30)],
         obt=[("J01DD04", 0.45), ("B05BA03", 0.70)],
         lab=[("BIL", 0.70, 1), ("GDP", 0.55, -1), ("HB", 0.60, 0)],
         komorbid=["P59"], berat=True),

    dict(icd="P59", nama="Ikterus neonatorum",
         inc=_v(14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), sex=0,
         kronis=False, tempat={RITL: 0.80, RJTL: 0.20},
         los=(4.0, 1.1),
         prc=[("99.83", 0.85)],
         obt=[("B05BA03", 0.40)],
         lab=[("BIL", 0.95, 1), ("HB", 0.55, 0)],
         komorbid=[], berat=False),

    # --- muskuloskeletal dan cedera ----------------------------------------
    dict(icd="S72", nama="Fraktur femur",
         inc=_v(0.3, 0.5, 1.0, 0.9, 0.8, 0.9, 1.4, 2.6, 5.0, 7.0), sex=0,
         kronis=False, tempat={RITL: 0.96, RJTL: 0.04},
         los=(8.0, 2.2),
         prc=[("88.21", 0.90), ("79.35", 0.55), ("78.55", 0.20),
              ("99.04", 0.30)],
         obt=[("N02BE01", 0.75), ("J01DD04", 0.60), ("M01AB05", 0.45),
              ("B01AB05", 0.30)],
         lab=[("HB", 0.85, -1), ("LEUKO", 0.55, 0), ("GDP", 0.40, 0)],
         komorbid=[], berat=True),

    dict(icd="S52", nama="Fraktur lengan bawah",
         inc=_v(1.6, 3.4, 2.4, 1.6, 1.2, 1.1, 1.2, 1.6, 2.2, 2.4), sex=0,
         kronis=False, tempat={RJTL: 0.45, RITL: 0.55},
         los=(3.5, 1.0),
         prc=[("88.23", 0.90), ("79.32", 0.40), ("93.54", 0.45)],
         obt=[("N02BE01", 0.70), ("M01AB05", 0.40), ("J01CR02", 0.30)],
         lab=[("HB", 0.45, 0)],
         komorbid=[], berat=False),

    dict(icd="S06", nama="Cedera intrakranial",
         inc=_v(1.2, 1.6, 3.0, 2.4, 1.8, 1.4, 1.2, 1.4, 1.8, 2.0), sex=0,
         kronis=False, tempat={RITL: 0.85, RJTL: 0.15},
         los=(6.0, 1.9),
         prc=[("87.03", 0.90), ("01.24", 0.10), ("96.71", 0.15)],
         obt=[("N02BE01", 0.60), ("B05BA03", 0.70), ("N03AA02", 0.20)],
         lab=[("HB", 0.70, 0), ("LEUKO", 0.55, 1), ("PT", 0.35, 0)],
         komorbid=[], berat=True),

    dict(icd="M17", nama="Gonartrosis",
         inc=_v(0.0, 0.0, 0.1, 0.4, 1.8, 6.0, 12.0, 16.0, 15.0, 11.0), sex=0,
         kronis=True, tempat={FKTP_ONLY: 0.35, RJTL: 0.58, RITL: 0.07},
         los=(5.0, 1.5),
         prc=[("88.27", 0.55), ("81.54", 0.05), ("93.11", 0.25)],
         obt=[("M01AB05", 0.70), ("M01AE01", 0.35), ("N02BE01", 0.45)],
         lab=[("LED", 0.30, 1)],
         komorbid=[], berat=False),

    dict(icd="M54", nama="Dorsalgia",
         inc=_v(0.1, 1.0, 8.0, 14.0, 18.0, 20.0, 20.0, 18.0, 15.0, 11.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.70, RJTL: 0.28, RITL: 0.02},
         los=(3.0, 1.0),
         prc=[("88.29", 0.30), ("93.11", 0.30)],
         obt=[("M01AB05", 0.65), ("N02BE01", 0.55), ("M03BX01", 0.30)],
         lab=[],
         komorbid=[], berat=False),

    # --- saraf dan jiwa -----------------------------------------------------
    dict(icd="G40", nama="Epilepsi",
         inc=_v(1.4, 1.0, 0.7, 0.6, 0.6, 0.7, 0.9, 1.2, 1.4, 1.4), sex=0,
         kronis=True, tempat={RJTL: 0.70, FKTP_ONLY: 0.18, RITL: 0.12},
         los=(4.0, 1.2),
         prc=[("89.14", 0.45), ("87.03", 0.25)],
         obt=[("N03AG01", 0.50), ("N03AX14", 0.35), ("N03AF01", 0.25)],
         lab=[("NA", 0.35, 0), ("SGPT", 0.30, 0)],
         komorbid=[], berat=True),

    dict(icd="F20", nama="Skizofrenia",
         inc=_v(0.0, 0.1, 0.6, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1), sex=0,
         kronis=True, tempat={RJTL: 0.72, RITL: 0.28},
         los=(14.0, 3.4),
         prc=[("94.38", 0.35)],
         obt=[("N05AX08", 0.55), ("N05AH03", 0.35), ("N05AA01", 0.25)],
         lab=[("GDP", 0.35, 0), ("SGPT", 0.30, 0)],
         komorbid=[], berat=False),

    dict(icd="E05", nama="Tirotoksikosis",
         inc=_v(0.02, 0.1, 0.5, 0.9, 1.1, 1.1, 0.9, 0.7, 0.5, 0.3), sex=0,
         kronis=True, tempat={RJTL: 0.80, FKTP_ONLY: 0.10, RITL: 0.10},
         los=(4.0, 1.2),
         prc=[("88.71", 0.45)],
         obt=[("H03BB02", 0.70), ("C07AB07", 0.45)],
         lab=[("TSH", 0.85, -1), ("FT4", 0.70, 1)],
         komorbid=["I48"], berat=False),

    # --- keluhan ringan yang menjadi mayoritas kunjungan primer -------------
    # Katalog awal hanya memuat penyakit bermakna, sehingga porsi FKTP jauh di
    # bawah angka nasional. Yang hilang adalah keluhan ringan yang tidak pernah
    # menjadi diagnosis besar tapi mengisi sebagian besar kunjungan RJTP.
    dict(icd="J00", nama="Nasofaringitis akut",
         inc=_v(45.0, 26.0, 16.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 8.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.985, RJTL: 0.015},
         los=(2.0, 0.8), prc=[],
         obt=[("N02BE01", 0.65), ("R05CB", 0.30)], lab=[],
         komorbid=[], berat=False),

    dict(icd="K30", nama="Dispepsia",
         inc=_v(1.0, 4.0, 14.0, 17.0, 17.0, 16.0, 15.0, 13.0, 11.0, 9.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.94, RJTL: 0.055, RITL: 0.005},
         los=(2.5, 0.9), prc=[],
         obt=[("A02BC01", 0.60), ("A03FA01", 0.35), ("A02BA02", 0.30)],
         lab=[], komorbid=[], berat=False),

    dict(icd="R51", nama="Nyeri kepala",
         inc=_v(1.0, 5.0, 13.0, 15.0, 15.0, 14.0, 12.0, 10.0, 8.0, 6.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.94, RJTL: 0.06},
         los=(2.0, 0.8), prc=[],
         obt=[("N02BE01", 0.70), ("M01AE01", 0.25)], lab=[],
         komorbid=[], berat=False),

    dict(icd="L30", nama="Dermatitis",
         inc=_v(16.0, 11.0, 9.0, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.90, RJTL: 0.10},
         los=(2.0, 0.8), prc=[],
         obt=[("D07AB02", 0.60), ("R06AE07", 0.35)], lab=[],
         komorbid=[], berat=False),

    dict(icd="H10", nama="Konjungtivitis",
         inc=_v(9.0, 7.0, 5.0, 4.5, 4.2, 4.0, 4.0, 4.2, 4.4, 4.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.90, RJTL: 0.10},
         los=(2.0, 0.7), prc=[],
         obt=[("S01AA13", 0.65)], lab=[], komorbid=[], berat=False),

    dict(icd="M79", nama="Mialgia dan nyeri jaringan lunak",
         inc=_v(0.2, 2.0, 9.0, 12.0, 14.0, 15.0, 15.0, 13.0, 11.0, 8.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.92, RJTL: 0.08},
         los=(2.0, 0.8), prc=[],
         obt=[("M01AB05", 0.60), ("N02BE01", 0.45)], lab=[],
         komorbid=[], berat=False),

    dict(icd="K02", nama="Karies gigi",
         inc=_v(6.0, 14.0, 12.0, 11.0, 10.0, 9.0, 7.0, 5.0, 3.0, 2.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.96, RJTL: 0.04},
         los=(2.0, 0.7), prc=[("23.09", 0.35)],
         obt=[("N02BE01", 0.50), ("J01CA04", 0.25)], lab=[],
         komorbid=[], berat=False),

    dict(icd="R50", nama="Demam tidak diketahui sebabnya",
         inc=_v(20.0, 10.0, 6.0, 5.5, 5.0, 5.0, 5.0, 5.5, 6.0, 6.0), sex=0,
         kronis=False, tempat={FKTP_ONLY: 0.88, RJTL: 0.07, RITL: 0.05},
         los=(3.0, 1.0), prc=[],
         obt=[("N02BE01", 0.85)], lab=[("LEUKO", 0.30, 0)],
         komorbid=[], berat=False),
]

KONDISI_BY_ICD = {k["icd"]: k for k in KONDISI}
ICD_LIST = [k["icd"] for k in KONDISI]

# Diagnosis sekunder yang tidak berdiri sendiri sebagai alasan kunjungan,
# tapi sering dicantumkan. Ini yang paling sering dipakai untuk menaikkan
# tingkat keparahan, jadi tiap entri menyimpan bukti yang seharusnya ada.
KOMORBID_TAMBAHAN = [
    dict(icd="E87.6", nama="Hipokalemia", berat=True,
         bukti_lab=[("KAL", -1)], bukti_obt=["A12BA01"]),
    dict(icd="E87.1", nama="Hipoosmolalitas dan hiponatremia", berat=True,
         bukti_lab=[("NA", -1)], bukti_obt=["B05XA03"]),
    dict(icd="D64.9", nama="Anemia tidak spesifik", berat=False,
         bukti_lab=[("HB", -1)], bukti_obt=["B03AA07"]),
    dict(icd="E86", nama="Deplesi volume", berat=False,
         bukti_lab=[("UR", 1)], bukti_obt=["B05BA03"]),
    dict(icd="N17", nama="Gagal ginjal akut", berat=True,
         bukti_lab=[("KREA", 1), ("UR", 1)], bukti_obt=["C03CA01"]),
    dict(icd="J96", nama="Gagal napas", berat=True,
         bukti_lab=[("AGD", -1)], bukti_obt=["V03AN01"]),
    dict(icd="E43", nama="Malnutrisi energi protein berat", berat=True,
         bukti_lab=[("ALB", -1)], bukti_obt=["B05BA10"]),
    dict(icd="I10", nama="Hipertensi esensial", berat=False,
         bukti_lab=[], bukti_obt=["C08CA01", "C09AA02"]),
    dict(icd="E11.9", nama="Diabetes tipe 2 tanpa komplikasi", berat=False,
         bukti_lab=[("GDP", 1)], bukti_obt=["A10BA02"]),
    dict(icd="R57.2", nama="Syok septik", berat=True,
         bukti_lab=[("LAKTAT", 1)], bukti_obt=["C01CA24"]),
    dict(icd="K72", nama="Gagal hati", berat=True,
         bukti_lab=[("BIL", 1), ("SGPT", 1)], bukti_obt=["A06AD11"]),
    dict(icd="D65", nama="Koagulasi intravaskular diseminata", berat=True,
         bukti_lab=[("TROMB", -1), ("PT", 1)], bukti_obt=["B02BD01"]),
]
KOMORBID_BY_ICD = {k["icd"]: k for k in KOMORBID_TAMBAHAN}

# Pemeriksaan penunjang: kode lokal, nama, rentang rujukan, dan satuan.
# Rentang dipakai untuk memitakan nilai secara relatif, bukan mutlak.
PEMERIKSAAN = {
    "HB":      ("Hemoglobin", 12.0, 16.0, "g/dL"),
    "HT":      ("Hematokrit", 37.0, 47.0, "%"),
    "LEUKO":   ("Leukosit", 4000.0, 10000.0, "/uL"),
    "TROMB":   ("Trombosit", 150000.0, 400000.0, "/uL"),
    "LED":     ("Laju endap darah", 0.0, 20.0, "mm/jam"),
    "GDP":     ("Glukosa darah puasa", 70.0, 100.0, "mg/dL"),
    "HBA1C":   ("HbA1c", 4.0, 5.7, "%"),
    "KREA":    ("Kreatinin", 0.6, 1.2, "mg/dL"),
    "UR":      ("Ureum", 15.0, 45.0, "mg/dL"),
    "NA":      ("Natrium", 135.0, 145.0, "mmol/L"),
    "KAL":     ("Kalium", 3.5, 5.1, "mmol/L"),
    "ALB":     ("Albumin", 3.5, 5.2, "g/dL"),
    "SGPT":    ("SGPT", 0.0, 41.0, "U/L"),
    "SGOT":    ("SGOT", 0.0, 37.0, "U/L"),
    "BIL":     ("Bilirubin total", 0.2, 1.2, "mg/dL"),
    "KOL":     ("Kolesterol total", 0.0, 200.0, "mg/dL"),
    "TG":      ("Trigliserida", 0.0, 150.0, "mg/dL"),
    "TROP":    ("Troponin", 0.0, 0.04, "ng/mL"),
    "CKMB":    ("CK-MB", 0.0, 25.0, "U/L"),
    "CRP":     ("C-reactive protein", 0.0, 5.0, "mg/L"),
    "PCT":     ("Prokalsitonin", 0.0, 0.5, "ng/mL"),
    "LAKTAT":  ("Laktat", 0.5, 2.0, "mmol/L"),
    "AGD":     ("Analisis gas darah, pO2", 80.0, 100.0, "mmHg"),
    "URIN":    ("Urinalisis, leukosit esterase", 0.0, 1.0, "skala"),
    "PT":      ("Waktu protrombin", 11.0, 14.0, "detik"),
    "APTT":    ("APTT", 25.0, 35.0, "detik"),
    "TSH":     ("TSH", 0.4, 4.0, "uIU/mL"),
    "FT4":     ("Free T4", 0.8, 1.8, "ng/dL"),
    "PSA":     ("PSA", 0.0, 4.0, "ng/mL"),
    "AFP":     ("Alfa fetoprotein", 0.0, 10.0, "ng/mL"),
    "CD4":     ("CD4", 500.0, 1500.0, "sel/uL"),
    "FERITIN": ("Feritin", 30.0, 300.0, "ng/mL"),
    "BTA":     ("BTA sputum", 0.0, 1.0, "skala"),
    "WIDAL":   ("Widal", 0.0, 1.0, "titer skala"),
    "MALARIA": ("Apusan malaria", 0.0, 1.0, "skala"),
}

# Ambang yang dipakai aturan penagihan. Modus M20 menggeser nilai supaya
# tepat melewati ambang ini, dan uji penumpukan di ambang menangkapnya.
AMBANG_PENAGIHAN = {
    "HB": 8.0,        # ambang transfusi
    "KREA": 2.0,      # ambang rujukan gangguan ginjal
    "TROMB": 100000.0,
    "LEUKO": 12000.0,
    "GDP": 200.0,
    "BIL": 12.0,      # ambang terapi sinar pada neonatus
    "ALB": 2.5,       # ambang klaim albumin
    "CD4": 350.0,
}


# --- pemitaan nilai pemeriksaan ---------------------------------------------
# Nilai dipita relatif terhadap rentang rujukan, bukan terhadap nilai mutlak.
# Leukosit 15.000 tidak berarti apa apa sampai kita tahu batas atasnya 10.000.
# Pemitaan relatif membuat satu vektor pita bisa dipakai lintas pemeriksaan,
# dan itu yang membuat uji penumpukan di ambang menjadi mungkin.

N_PITA_LAB = 8


def pita_lab(kode: str, nilai: float) -> int:
    """Pita nol sampai tujuh untuk satu nilai pemeriksaan.

    0 sangat rendah, 1 rendah, 2 rendah normal, 3 normal, 4 tinggi normal,
    5 tinggi, 6 sangat tinggi, 7 ekstrem tinggi.
    """
    lo, hi = PEMERIKSAAN[kode][1], PEMERIKSAAN[kode][2]
    lebar = max(hi - lo, 1e-9)
    z = (nilai - lo) / lebar
    if z < -0.5:
        return 0
    if z < 0.0:
        return 1
    if z < 0.25:
        return 2
    if z < 0.75:
        return 3
    if z <= 1.0:
        return 4
    if z <= 1.5:
        return 5
    if z <= 3.0:
        return 6
    return 7


# --- kondisi yang secara klinis wajib rawat inap ---------------------------
# Penyetel bauran tempat layanan tidak boleh menyentuh kondisi ini. Kalau
# disentuh, penyetel akan memindahkan infark miokard akut dan sepsis ke rawat
# jalan demi mengejar sasaran agregat nasional, dan itu menghasilkan data yang
# lulus uji angka tapi salah secara klinis.

WAJIB_INAP = {"I21", "I61", "I63", "A41", "K35", "S72", "S06", "O82", "O14",
              "P07", "P59", "C92", "K92", "J18", "A91", "O80", "S52"}


# --- frekuensi kunjungan kondisi kronis ------------------------------------
# Berapa kali setahun satu pasien kronis datang. Ini bukan turunan insidens,
# ini pola layanan. Peserta hipertensi dan diabetes di FKTP mengambil obat
# bulanan lewat program pengelolaan penyakit kronis, jadi dua belas kali
# setahun. Pasien dialisis datang dua kali seminggu. Perbedaan sebesar itu
# tidak bisa diwakili satu angka rata rata, dan kalau dipaksa rata rata,
# bauran tempat layanan nasional tidak akan pernah cocok.
#
# Angka di bawah asumsi kami, disusun dari pola layanan yang lazim. Yang
# paling menentukan bauran adalah dua belas untuk hipertensi dan diabetes.

KUNJUNGAN_KRONIS_PER_TAHUN = {
    "I10": 12.0, "E11": 12.0, "E78": 8.0,
    "J45": 6.0, "M17": 5.0, "G40": 6.0, "F20": 6.0, "H40": 4.0,
    "N40": 4.0, "B20": 6.0, "B18": 5.0, "E05": 5.0, "J44": 6.0,
    "N18": 8.0, "I50": 6.0, "I20": 5.0, "I48": 5.0,
    "Z49": 100.0, "D56": 14.0, "D66": 12.0,
    "C50": 8.0, "C53": 7.0, "C34": 7.0, "C18": 7.0, "C11": 8.0,
    "C22": 6.0, "C92": 9.0,
}
KUNJUNGAN_KRONIS_BAWAAN = 4.0

# Dialisis: sekitar dua ratus ribu pasien dari 282,7 juta peserta. Insidens
# di katalog jauh lebih tinggi dari itu, jadi ditekan di sini. Menekannya di
# satu tempat lebih mudah diperiksa daripada mengubah vektor insidensnya.
KOREKSI_INSIDENS = {"Z49": 0.09, "D66": 0.5}
