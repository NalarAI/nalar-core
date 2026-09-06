# NALAR

[![uji](https://github.com/NalarAI/nalar-core/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/NalarAI/nalar-core/actions/workflows/ci.yml)
[![lisensi](https://img.shields.io/badge/lisensi-Apache%202.0-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.12-blue.svg)](.python-version)

**Menghitung berapa rupiah dari sebuah tagihan klaim JKN yang tidak didukung
oleh buktinya sendiri, tanpa satu pun contoh kecurangan berlabel.**

Untuk Healthkathon BPJS Kesehatan 2026, kategori Efisiensi Risiko pada
Fasilitas Kesehatan.

| | |
|---|---|
| Porsi batas atas pada seribu klaim | 0,713 |
| Rasio pengembalian audit | 2,32 banding 1 |
| Laju penandaan klaim bersih | 1,10 persen pada alpha dua persen |
| Presisi profil faskes pada 25 teratas | 1,000 |
| Target tercapai | 4 dari 7, dan tiga kegagalannya ditulis |

Angka rupiah sengaja tidak ditaruh di tabel ini. Ia bergeser empat puluh
persen antar benih acak, jadi mengutipnya sendirian akan menyesatkan.
Alasannya di [TEMUAN.md](TEMUAN.md).

Rancangan lengkapnya ada di [docs/rancangan_model_ai_nalar_jkn.yaml](docs/rancangan_model_ai_nalar_jkn.yaml).
Seluruh hasil percobaan beserta kegagalannya ada di `TEMUAN.md`.
Berkas ini hanya menjelaskan kode yang sudah jalan.

## Gagasannya satu kalimat

Kecurangan tidak perlu dikenali dari contohnya. Ia bisa dikenali dari seberapa
jauh sebuah klaim menyimpang dari apa yang dibutuhkan untuk menjelaskan dirinya
sendiri.

Satu penebak mempelajari berapa tarif yang wajar bagi bukti yang menyertai
sebuah klaim. Selisih antara yang ditagih dan yang didukung bukti menjadi
skornya. Tidak ada satu pun label kecurangan yang dipakai saat melatih.

## Yang benar benar dikirim

`src/nalar/detektor.py`. Isinya pohon berpenguat sebagai penebak normatif,
kalibrasi konformal bertingkat yang himpunannya disaring dari kontaminasi,
dua profil faskes, antrean audit yang sadar biaya, dan lapisan penjelasan.

Transformer yang ditulis dari nol ada di `model.py`, `tokenizer.py`, dan
`train.py`, dan ia kalah. Pohon normatif mencapai porsi batas atas 0,721
melawan 0,649 miliknya. Kodenya ditinggalkan utuh karena percobaan yang
menghasilkan kesimpulan itu harus bisa diulang, bukan karena masih dipakai.

Yang tetap dipakai dari rancangan adalah bagian yang tidak bergantung pada
bentuk modelnya: kalibrasi konformal, evaluasi terhadap pelaku yang
beradaptasi, tarif Permenkes yang sungguhan, keluaran dalam rupiah, dan
penjelasan yang bisa dibantah.

## Menjalankan

```
python tests/test_inti.py               25 uji, semuanya harus lulus
python scripts/uji_detektor.py          model yang dikirim, ujung ke ujung
python scripts/uji_ketahanan.py         lima benih, empat prevalensi, pisah waktu
python scripts/uji_lawan.py             tiga pelaku yang beradaptasi
python scripts/uji_profil.py            profil faskes melawan tiga pembanding
python scripts/uji_perubahan.py         kepala titik perubahan
python scripts/uji_transfer.py          latih di sintetis, uji di klaim Amerika
```

Hasilnya ditulis ke `runs/`. Butuh Python 3.12, scikit-learn, dan NumPy.
PyTorch hanya diperlukan untuk menjalankan ulang percobaan transformer.

Pakai venv proyek supaya versinya sama:

```
./.venv/Scripts/python.exe scripts/uji_detektor.py
```

## Angka yang berlaku

| Ukuran | Nilai |
|---|---|
| Porsi batas atas pada seribu klaim | 0,713 |
| Rasio pengembalian audit | 2,32 banding 1 |
| Laju penandaan klaim bersih | 1,10 persen pada alpha dua persen |
| Keadilan berarah | 1,579, batasnya dua |
| Presisi profil faskes pada 25 teratas | 1,000 |

Satu peringatan yang harus ikut. Rupiah yang ditemukan bergeser empat puluh
persen antar benih acak, jadi angka rupiah tidak boleh dikutip sendirian.
Porsi batas atas hanya bergeser sepuluh persen, dan itulah metrik yang
dipakai. Rinciannya di `TEMUAN.md`.

Empat dari tujuh target tercapai. Tiga gagal, dan ketiganya punya sebab yang
bisa ditunjuk beserta angkanya. Yang paling perlu dibaca lebih dulu adalah
kegagalan T6: rumah sakit yang mau membayar ongkos mencoba coba sampai tahu
di mana garisnya masih bisa mengambil uang tanpa satu klaim pun ditandai.

## Isi

| Berkas | Isi |
|---|---|
| `schema.py` | Dua belas bidang episode, pola penutupan, panjang barisan |
| `katalog.py` | 66 kondisi klinis, obat ATC, prosedur ICD-9-CM, 35 pemeriksaan |
| `tarif.py` | Pengelompokan bergaya INA-CBG dan tabel tarif |
| `wilayah.py` | 38 provinsi, jaringan faskes, regional tarif |
| `generator.py` | SIMJKN, pembangkit tujuh tahap |
| `fraud.py` | Kebijakan faskes dan injeksi modus |
| `kalibrasi.py` | Penyetelan terhadap angka terbitan BPJS dan DJSN |
| `vocab.py` | Kamus token dan pohon hierarki ICD-10, ATC, ICD-9-CM |
| `tokenizer.py` | Episode menjadi barisan token bertipe |
| `model.py` | Encoder dengan embedding ontologi dan bias antar-bidang |
| `dataset.py` | Penutupan menurut peran, pemisahan menurut entitas |
| `train.py` | Pralatih |
| `heads.py` | Kepala K1 konsistensi, K2 tarif kontrafaktual, K5 kemiripan |
| `konformal.py` | Kalibrasi konformal dengan jaminan laju penandaan |
| `pembanding.py` | Mesin aturan, regresi logistik, fitur tangan |
| `metrik.py` | Rupiah pada k, presisi pada k, keadilan antar-kelompok |
| `detektor.py` | **Yang dikirim.** Penebak normatif, kalibrasi, antrean, penjelasan |
| `profil.py` | Profil faskes dengan penyusutan Bayes, dan titik perubahan |
| `tarif_resmi.py` | Tarif Permenkes 3/2023, 76.970 baris dari 885 kode |
| `peta_cbg.py` | Peta 66 kondisi ke kelompok INA-CBG yang sungguhan |
| `adversarial.py` | Tiga pelaku yang beradaptasi, serakah hati hati menyebar |
| `nyata.py` | Pemuat DE-SynPUF dan LEIE, untuk uji terhadap data nyata |

## Yang dipakai dari luar

PyTorch dipakai untuk tensor, turunan otomatis, `Linear`, `Embedding`, dan
`LayerNorm`. Modul transformer bawaan dan modul perhatian bawaan tidak dipakai,
karena bias antar-bidang tidak bisa disisipkan ke dalamnya tanpa menulis ulang
perhitungan skornya. Tidak ada bobot terlatih dari pihak mana pun. Tidak ada
pustaka jaringan graf. Tidak ada model bahasa besar.

Cara memeriksanya: buka `model.py`, cari `nn.Transformer` atau
`nn.MultiheadAttention`. Tidak ada.

## Sumber data

Yang sudah dipakai:

- **ICD-10 asli**, 71.704 kode dengan hierarkinya, dari daftar publik.
  Dipakai membangun pohon leluhur untuk embedding ontologi.
- **Kode ATC dan ICD-9-CM asli**, dipilih manual sesuai kondisi di katalog.
- **Angka terbitan BPJS Kesehatan 2025**: 282,7 juta peserta, 725,3 juta
  kunjungan, 23.770 FKTP, 3.194 FKRTL. Dipakai menyetel pembangkit.

Yang belum dipakai dan seharusnya:

- Tabel tarif INA-CBG resmi dari lampiran Permenkes 3/2023. Sekarang tarif
  memakai pendekatan sendiri. Antarmuka `tarif.py` sengaja dijaga supaya
  penggantiannya tidak menyentuh bagian lain.
- Registri rumah sakit Kemenkes. Sekarang jaringan faskes dibangkitkan dengan
  sebaran mengikuti bobot penduduk.
- MIMIC-IV untuk sebaran bersyarat diagnosis, laboratorium, dan obat.
  Kredensial PhysioNet belum diajukan.
- Data Sampel BPJS Kesehatan lewat PPID.

## Keadaan pembangkit

Uji kecocokan agregat lulus terhadap empat sasaran:

| Besaran | Sasaran | Sumber sasaran |
|---|---|---|
| Kunjungan per peserta per tahun | 2,57 | 725,3 juta dibagi 282,7 juta, Public Expose 2025 |
| Porsi FKTP | 0,75 | Laporan bulanan DJSN, RJTP disetahunkan |
| Porsi rawat jalan lanjut | 0,23 | sisa |
| Porsi rawat inap | 0,02 | sisa |

Penempatan klinis dijaga terpisah dari penyetel agregat. Penyetel boleh
menggeser bauran, tidak boleh memindahkan infark miokard akut ke rawat jalan
demi mengejar sasaran nasional. Daftar kondisi yang dilindungi ada di
`katalog.WAJIB_INAP`.

## Batasan yang harus dibaca sebelum memakai angka apa pun

1. **Tabel tarif belum resmi.** Struktur perbedaannya benar, angkanya belum.
   Selisih keparahan I ke III pada pneumonia keluar Rp 4,83 juta, dekat dengan
   angka yang beredar sekitar Rp 4,9 juta. Itu kebetulan yang menyenangkan,
   bukan bukti.

2. **Rasio peserta per faskes termampatkan.** Secara nasional satu FKRTL
   melayani sekitar 88.500 peserta. Pada simulasi ini jauh lebih padat, karena
   kalau rasio nyata dipertahankan hanya ada satu rumah sakit dan kepala
   kelompok sebaya tidak punya apa apa untuk dibandingkan. Akibatnya, deteksi
   tingkat entitas di sini lebih mudah daripada di dunia nyata. Angka
   `faktor_kompresi` di keluaran percobaan merekam seberapa besar
   penyimpangannya.

3. **Kamus token masih kecil.** 2.121 token, karena katalog memuat 66 kondisi.
   Arsitekturnya mendukung kamus penuh, datanya belum menguji itu.

4. **Kepala K3, K4, dan K6 belum ditulis.** Yang jalan baru K1, K2, dan K5.
   Proses titik temporal, kelompok sebaya, dan titik perubahan masih rancangan.

5. **Memperbesar model tidak menambah rupiah yang ditemukan.** Model 7 juta
   parameter dilatih 3.000 langkah menemukan Rp 1.430,3 juta. Model 0,97 juta
   parameter dilatih 600 langkah menemukan Rp 1.439,7 juta. Rugi pralatih turun
   jelas, jadi model besar memang menebak lebih baik, tapi kemampuan itu tidak
   berubah menjadi uang. Penghambatnya cakupan kepala, bukan kapasitas model.

6. **Semua data sintetis.** Tidak ada satu baris pun data peserta JKN yang
   nyata dipakai, sesuai butir 5.o dan bagian 12 panduan lomba.

## Yang sudah dibuktikan dan yang belum

Sudah dibuktikan:

- Alur berjalan dari klaim sintetis sampai peringkat audit.
- Pembangkit cocok dengan empat sasaran agregat nasional.
- Penempatan klinis tetap benar setelah penyetelan.
- Jaminan konformal terpenuhi pada data buatan, tiga tingkat alpha.
- Aturan tarif berperilaku seperti INA-CBG pada tujuh uji.
- Kebenaran dasar konsisten: klaim jujur berselisih nol, upcoding berselisih
  positif.
- Pemisahan latih dan uji tidak bocor antar-faskes.

- Kalibrasi konformal memenuhi jaminannya pada empat percobaan dan tiga
  tingkat alpha, diuji dengan pemisahan menurut faskes.
- Detektor membuat kecurangan tidak sepadan. Pelaku yang bisa melihat skor
  detektor hanya sanggup mengambil dua sampai empat persen dari yang bisa
  diambilnya tanpa pengawasan.

Gagal, dan dilaporkan apa adanya:

- Target T1, dua kali lipat rupiah atas mesin aturan. Yang didapat 1,20 sampai
  1,44 kali.
- Target T5, keadilan antar kelompok faskes. Rasio 2,46 sampai 5,09 kali,
  batasnya dua kali. Model yang lebih baik justru lebih tidak adil.
- Kepala K4 kelompok sebaya nyaris tidak lebih baik daripada menebak acak.

Belum diuji:

- Apakah model mengalahkan pohon berpenguat. Target T3. Pustakanya tidak
  terpasang.
- Apakah pralatih memberi perbaikan nyata. Target T4. Ablasi belum dijalankan.
- Apakah data sintetis cukup realistis. Uji latih di sintetis uji di nyata
  belum dijalankan, karena butuh MIMIC atau DE-SynPUF.

Rincian lengkap keempat percobaan ada di `TEMUAN.md`.
