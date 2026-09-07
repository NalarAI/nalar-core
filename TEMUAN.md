# Temuan percobaan

Ditulis mengikuti aturan yang ditetapkan rancangan: tidak ada angka hasil yang
ditulis sebelum percobaan dijalankan, dan kegagalan dilaporkan apa adanya.

---

## Percobaan 1, 5 September 2026

`runs/percobaan_cpu.json`

Pengaturan: 10.000 peserta, 3 tahun, 350 FKTP, 60 FKRTL, 80.614 episode.
Model 0,97 juta parameter, 500 langkah, CPU, 900 detik.
Pemisahan latih dan uji menurut faskes. Himpunan uji 19.877 klaim.

### Yang berjalan

Rugi pralatih turun dari 7,657 ke 2,959. Nilai awal itu sama dengan logaritma
natural ukuran kamus, jadi model memang mulai dari tebakan buta dan belajar
sesuatu. Tidak satu pun label kecurangan dipakai selama pralatih.

Uji kecocokan agregat lulus. Empat sasaran dari angka terbitan BPJS dan DJSN
terpenuhi di bawah toleransi lima belas persen.

Kecurangan yang terinjeksi: 4,51 persen klaim, 7,63 persen nilai. Berada di
rentang tiga sampai sepuluh persen yang sering disebut literatur.

### Hasil utama

Total selisih rupiah yang tersedia di himpunan uji: Rp 1,1 miliar.

| Penskor | rp@100 | rp@500 | rp@1000 | presisi@1000 |
|---|---:|---:|---:|---:|
| NALAR gabungan | 557,2 jt | 825,8 jt | 856,3 jt | 0,113 |
| NALAR K2 saja | 585,2 jt | 883,0 jt | 895,0 jt | 0,112 |
| NALAR K1 saja | 93,0 jt | 363,0 jt | 561,9 jt | 0,507 |
| Mesin aturan | 462,8 jt | 569,6 jt | 595,3 jt | 0,250 |
| Regresi logistik | 653,3 jt | 947,1 jt | 1.061,7 jt | 0,215 |
| Acak | 15,3 jt | 30,2 jt | 38,7 jt | 0,035 |

### Target yang tercapai

**T2 tercapai.** Jaminan konformal terpenuhi secara empiris pada tiga tingkat
alpha, dan pengujiannya dilakukan pada himpunan uji yang dipisah menurut faskes,
jadi ada pergeseran distribusi dan jaminannya tetap berlaku.

| alpha | laju penandaan klaim bersih | batas lulus |
|---|---:|---:|
| 0,01 | 0,0032 | 0,015 |
| 0,02 | 0,0065 | 0,030 |
| 0,05 | 0,0171 | 0,075 |

### Target yang tidak tercapai

**T1 tidak tercapai.** Target menyebut model harus menemukan setidaknya dua
kali lipat rupiah dibanding mesin aturan pada anggaran audit seribu klaim.
Yang didapat 1,44 kali. Pada lima puluh klaim teratas model justru kalah,
0,75 kali.

Rancangan sudah menuliskan apa yang dilakukan bila ini terjadi, dan kami
melakukannya: posisi proposal berubah dari model menggantikan aturan menjadi
model melengkapi aturan. Alasannya diperkuat oleh angka di bawah.

### Tiga hal yang dipelajari, dan satu kesalahan desain

**1. Rumus penggabungan skor kami salah.**

K2 sendirian, Rp 895,0 juta, mengalahkan gabungan K1 dikali K2, Rp 856,3 juta.
Sebabnya jelas begitu dilihat. Nilai harapan tarif sudah mengandung peluang di
dalamnya. Mengalikannya lagi dengan persentil kejutan menghitung peluang dua
kali, dan itu menekan klaim bernilai besar yang kejutannya sedang.

Rumus yang benar, dan yang sebenarnya sudah tertulis di rancangan bagian 9.8,
adalah peluang bahwa kelompok yang ditagihkan salah, dikali besar selisih bila
memang salah. Sudah diperbaiki untuk percobaan kedua.

**2. Presisi dan rupiah menunjuk arah berlawanan, dan itu justru bukti.**

K1 punya presisi tertinggi, 0,507, tapi rupiah terendah kedua. Mesin aturan
punya presisi 0,250 dengan rupiah 595 juta. K2 punya presisi 0,112 dengan
rupiah 895 juta.

Artinya K2 menandai lebih sedikit kasus dengan benar, tapi kasus yang
ditandainya membawa uang jauh lebih besar. Ini persis alasan rancangan menolak
presisi sebagai metrik utama. Kalau proposal ini dinilai dengan presisi, mesin
aturan menang dan BPJS kehilangan tiga ratus juta rupiah per seribu audit.

**3. Regresi logistik mengalahkan kami, dan itu perlu dijelaskan.**

Rp 1.061,7 juta melawan Rp 895,0 juta. Tapi regresi itu dilatih memakai label
kecurangan yang sebenarnya. Di Indonesia label seperti itu tidak ada, dan
seluruh rancangan ini lahir dari kenyataan tersebut. Jadi regresi logistik di
sini bukan pembanding yang bisa dipakai, ia batas atas dari dunia yang tidak
kita punya.

Yang layak dibaca dari angka itu adalah jarak antara sistem tanpa label dan
sistem berlabel: sekitar seperlima. Itu ukuran seberapa besar nilai rekomendasi
P4 pada rancangan, yaitu menulis hasil audit sebagai label.

### Batasan percobaan ini

- Mesin aturan pembanding ditulis oleh orang yang sama yang menulis injeksi
  modus, jadi ia tahu persis bentuk kecurangan yang ada. Mesin aturan di dunia
  nyata tidak punya keuntungan itu.
- Kepala K3, K4, K5, dan K6 tidak ikut dalam angka di atas. K1 dan K2 hanya
  menyentuh keluarga A, yaitu isi klaim yang tidak didukung bukti. Sebagian
  besar modus yang terinjeksi ada di keluarga lain.
- Kepala K2 pada percobaan ini menahan kelas rawat pada nilai yang ditagihkan,
  sehingga manipulasi kelas perawatan tidak terlihat sama sekali. Sudah
  diperbaiki untuk percobaan kedua.
- Modus perpanjangan lama rawat secara struktural tidak terlihat oleh K2, karena
  lama rawat adalah masukan bagi aturan keparahan, jadi tarif yang lebih tinggi
  memang konsisten dengan lama rawat yang dipanjangkan. Menangkapnya butuh model
  perkiraan lama rawat, dan itu kepala K3 yang belum ditulis.
- Model 0,97 juta parameter, jauh di bawah ukuran yang dirancang. PyTorch di
  mesin ini berjalan di CPU.

### Catatan tambahan

Pinalti hierarki menyumbang 0,00017 pada rugi total sekitar 2,9, yaitu enam per
seratus ribu. Praktis tidak melakukan apa apa. Dugaan kami, perakitan vektor
dari leluhur sudah membuat kode dekat dengan induknya, sehingga pinaltinya
hampir terpenuhi tanpa dilatih. Perlu ablasi yang benar sebelum komponen ini
dibuang, tapi arahnya sudah terlihat.

---

## Percobaan 2, 5 September 2026

`runs/percobaan2.json`

Pengaturan: 20.000 peserta, 3 tahun, 900 FKTP, 150 FKRTL, 164.353 episode.
600 langkah, CPU, 1.780 detik. Himpunan uji 42.676 klaim, selisih tersedia
Rp 2,29 miliar. Rugi 7,766 turun ke 2,721.

Yang berubah dari percobaan 1: rumus penggabungan diperbaiki, K2 menaksir
kelas rawat juga, kebijakan faskes ditetapkan berstrata, K4 dan K5 ikut
dijalankan, dan uji pelaku yang beradaptasi ditambahkan.

### Hasil utama

| Penskor | rp@100 | rp@500 | rp@1000 | presisi@1000 |
|---|---:|---:|---:|---:|
| NALAR rumus baru | 454,1 jt | 1.355,4 jt | 1.544,4 jt | 0,165 |
| NALAR rumus lama | 445,2 jt | 1.198,0 jt | 1.399,8 jt | 0,155 |
| NALAR K1 saja | 96,6 jt | 355,5 jt | 596,4 jt | 0,757 |
| Mesin aturan | 804,4 jt | 1.250,7 jt | 1.330,6 jt | 0,501 |
| Regresi logistik | 668,0 jt | 1.372,7 jt | 1.747,7 jt | 0,261 |
| Acak | 1,2 jt | 8,8 jt | 24,3 jt | 0,039 |

### Perbaikan rumus penggabungan terbukti

Rumus baru Rp 1.544,4 juta melawan rumus lama Rp 1.399,8 juta, naik sepuluh
persen. Perbaikan yang lahir dari membaca hasil percobaan pertama, bukan dari
menyetel parameter.

### Empat kegagalan

**1. Target T1 tetap tidak tercapai, dan malah memburuk.**

Peningkatan atas mesin aturan turun dari 1,44 kali menjadi 1,16 kali. Pada
seratus klaim teratas model kalah telak, 0,57 kali.

Penyebabnya ditemukan, dan itu kesalahan pembangkit, bukan kesalahan model.
Penetapan kebijakan berstrata menghasilkan lebih banyak faskes ekstrem, dan
faskes ekstrem menghasilkan klaim fiktif. Injeksi klaim fiktif kami
mengosongkan obat dan pemeriksaan, sehingga aturan paling sederhana, rawat
inap tanpa obat, menangkapnya sempurna. Presisi mesin aturan melonjak dari
0,250 ke 0,501 karena itu.

Klaim fiktif yang dibuat orang justru dilengkapi supaya lolos verifikasi
berkas. Jejak yang hilang bukan di dalam berkas, melainkan di luar berkas:
pasiennya tidak pernah datang. Sudah diperbaiki untuk percobaan ketiga.

**2. Kepala K4 kelompok sebaya gagal.**

Presisi sepuluh teratas 0,2. Dari 38 faskes yang dinilai, 6 benar benar nakal,
jadi menebak acak memberi 0,16. K4 nyaris tidak lebih baik daripada acak.

Sebabnya, divergensi Jensen Shannon antara sebaran yang teramati dan yang
diharapkan terlalu berisik pada faskes dengan sedikit klaim. Peringkat teratas
diisi faskes kecil yang sebarannya kebetulan menyimpang.

Diganti untuk percobaan ketiga: peringkat memakai rata rata kelebihan rupiah
per klaim, distandarkan di dalam kelompok sebaya. Satuannya langsung rupiah
dan jauh lebih stabil.

**3. Uji keadilan T5 gagal.**

Rasio laju penandaan tertinggi terhadap terendah 5,09 kali, jauh di atas batas
dua kali. Rumah sakit kelas C ditandai 2,2 persen, FKTP 0,43 persen, semuanya
dihitung hanya pada klaim yang bersih.

Kalibrasi konformal sudah dijalankan per kelas faskes, jadi jaminannya
seharusnya menyamakan laju. Yang tidak tertangani adalah pergeseran antara
faskes latih dan faskes uji di dalam kelas yang sama. Kalibrasi bersyarat
kelompok mengurangi ketimpangan, tapi tidak menghapusnya.

Ini kegagalan yang paling serius untuk penerapan. Sistem yang menandai rumah
sakit kelas C lima kali lebih sering daripada FKTP akan dipersoalkan, dan
pantas dipersoalkan.

**4. Uji pelaku yang beradaptasi tidak konklusif.**

Hanya delapan klaim yang bisa diserang, karena sampel yang diambil enam ratus
klaim pertama dan rawat inap cuma dua persen dari klaim. Angka penurunan
keuntungan maksimum yang keluar, 1,0, tidak berarti apa apa pada sampel
sebesar itu. Dinaikkan menjadi empat ratus klaim rawat inap untuk percobaan
ketiga.

### Yang tetap bertahan

**T2 tercapai lagi.** Jaminan konformal terpenuhi pada tiga tingkat alpha:
0,47 persen pada alpha satu persen, 0,74 persen pada dua persen, 1,41 persen
pada lima persen. Semuanya di bawah batas lulus.

**K1 presisi 0,757.** Naik dari 0,507. Kepala konsistensi bukti sangat akurat
menunjuk klaim yang bermasalah, meski nilainya kecil. Ini menguatkan
pemakaiannya untuk penjelasan, bukan untuk peringkat.

**K5 presisi sepuluh teratas 0,3**, lebih baik daripada K4 tapi masih lemah.

---

## Percobaan 3, 5 September 2026

`runs/percobaan3.json`

Pengaturan sama dengan percobaan 2. Yang berubah: klaim fiktif dibuat tampak
lengkap, dan peringkat K4 memakai rata rata kelebihan rupiah per klaim.
Uji pelaku dinaikkan menjadi empat ratus klaim rawat inap.

### Hasil utama

| Penskor | rp@100 | rp@500 | rp@1000 | presisi@1000 |
|---|---:|---:|---:|---:|
| NALAR | 454,1 jt | 1.258,8 jt | 1.439,7 jt | 0,160 |
| NALAR rumus lama | 433,0 jt | 1.176,7 jt | 1.358,9 jt | 0,154 |
| NALAR K1 saja | 62,5 jt | 291,6 jt | 535,5 jt | 0,762 |
| Mesin aturan | 677,9 jt | 1.111,3 jt | 1.189,0 jt | 0,498 |
| Regresi logistik | 684,4 jt | 1.324,1 jt | 1.639,1 jt | 0,260 |
| Acak | 2,5 jt | 10,5 jt | 53,5 jt | 0,039 |

Peningkatan atas mesin aturan naik dari 1,16 menjadi 1,21 kali setelah klaim
fiktif dibuat realistis. Target T1, dua kali, tetap tidak tercapai.

### Hasil terkuat proyek ini: uji pelaku yang beradaptasi

Dua ratus sembilan puluh delapan klaim rawat inap bisa diserang.

| Pelaku | Klaim diserang | Total diambil | Maksimum per klaim | Tertangkap |
|---|---:|---:|---:|---:|
| Serakah | 298 | Rp 3.241,3 jt | Rp 112,2 jt | 99,3% |
| Hati hati, bisa melihat skor | 10 | Rp 11,8 jt | Rp 2,1 jt | 0% |
| Menyebar | 298 | Rp 2.311,1 jt | Rp 59,9 jt | 96,6% |

**Target T6 tercapai.** Penurunan keuntungan maksimum 98,1 persen, jauh di atas
ambang setengah.

Cara membacanya. Pelaku serakah mengambil Rp 3,24 miliar tapi hampir seluruhnya
tertangkap. Pelaku yang punya orang dalam dan bisa melihat skor detektor lolos
sepenuhnya, tapi ia hanya menemukan sepuluh klaim dari dua ratus sembilan puluh
delapan yang bisa diserang tanpa memicu alarm, dan totalnya cuma Rp 11,8 juta.

Ini ukuran yang benar untuk sistem pengawasan. Bukan berapa persen tertangkap,
tapi apakah kecurangan masih sepadan dilakukan. Turun dari Rp 3,24 miliar
menjadi Rp 11,8 juta berarti tidak sepadan lagi.

Sepanjang penelusuran kami, evaluasi deteksi kecurangan kesehatan hampir selalu
dilakukan pada data statis dengan pelaku yang dianggap tidak bergerak. Kami bisa
mengujinya justru karena pembangkit datanya kami tulis sendiri.

### Yang masih gagal

**K4 tetap gagal.** Presisi sepuluh teratas tetap 0,2, sama dengan sebelum
perubahan peringkat. Menebak acak memberi 0,16. Mengganti divergensi sebaran
dengan rata rata kelebihan rupiah per klaim tidak menolong.

Dugaan kami sekarang, masalahnya bukan pada statistiknya melainkan pada jumlah
klaim per faskes di himpunan uji. Tiga puluh delapan faskes dinilai, banyak di
antaranya di bawah dua ratus klaim. Pada jumlah sekecil itu, sinyal tingkat
entitas tenggelam dalam derau. Perlu dijalankan ulang pada faskes dengan lebih
banyak klaim sebelum menyimpulkan K4 tidak bekerja.

**Uji keadilan T5 tetap gagal**, meski membaik dari 5,09 menjadi 2,46 kali.
Batasnya dua kali. Rumah sakit tertentu masih ditandai lebih sering daripada
FKTP pada klaim yang sama sama bersih.

**K5 membaik** dari 0,3 ke 0,4.

**Jaminan konformal tetap terpenuhi** pada tiga tingkat alpha.

---

## Percobaan 4, 5 September 2026, model ukuran penuh di GPU

`runs/percobaan_gpu.json`

Data sama persis dengan percobaan 3. Yang berubah hanya modelnya: 7,00 juta
parameter melawan 0,97 juta, delapan lapis melawan empat, 3.000 langkah
melawan 600. Dijalankan di RTX 5060 setelah PyTorch CUDA selesai terpasang.

### Perbandingan langsung

| | Kecil, 0,97 jt | Penuh, 7,00 jt |
|---|---:|---:|
| Langkah | 600 | 3.000 |
| Rugi akhir | 2,848 | 2,110 |
| Waktu total | 3.129 detik | 1.136 detik |
| rp@1000 NALAR | 1.439,7 jt | 1.430,3 jt |
| rp@1000 K1 saja | 535,5 jt | 725,9 jt |
| presisi@1000 NALAR | 0,160 | 0,173 |
| K4 presisi@10 | 0,2 | 0,3 |
| K5 presisi@10 | 0,4 | 0,4 |
| Keadilan, rasio maks min | 2,46 | 4,92 |
| T6 penurunan keuntungan | 0,981 | 0,963 |

### Temuan utama, dan ini temuan negatif

**Model tujuh kali lebih besar, dilatih lima kali lebih lama, tidak menemukan
rupiah lebih banyak.** Rp 1.430,3 juta melawan Rp 1.439,7 juta. Selisihnya
kurang dari satu persen, dan arahnya justru sedikit turun.

Rugi pralatih turun jelas, dari 2,848 ke 2,110, jadi model besar memang belajar
menebak isi klaim lebih baik. Kemampuan menebak yang lebih baik itu tidak
diterjemahkan menjadi uang yang ditemukan.

Artinya penghambatnya bukan kapasitas model. Penghambatnya ada di kepala dan
di cakupan. K1 dan K2 hanya menyentuh keluarga A, yaitu isi klaim yang tidak
didukung bukti. Sebagian besar modus yang terinjeksi ada di keluarga B, yang
soal waktu, dan keluarga C, yang soal pola entitas. Menambah parameter tidak
membuat model melihat sesuatu yang tidak ada di pertanyaan yang diajukannya.

Ini kesimpulan yang mahal untuk didapat dan murah untuk dipakai. Fase
berikutnya harus dipakai menulis kepala K3, bukan memperbesar model.

### Dua temuan tak terduga

**1. Model yang lebih baik justru lebih mudah dihindari.**

Pelaku hati hati yang bisa melihat skor detektor menemukan 38 klaim yang bisa
diserang tanpa memicu alarm pada model besar, melawan 10 klaim pada model
kecil. Yang bisa diambilnya naik dari Rp 11,8 juta menjadi Rp 81,3 juta, tujuh
kali lipat.

Dugaan kami, model yang lebih tajam memberi permukaan skor yang lebih halus,
dan permukaan yang lebih halus lebih mudah ditelusuri pelaku yang mencari
celah. Model yang kabur justru memaksa pelaku menebak.

Kalau dugaan ini benar, ia menyentuh sesuatu yang jarang disebut: ketepatan dan
ketahanan bisa saling bertentangan pada sistem yang lawannya manusia. Belum
diuji cukup untuk disebut kesimpulan, tapi cukup untuk dijadikan pertanyaan
penelitian.

**2. Model yang lebih baik lebih tidak adil.**

Rasio laju penandaan tertinggi terhadap terendah naik dari 2,46 menjadi 4,92
kali. Keduanya di atas batas dua kali, jadi target T5 gagal pada keduanya, tapi
arah perubahannya penting. Model yang lebih tajam memperbesar perbedaan antar
kelompok faskes, bukan memperkecilnya.

### Yang tetap bertahan

Jaminan konformal terpenuhi pada tiga tingkat alpha, sekarang lebih rapat ke
alpha yang diminta: 0,78 persen pada alpha satu persen, 1,80 persen pada dua
persen, 4,76 persen pada lima persen. Model yang lebih terkalibrasi membuat
jaminannya lebih efisien, bukan hanya aman.

Target T6 tetap tercapai. Pelaku serakah mengambil Rp 3,24 miliar dan 93,6
persen tertangkap. Pelaku hati hati turun ke Rp 81,3 juta, yaitu 2,5 persen
dari yang bisa diambil tanpa pengawasan.

---

## Ringkasan seluruh percobaan

| Target | Bunyi | Hasil |
|---|---|---|
| T1 | Dua kali lipat rupiah atas mesin aturan | **Gagal.** Terbaik 1,44 kali, terakhir 1,20 kali |
| T2 | Jaminan konformal terpenuhi | **Tercapai** pada empat percobaan, tiga tingkat alpha |
| T3 | Mengalahkan pohon berpenguat | **Belum diuji.** Pustakanya tidak terpasang |
| T4 | Pralatih memberi perbaikan | **Belum diuji.** Ablasi belum dijalankan |
| T5 | Laju penandaan antar kelompok tidak lebih dari dua kali | **Gagal.** 2,46 sampai 5,09 kali |
| T6 | Keuntungan maksimum pelaku turun setengah | **Tercapai.** Turun 96 sampai 98 persen |
| T7 | Bertahan pada faskes yang tidak pernah dilihat | **Tercapai sebagian.** Seluruh angka di atas sudah memakai pemisahan menurut faskes |

Dua tercapai, dua gagal, dua belum diuji, satu tercapai sebagian.

Yang paling perlu dikerjakan berikutnya, menurut urutan nilainya:

1. Kepala K3 proses titik temporal. Percobaan 4 membuktikan memperbesar model
   tidak menolong, dan sebagian besar modus ada di keluarga waktu dan entitas.
2. Uji keadilan. Dua kali gagal, dan ini yang paling berbahaya bila diterapkan.
3. Pohon berpenguat sebagai pembanding. Target T3 belum bisa dijawab.
4. Menahan sebagian modus dari penulis mesin aturan, supaya pembandingnya adil.

---

## Perubahan besar, 6 September 2026

### Tabel tarif resmi menggantikan tabel tebakan

Lampiran Permenkes 3/2023 berhasil diunduh dan diekstraksi: 76.970 baris,
885 kode INA-CBG, lima regional, empat kelas rumah sakit, pemerintah dan
swasta. Ini menutup risiko R3, risiko berdampak tertinggi pada rancangan.

Dua pemeriksaan kewajaran lulus tanpa satu pun pengecualian. Tarif kelas 1
tidak pernah lebih murah dari kelas 3 pada seluruh 76.970 baris, dan seluruh
10.066 pasangan keparahan I ke III naik.

Selisih keparahan I ke III pada rumah sakit kelas C regional 1 kelas rawat 3
rata rata **Rp 5.032.284**. Angka Rp 4,9 juta yang selama ini dikutip dari
pustaka terkonfirmasi dari sumber primernya.

### Seberapa salah tabel tebakan kami

Lebih salah daripada dugaan. Dari 594 kode yang kami karang, hanya **10 persen**
benar benar ada di peraturan. Huruf CMG-nya pun banyak meleset: stroke ternyata
masuk G bukan A, pneumonia masuk J bukan D.

Dua hal yang sama sekali tidak ada di model tebakan kami dan ternyata penting:

- **Kepemilikan rumah sakit memengaruhi tarif.** Pemerintah dan swasta punya
  angka berbeda untuk kode yang sama.
- **Rawat inap dan rawat jalan adalah keluarga kelompok yang terpisah**, bukan
  tarif yang sama dengan pengali. Tidak satu pun dari 885 kode punya versi
  rawat inap dan rawat jalan sekaligus.

Enam puluh enam kondisi katalog dipetakan ulang ke kelompok asli: 32 tepat,
31 dekat, 3 payung. Cakupan tarif 95 persen. Kamus token menyusut dari 2.121
ke 1.418 karena kode kelompoknya sekarang 226 yang asli, bukan 594 karangan.

Yang belum tercakup hampir seluruhnya kelompok rawat jalan bukan prosedur.
Ekstraksi menangkap 885 dari sekitar 1.077 kelompok, dan yang hilang ada di
halaman yang belum terbaca benar.

### MIMIC-IV dilepas

Kredensial PhysioNet tidak bisa diurus, jadi MIMIC-IV keluar dari rencana.
Rancangan sudah menyiapkan jalur ini sebagai risiko R2 dengan mitigasi yang
sudah tertulis: pakai DE-SynPUF untuk struktur klaim.

Yang sudah ada di tangan sekarang: CMS DE-SynPUF bagian penerima manfaat,
rawat inap, dan rawat jalan, ditambah daftar pengecualian LEIE. Semuanya
domain publik tanpa perjanjian.

Akibat yang harus ditulis: sebaran bersyarat antara diagnosis, nilai
laboratorium, dan obat di dalam pembangkit tetap berasal dari katalog yang
kami susun sendiri, bukan dari data klinis nyata. Realisme lapisan itu lebih
rendah daripada yang dirancang, dan uji latih di sintetis uji di nyata jadi
hanya bisa dijalankan terhadap DE-SynPUF, bukan terhadap rekam klinis.

### Kepala K3 ditulis

Proses titik temporal bertanda. Jarak antar-episode dimodelkan sebagai campuran
log-normal bersyarat representasi episode, ditambah sebaran tanda apakah episode
berikutnya melanjutkan diagnosis yang sama, berpindah, atau tidak ada lagi.

Campuran log-normal dipilih daripada intensitas kontinu, karena rapatnya
ternormalkan sendiri sehingga integral kompensatornya tidak perlu dihitung
numerik. Untuk pertanyaan yang diajukan, yaitu seberapa mengejutkan jarak
sampai kejadian berikutnya, rapat jarak antar-kejadian sudah memuat jawabannya.

Keluarannya berdenominasi rupiah, sama seperti K2: peluang pasangan ini
sebenarnya satu episode, dikali rupiah yang didapat dari memecahnya. Dengan
begitu K2 dan K3 bisa diperingkat bersama, bukan digabung lewat bobot manual.

Pada uji kecil, rugi turun dari 5,79 ke 5,28. Jarak antar-episode nyata pada
data sintetis: median 19 hari, persentil 10 sebesar 2 hari, persentil 90
sebesar 90 hari.

---

## Percobaan 5, 6 September 2026, tarif resmi dan kepala K3

`runs/percobaan5.json`

Data dan model sama persis dengan percobaan 4: 20.000 peserta, 164.301 episode,
model 7 juta parameter, 3.000 langkah, GPU, 884 detik. Yang berubah dua:
tarif resmi menggantikan tarif tebakan, dan kepala K3 ikut serta.

Himpunan uji 42.624 klaim, selisih tersedia Rp 1,82 miliar.
Rugi pralatih 7,335 turun ke 2,142.

### Hasil

| Penskor | rp@50 | rp@100 | rp@500 | rp@1000 | presisi@1000 |
|---|---:|---:|---:|---:|---:|
| NALAR K2 | 322,0 jt | 429,7 jt | 633,3 jt | 682,6 jt | 0,121 |
| NALAR K2+K3 | 322,0 jt | 429,7 jt | 680,3 jt | 727,2 jt | 0,131 |
| NALAR K3 saja | 285,9 jt | 349,8 jt | 353,9 jt | 373,4 jt | 0,071 |
| NALAR K1 saja | 99,7 jt | 125,6 jt | 318,1 jt | 560,9 jt | 0,720 |
| Mesin aturan | 127,1 jt | 247,2 jt | 573,6 jt | 658,9 jt | 0,312 |
| Regresi logistik | 319,0 jt | 464,7 jt | 870,9 jt | 1.207,7 jt | 0,345 |
| Acak | 2,3 jt | 3,0 jt | 12,2 jt | 80,4 jt | 0,039 |

Peningkatan K2+K3 atas mesin aturan: **2,534 kali pada lima puluh teratas**,
1,738 pada seratus, 1,355 pada dua ratus lima puluh, 1,186 pada lima ratus,
1,104 pada seribu.

### Papan skor berubah

Empat dari tujuh target tercapai, naik dari dua.

| Target | Sebelum | Sekarang |
|---|---|---|
| T1 dua kali atas aturan | gagal, 1,16 sampai 1,44 | **tercapai di lima puluh teratas, 2,53 kali.** Pada seribu masih 1,10 |
| T2 jaminan konformal | tercapai | tercapai, dan lebih rapat |
| T5 keadilan antar kelompok | gagal, 2,46 sampai 5,09 | **tercapai, 1,72 kali** |
| T6 ketahanan pelaku | tercapai, 96 sampai 98 persen | tercapai, 87,3 persen |

**Soal T1, harus dibaca hati hati.** Targetnya ditulis untuk anggaran audit
seribu klaim, dan pada angka itu yang didapat 1,10 kali, jadi **sebagaimana
ditulis, T1 masih gagal**. Yang tercapai adalah pada lima puluh dan seratus
klaim teratas. Kami tidak mengubah bunyi targetnya untuk mengaku menang.

Tapi perubahan bentuknya sendiri yang menarik. Sebelum tarif resmi masuk, model
justru kalah di puncak peringkat, 0,57 sampai 0,75 kali, dan hanya unggul tipis
di ekor. Sekarang terbalik: unggul telak di puncak, menyempit di ekor. Puncak
peringkat adalah tempat anggaran audit sebenarnya bekerja.

Sebabnya bisa diterka. Tarif resmi punya rentang Rp 222.500 sampai
Rp 458.181.300, jauh lebih lebar daripada tarif tebakan yang hampir seragam.
Sinyal selisih rupiah jadi jauh lebih tajam di kelompok bernilai besar.

### Kepala K3 memberi hasil, tapi cakupannya sempit

K3 sendirian menemukan Rp 373,4 juta, dan itu **dari 93 klaim saja** di antara
42.624. Pemusatan yang luar biasa, rata rata sekitar Rp 4 juta per klaim yang
diskornya bukan nol.

Digabung, K2+K3 menaikkan hasil pada dua ratus lima puluh teratas dari 1,288
menjadi 1,355 kali, dan pada seribu dari 1,036 menjadi 1,104.

Cakupan 93 klaim itu terlalu sempit dan harus diperbaiki. Sebabnya, skor hanya
diberikan pada pasangan episode yang keduanya rawat inap dan selisih
pemecahannya positif. Rawat inap cuma dua persen klaim, jadi calonnya memang
sedikit. Perluasan ke rawat jalan berulang, misalnya hemodialisis dan
kemoterapi, belum dikerjakan.

### Uji keadilan akhirnya lulus

Rasio laju penandaan antar kelas faskes 1,72 kali, di bawah batas dua kali.
Sebelumnya 4,92 pada model yang sama dengan tarif tebakan.

Yang berubah cuma tabel tarifnya. Dugaan kami, tarif tebakan yang hampir
seragam membuat model bersandar pada ciri faskes untuk membedakan klaim, dan
ciri faskes itulah yang menghasilkan ketimpangan. Dengan tarif yang benar
benar berbeda antar kelompok, sinyalnya pindah ke isi klinis. Ini dugaan,
belum diuji dengan ablasi.

### Yang memburuk

Pelaku serakah sekarang hanya tertangkap 49 persen, turun dari 94 persen. Tapi
pelaku hati hati tetap terkekang: keuntungan maksimum per klaim Rp 4,6 juta
melawan Rp 36,2 juta tanpa pengawasan, turun 87,3 persen.

Presisi NALAR 0,121 melawan mesin aturan 0,312. Pembalikan presisi dan rupiah
tetap ada, dan tetap menjadi bukti terkuat bahwa presisi metrik yang salah
untuk soal ini.

Regresi logistik berlabel tetap unggul, Rp 1.207,7 juta. Jaraknya melebar dari
seperlima menjadi sekitar sepertiga. Sistem berlabel makin bernilai, dan itu
memperkuat rekomendasi P4.

---

## Percobaan 6 sampai 9, 6 September 2026

Empat percobaan yang saling menjawab. Yang paling berharga di antaranya adalah
yang menunjukkan model kami kalah dari sesuatu yang gratis.

### Ablasi tabel tarif: dugaan soal keadilan terkonfirmasi

`runs/p6_penuh.json` melawan `runs/p6_ablasi_tarif.json`. Data, model, benih,
dan langkah pelatihan persis sama. Yang berbeda hanya tabel tarifnya.

| | Tarif resmi | Tarif tebakan |
|---|---:|---:|
| Keadilan, rasio maks min | **1,737 lulus** | **3,539 gagal** |
| rp@50 | 322,0 jt | 112,2 jt |
| lift@50 atas aturan | 2,534 | 0,777 |
| lift@1000 atas aturan | 1,162 | 0,770 |

Dugaan pada percobaan 5 benar. **Tabel tarif yang menyebabkan uji keadilan
berubah dari gagal menjadi lulus.** Dengan tarif tebakan yang hampir seragam,
model bersandar pada ciri faskes untuk membedakan klaim, dan ciri faskes itulah
yang menghasilkan ketimpangan antar kelas rumah sakit. Dengan tarif yang benar
benar berbeda antar kelompok, sinyalnya pindah ke isi klinis.

Ini temuan yang layak dibawa ke proposal. Masalah keadilan diselesaikan dengan
memperbaiki data acuan, bukan dengan menyetel model.

Angka lain di tabel itu juga menegaskan: tanpa tabel tarif resmi, seluruh
keunggulan model hilang. Dari 2,534 kali menjadi 0,777 kali, artinya kalah dari
mesin aturan di mana mana.

### Garis dasar yang seharusnya sejak awal ada

Ablasi pralatih memberi hasil yang mengganggu. Model dengan tiga puluh langkah
menemukan Rp 862,3 juta, sedangkan model dengan tiga ribu langkah Rp 765,7 juta.
Model yang nyaris tanpa latihan **lebih baik**.

Sebabnya ketahuan begitu dipikirkan. Pada model tanpa latihan, sebaran atas
kelompok tarif hampir seragam, sehingga skornya menyusut menjadi tarif dikurangi
rata rata tarif. Itu sama saja dengan mengurutkan klaim menurut nilainya.

Jadi kami menambahkan garis dasar yang seharusnya sejak awal ada:
**urutkan menurut nilai klaim**. Gratis, tanpa model, tanpa data acuan apa pun.

Hasilnya menampar. Sebelum K7 ditambahkan:

| k | NALAR K2+K3 | Nilai klaim saja | Lift |
|---|---:|---:|---:|
| 50 | 322,0 jt | 298,6 jt | 1,078 |
| 100 | 429,7 jt | 453,0 jt | 0,949 |
| 500 | 685,6 jt | 810,1 jt | 0,846 |
| 1000 | 750,5 jt | 978,8 jt | 0,767 |

**Model kalah dari mengurutkan klaim mahal lebih dulu**, kecuali tipis di lima
puluh teratas. Seluruh keunggulan 2,53 kali atas mesin aturan itu nyata, tapi
mesin aturan ternyata tolok ukur yang salah. Yang benar tolok ukur gratis ini.

### Membedah dari mana uangnya berasal

Sebelum menebak lagi, kami hitung. Dari Rp 5,23 miliar selisih pada 7.356 klaim:

| Modus | Porsi rupiah |
|---|---:|
| Barang habis pakai fiktif, M17 | sekitar 36 persen bersama kombinasinya |
| Penagihan berulang, M11 | sekitar 24 persen |
| Harga digelembungkan, M07 | sekitar 17 persen |
| **Upcoding, M04** | **sekitar 12 persen** |
| Klaim fiktif, M06 | sekitar 4 persen |

**Upcoding, sasaran utama kepala K2, hanya dua belas persen uangnya.** Dua modus
terbesar menyentuh tagihan barang, dan tidak satu pun kepala punya mekanisme
melihatnya, karena semuanya menyasar kelompok tarif.

Sebelum ini kami sempat menduga masalahnya pada penutupan bidang, dan menambah
diagnosis sekunder ke daftar yang ditutup. Perbaikan itu benar secara prinsip,
tapi hasilnya hampir tidak berubah, 764,8 juta melawan 750,5 juta. Menebak dua
kali, meleset dua kali. Menghitung sekali, langsung ketemu.

### Kepala K7 dan hasilnya

Token bahan habis pakai diberi pita jumlah, lalu K7 menutup bidang itu dan
membandingkan nilai yang ditagihkan dengan nilai yang wajar untuk tindakan dan
lama rawat seperti ini.

`runs/p9_k7.json`, konfigurasi sama persis dengan sebelumnya:

| Penskor | rp@50 | rp@100 | rp@500 | rp@1000 | presisi@1000 |
|---|---:|---:|---:|---:|---:|
| **NALAR semua** | 298,6 jt | 453,0 jt | 922,9 jt | **1.152,4 jt** | **0,362** |
| NALAR K7 saja | 95,1 jt | 217,4 jt | 643,6 jt | 737,3 jt | 0,477 |
| NALAR K2+K3 | 298,6 jt | 429,7 jt | 711,4 jt | 754,2 jt | 0,162 |
| Nilai klaim saja | 298,6 jt | 453,0 jt | 810,1 jt | 978,8 jt | 0,199 |
| Mesin aturan | 127,1 jt | 247,2 jt | 573,6 jt | 658,9 jt | 0,312 |
| Regresi logistik berlabel | 319,0 jt | 464,7 jt | 870,9 jt | 1.207,7 jt | 0,345 |

Peningkatan atas mesin aturan: 2,35 kali pada lima puluh, 1,833 pada seratus,
**1,749 pada seribu**, naik dari 1,161.

Peningkatan atas nilai klaim: 1,056 pada dua ratus lima puluh, 1,139 pada lima
ratus, **1,177 pada seribu**. Model akhirnya mengalahkan garis dasar gratis itu.

Tiga hal yang berubah sekaligus:

1. **Presisi melonjak dari 0,112 ke 0,362**, melewati mesin aturan yang 0,312.
   Pembalikan presisi dan rupiah yang selama empat percobaan menjadi ciri khas
   hasil kami sebagian besar hilang.
2. **Jarak ke sistem berlabel nyaris tertutup.** Rp 1.152,4 juta melawan
   Rp 1.207,7 juta, yaitu 95 persen, tanpa memakai satu pun label.
3. **K7 punya presisi tertinggi di antara seluruh kepala, 0,477.**

### Papan skor sekarang

| Target | Hasil |
|---|---|
| T1 dua kali atas aturan pada seribu klaim | **belum**, 1,749. Tercapai pada lima puluh teratas, 2,35 |
| T2 jaminan konformal | **tercapai**, tiga tingkat alpha |
| T3 mengalahkan pohon berpenguat | belum diuji |
| T4 pralatih memberi perbaikan | perlu diuji ulang setelah K7 |
| T5 keadilan antar kelompok | **gagal tipis**, 2,017 dari batas 2,0. Sebelum K7 lulus di 1,737 |
| T6 ketahanan pelaku | **tercapai**, 87,3 persen |
| T7 faskes tak dikenal | tercapai, seluruh angka memakai pemisahan menurut faskes |

T5 kembali gagal setelah K7 masuk, meski tipis. Perlu ditelusuri apakah kepala
tagihan memperkenalkan ketimpangan baru, misalnya karena rumah sakit besar
memakai lebih banyak bahan habis pakai.

### Pelajaran metodologisnya

Tiga kali berturut turut kami menebak penyebab dan meleset. Rumus penggabungan,
penutupan bidang, lalu ukuran model. Yang akhirnya menyelesaikan bukan tebakan
keempat, melainkan menghitung komposisi kebenaran dasar, sesuatu yang bisa
dilakukan sejak hari pertama dan memakan waktu lima menit.

Dan yang membuat seluruh rangkaian ini terjadi adalah satu garis dasar gratis
yang sebelumnya tidak ada di daftar pembanding. Tanpa mengurutkan menurut nilai
klaim, kami akan melaporkan 2,53 kali atas mesin aturan dan merasa berhasil,
padahal saat itu model kalah dari menyortir spreadsheet.

---

## Percobaan 10, 6 September 2026: T4 terjawab, dan salah paham soal keadilan diluruskan

`runs/p10_penuh.json` dan `runs/p10_tanpa_pralatih.json`. Konfigurasi sama,
yang berbeda hanya jumlah langkah pralatih.

### T4 tercapai, dan temuan negatif sebelumnya batal

| | 3.000 langkah | 30 langkah |
|---|---:|---:|
| Rugi pralatih akhir | 2,131 | 4,594 |
| rp@1000 semua | **1.106,1 jt** | 861,6 jt |
| Lift atas mesin aturan | 1,679 | 1,308 |
| Lift atas nilai klaim | **1,130** | **0,880** |
| Presisi@1000 | 0,354 | 0,212 |

**Pralatih memberi perbaikan nyata. T4 tercapai.**

Ini membatalkan temuan negatif percobaan 4 dan ablasi sebelumnya, yang
menyimpulkan memperbesar model dan melatih lebih lama tidak menambah rupiah.
Kesimpulan itu benar untuk susunan kepala saat itu, dan salah sebagai
pernyataan tentang arsitekturnya. Penghambatnya memang cakupan kepala, dan
begitu K7 masuk, kapasitas model mulai terpakai.

Perhatikan baris terakhir. Tanpa pralatih, model kalah dari mengurutkan menurut
nilai klaim, 0,880. Dengan pralatih, menang, 1,130. Jadi seluruh keunggulan
atas garis dasar gratis itu memang berasal dari yang dipelajari model.

### Keadilan: dua dugaan saya keliru, dan yang benar lebih menarik

Pada percobaan 9 saya menduga K7 memperkenalkan ketimpangan. Pada uji kecil
penguraian menunjuk K3. Keduanya salah.

Laju penandaan per kelas faskes pada anggaran dua persen, dihitung hanya pada
klaim yang bersih:

| Penskor | B | C | D | FKTP |
|---|---:|---:|---:|---:|
| K2 | 7,7% | 4,2% | 5,4% | 0,25% |
| K3 | 5,6% | 2,6% | 2,4% | 1,00% |
| K7 | 4,3% | 2,7% | 3,3% | 0,09% |
| Semua | 6,4% | 3,1% | 3,8% | 0,06% |
| **Nilai klaim saja** | **8,1%** | **4,9%** | **4,5%** | **0,00%** |
| Mesin aturan | 3,3% | 1,3% | 1,0% | 1,32% |

Baris yang menjelaskan segalanya adalah nilai klaim saja. Garis dasar gratis
yang tidak memakai model sama sekali justru **paling timpang**, dan tidak
menandai satu pun klaim FKTP.

Sebabnya sederhana. Klaim FKTP bernilai ratusan ribu, klaim rumah sakit
bernilai jutaan. Antrean yang diurutkan menurut rupiah pasti menaruh rumah
sakit di atas. Itu bukan ketimpangan model, itu tujuan sistemnya. Uangnya
memang ada di sana.

Jadi tidak ada kepala yang bersalah. Yang ada, seluruh skor berdenominasi
rupiah memusat ke faskes mahal, termasuk yang gratis.

### Yang benar benar menyelesaikannya

| | Rasio maks min | Lulus |
|---|---:|---|
| Ambang tunggal, anggaran tetap | 105,2 | tidak |
| Ambang konformal per kelas faskes | **1,774** | **ya** |

Kalibrasi konformal per kelompok bukan hiasan. Ia satu satunya yang membuat
laju gangguan terhadap faskes jujur sebanding antar kelas. Tanpa itu, FKTP
tidak pernah diperiksa dan rumah sakit kelas B diperiksa seratus kali lebih
sering, pada klaim yang sama sama bersih.

Angka 105 banding 1,774 itu argumen terkuat untuk bagian kalibrasi pada
rancangan, dan sebelumnya kami hanya bisa menyatakannya sebagai prinsip.

Catatan koreksi: pada percobaan 9 saya melaporkan T5 gagal di 2,017. Pada
percobaan 10 dengan konfigurasi yang sama angkanya 1,774 dan lulus. Selisih
antar-jalannya cukup besar untuk menyimpulkan T5 berada tepat di batas, bukan
lulus dengan aman.

### Papan skor

| Target | Hasil |
|---|---|
| T1 dua kali atas aturan pada seribu klaim | belum, 1,679 sampai 1,749. Tercapai pada lima puluh teratas |
| T2 jaminan konformal | **tercapai** |
| T3 mengalahkan pohon berpenguat | belum diuji, pustakanya tidak terpasang |
| T4 pralatih memberi perbaikan | **tercapai**, 1,130 melawan 0,880 |
| T5 keadilan antar kelompok | **tercapai tipis**, 1,774 dan 2,017 pada dua jalan |
| T6 ketahanan pelaku | **tercapai** |
| T7 faskes tak dikenal | tercapai |

Empat tercapai, satu belum, satu belum diuji, satu tercapai sebagian.

### Catatan tentang cara kerja

Empat kali berturut turut saya menebak penyebab dan meleset: rumus
penggabungan, penutupan bidang, ukuran model, lalu kepala mana yang membuat
timpang. Yang menyelesaikan selalu pengukuran, bukan tebakan berikutnya.

Pola yang berulang: begitu satu garis dasar atau satu penguraian ditambahkan,
kesimpulan sebelumnya berubah. Garis dasar nilai klaim membatalkan klaim
keunggulan 2,53 kali. Kepala K7 membatalkan temuan bahwa model besar tidak
berguna. Penguraian per kepala membatalkan dua dugaan soal keadilan sekaligus.

---

## Percobaan 11 dan 12, 6 September 2026: T3 terjawab, dan kami kalah

`runs/p11_pohon.json` dan `runs/p12_gabung.json`

scikit-learn akhirnya terpasang, jadi target T3 bisa dijawab. Pohon berpenguat
dijalankan dua bentuk, dan membedakannya menentukan seluruh penafsiran.

**Terawasi** dilatih memakai label kecurangan. Itu batas atas dari dunia yang
tidak kita punya, sekelas regresi logistik berlabel.

**Normatif** tidak memakai satu pun label. Ia menebak tarif dan nilai tagihan
barang dari bukti, lalu selisihnya menjadi skor. Itu pekerjaan yang persis sama
dengan tulang punggung kami, dikerjakan pohon. Inilah uji T3 yang sesungguhnya.

### Hasil

Batas atas pada seribu klaim, kalau kita tahu jawabannya: Rp 1.753,6 juta.

| Penskor | rp@50 | rp@500 | rp@1000 | Porsi batas atas |
|---|---:|---:|---:|---:|
| Pohon terawasi, berlabel | 354,6 jt | 1.078,7 jt | 1.417,8 jt | 0,808 |
| Pohon + K3 + K7 | 233,8 jt | 1.141,3 jt | 1.272,3 jt | 0,726 |
| **Pohon normatif, tanpa label** | 216,0 jt | 1.009,6 jt | **1.264,3 jt** | **0,721** |
| Pohon + K3 | 262,2 jt | 1.097,1 jt | 1.246,4 jt | 0,711 |
| **NALAR semua** | 322,0 jt | 900,5 jt | **1.138,8 jt** | **0,649** |
| Nilai klaim saja | 298,6 jt | 810,1 jt | 978,8 jt | 0,558 |
| Mesin aturan | 127,1 jt | 573,6 jt | 658,9 jt | 0,376 |

### T3 gagal, dan lebih telak daripada yang diantisipasi

Pohon normatif menemukan Rp 1.264,3 juta, NALAR Rp 1.138,8 juta. **Pohon
mengalahkan kami sebelas persen, tanpa memakai satu pun label, pada pekerjaan
yang persis sama.**

Rancangan sudah menyiapkan jawaban bila ini terjadi: pertahankan model dalam
untuk keluarga B dan C, yang tidak bisa dikerjakan pohon karena pohon bekerja
satu baris satu baris. Kami menguji jalan keluar itu, dan **jalan keluar itu
juga tidak berlaku**.

Menambahkan kepala K3 di atas pohon justru **menurunkan** hasilnya, dari
1.264,3 menjadi 1.246,4. Menambahkan K3 dan K7 sekaligus menaikkannya
**0,6 persen**, dari 1.264,3 menjadi 1.272,3. Itu di dalam derau.

Jadi tidak ada bagian dari arsitektur kami yang terbukti menyumbang di atas
pohon berpenguat sederhana.

### Yang tetap berdiri

Kesimpulan di atas menjatuhkan pilihan modelnya, bukan pendekatannya. Yang
terbukti dan tidak bergantung pada model mana yang dipakai:

1. **Pemodelan kewajaran tanpa label bekerja.** Pohon normatif, yang tidak
   pernah melihat satu pun label kecurangan, menemukan Rp 1.264,3 juta melawan
   Rp 658,9 juta milik mesin aturan. Hampir dua kali lipat. Itu tesis pokok
   rancangan, dan tesis itu bertahan.

2. **Jarak ke sistem berlabel tinggal sebelas persen.** 0,721 melawan 0,808
   porsi batas atas. Kecil, dan itu memperkuat rekomendasi P4 sekaligus
   menunjukkan sistem tanpa label sudah mendekati langit langitnya.

3. **Kalibrasi konformal per kelompok** yang mengubah rasio ketimpangan dari
   105 menjadi 1,77 sama sekali tidak bergantung pada model. Ia berlaku untuk
   pohon juga.

4. **Uji pelaku yang beradaptasi, tabel tarif resmi, metrik porsi batas atas,
   dan pembangkit datanya** semuanya model-agnostik.

### Rekomendasi yang berubah

Yang jujur sekarang: **pakai pohon berpenguat sebagai penebak normatifnya, dan
pertahankan seluruh sisanya.**

Keuntungannya bukan cuma angka. Pohon dilatih dalam hitungan detik, sedangkan
transformer memakan sekitar seribu detik di kartu grafis. Untuk BPJS artinya
sistem bisa dilatih ulang tiap hari di perangkat biasa, tanpa kartu grafis,
tanpa bergantung pada penyedia awan.

Proposal yang keluar dari sini lebih sederhana, lebih murah, dan lebih mudah
dipertanggungjawabkan daripada yang kami rancang di awal. Itu hasil yang baik,
meski bukan hasil yang menyenangkan.

Transformer tetap disimpan di repositori, karena ia yang menghasilkan seluruh
pembedahan yang membawa kami ke sini, dan karena ablasi lanjutan mungkin
menemukan konfigurasi yang berbeda. Tapi ia tidak lagi menjadi usulan utama
sampai ada bukti yang mendukungnya.

### Papan skor akhir

| Target | Hasil |
|---|---|
| T1 dua kali atas aturan pada seribu klaim | belum, 1,73. Tercapai pada lima puluh teratas, 2,53 |
| T2 jaminan konformal | **tercapai** |
| T3 mengalahkan pohon berpenguat | **gagal**, 0,649 melawan 0,721 porsi batas atas |
| T4 pralatih memberi perbaikan | tercapai, tapi menjadi tidak relevan bila tulang punggungnya diganti pohon |
| T5 keadilan antar kelompok | tercapai tipis, 1,77 dan 2,02 pada dua jalan |
| T6 ketahanan pelaku | **tercapai** |
| T7 faskes tak dikenal | tercapai |

---

## Detektor yang diusulkan, 6 September 2026

`src/nalar/detektor.py`, diuji lewat `scripts/uji_detektor.py`,
hasil di `runs/detektor.json`, bobot di `runs/detektor.pkl`.

Sampai percobaan 12, kesimpulan sudah menyatakan pohon berpenguat yang menang,
tapi tidak ada satu berkas pun yang berisi konfigurasi itu sebagai model jadi.
Yang ada masih transformer yang sudah dinyatakan kalah. Berkas ini menutup
jarak antara kesimpulan dan barang yang bisa dipakai.

Isinya: penebak normatif berbasis pohon, kalibrasi konformal bertingkat,
antrean audit yang sadar biaya, dan lapisan penjelasan. Tidak memakai satu pun
label kecurangan.

### Hasil

| k | Rupiah ditemukan | Porsi batas atas |
|---|---:|---:|
| 50 | 222,3 jt | 0,336 |
| 100 | 381,1 jt | 0,448 |
| 500 | 1.005,6 jt | 0,679 |
| 1000 | 1.249,3 jt | 0,713 |

Peningkatan atas mesin aturan 1,896 kali pada seribu klaim. Atas garis dasar
urutkan menurut nilai klaim, 1,276 kali.

Jaminan konformal terpenuhi: laju penandaan klaim bersih 0,673 persen pada
alpha dua persen.

### Antrean audit, dan angka yang bisa dibawa ke rapat

Dari kapasitas seribu pemeriksaan, antrean hanya terisi 541. Sisanya tidak
diisi karena selisihnya lebih kecil daripada biaya memeriksanya, jadi memeriksa
tidak sepadan. Itu perilaku yang benar, bukan kekurangan.

  Rupiah ditemukan       Rp 942,2 juta
  Biaya audit            Rp 405,8 juta pada asumsi Rp 750.000 per berkas
  **Rasio pengembalian   2,32 banding 1**

NHS melaporkan 3 banding 1 untuk program yang sudah berjalan bertahun tahun.
Angka kami sejenis dan bisa dibandingkan langsung. Biaya per berkas adalah
parameter kebijakan yang harus diisi BPJS, bukan angka yang kami tetapkan.

### Penjelasan yang bisa dibantah

Contoh keluaran pada klaim berperingkat teratas:

  Tarif ditagihkan            Rp 134.341.600
  Tarif didukung bukti        Rp  72.141.295
  Selisih                     Rp  62.187.912

  Bukti yang bila ada akan mengubah penilaian:
    leukosit      menurunkan selisih Rp 4.725.894
    trombosit     menurunkan selisih Rp 3.928.075
    kreatinin     menurunkan selisih Rp 3.258.344

  Status: ketidaksesuaian yang perlu dikonfirmasi

Bentuk ini yang membuat P5 pada rancangan bisa dijalankan. Rumah sakit tidak
menerima skor, ia menerima daftar pemeriksaan yang bila dikirim akan menggugurkan
penandaannya. Kata curang tidak pernah muncul.

### Keadilan: empat percobaan perbaikan, dan satu kegagalan yang jujur

Perbaikan yang dicoba, berurutan, beserta hasilnya:

1. Kunci kalibrasi ditambah status daerah tertinggal dan ada tidaknya
   laboratorium. Rasio daerah tertinggal turun dari 5,3 ke 3,6.
2. Kalibrasi mundur bertingkat, dari kunci halus ke kasar. Turun tipis ke 3,63.
3. Syarat jumlah faskes minimum per kelompok. **Gagal dan salah sasaran**:
   yang menahan diri malah rumah sakit kelas B, sedangkan daerah tertinggal
   tidak berubah. Dikembalikan.
4. Pengecualian kebijakan yang eksplisit untuk daerah tertinggal.

Yang keempat berhasil untuk arah yang berbahaya. Faskes di daerah tertinggal
sekarang 0,0 persen melawan 0,70 persen. Tapi itu bukan perbaikan teknis, itu
keputusan untuk tidak menandai apa pun di sana sampai kami bisa menjamin
keadilannya. Mereka tetap masuk lewat porsi sampel acak lima persen.

Dan target T5 tetap gagal, pada dua ukuran sekaligus:

| Ukuran | Nilai | Batas | Lulus |
|---|---:|---:|---|
| Rasio simetris antar kelas faskes | 5,263 | 2,0 | tidak |
| Kelebihan berarah, kelompok terbanyak ditandai | 2,588 pada kelas B | 2,0 | tidak |

Rasio simetris yang 5,26 itu justru naik setelah perbaikan, karena FKTP
sekarang ditandai lebih jarang. Ditandai lebih jarang bukan kerugian, jadi
ukuran simetris menyamakan dua hal yang berbeda. Karena itu ditambahkan ukuran
berarah, yang hanya menghitung kelompok yang ditandai di atas laju keseluruhan.

Ukuran berarah pun gagal, 2,588 pada rumah sakit kelas B. Tapi arah masalahnya
sudah berpindah dari puskesmas di daerah terpencil ke rumah sakit besar, dan
itu posisi yang jauh lebih bisa dipertahankan.

Ukuran simetris tetap dilaporkan, supaya tidak ada yang disembunyikan dengan
mengganti definisi setelah melihat hasil.

### Yang masih terbuka

- Uji latih di sintetis uji di nyata terhadap DE-SynPUF, belum dijalankan
- Kontrol negatif pada label LEIE, belum dijalankan
- Kepala K4 kelompok sebaya, presisi 0,2 sampai 0,3 melawan tebakan acak 0,16,
  belum diperbaiki dan belum dipensiunkan resmi
- Kepala K6 titik perubahan, belum ditulis
- Ketimpangan pada rumah sakit kelas B, 2,588 kali

---

## Menutup empat lubang yang tersisa, 6 September 2026

Empat hal yang ditinggalkan pada catatan sebelumnya dikerjakan. Dua selesai,
satu gagal dengan sebab yang bisa ditunjuk, satu terhalang data.

### Uji latih di sintetis uji di nyata. Gagal.

Rancangan bagian 12.6 menuliskan uji ini sebagai syarat kelulusan. Tugasnya
menebak biaya klaim rawat inap dari umur, jenis kelamin, lama rawat, banyak
diagnosis, dan banyak prosedur. Kode diagnosis tidak ikut, karena Amerika
memakai ICD-9 dan kami ICD-10.

Satu peringatan harus ikut setiap kali angka di bawah dikutip. DE-SynPUF
sendiri sudah disintesis CMS dari klaim asli demi privasi. Jadi yang diadu
bukan karangan melawan nyata, melainkan karangan kami melawan sintetis yang
diturunkan dari klaim betulan.

| Model | Spearman | R² |
|---|---:|---:|
| tebakan rata rata | 0,000 | 0,000 |
| dilatih di data kami, diuji di klaim Amerika | 0,270 | 0,073 |
| dilatih dan diuji di klaim Amerika | 0,540 | 0,291 |

Penurunannya 50 persen pada Spearman dan 75 persen pada R². Batas yang kami
tetapkan sebelum melihat data adalah sepertiga. **Gagal, pada dua ukuran.**

Yang bisa dinyatakan: data karangan kami memuat struktur biaya yang benar
benar berpindah ke klaim betulan, terukur pada lima belas ribu klaim dari
enam ratus tujuh puluh rumah sakit yang tidak pernah dilihat model. Itu bukan
nol dan bukan hal yang dijamin sebelumnya. Yang tidak bisa dinyatakan: bahwa
data kami wakil yang setia. Ia mencapai separuh sinyal peringkat yang didapat
model yang belajar dari klaim betulan.

Dua hal yang muncul dari uji ini lebih berguna daripada nilai lulus gagalnya.

Pertama, kami sempat menyimpulkan generator kami kurang mengode penyakit
penyerta. Milik kami satu koma satu diagnosis sekunder per klaim rawat inap,
Amerika tujuh koma nol tujuh, dan bedanya tetap di setiap pita umur. Tapi
sebaran Amerika ternyata memusat: lima puluh sembilan persen klaim berisi
persis delapan diagnosis dari sembilan slot yang tersedia. Itu perilaku
mengisi slot, bukan gambaran klinis, dan korelasinya dengan biaya hanya nol
koma lima belas melawan nol koma empat enam milik jumlah prosedur. Kolom yang
sebarannya begitu tidak bisa dipakai menghakimi generator siapa pun.

Kedua, arah sebaliknya dicoba. Model yang belajar dari klaim Amerika lalu
diuji pada data kami jatuh delapan puluh lima persen, jauh lebih buruk
daripada arah pertama yang lima puluh persen. Kalau data kami sekadar versi
miskin dari kenyataan, arah itu seharusnya mulus. Yang terjadi kebalikannya.
Sebabnya kelihatan pada langit langit masing masing: dengan lima kolom yang
sama, model yang dilatih dan diuji di data kami hanya sampai nol koma tiga
enam, sedangkan di data Amerika nol koma lima empat. Lima kolom bersama itu
memerikan dunia mereka jauh lebih baik daripada dunia kami, karena tarif
INA-CBG ditentukan pencarian kode, bukan lama rawat.

Jadi ambang sepertiga yang kami tulis mengandaikan dua dunia yang lebih mirip
daripada kenyataannya. Kami tidak mengganti ambangnya sesudah melihat hasil.
Kami melaporkan gagal, dan menuliskan sebabnya.

### Kontrol negatif LEIE. Terhalang, dan bukan karena kurang usaha.

LEIE terunduh, delapan ribu enam ratus NPI sah dari delapan puluh tiga ribu
baris. Rencananya disambungkan ke DE-SynPUF lewat NPI dokter.

Irisannya nol persis. NPI dokter DE-SynPUF diawali angka nol, di luar rentang
NPI yang sah, jadi memang pengganti buatan CMS. Sambungan itu mustahil, dan
kami tahu itu dari mengukur, bukan dari membaca dokumentasi.

Sumber publik satu satunya yang memuat NPI sungguhan beserta pola penagihan
adalah tabel pemanfaatan dokter Medicare di data.cms.gov. Situs itu menolak
setiap klien dengan 403 dari Akamai: urllib, curl dengan tajuk peramban penuh,
Chromium tanpa jendela, dan Chromium berjendela sekalian. Empat cara, semuanya
tertutup di sisi tepi jaringan.

Jadi uji ini tetap terbuka, dan kami menuliskannya sebagai terhalang, bukan
sebagai belum sempat. Kalimat yang kami tulis sendiri di catatan sebelumnya
tetap berlaku: kalau arsitektur kami tidak bisa menemukan kecurangan nyata
pada data nyata, keberhasilannya pada data sintetis kami tidak berarti apa
apa.

### Kepala K4 ditulis ulang. Dari 1,5 kali menjadi 5,5 kali.

Versi lama membentuk kelompok sebaya dari representasi transformer lalu
membandingkan sebaran kode INA-CBG dengan divergensi Jensen Shannon.
Presisinya pada sepuluh teratas 0,2 sampai 0,3 melawan tebakan acak 0,16.

Sebabnya bisa ditunjuk. Divergensi itu dihitung atas sebaran sepanjang 885
kode yang ditaksir dari empat puluh klaim. Sebagian besar yang terukur adalah
derau pencuplikan, dan statistiknya tidak pernah mengoreksi banyaknya klaim.
Yang diurutkan pada akhirnya adalah kekecilan faskes.

Versi baru mengganti keduanya. Kelompok sebaya dari sifat administratif yang
bisa dilihat siapa saja, yaitu kelas, wilayah, kepemilikan, dan status daerah
tertinggal. Statistiknya penyusutan Bayes empiris, yang pekerjaannya justru
menarik taksiran dari sedikit data mendekat ke rata rata kelompoknya.

| Cara memberi peringkat | presisi@10 | presisi@25 | presisi@50 |
|---|---:|---:|---:|
| urutkan menurut total nilai klaim | 0,300 | 0,280 | 0,200 |
| rata rata selisih, tanpa penyusutan | 0,500 | 0,600 | 0,660 |
| **dengan penyusutan** | **1,000** | **1,000** | **0,740** |

Prevalensi faskes nakal di antara yang dinilai 0,181, jadi angka satu itu
lima koma lima kali tebakan acak. Penyusutannya bekerja: tanpa itu presisi
pada sepuluh teratas cuma separuh.

Yang tertangkap juga masuk akal. Seluruh faskes berkebijakan sistematis dan
ekstrem masuk dua puluh lima teratas, sembilan dari sembilan dan lima dari
lima. Yang oportunis sebelas dari dua puluh sembilan. Tidak ada satu pun
faskes jujur di dalamnya.

Angka sesempurna itu wajib dicurigai, jadi dua kebocoran diperiksa. Pemisahan
latih dan uji memang per faskes, jadi faskes uji tidak pernah dilihat saat
latih. Dan fitur pohonnya memuat sifat faskes, bukan identitasnya. Yang
tersisa satu peringatan jujur: mencurigai faskes memang lebih mudah daripada
mencurigai klaim. Faskes sistematis menaikkan tarif pada enam dari sepuluh
klaim yang memenuhi syarat, dan dengan dua ratus klaim tandanya terang.

### Ketimpangan kelas B. Selesai, dan sebabnya bukan yang kami kejar.

Empat percobaan sebelumnya salah sasaran. Yang kelima berhasil karena
diukur lebih dulu.

Dugaan pertama dipatahkan cepat. Membatasi hitungan hanya pada faskes jujur
justru memperburuk, dari 2,588 ke 2,868. Jadi ini bukan soal klaim bersih di
faskes nakal.

Angka mentahnya yang menunjukkan jalan. Kelas B ditandai 2,10 persen dan
kelas D 1,78 persen, keduanya persis di sekitar alpha dua persen yang memang
dijanjikan. Yang menyimpang FKTP, di 0,34 persen, seperenam jatahnya. FKTP
memikul tujuh puluh dua persen klaim, jadi laju keseluruhan tertarik turun ke
0,73 persen dan setiap kelas rumah sakit otomatis terlihat berlebih.

Ketimpangannya bukan rumah sakit ditandai terlalu sering. Ketimpangannya
FKTP ditandai terlalu jarang.

Sebabnya kontaminasi himpunan kalibrasi. Nama parameternya berbunyi bersih,
tapi yang masuk adalah klaim apa adanya dan sebagiannya curang. Persentil
sembilan puluh delapan selisih klaim bersih FKTP 7.415 rupiah, sedangkan
ambang yang terhitung 18.719. Pada kelas B pengangkatannya hanya sepertiga.
Bukan karena kelas B lebih jujur, melainkan karena sebaran selisih bersihnya
sudah lebar sejak awal sehingga tambahan klaim curang tidak banyak menggeser
ujungnya. Sebaran FKTP rapat, enam puluh persen selisihnya nol persis, jadi
sedikit klaim curang langsung mengangkatnya.

Perbaikannya memakai kepala K4 yang baru untuk menyaring: faskes yang
selisihnya menonjol terhadap sebayanya dikeluarkan dari himpunan kalibrasi.
Tidak ada label yang dipakai. Batas pemotongannya disapu, dan seluruh
sapuannya dilaporkan, bukan hanya yang paling menguntungkan.

| Batas z | Klaim dibuang | FKTP | Kelas B | Kelebihan berarah | Rupiah pada seribu |
|---|---:|---:|---:|---:|---:|
| tidak menyaring | 0% | 0,003 | 0,017 | 2,588 | 1.249,3 jt |
| 2,00 | 1% | 0,005 | 0,017 | 2,202 | 1.249,3 jt |
| 1,50 | 2% | 0,007 | 0,017 | 1,866 | 1.249,3 jt |
| **1,00** | **3%** | **0,009** | **0,017** | **1,579** | **1.249,3 jt** |
| 0,50 | 6% | 0,012 | 0,017 | 1,361 | 1.249,3 jt |

Kelas rumah sakit hampir tidak bergerak, FKTP naik menuju jatahnya, dan
rupiah yang ditemukan tidak berubah satu digit pun karena peringkatnya memang
tidak disentuh. Yang dipilih 1,00, satu simpangan baku di atas rata rata
sebaya, membuang tiga persen klaim kalibrasi dan lulus dengan jarak, bukan
lulus tipis.

Risikonya kami tuliskan: model ikut memilih data yang mengkalibrasi dirinya
sendiri. Itu sebabnya sapuannya dilaporkan utuh.

Hasil akhir pada target T5:

| Ukuran | Sebelum | Sesudah | Batas | Lulus |
|---|---:|---:|---:|---|
| Rasio simetris antar kelas faskes | 5,263 | **1,879** | 2,0 | ya |
| Kelebihan berarah | 2,588 | **1,579** | 2,0 | ya |

Sisa detektornya tidak bergeser. Rupiah pada seribu tetap 1.249,3 juta, porsi
batas atas 0,713, rasio pengembalian audit 2,32.

### Daerah tertinggal. Tiga aturan umum dicoba, ketiganya gagal.

Pengecualian kebijakan untuk daerah tertinggal masih ada, dan kami mencoba
menggantinya dengan aturan umum supaya tidak perlu menyebut satu kelompok
secara khusus. Tiga cara dicoba dan ketiganya diukur.

Ambang yang mengeluarkan satu faskes bergantian lalu mengambil yang terbesar
tidak menggerakkan apa pun. Laju penandaan daerah tertinggal tetap 2,53
persen dengan dan tanpa. Mengeluarkan satu dari tiga puluh faskes hanya
membuang dua setengah persen klaim, dan persentil sembilan puluh delapan
tidak bergeser sebanyak itu.

Menaikkan syarat jumlah faskes minimum salah sasaran, sama seperti percobaan
sebelumnya. Pada dua puluh, kelas B yang menahan diri sementara daerah
tertinggal tidak bergerak.

Membuat penolakan karena kurang faskes berarti menahan diri, bukan turun ke
kelompok yang lebih kasar, juga gagal. Pada empat puluh, laju daerah
tertinggal justru melonjak ke 9,4 persen, karena klaim yang kelompok
halusnya ditolak karena kurang klaim tetap jatuh ke ambang FKTP umum yang
terlalu ketat baginya.

Sesudah tiga kegagalan itu, sebabnya diukur langsung pada kelompoknya. FKTP
daerah tertinggal punya tiga puluh faskes kalibrasi dan delapan belas faskes
uji, dan persentil sembilan puluh delapan klaim bersihnya 15.233 di kalibrasi
melawan 30.937 di uji. Dua kali lipat. Bandingkan dengan kelompok yang sehat:
FKTP biasa tanpa laboratorium punya enam ratus empat puluh faskes kalibrasi
dan rasionya 1,08.

Jaminan konformal menuntut klaim kalibrasi dan klaim uji saling
terpertukarkan. Kami memisah per faskes, jadi ukuran contoh yang menentukan
bukan seribu lima ratus klaim melainkan delapan belas faskes. Pada jumlah
itu, tidak ada penaksir yang bisa memindahkan ambang dengan andal.

Jadi pengecualiannya tetap, dan sekarang punya alasan terukur. Kami tidak
menyatakan faskes di daerah tertinggal bersih. Kami menyatakan belum cukup
tahu untuk berjanji apa apa tentang mereka. Mereka tetap masuk pemeriksaan
lewat porsi sampel acak lima persen.

### Kepala K6 ditulis. Terkalibrasi, tapi lemah.

Generator diberi saklar supaya sebagian faskes nakal baru mulai nakal di
tengah rentang waktu. Tanpa itu K6 tidak punya apa apa untuk ditemukan.
Saklarnya mati secara bawaan, jadi seluruh angka percobaan lain tidak
bergeser.

Kendali positif palsu dijalankan lebih dulu, sebelum melihat daya temunya.
Pada data tanpa satu pun perubahan, 6,1 persen faskes ditandai berubah pada
ambang lima persen dan 0,9 persen pada ambang satu persen. Uji permutasinya
sah.

Satu jebakan ditemukan di jalan, dan pantas dicatat. Versi pertama memakai
peringkat tanpa memutus nilai yang seri. Enam puluh persen selisih klaim
bernilai nol persis, dan pengurutan yang stabil memberi klaim nol itu
peringkat menurut urutan kemunculannya, yaitu urutan waktu. Urutan waktu
tersuntik ke dalam nilai yang seharusnya tidak membawanya, dan tujuh puluh
satu persen faskes ditandai berubah pada data yang tidak memuat perubahan
apa pun. Diputus acak, angkanya kembali ke enam koma satu.

Daya temunya lemah, dan kami tidak membungkusnya:

| Kebijakan sesudah berubah | Ada | Tertangkap |
|---|---:|---:|
| oportunis | 8 | 12% |
| sistematis | 6 | 33% |
| ekstrem | 4 | 25% |

Tanggal tebakannya meleset dua ratus lima puluh dua hari dari rentang seribu
sembilan puluh lima hari. Terlalu kasar untuk ditindak langsung. Dan dari
delapan belas faskes yang berubah, sepuluh sudah tertangkap K4, sehingga
tambahan bersih K6 hanya dua faskes.

Jadi K6 dikirim sebagai isyarat pendamping dengan angkanya ditulis apa
adanya, bukan sebagai kemampuan yang dijual. Ia benar secara statistik dan
kecil secara guna.

### Yang masih terbuka

- Kontrol negatif LEIE, terhalang di sisi data
- T1 pada seribu klaim, 1,896 kali melawan target dua kali
- T3, pohon normatif tetap mengalahkan NALAR
- Uji transfer gagal, dan sebabnya sudah ditulis di atas

---

## Seberapa kokoh angkanya, dan satu kegagalan yang harus ditulis besar

### Kestabilan benih. Ini mengubah cara seluruh angka kami boleh dikutip.

Semua yang kami laporkan sampai sekarang berasal dari satu benih acak. Lima
benih dijalankan, dan hasilnya membelah dua kelompok yang sangat berbeda
sifatnya.

| Ukuran | Rata rata | Sebaran relatif | Terendah | Tertinggi |
|---|---:|---:|---:|---:|
| Rupiah pada seribu klaim | 1.398 jt | **40,0%** | 841 jt | 2.304 jt |
| Porsi batas atas | 0,752 | **10,1%** | 0,688 | 0,882 |
| Peningkatan atas mesin aturan | 1,853 | 8,4% | 1,608 | 2,027 |
| Laju penandaan klaim bersih | 0,0125 | 18,5% | - | - |
| Kelebihan berarah | 1,341 | 12,4% | 1,148 | 1,579 |

Angka rupiah bergeser empat puluh persen antar benih. **Rp 1.249,3 juta tidak
boleh dikutip sendirian.** Yang stabil adalah porsi batas atas, dan itu memang
alasan kami memilihnya sebagai metrik utama sejak rancangan. Sekarang alasan
itu punya bukti, bukan hanya niat.

Dua hal lain yang keluar dari sini. Peningkatan atas mesin aturan 1,853 dengan
simpangan 0,155, jadi target T1 yang dua kali itu berada di dalam jangkauan
satu simpangan, dan satu dari lima benih benar benar mencapainya di 2,027.
Jujurnya: T1 gagal pada rata rata, lulus pada satu benih. Bukan gagal telak.

Dan keadilan berarah lulus di kelima benih, tertinggi 1,579 melawan batas dua.
Perbaikan penyaringan kontaminasi itu nyata, bukan kebetulan satu benih.

### Kepekaan prevalensi. Hasil terkuat yang tidak kami duga.

Prevalensi 22 persen faskes nakal adalah asumsi kami, dan semua berdiri di
atasnya. Yang diperiksa: apakah detektornya masih berguna kalau kecurangan
jauh lebih jarang.

| Faskes nakal | Klaim curang | Rupiah pada seribu | Porsi batas atas | Atas aturan |
|---:|---:|---:|---:|---:|
| 8% | 0,8% | 145 jt | 0,711 | 1,775 |
| 15% | 3,0% | 927 jt | 0,767 | 1,506 |
| 22% | 4,5% | 1.249 jt | 0,713 | 1,896 |
| 35% | 6,7% | 2.099 jt | 0,803 | 1,676 |

Rupiahnya turun sembilan kali lipat dari yang tertinggi ke yang terendah,
tapi porsi batas atas hampir tidak bergerak. Mutunya tidak bergantung pada
seberapa banyak kecurangan yang ada, yang bergantung hanya uangnya. Itu
perilaku yang benar untuk sistem pengawasan, dan artinya angka mutu kami tidak
dibesarkan oleh asumsi prevalensi yang mungkin terlalu tinggi.

Satu batasnya ditemukan di ujung atas. Pada 35 persen, kelebihan berarah naik
ke 2,025 dan melewati batas dua. Jadi jaminan keadilan kami berlaku sampai
sekitar dua puluh dua persen dan mulai selip di atas itu.

### Pemisahan menurut waktu. T7 akhirnya tuntas.

Belum pernah dijalankan sama sekali sampai sekarang, dan inilah bentuk
pemakaian yang sebenarnya: dilatih pada masa lalu, dipakai pada masa depan.
Dua tahun pertama untuk latih dan kalibrasi, tahun ketiga untuk uji.

Porsi batas atas 0,756 melawan 0,713 pada pemisahan menurut faskes. Rasionya
1,06, jadi sedikit lebih baik, bukan lebih buruk. Jaminan konformal tetap
berlaku, laju penandaan klaim bersih 0,71 persen. Keadilan 1,457, lulus.

T7 naik dari tercapai sebagian menjadi tercapai.

### Target T6 gagal pada model yang benar benar kami kirim.

Ini lubang yang harus ditulis besar. Rancangan menyebut T6 sebagai hasil
terkuat kami, dan angkanya diukur pada transformer. Sejak percobaan kedua
belas yang kami kirim adalah pohon berpenguat. Jadi klaim terkuat pada dokumen
kami diukur pada model yang sudah tidak ada.

Diukur ulang pada detektor yang dikirim:

| Pelaku | Diambil | Tertangkap | **Uang yang lolos** | Maks per klaim |
|---|---:|---:|---:|---:|
| serakah | 1.793 jt | 78,5% | 385 jt | 36,2 jt |
| hati hati | 273 jt | 0,0% | 273 jt | 27,0 jt |
| menyebar | 1.268 jt | 54,4% | **579 jt** | 30,6 jt |

Penurunan keuntungan maksimum per klaim hanya 25,6 persen melawan batas
setengah. **Gagal.** Transformer dulu mencapai 96 persen.

Dan ada yang lebih buruk daripada sekadar gagal. Pelaku menyebar meloloskan
lebih banyak uang daripada pelaku serakah, 579 juta melawan 385 juta. Sistem
kami membuat menyebar lebih menguntungkan daripada serakah. Itu kebalikan dari
yang seharusnya dilakukan sistem pengawasan.

Pembandingnya tetap perlu disebut supaya tidak salah baca. Melawan mesin
aturan, pelaku hati hati meloloskan 1.440 juta. Melawan detektor kami, 273
juta. Jadi detektornya jauh lebih baik daripada aturan, ia hanya tidak membuat
kecurangan berhenti sepadan.

### Kepala kelompok sebaya juga gagal, dan sekarang kami tahu kenapa.

Rancangan sudah menyiapkan jawabannya: deteksi per klaim akan gagal menangkap
pelaku menyebar, dan yang seharusnya menangkap adalah kepala kelompok sebaya.
Kalimat berikutnya kami tulis sendiri, bahwa kalau kepala itu juga gagal kami
akan menuliskan gagal.

Diuji. Satu rumah sakit dibuat menagih tepat di bawah garis pada seluruh klaim
yang bisa diserang. Ia mengambil Rp 36,4 juta, yaitu sepuluh persen dari
seluruh tagihannya. Peringkat profilnya 221 dari 238 sebelum diserang, dan 221
sesudahnya. Tidak bergerak satu langkah pun.

Sebabnya diukur, bukan diduga, dan angkanya menutup perkara.

  Serangan menggeser rata rata selisih faskes       0,156 jt
  Lantai deteksi pada 233 klaim, dua simpangan      0,189 jt

Serangannya memang berada di bawah lantai derau. Simpangan baku selisih di
dalam satu faskes 1,44 juta, sedangkan antar faskes hanya 0,076 juta. Derau di
dalam faskes hampir dua puluh kali lebih besar daripada sinyal antar faskes.
Tidak ada penaksir rata rata rupiah yang bisa melihat serangan ini, berapa pun
pintarnya. Itu bukan kekurangan penyusutan Bayes kami, itu batas informasi.

Dua percobaan perbaikan dijalankan dan keduanya gagal. Memakai selisih yang
tidak dipotong di nol tidak menggerakkan peringkat sama sekali, dan malah
menurunkan presisi tugas biasa dari 1,000 ke 0,760. Membuang klaim yang
kelompoknya menahan diri juga tidak menolong.

### Ukuran posisi. Mekanismenya benar, kalibrasinya belum.

Kalau pelakunya menagih tepat di bawah garis, maka yang harus diukur adalah
jaraknya ke garis, bukan rupiahnya. Selisih dibagi ambang kelompoknya sendiri.
Nol berarti persis sebesar yang didukung bukti, satu berarti persis di ambang.

Pada serangan yang sama, ukuran ini bergeser 3,6 simpangan baku di dalam
faskes itu. Bandingkan dengan rata rata rupiah yang tenggelam di bawah derau.
Mekanismenya benar.

Tapi arahnya bukan melintang, melainkan memanjang. Sesudah diserang, faskes
itu hanya berada 0,52 simpangan di atas sebaran antar faskes, jadi
membandingkannya dengan tetangganya tetap tidak menunjukkan apa apa. Yang
menunjukkan adalah membandingkannya dengan dirinya sendiri di masa lalu.
Artinya penangkap pelaku beradaptasi adalah kepala titik perubahan, bukan
kepala kelompok sebaya. Itu membalik pembagian tugas yang kami tulis di
rancangan.

Diuji, dan hasilnya setengah jalan. Pada rumah sakit yang mengambil Rp 30,9
juta, ukuran posisi memberi p sebesar 0,0025 sedangkan rupiah 0,0848. Jadi
posisi menangkap yang rupiah lewatkan. Tapi dua rumah sakit lain yang
mengambil jauh lebih sedikit terlewat oleh keduanya, dan tanggal tebakannya
tetap tidak berguna.

Dan kalibrasinya meleset. Pada data tanpa serangan apa pun, sembilan koma dua
persen faskes ditandai berubah pada ambang lima persen, hampir dua kali
nominal. Dugaan bahwa penyebabnya klaim yang menahan diri diuji dan salah:
porsinya stabil sepanjang waktu, dan membuangnya justru menaikkan angka itu ke
sembilan koma enam. Dugaan yang tersisa, belum diuji, adalah klaim dari satu
pasien yang berkerumun di waktu berdekatan sehingga syarat keterpertukaran uji
permutasi tidak berlaku.

Jadi ukuran posisi dikirim sebagai alat pemeringkat dengan kalibrasi yang
diketahui meleset, bukan sebagai uji peluang. Nilai p nya dibaca sebagai
urutan, bukan sebagai probabilitas, dan itu ditulis di tempat angkanya
muncul.

### Yang masih terbuka

- T6 gagal pada model yang dikirim, dan pelaku menyebar meloloskan lebih
  banyak uang daripada pelaku serakah
- Kalibrasi uji permutasi pada ukuran posisi meleset dua kali lipat
- Kontrol negatif LEIE, terhalang di sisi data
- Uji latih di sintetis uji di nyata, gagal
- T3, pohon normatif tetap mengalahkan transformer yang kami rancang

---

## Dua daftar yang saling melengkapi, dan satu kalibrasi yang akhirnya benar

### Profil rupiah dan profil posisi menangkap hal yang berbeda

Sesudah tahu bahwa serangan menempel garis berada di bawah lantai derau
rupiah, ukuran posisi diuji sebagai profil faskes. Hasilnya bukan pengganti,
melainkan pelengkap, dan masing masing buruk persis di tempat yang lain kuat.

| | Presisi pada 25 teratas, tugas biasa | Terhadap pelaku beradaptasi |
|---|---:|---|
| diurut menurut rupiah | **1,000** | buta, peringkat 221 tetap 221 |
| diurut menurut posisi | 0,240 | peringkat 223 naik ke **87** dari 238 |

Jadi keduanya dikirim sebagai dua daftar terpisah, bukan digabung jadi satu
skor. Menggabungkannya akan merusak keduanya. Daftar pertama bertanya siapa
menagih lebih daripada yang didukung bukti. Daftar kedua bertanya siapa
menagih terus menerus persis sebanyak yang masih diizinkan.

Daftar kedua bukan tuduhan, dan itu ditulis di dalam keluarannya. Menagih
menempel batas bisa berarti pengodean yang rapi dan bisa berarti sesuatu yang
lain. Yang dituntut darinya penjelasan, bukan pengembalian.

Peringkat 87 dari 238 masih di luar antrean audit dua puluh lima teratas, jadi
ini peredaman sebagian dan bukan penyelesaian. Tapi pergerakan dari 223 ke 87
pada pencurian sepuluh persen tagihan itu nyata, sedangkan daftar rupiah
memberi nol pergerakan.

### Satu perbaikan yang dicoba dan gagal

Sampel audit acak dicoba ditimbang menurut posisi, dengan harapan mengejar
pelaku yang menempel garis. Hasilnya lebih buruk daripada acak seragam, 3,3
persen melawan 4,4 persen uang tertangkap. Sebabnya klaim yang diserang
berkerumun pada posisi yang mirip mirip, jadi menimbang menurut posisi tidak
memusatkan anggaran ke klaim yang nilainya paling besar. Acak seragam justru
menyebar peluang sebanding dengan uangnya.

### Kalibrasi uji permutasi akhirnya benar, dan itu menurunkan angka kami sendiri

Ukuran posisi menandai 9,2 persen faskes berubah pada data yang tidak memuat
perubahan apa pun, hampir dua kali nominal. Dua dugaan diuji dan gugur, yaitu
klaim yang menahan diri dan nilai yang seri.

Yang ketiga benar. Posisi dua klaim milik pasien yang sama berkorelasi 0,135,
sedangkan dua klaim yang diambil acak berkorelasi nol. Pasien yang sama datang
berdekatan waktunya, jadi korelasi itu tersalin menjadi struktur waktu yang
tidak pernah dihancurkan oleh pengacakan per klaim. Uji permutasi
mengandaikan klaim saling terpertukarkan, dan klaim dari satu pasien memang
tidak.

Perbaikannya mengacak urutan blok pasien, bukan isinya:

| | p<0,05 sebelum | p<0,05 sesudah |
|---|---:|---:|
| ukuran posisi | 9,2% | **6,1%** |
| selisih rupiah | 6,1% | **4,8%** |

Dan inilah bagian yang tidak menyenangkan. Kalibrasi yang benar menurunkan
angka daya temu kami sendiri. Kepala K6 pada selisih rupiah yang tadinya
tertangkap 22 persen turun menjadi 16,7 persen, dan pada ambang satu persen
menjadi nol. Pecahan menurut kebijakan yang tadinya terlihat naik seiring
keparahan sekarang berantakan, dan dengan empat sampai delapan faskes per
kelompok memang itu yang seharusnya terlihat.

Jadi kesimpulan tentang K6 diperbaiki ke bawah. Pada tugas menemukan
kemunculan kecurangan, kepala ini praktis tidak punya daya pada ukuran faskes
yang kami punya. Angka 22 sampai 33 persen yang kami tulis sebelumnya
dibesarkan oleh uji yang mis-kalibrasi.

Yang bertahan adalah tugas yang lain. Pada pelaku beradaptasi, dengan
pengacakan per pasien dan laju salah tuduh yang sudah kembali ke nominal:

  Rumah sakit mengambil Rp 30,9 juta
    ukuran posisi   p = 0,0125
    selisih rupiah  p = 0,0723
  Salah tuduh pada 226 faskes lain
    ukuran posisi   5,3 persen
    selisih rupiah  4,9 persen

Posisi menangkap yang rupiah lewatkan, pada laju salah tuduh yang benar. Dua
rumah sakit lain yang mengambil jauh lebih sedikit terlewat oleh keduanya.

### Satu cacat ketelitian yang ditemukan di jalan

Profil faskes membulatkan seluruh kolomnya ke rupiah bulat. Ketika yang
dimasukkan bukan rupiah melainkan posisi, yang nilainya di antara minus satu
dan satu, seluruh kolomnya menjadi nol. Peringkatnya masih bekerja karena skor
baku dihitung sebelum pembulatan, tapi angka yang dilaporkan tidak berarti apa
apa. Ketelitiannya sekarang mengikuti besaran yang masuk.

### Papan skor sesudah semuanya

| Target | Hasil |
|---|---|
| T1 dua kali lipat atas mesin aturan | gagal, 1,853 ± 0,155, satu benih mencapai 2,027 |
| T2 jaminan konformal | tercapai |
| T3 mengalahkan pohon berpenguat | gagal |
| T4 pralatih menolong | tercapai |
| T5 keadilan antar kelompok | **tercapai**, lulus di kelima benih |
| T6 pelaku beradaptasi | **gagal**, dan menyebar lebih untung daripada serakah |
| T7 faskes dan periode tak dikenal | **tercapai** |

Empat tercapai, tiga gagal, dan ketiga kegagalannya punya sebab yang bisa
ditunjuk beserta angkanya.

---

## Lapisan agen, 7 September 2026: model 4B tidak mengalahkan aturan

`runs/ukur_agen.json`

Pengaturan: Qwen3 4B varian instruksi, berbobot terbuka, berjalan setempat di
GPU laptop delapan gigabita lewat Ollama. Suhu nol, jendela nalar dua belas
ribu token. Empat puluh berkas dengan selisih terbesar. Lima alat tersedia,
dan tidak satu pun di antaranya bisa mengubah penilaian.

Rencananya menuliskan satu aturan yang tidak boleh dilanggar: model bahasa
tidak pernah menentukan sebuah berkas ditandai atau tidak, dan tidak pernah
menyebut angka rupiah yang tidak berasal dari pemanggilan alat. Percobaan ini
menguji yang kedua.

### Yang berjalan

Tidak ada satu pun angka tak bersumber pada berkas perkara yang benar benar
keluar. Target A1 terpenuhi, dan terpenuhinya bukan karena modelnya patuh.

Biayanya Rp 51 per berkas, dibanding ongkos periksa manual Rp 750 ribu. Itu
sepersepuluh ribu, sepuluh kali lebih murah daripada ambang A7 yang kami
tulis sebelum percobaan. Lamanya sebelas setengah detik per berkas.

### Yang gagal, dan ini yang lebih penting

Dua puluh enam dari empat puluh berkas mundur ke versi aturan. Dua puluh tiga
di antaranya mundur karena berkasnya tidak lolos penjaga A1, artinya model
tetap mengetik angka yang tidak pernah dikembalikan alat, sekalipun arahannya
melarang mengetik angka sama sekali dan menyediakan nama isian untuk tiap
besaran yang mungkin dibutuhkannya.

Angka yang diketiknya bukan karangan bebas. Ia mengambil nilai mutlak dari
butir pengandaian yang bertanda negatif, lalu menuliskannya sebagai
penurunan. Itu persis cacat yang pernah lolos ke antarmuka kami sendiri
beberapa hari sebelumnya, dan sekarang model kecil mengulanginya tanpa
diajari.

Dari empat belas berkas yang lolos saringan cepat, sebelas membawa cacat
ikatan: sebuah nama diikuti angka yang bukan miliknya. Satu contohnya menulis
selisih Rp 489.690 padahal selisih berkas itu Rp 6.047.842. Angka yang
disebutnya sah, ia memang dikembalikan alat, hanya saja ia milik satu butir
bukti, bukan milik selisih. Penjaga A1 tidak bisa menangkap yang seperti itu,
dan memang bukan tugasnya.

Jadi dari empat puluh berkas, tiga keluar dari agen dalam keadaan bersih.

### Putusannya

Rencana sudah menuliskan apa yang dilakukan bila ini terjadi. Berkas perkara
versi aturan adalah garis dasar, dan agen yang tidak mengalahkannya dicabut.
Model 4B tidak mengalahkannya, jadi yang dilayani peragaan tetap versi
aturan, dan itu yang sudah dikerjakan kode tanpa perlu diubah: berkas yang
jatuh di saringan otomatis keluar sebagai versi aturan.

Yang tidak dicabut lapisan alat, jejak audit, dan kedua penjaganya. Ketiganya
justru terbukti bekerja, dan ketiganya yang membuat kegagalan ini terlihat
sebagai angka alih alih sebagai surat salah yang terlanjur dikirim.

### Tiga hal yang dipelajari

**Larangan pada arahan bukan penjagaan.** Model 4B melanggar larangan
mengetik angka pada lebih dari separuh berkas. Yang menahan bukan
arahannya, melainkan penjaga yang memeriksa keluarannya.

**Penjaga yang benar menangkap penulisnya sendiri.** Penjaga A1 ditulis
sebelum ada agen, dan yang pertama ditangkapnya penyusun berbasis aturan
buatan kami. Kalau ia ditulis sesudah agennya jadi, yang terjadi bukan
penjagaan melainkan penyesuaian penjaga terhadap kelakuan agen.

**Angka yang benar bisa dilekatkan pada nama yang salah.** Ini kelas cacat
yang tidak tersentuh pemeriksaan asal usul angka, muncul pada sebelas dari
empat belas berkas, dan hanya terlihat oleh pemeriksaan yang membongkar tiap
pernyataan jadi pasangan nama dan nilai. Pemeriksaan itu terlalu mahal untuk
dijalankan pada tiap berkas, dan itu sebabnya gerbang layak kirim ditera,
bukan ditetapkan.

### Batasan percobaan ini

Empat puluh berkas, satu model, satu benih. Model yang lebih besar hampir
pasti lebih patuh, dan yang belum diuji berapa besar yang cukup. Yang bisa
disimpulkan cuma satu: 4B tidak cukup, dan lapisan penjaganya menahan
ketidakcukupan itu tanpa satu pun surat salah keluar.

### Satu cacat yang ketahuan dari membaca layarnya, bukan dari uji

Berkas perkara yang tayang di halaman klaim berbunyi diajukan Rp 3.498.300,
didukung bukti Rp 3.086.958, selisih Rp 411.341. Pengurangannya memberi
Rp 411.342.

Sebabnya tiap bagian dibulatkan sendiri sendiri. Selisih dihitung dalam
pecahan lalu dibulatkan, dan jumlah bagian yang dibulatkan tidak selalu sama
dengan pembulatan jumlahnya. Bedanya satu rupiah, dan satu rupiah itu tidak
penting sama sekali bagi penilaiannya. Yang penting akibatnya: verifikator
yang mengurangkan dua angka pertama dan mendapat angka ketiga yang berbeda
akan berhenti mempercayai seluruh suratnya, dan ia benar berhenti.

Diukur sesudahnya, tiga puluh dua dari empat ratus berkas meleset. Uji
peladen sudah memeriksa pengurangan ini sejak lama, tapi hanya pada satu
berkas, dan berkas itu kebetulan cocok. Sekarang diperiksa pada enam puluh
berkas untuk penilaian, empat puluh untuk kalimat faskes, dan empat puluh
untuk berkas perkara.

Pembulatannya sekarang dikerjakan sekali di `nalar/pembulatan.py`, dan
seluruh angka turunan disusun dari empat angka yang sudah dibulatkan
bersama. Ada satu pengecualian yang harus ditulis: selisih dijepit di nol
mengikuti penebak, jadi berkas yang ditagihkan lebih kecil daripada yang
didukung bukti memang tidak bisa dikurangkan. Kalimatnya dibedakan untuk
berkas seperti itu, bukan dipaksa memuat tiga angka yang tidak bertemu.

---

## Lapisan lawan, 7 September 2026: lubang yang kami buat sendiri

`runs/agen_lawan.json`

Pengaturan: 160.455 episode, 41.741 masuk uji, detektor yang benar benar
dikirim. Himpunan uji dibelah dua menurut faskes: separuh untuk menemukan
siasat, separuh untuk mengesahkannya. Pelaku diberi akses penuh ke skor
detektor, dan ambangnya diambil sebelum satu serangan pun.

Ketiga pelaku yang selama ini dipakai mengukur T6 kami tulis sendiri, dan
ketiganya memakai satu modus saja. Pertanyaan yang tidak bisa dijawab
pengujian seperti itu: apakah ada siasat yang tidak terpikir oleh kami.

### Ada, dan yang terbaik bukan yang paling rumit

Siasatnya ditulis sebagai data, bukan sebagai program, memakai
perbendaharaan enam gerakan, empat sasaran, dan lima cara memilih. Seluruh
ruangnya seratus dua puluh siasat, dan seratus dua puluhnya ditelusuri habis
dalam tiga puluh detik tanpa model bahasa sama sekali.

Lima siasat mengalahkan garis dasar di kedua himpunan. Yang terbaik satu
kalimat panjangnya: tambahkan diagnosis sekunder, lalu lampirkan tiga hasil
pemeriksaan penunjang, dan berhenti sebelum ambang.

| Pelaku | Uang yang lolos | Tertangkap |
|---|---:|---:|
| serakah | 227,6 jt | 64,0% |
| hati hati | 314,2 jt | 0,0% |
| menyebar | 247,0 jt | 43,8% |
| **upcode berlapis bukti** | **427,2 jt** | **0,0%** |

Angka itu dari himpunan pengesahan, yang tidak pernah dilihat selama
pencarian. Seratus tiga belas juta lebih banyak daripada pelaku terbaik yang
kami tulis sendiri, dan tidak satu berkas pun tertangkap.

### Kenapa ia bekerja, dan kenapa kami seharusnya sudah tahu

Diagnosis sekunder sengaja dibuang dari penciri penebak. Itu keputusan sadar
dan benar: kalau ia jadi penciri, menambahkannya menaikkan tebakan dan
selisihnya menghilang.

Pemeriksaan penunjang justru dipakai sebagai penciri. Melampirkannya
menaikkan tarif yang dianggap wajar tanpa menaikkan satu rupiah pun tarif
yang ditagihkan.

Gabungan keduanya menaikkan tagihan lewat pintu yang tidak diawasi, lalu
menurunkan kecurigaan lewat pintu yang diawasi. Kami sudah menulis sendiri di
pustaka aturan bahwa lama rawat, kelas rawat, dan bukti penyerta adalah titik
buta penebak normatif. Yang tidak kami lakukan menguji titik buta itu sebagai
serangan.

### Dua puluh empat siasat yang tidak pernah tertangkap sama sekali

Dilaporkan terpisah dan tidak dihitung sebagai temuan, karena sebagian besar
mengambil lebih sedikit daripada garis dasar. Tapi bentuknya perlu ditulis:
menyasar berkas yang selisih awalnya kecil, dan menyasar kelompok yang
sistemnya sendiri menahan diri. Menahan diri adalah keputusan yang benar
ketika pembandingnya kurang dari tiga, dan ia juga tempat berteduh yang kami
sediakan sendiri dan umumkan di dokumen.

### Agen Lawan sendiri tidak menemukan apa pun

Model 4B mencoba tiga siasat lalu mengulang siasat yang sama, dan penyelia
memutus rantainya. Nol temuan. Papan skornya diberikan utuh tiap giliran,
lengkap dengan daftar siasat yang sudah dicoba, dan ia tetap mengulang.

Satu kegagalan sebelumnya adalah kesalahan kami, bukan kesalahan model. Agen
diberi alat kedua untuk membaca papan skor, padahal papan skornya sudah ada
di dalam arahan. Memanggilnya adalah hal pertama yang masuk akal dilakukan,
dan karena tiap giliran disusun ulang dari nol ia tidak ingat sudah
memanggilnya, jadi penyelia memutus rantainya sebelum satu siasat pun dicoba.
Alatnya dibuang, dan sesudah itu barulah kegagalannya milik model.

Jadi yang menemukan kelima siasat itu pencarian biasa, bukan agen. Ditulis
apa adanya: pada tahap ini model bahasa tidak menambah apa pun di atas
menelusuri ruang yang kecil sampai habis.

### Papan skor sesudah percobaan ini

| Target | Hasil |
|---|---|
| A4 tiga siasat penghindaran baru yang bisa diulang | **tercapai**, lima siasat bertahan di himpunan pengesahan |
| A5 T6 naik dari 25,6 persen ke 40 persen | belum diuji, kasus ujinya baru ada sekarang |

Yang berubah dari percobaan ini bukan angkanya, melainkan daftar pekerjaan.
Sebelum ini kami tahu T6 gagal. Sekarang kami tahu satu sebab yang bisa
ditunjuk dan diulang, dan tambalannya punya bentuk: bukti penyerta tidak
boleh menurunkan kecurigaan pada berkas yang tarifnya baru saja naik karena
diagnosis sekunder.

---

## Tambalan yang diuji lalu tidak dipasang, 7 September 2026

`runs/tambal_bukti.json`, `runs/tambal_bukti_p99.json`

Lapisan lawan menemukan siasat yang meloloskan Rp 427,2 juta tanpa satu
berkas pun tertangkap: tambahkan diagnosis sekunder, lalu lampirkan hasil
pemeriksaan penunjang. Naik lewat pintu yang tidak diawasi, turun lewat pintu
yang diawasi.

Tambalan yang masuk akal langsung terlihat. Batasi seberapa jauh lampiran
boleh menurunkan kecurigaan, sebanyak yang biasanya diturunkannya pada berkas
jujur, dan tidak lebih. Batasnya dipelajari dari himpunan latih, jadi tidak
ada angka rupiah yang ditulis tangan.

Dua detektor dilatih pada data yang sama persis, 160.455 episode, satu
bertambal dan satu tidak.

### Sumbangan bukti ternyata berekor sangat panjang

| Kuantil | Sumbangan lampiran pada tebakan tarif |
|---|---:|
| p50 | Rp 0 |
| p80 | Rp 0 |
| p95 | Rp 36.494 |
| p99 | Rp 452.970 |
| maksimum | Rp 24.422.284 |

Pada delapan puluh persen berkas, membuang seluruh lampiran tidak menggeser
tebakan tarif sama sekali. Ekornya yang menggeser, dan di ekor itulah
serangan hidup. Jadi batas pada kuantil 0,8 bukan potongan, itu larangan
penuh.

### Diuji dua kali, dan dua duanya hampir tidak menolong

| Siasat | Polos | Larangan penuh | Potongan ekor p99 |
|---|---:|---:|---:|
| serakah | 195,7 jt | 295,0 jt | 271,6 jt |
| hati hati | 275,3 jt | 380,1 jt | 352,8 jt |
| menyebar | 232,6 jt | 279,6 jt | 268,1 jt |
| upcode berlapis bukti | **384,2 jt** | 381,1 jt | 368,2 jt |
| upcode berlapis bukti, berkas kecil | 367,6 jt | 357,6 jt | 356,9 jt |
| upcode berlapis bukti, menyebar | 312,7 jt | 280,6 jt | 269,9 jt |
| upcode berlapis barang | 280,2 jt | 371,3 jt | 346,3 jt |

Uang yang lolos pelaku terburuk turun 0,8 persen pada larangan penuh dan 4,2
persen pada potongan ekor. Sementara itu siasat yang tidak memakai bukti
justru meloloskan jauh lebih banyak, sampai seratus juta lebih.

Ongkosnya nyata. Presisi pada anggaran seribu berkas turun dari 0,551 ke
0,496 pada larangan penuh, dan ke 0,543 pada potongan ekor. Laju penandaan
berkas bersih tetap aman, 0,0091 menjadi 0,0098 dan 0,0103, jauh di bawah
batas 0,03.

**Tambalannya tidak dipasang.** Mesinnya dibiarkan hidup dan mati secara
bawaan, karena ia yang menghasilkan angka di atas dan yang akan menguji
tambalan berikutnya.

### Kenapa gagal, dan ini yang paling berguna dari percobaan ini

Menutup satu pengungkit tidak menolong karena pelaku tidak bergantung pada
satu pengungkit. Ia punya akses ke skor, jadi ditutup satu ia memakai yang
lain. Dan ambang konformal bergeser mengikuti sebaran skor: menaikkan seluruh
selisih menaikkan pula ambangnya, sehingga ruang di bawah garis kembali
seperti semula.

Dugaan kami waktu itu: yang membuat serangan bekerja bukan bukti penyerta,
melainkan kemampuan menanyai skor sampai tahu apa yang lolos. Dugaan itu
langsung diukur, dan hasilnya ada di bagian berikutnya. Ia benar arahnya dan
terlalu besar kalau ditulis begitu saja: kemampuan bertanya bernilai
sepertiga dari uang yang lolos, bukan sebagian besarnya.

### Papan skor A5

| Target | Hasil |
|---|---|
| A5 T6 naik dari 25,6 persen ke minimal 40 persen | **gagal lewat jalur ini**, turun 0,8 sampai 4,2 persen saja |

Kegagalan keempat proyek ini, dan sebabnya bisa ditunjuk. Rancangan sudah
menuliskan apa yang dilakukan bila A5 gagal, dan ini pelaksanaannya:
ditulis seperti tiga kegagalan sebelumnya, bukan disembunyikan.


---

## Berapa nilai kemampuan bertanya, 7 September 2026

`runs/pengetahuan_pelaku.json`

Percobaan sebelumnya berakhir dengan satu dugaan, dan dugaan itu terdengar
benar. Terdengar benar bukan alasan menuliskannya sebagai temuan, jadi ia
diukur. Yang diubah cuma satu hal, dan bukan detektornya, melainkan apa yang
boleh dilihat pelaku.

Penuh berarti pelaku melihat skor tiap varian sebelum memilih, sebanyak yang
ia mau. Ini asumsi terburuk, dan yang dipakai seluruh pengujian kami sampai
sekarang. Belajar berarti ia melihat skor pada lima puluh berkas pertama,
menyimpulkan satu batas keuntungan yang aman, lalu memakainya pada sisanya
tanpa bertanya lagi. Buta berarti tidak melihat sama sekali.

Yang kedua paling mendekati keadaan sebenarnya. Rumah sakit tidak punya
tombol yang mengembalikan skor sebuah berkas. Yang ia punya hasil berkas yang
sudah dikirim, satu pengamatan per berkas, dan itu datang belakangan.

### Uang yang lolos

| Siasat | Penuh | Belajar | Buta |
|---|---:|---:|---:|
| serakah | 195,7 jt | 177,0 jt | 195,7 jt |
| hati hati | 275,3 jt | 186,0 jt | 195,7 jt |
| menyebar | 232,6 jt | 184,3 jt | 195,7 jt |
| upcode berlapis bukti | **384,2 jt** | 230,7 jt | 263,4 jt |
| upcode berlapis bukti, berkas kecil | 367,6 jt | 258,9 jt | 256,3 jt |
| upcode berlapis bukti, menyebar | 312,7 jt | 226,3 jt | 263,4 jt |
| upcode berlapis barang | 280,2 jt | 184,7 jt | 190,8 jt |
| berteduh di kelompok menahan diri | 5,1 jt | 5,1 jt | 5,1 jt |

Pelaku terburuk turun dari Rp 384,2 juta ke Rp 258,9 juta. Yang tersisa 67,4
persen.

### Dugaannya benar arahnya, dan terlalu besar

Sepertiga jauh lebih banyak daripada yang diberikan tambalan penciri, yang
cuma 0,8 sampai 4,2 persen. Jadi arah dugaannya benar dan pantas dikerjakan.

Tapi dua pertiga uangnya tetap lolos terhadap pelaku yang tidak bisa bertanya
sama sekali. Menambah diagnosis sekunder bekerja tanpa perlu tahu apa pun,
karena diagnosis sekunder memang bukan penciri. Jadi kalimat "pertahanannya
membatasi berapa banyak ia boleh bertanya" terlalu besar, dan sudah diralat
di bagian sebelumnya.

### Kenapa turun, dan ini yang tidak terduga

| Siasat | Tingkat | Diambil | Tertangkap |
|---|---|---:|---:|
| hati hati | penuh | 275,3 jt | 0,0% |
| hati hati | belajar | 310,9 jt | 34,2% |
| upcode berlapis bukti | penuh | 384,2 jt | 0,0% |
| upcode berlapis bukti | belajar | 429,4 jt | 39,6% |
| upcode berlapis barang | penuh | 280,2 jt | 0,0% |
| upcode berlapis barang | belajar | 327,0 jt | 38,5% |

Pelaku yang berhenti bisa bertanya tidak jadi lebih hati hati. Ia mengambil
lebih banyak, lalu kehilangan hampir empat puluh persennya. Uang yang lolos
turun bukan karena ia menahan diri, melainkan karena detektornya benar benar
menangkapnya.

Itu kabar baik yang selama ini tertutup asumsi terburuk. Diukur pada pelaku
yang punya akses penuh ke skor, detektor terlihat tidak menangkap apa apa,
nol persen pada empat siasat sekaligus. Diukur pada pelaku yang cuma bisa
belajar dari hasil, ia menangkap sekitar empat dari sepuluh berkas yang
diserang.

### Satu cacat yang ditemukan sebelum angkanya dipakai

Versi pertama pengukuran ini menyimpulkan batas pelaku di dalam cabang berkas
yang tidak tertangkap, pada pengamatan terakhir. Kalau pengamatan terakhir
kebetulan tertangkap, batasnya tidak pernah tersimpul, dan pelaku diam diam
kembali punya akses penuh ke skor untuk sisa berkasnya.

Ketahuan dari uji yang memberi nol berkas pengamatan lalu memeriksa bahwa
pelakunya tidak mengambil apa apa. Ia mengambil enam belas. Angka yang
terlanjur terhitung meleset sekitar empat persen, dan yang lebih parah, kolom
diambil melaporkan Rp 1,8 miliar padahal seharusnya Rp 430 juta. Diperbaiki,
diukur ulang, dan yang tertulis di atas hasil pengukuran ulang.

### Yang berubah dari daftar pekerjaan

Dua hal, dan keduanya bukan model.

Pertama, portal faskes tidak boleh jadi tempat mencoba coba. Ia sudah
menghitung ulang selisih ketika bukti dicentang, dan itu memang gunanya. Yang
belum ada batas berapa kali sebuah berkas boleh dihitung ulang, dan catatan
siapa yang menghitung ulang berapa kali. Rumah sakit yang mengulang tiga
puluh kali pada satu berkas sedang mencari garis, bukan melengkapi bukti.

Kedua, angka T6 kami selama ini diukur pada pelaku yang paling kuat yang bisa
dibayangkan. Itu tetap yang dilaporkan, karena melaporkan yang lebih lemah
berarti menghibur diri sendiri. Tapi sekarang ada dua angka, dan yang kedua
menunjukkan detektornya bekerja lebih baik daripada yang tertulis.

---

## Harga daftar pengandaian yang kami tampilkan sendiri, 7 September 2026

`runs/harga_pengandaian.json`

Percobaan sebelumnya menyimpulkan bahwa portal faskes tidak boleh jadi tempat
mencoba coba, dan pekerjaannya membatasi berapa kali sebuah berkas boleh
dihitung ulang. Waktu hendak mengerjakannya, ternyata batas itu tidak ada
gunanya, karena tidak ada yang dihitung ulang.

Portal tidak memanggil apa pun ketika bukti dicentang. Ia menghitung dari
daftar yang sudah ada di jawaban: bukti apa saja yang bila dilampirkan
menurunkan selisih, beserta besar penurunan tiap butirnya, seluruhnya
sekaligus, dalam satu jawaban.

Jadi bukan pelaku yang bertanya berkali kali. Kami yang memberikan seluruh
petanya sekali jalan.

### Harganya diukur

Dua siasat kembar diadu, beda pada satu hal saja. Melampirkan pemeriksaan
sembarang, dan melampirkan pemeriksaan teratas menurut daftar itu.

| Siasat | Pengetahuan | Sembarang | Menurut daftar | |
|---|---|---:|---:|---:|
| hati hati | penuh | 384,2 jt | 438,1 jt | +14,0% |
| hati hati | buta | 263,4 jt | 315,3 jt | +19,7% |
| hati hati | belajar | 230,7 jt | **335,0 jt** | **+45,2%** |
| menyebar | penuh | 312,7 jt | 355,6 jt | +13,7% |
| menyebar | buta | 263,4 jt | 315,3 jt | +19,7% |
| menyebar | belajar | 226,3 jt | 327,3 jt | +44,6% |

Yang paling mahal justru baris paling realistis. Pelaku yang tidak bisa
menanyai skor mendapat empat puluh lima persen lebih banyak dari daftar yang
kami tampilkan sendiri.

Itu masuk akal sesudah dilihat: daftarnya menggantikan persis kemampuan yang
tidak ia punya. Mencabut akses skor menurunkan uang yang lolos sepertiga,
lalu daftar pengandaian mengembalikan hampir seluruhnya.

### Menyembunyikan angkanya tidak menolong

Reaksi pertama kami menyembunyikan besar penurunan tiap butir dan menampilkan
urutannya saja. Itu tidak menolong, dan sebabnya ada di gerakan yang dipakai
mengukur: ia cuma memakai urutannya. Tiga butir teratas, tanpa melihat satu
angka pun.

Urutannya sendiri yang bocor, dan urutan itu persis yang dibutuhkan faskes
yang jujur. Tidak ada cara memberi urutan kepada yang berhak tanpa memberi
urutan kepada yang tidak.

### Dan daftarnya tetap ditampilkan

Tanpa daftar itu, penandaan cuma tuduhan yang tidak bisa dibantah. Faskes
yang buktinya sah akan kalah karena tidak tahu bukti mana yang diminta, dan
itu persis keadaan yang kami bilang hendak diperbaiki.

Yang berubah bukan keputusannya, melainkan bahwa harganya sekarang tertulis.
Empat puluh lima persen lebih banyak uang lolos pada pelaku yang paling
mungkin ada di lapangan. Angka itu masuk ke bagian risiko, bukan disimpan.

Yang bisa dikerjakan tanpa mencabut daftarnya ada dua, dan keduanya sudah ada
bentuknya di sistem. Porsi sampel acak pada antrean, yang membuat tidak ada
berkas yang bisa dipastikan aman berapa pun rapinya siasat. Dan profil
faskes, yang menanyakan siapa yang paling sering menagih di dekat garis, bukan
berkas mana yang melewatinya.

### Satu batasan yang berlaku pada seluruh angka lawan di atas

Gelanggangnya cuma memodelkan ambang penandaan dan lantai biaya pemeriksaan.
Ia tidak memodelkan porsi sampel acak pada antrean audit, padahal antrean
yang benar benar dikirim mengisi lima persen tempatnya dengan undian.

Artinya seluruh angka "uang yang lolos" di bagian bagian lawan adalah batas
atas. Berkas yang lolos ambang di gelanggang kami tidak pernah diperiksa,
sedangkan pada sistem yang dikirim ia masih punya peluang kena undian.

Ditulis di sini, bukan di catatan kaki, karena batas atas yang disebut
sebagai hasil adalah cara paling halus melebih lebihkan kegagalan sendiri.
Arah kesimpulannya tidak berubah, besarnya berubah.

---

## Tahap empat, 7 September 2026: dua agen yang menunggu peristiwa

Dua lubang yang disebut survei tujuh dimensi agen kesehatan akhirnya diisi.
Sekitar 92 persen sistem yang ditinjau tidak punya pengaktifan oleh
peristiwa, dan sekitar 98 persen tidak punya mekanisme memperbarui serta
melupakan pengetahuan lama.

### Agen Pola

Titik perubahan pola sudah dihitung sejak lama dan tampil di halaman
analitik. Yang belum ada, sesuatu yang membangunkan orang ketika sebuah
faskes bergeser. Kalau tidak ada yang membuka halaman itu bulan ini,
pergeserannya tidak diketahui bulan ini.

Yang membedakannya dari laporan bukan kecanggihannya. Laporan menyusun daftar
terurut dan menyerahkan pemilihan kepada pembacanya. Agen ini memilih
sendiri, memakai tiga ambang yang ditetapkan sebelum satu perkara pun dibuka:
p paling besar 0,01, sekurangnya enam puluh klaim, dan pergeseran sekurangnya
Rp 500 ribu. Kalau tidak ada yang melewatinya, ia diam.

Diam itu diuji, bukan diharapkan. Dengan ambang yang mustahil, ia
mengembalikan nol perkara dan tetap melaporkan berapa faskes yang diuji.
Agen yang selalu punya sesuatu untuk dilaporkan akan berhenti dibaca dalam
sebulan.

Yang dilaporkan tiga hal yang bisa ditindaklanjuti: tanggal pergeserannya,
besarnya, dan nomor berkas yang menyumbang. Bukan skor, bukan peringkat.
Dan satu hal yang sengaja tidak dilaporkan: sebabnya. Faskes bisa bergeser
karena berganti dokter, membuka layanan baru, atau kedatangan wabah.

### Agen Aturan, dan target A6

Diuji dengan terbitan buatan, seluruh tarif naik sepuluh persen. Ia
melaporkan kode mana yang bergerak, berapa berkas yang berpindah putusan,
dan nomor berkasnya, bukan cuma cacahnya.

**A6 tercapai.** Penilaian ulang selesai dalam 0,24 detik untuk 1.738 berkas,
melawan batas satu hari kerja. Memasang tabel barunya tetap pekerjaan orang
yang berwenang, dan itu memang seharusnya.

Dua hal yang dijaga uji, dan keduanya pernah jadi cara sistem rusak diam
diam. Tabel tarif aslinya dikembalikan apa pun yang terjadi, termasuk ketika
penilaiannya sengaja dibuat gagal di tengah. Dan aturan yang dicabut ditandai
kedaluwarsa, bukan dihapus, karena berkas perkara yang terlanjur dikirim
mengutipnya dan pembacanya setahun lagi berhak tahu.

### Satu cacat yang gagalnya diam

Versi pertama mencocokkan peraturan yang dicabut dengan mencari potongan
teks. Pustaka menulis "Peraturan Menteri Kesehatan Nomor 3 Tahun 2023", yang
mencabut menulis "Permenkes 3 Tahun 2023", dan tidak ada yang tertandai.

Yang paling buruk bukan besarnya kesalahan, melainkan diamnya. Seluruh uji
lain lulus, laporannya terlihat normal, dan pustakanya tetap mengutip
peraturan yang sudah dicabut. Persis bentuk kegagalan yang agen ini dibuat
untuk mencegah.

Sekarang tiap dasar hukum punya pengenal berstruktur, nomor dan tahun, dan
pencocokannya memakai itu. Tiga ejaan berbeda dari peraturan yang sama diuji
mengenai entri yang sama.

### Target A2

Lapisan agen tidak menggeser satu pun penandaan. Diperiksa dengan menandai
seluruh berkas, menjalankan dua puluh lima berkas lewat penyusun perkara dan
Agen Berkas, lalu menandai ulang dan membandingkan. Nol bergeser.

Laju penandaan berkas bersih 0,0137, di bawah alpha 0,02 dan jauh di bawah
batas lulus 0,03. **A2 tercapai.**

### Papan skor lapisan agen, lengkap

| Kode | Target | Hasil |
|---|---|---|
| A1 | Nol angka tak bersumber dari 500 berkas | **tercapai**, nol dari 500 berkas, seluruhnya disusun agen |
| A2 | Laju salah tuduh tidak naik | **tercapai**, 0,0137 |
| A3 | Berkas perkara diterima verifikator tanpa koreksi | **tidak terukur**, butuh pembaca manusia |
| A4 | Tiga siasat penghindaran baru yang bisa diulang | **tercapai**, lima |
| A5 | T6 naik dari 25,6 ke 40 persen | **gagal**, tengahnya 0,208 pada enam benih di luar sampel |
| A5b | penyusutan uang, ambang didaftarkan lebih dulu | **terlampaui**, tengah 0,745 dan terkecil 0,571 |
| A6 | Berkas yang berubah putusan dilaporkan dalam satu hari kerja | **tercapai**, 0,24 detik |
| A7 | Biaya token di bawah Rp 500 per berkas | **tercapai**, Rp 49,77 pada 500 berkas |

Lima tercapai, satu gagal, satu tidak terukur. Papan skor ini pernah
berbunyi begitu dengan A1 di kolom tercapai atas empat puluh berkas, dan
sekarang A1 berdiri atas lima ratus seperti yang targetnya minta, jadi
angkanya tetap lima tapi pijakannya berbeda.

A3 menuntut verifikator sungguhan membaca berkas perkara sungguhan, dan itu
tidak ada di lomba ini.
Menggantinya dengan ukuran buatan lalu menyebutnya tercapai akan jadi
kebohongan yang paling mudah tidak ketahuan, jadi ia ditulis tidak terukur.

### Angka aslinya mengubah ambang Agen Pola, dan menemukan cacat di halaman sendiri

Ambang Agen Pola mula mula ditulis tanpa melihat data: nilai p paling besar
0,01 dan pergeseran sekurangnya Rp 500 ribu. Diukur pada data peragaan,
keduanya mustahil. Nilai p terkecil yang bisa dicapai uji permutasi dua ratus
kali adalah 0,0149, dan pergeseran terbesar di seluruh seratus empat faskes
Rp 517 ribu.

Yang lebih penting muncul dari mengukurnya. Uji titik perubahan dijalankan
pada tiap faskes yang klaimnya cukup banyak, jadi seratus empat faskes
berarti seratus empat uji. Pada ambang lima persen tanpa koreksi, sekitar
lima akan lolos karena undian. Yang benar benar lolos tujuh.

Halaman analitik kami sendiri menampilkan ketujuhnya, di bawah judul "Faskes
yang perlu ditanya", tanpa satu kalimat pun yang menyebut bahwa lima di
antaranya diperkirakan undian.

Jadi ambang Agen Pola sekarang dikendalikan Benjamini-Hochberg pada laju
penemuan palsu sepuluh persen, bukan angka tetap. Hasilnya nol perkara, dan
nol itu jawaban yang benar.

Panelnya tetap tampil ketika nol, dan justru itu isinya yang paling berguna:
seratus empat faskes diuji, tujuh lolos tanpa koreksi, nol tersisa sesudahnya.
Tanpa kalimat itu, tabel di bawahnya terbaca seperti tujuh temuan.

## Lapisan agen yang berkasnya benar benar disusun model, 7 September 2026

Tahap satu sampai empat memasang lima agen. Satu pertanyaan tidak pernah
dijawabnya: apakah model berbobot terbuka yang muat di dalam pusat data
sanggup menyusun berkas perkaranya sendiri, atau ia cuma terlihat berhasil
karena versi aturannya selalu siap menggantikan.

Jawaban pertamanya tidak enak dibaca. Dari empat puluh berkas, model
menyusun empat belas, dan sebelas di antaranya melekatkan angka yang sah
pada nama yang salah. Sisanya mundur tanpa ada yang tahu kenapa.

Sekarang seratus dua puluh berkas disusun agen seluruhnya, dan tidak satu
pun membawa cacat. Yang berubah bukan modelnya. Yang berubah empat cacat
kami sendiri, dan tiga di antaranya ada pada pemeriksanya.

### Menyebut sesuatu mahal tanpa pernah menimbangnya

Pemeriksaan berkas dibagi dua sejak awal. Yang cepat jalan tiap berkas. Yang
teliti disebut terlalu mahal untuk itu, jadi ia disimpan untuk himpunan
kalibrasi saja, dan seluruh gerbang layak kirim dibangun di atas kalimat
itu.

Kalimat itu tidak pernah ditimbang. Sesudah ditimbang, yang teliti berharga
satu milidetik per berkas, sedangkan menyusun berkasnya sendiri memakan dua
ratus enam puluh empat milidetik dan satu giliran model bahasa sekitar
delapan ribu.

Empat persepuluh persen. Itu harga pemeriksaan yang selama ini kami sebut
mahal. Sekarang keduanya jalan pada tiap berkas, dan kelas cacat yang dulu
lolos ke keluaran disaring sebelum keluar.

Gerbangnya tetap ada dengan alasan yang sudah diganti. Ada cacat yang tidak
bisa diperiksa mesin berapa pun murahnya, dan gerbang itu yang menjaganya.
Apakah modus yang dipilih masuk akal bagi berkas ini. Apakah kalimatnya
terbaca oleh orang klaim. Tidak ada pola pencarian untuk keduanya.

### Model menyalin apa yang dilihatnya

Dua belas berkas memakai nama isian yang tidak ada. Nama yang dipakainya
selalu nama medan pada balasan alat, seperti total_diajukan_rp, padahal
arahan menuliskan nama pendek seperti diajukan.

Dilihat dari sisi model, itu masuk akal. Nama pendek cuma ada di arahan,
jauh di awal percakapan, sedangkan nama medan berdiri di dalam balasan alat
beberapa baris sebelum ia menulis, dengan angkanya menempel di sebelahnya.

Melarangnya tidak akan menolong. Yang menolong membuat yang disalinnya
benar. Tiap medan tunggal yang dikembalikan alat sekarang jadi nama isian
juga, jadi menyalin yang terlihat menghasilkan kalimat yang sah.

### Angka yang tidak ada di depan mata tidak bisa disalahtempatkan

Penjaga A1 mengizinkan angka yang berasal dari alat, dan izin itu benar.
Yang tidak diizinkan siapa pun terjadi sesudahnya. Angka sah itu dilekatkan
pada nama yang salah, dan di situlah sebelas berkas tadi jatuh.

Maka rupiah dihapus dari balasan alat sebelum model melihatnya, dan di
tempat angkanya sekarang berdiri nama isiannya. Menyalin yang terlihat
justru menghasilkan kalimat yang benar. Mengarang angka sekarang menuntut
mengarang sesuatu yang tidak ada satu pun contohnya di layar.

Besaran per butir bukti diganti arahnya saja, naik atau turun. Model tetap
bisa memilih butir mana yang pantas disebut, tanpa satu digit pun yang bisa
disalahtempatkan.

### Pemeriksa yang menuduh berkas yang benar

Dua tuduhan palsu ditemukan pada berkas susunan model, bukan pada uji.

Yang pertama titik dua. Pencarian besaran menyeberanginya, jadi kalimat
"bukti yang menurunkan selisih: HB Rp 489.690" dibaca seolah selisihnya Rp
489.690. Yang kedua kode. Angka di dalam M02 terbaca sebagai besaran
bernilai dua.

Membuang seluruh titik dua sempat jadi perbaikannya, dan itu salah juga,
karena "Diajukan: Rp 20.107.500" memakai titik dua dan bentuk itu justru
yang paling lazim di berkas klaim. Yang membedakan keduanya bukan tanda
bacanya. Yang membedakan apa yang berdiri sesudahnya.

Sekarang yang boleh berdiri di antara sebutan dan angkanya didaftar satu
satu. Kata sambung dan satuan boleh, dan apa pun yang lain menghentikan
pembacaan, sehingga sebuah kode atau kata benda baru memutus ikatannya.

Empat berkas yang dituduh cacat ternyata benar seluruhnya.

### Angka yang keluar sesudah keempatnya diperbaiki

Model nalar-qwen3-4b, jendela dua belas ribu token, suhu nol, jalan di satu
mesin biasa tanpa kartu grafis pusat data.

Seluruh berkas disusun agen. Nol angka tak bersumber, nol cacat pemeriksaan
dalam, Rp 49,77 per berkas. Ongkos periksa manual satu berkas Rp 750 ribu.

Lingkaran perbaikan yang dipasang di tengah jalan tidak pernah terpakai, dan
itu hasil yang benar. Ia cuma menyala ketika naskah pertama jatuh, dan
naskah pertama tidak jatuh lagi.

### Gerbang yang menolak menjanjikan apa pun

Pada empat puluh berkas, gerbang layak kirim menahan seluruhnya. Tidak satu
pun boleh dikirim, padahal tidak satu pun bercacat.

Itu jawaban yang benar atas pertanyaan yang salah. Separuh berkas dipakai
menera, dan dua puluh berkas bersih tidak cukup untuk menjanjikan laju cacat
lima persen dengan keyakinan sembilan puluh lima persen. Seandainya laju
sebenarnya memang lima persen, peluang melihat nol cacat dari dua puluh
berkas masih tiga puluh enam persen. Terlalu besar untuk disebut bukti.

Batas bawahnya bisa dihitung, dan hasilnya lima puluh sembilan berkas bersih
berturut turut. Enam puluh masuk kalibrasi sekarang, jadi janjinya berdiri.
Ambangnya turun ke nol, dan seluruh berkas penilaian layak kirim tanpa satu
cacat pun di antaranya.

Yang perlu diingat dari sini bukan angkanya. Gerbang ini menolak berjanji
ketika buktinya kurang, dan penolakan itu terlihat persis seperti sistem
yang macet.

### Agen Sanggah, dan janji yang ditagih

Berkas sanggah.py sejak tahap dua menuliskan satu janji. Pencocokan kata
jadi garis dasarnya, model bahasa dipasang di atasnya, dan kalau model tidak
menang ia dicabut. Janji itu tidak pernah ditagih sampai sekarang.

Dua puluh empat surat ditulis lebih dulu, sebelum kedua cara dijalankan.
Bentuknya meniru surat balasan rumah sakit. Ada yang menyebut nama katalog
persis, ada yang memakai sebutan sehari hari, dan ada yang menyebut sebuah
pemeriksaan justru untuk bilang ia tidak dikerjakan.

Pencocokan kata benar pada dua puluh surat.

Empat yang salah punya dua sebab. Nama katalog yang berekor, seperti
urinalisis leukosit esterase, menuntut seluruh ekornya ada di surat, jadi
surat yang menulis urinalisis saja terlewat. Dan surat yang bilang
pemeriksaan trombosit tidak dilakukan tetap dipetakan jadi trombosit.

Model bahasa benar pada seluruhnya. Ingatan dan ketepatannya penuh, melawan
0,946 pada keduanya di pencocokan kata. Harganya kurang dari dua detik per
surat.

### Penjaga yang membuang jawaban yang benar

Angka di atas bukan angka percobaan pertama, dan bedanya perlu ditulis.

Percobaan pertama memberi model ketepatan penuh tapi ingatan 0,865, lebih
rendah daripada pencocokan kata. Lima pemetaan dibuang penjaga kutipan.
Sesudah dilihat satu satu, kelimanya benar.

Sebabnya selalu sama. Surat menulis "kami lampirkan hasil prokalsitonin dan
laktat", model mengutip "kami lampirkan hasil laktat", dan penjaga menuntut
kutipan yang utuh huruf demi huruf. Penyingkatan yang wajar dihukum sebagai
karangan.

Penjaganya sekarang menuntut tiap kata pada kutipan ada di surat, bukan
kutipannya utuh. Model yang memetakan kreatinin pada surat yang tidak pernah
menyebutnya tetap harus mengarang kata itu, dan kata karangan tetap tidak
akan ketemu.

Ada yang tidak dibuktikan penjaga ini, dan batasnya perlu ditulis terang
terangan. Ikatan antara kodenya dan suratnya tidak diperiksa, sehingga
kutipan yang seluruhnya kata umum bisa menemani kode apa pun. Yang
menahannya dua hal lain. Alasannya ikut tercetak supaya bisa dibantah, dan
yang menghitung ulang selisihnya penebak tarif, bukan agen.

Penjaganya diperbaiki sesudah hasil pertama terlihat. Suratnya tidak.
Seluruhnya ditulis sekali dan tidak disunting sesudahnya, dan melonggarkan
penjaga tidak bisa menolong model menemukan kode yang tidak disebutnya
sendiri.

Dua puluh empat surat tulisan tangan bukan bukti yang besar. Yang bisa
dikatakan dari situ satu kalimat saja. Pada bentuk surat yang kami tulis,
model membaca lebih baik daripada pencocokan kata, dan bedanya ada pada
penyangkalan dan nama berekor.

### Sanggahan sampai ke portal

Agen Sanggah sebelumnya hidup di dalam kode dan uji saja. Tidak ada satu
layar pun yang memanggilnya, jadi rumah sakit yang mengirim salinan hasil
laboratorium tetap kalah karena bentuk kirimannya salah, persis keadaan yang
agen ini dibuat untuk mengakhirinya.

Sekarang portal faskes punya tombol di bawah kotak keterangan. Kalimat biasa
yang ditulis rumah sakit dibaca, pemeriksaan yang disebutnya dicentang
sendiri, dan alasan tiap pemetaan ikut tampil supaya bisa dibantah.

Tanpa peladen menyala, pembacaannya jatuh ke pencocokan nama di peramban.
Nama yang dicocokkan cuma yang memang sudah dikirim peladen untuk berkas
itu, jadi katalognya tidak disalin ke peramban dan tidak bisa menyimpang
darinya.

Yang dilihat faskes tetap dijaga sempit: pemeriksaan yang terbaca beserta
alasannya, lalu selisih barunya. Berkas perkara dan daftar modus tidak ikut,
dan ada uji yang menjatuhkan peladen kalau salah satunya bocor ke sana.

### Uji yang hijau seluruhnya, dan tombol yang mati

Jalur sanggahan diuji sembilan kali lewat peladen dan lulus sembilan kali.
Di portal, tombolnya tetap mati.

Sebabnya izin lintas asal. Peramban menanyakan izin lebih dulu sebelum
mengirim kiriman ke asal yang berbeda, dan peladen menolaknya karena yang
diizinkan cuma pengambilan. Uji memanggil peladen dari dalam, jadi ia tidak
pernah menanyakan izin, jadi ia tidak pernah melihat penolakannya.

Yang menemukannya bukan uji. Yang menemukannya membuka halaman itu sebagai
penggunanya. Sekarang ada uji yang menanyakan izin persis seperti peramban,
dan uji itu yang akan menjatuhkan peladen kalau izinnya dicabut lagi.

### Kalimat yang berbohong tentang apa yang terjadi

Surat percobaannya menyebut tiga pemeriksaan. Hemoglobin dan trombosit
dilampirkan, kreatinin disebut justru untuk bilang ia tidak dikerjakan.

Tiap lapisan memperlakukannya dengan benar. Model menolak kreatinin.
Hemoglobin memang sudah tercatat pada berkas itu, jadi peladen
mengeluarkannya dari daftar yang perlu dicentang. Trombosit terbaca, tapi
melampirkannya justru menaikkan selisih berkas itu, jadi portal memang tidak
punya kotak centang untuknya.

Layarnya merangkum ketiganya jadi satu kalimat. Tidak ada pemeriksaan yang
dikenali dari keterangan ini. Itu bukan ringkasan, itu kebalikan dari yang
terjadi, dan rumah sakit yang membacanya akan menulis suratnya lagi.

Sekarang ketiganya disebut terpisah. Yang dicentang, yang memang sudah
tercatat, dan yang terbaca tapi tidak menurunkan selisih berkas ini. Peladen
juga berhenti membuang pemeriksaan yang sudah ada di berkas, dan mulai
menyebutnya.

## A5 dikejar sekali lagi, dan yang ketemu bukan yang dicari, 7 September 2026

A5 sudah gagal dua kali lewat jalur model. Membatasi sumbangan bukti
menurunkan uang yang lolos kurang dari lima persen. Mencabut kemampuan
pelaku menanyai skor bernilai sepertiga, tapi ia bukan tombol yang ada di
dunia nyata.

Dua dugaan baru diuji hari ini. Keduanya salah, dan yang ketiga muncul dari
mencoba memahami kenapa.

### Anggaran penandaan bukan pengikatnya

Dugaannya begini. Penebak tarif sudah tidak melihat diagnosis sekunder sama
sekali, jadi upcoding menaikkan tagihan tanpa menaikkan tebakan. Yang membuat
pelaku tetap lolos bukan tebakan yang tertipu melainkan jarak antara selisih
berkasnya dan ambang penandaan. Kalau benar, T6 ditentukan alpha, dan alpha
ditentukan berapa banyak berkas yang sanggup dibaca manusia.

Diukur, dan tidak. Menaikkan alpha lima kali menaikkan laju penandaan dari
satu persen ke sembilan persen, dan dari tujuh puluh empat serangan yang
mungkin ia cuma memindahkan dua ke kolom tertangkap. Uang yang lolos hampir
tidak bergerak.

### Menahan diri terlihat seperti lubang, dan itu tipuan ukuran data

Pembongkaran per berkas memberi angka yang menggoda. Dari tujuh puluh empat
serangan, lima puluh satu lolos bukan karena skornya rendah melainkan karena
kelompok sebayanya kurang dari tiga faskes sehingga tidak ada ambang yang
bisa dilewati.

Jaring pengaman dipasang. Berkas semacam itu tunduk pada satu ambang tunggal
yang jauh lebih ketat, sementara perbandingan dengan sebayanya tetap
ditiadakan. T6 naik dari nol ke delapan puluh tujuh persen. Uang yang lolos
turun tiga perempat.

Pada data penuh seluruhnya menguap. Dengan seratus enam puluh ribu episode,
kelompok sebaya jadi cukup besar, sehingga satu satunya yang masih menahan
diri justru yang memang sengaja dikecualikan, yaitu daerah tertinggal.
Jaringnya menggeser uang yang lolos kurang dari dua persen, dan satu satunya
yang ikut tertandai berkas daerah tertinggal.

Itu persis pertukaran yang skrip pengukurnya sendiri melarang. Jaringnya
tetap ada di kode, mati, supaya kesimpulan ini bisa dibantah dengan data
yang lebih besar dan bukan dengan pendapat.

### Angka yang naik dua kali lipat tanpa satu baris pun menyentuh detektor

Di tengah pengukuran itu T6 terbaca 0,55, sedangkan yang tercatat di
repositori 0,256. Skripnya sama, benihnya sama, ukuran datanya sama.

Pertama yang dicurigai versi pustaka. Sumber lama dijalankan dengan
lingkungan hari ini dan memberi 0,256 persis, jadi bukan itu.

Pembagian dua atas dua puluh satu commit menunjuk satu commit penataan gaya.
Di dalamnya, satu berkas: pembangkit kecurangan. Ditukar berkas itu saja ke
pohon lama, sidik dunianya langsung sama persis dengan yang baru.

Barisnya satu:

    if rec["rawat_inap"] and rng.random() < _peluang(kode, "M12"):
        if los < 10:

    if rec["rawat_inap"] and los < 10 and rng.random() < _peluang(kode, "M12"):

Keputusan untuk berkas itu tidak berubah. Yang berubah berapa kali pengacak
dipanggil, dan itu menggeser seluruh undian sesudahnya. Delapan ribu tujuh
ratus lima puluh delapan episode jadi delapan ribu lima ratus delapan puluh
dua, dan tarif totalnya bergeser tujuh persen.

Jadi 0,256 dan 0,55 bukan dua keadaan detektor. Keduanya dua dunia.

### Berapa lebar T6 kalau dunianya diganti

Pertanyaan itu tidak pernah ditanyakan di proyek ini, dan seharusnya
ditanyakan sejak percobaan pertama.

Enam benih, ukuran data penuh, detektor yang sama:

| benih | T6 |
|---|---|
| 7 | 0,550 |
| 8 | 0,324 |
| 9 | 0,330 |
| 10 | 0,180 |
| 11 | 0,399 |
| 12 | 0,305 |

Terkecil 0,180, tengah 0,327, terbesar 0,550, simpangan baku 0,122. Satu
dari enam melewati batas 0,40.

Angka 0,256 yang kami laporkan empat percobaan berturut turut ada di dalam
sebaran itu. Begitu juga 0,55 yang sempat terbaca sebagai keberhasilan hari
ini. Keduanya satu undian.

**A5 tetap gagal.** Yang berubah bukan status targetnya melainkan kepercayaan
kami pada cara menilainya. Target yang dinilai dari satu undian statistik
yang simpangannya 0,12 tidak bisa dinyatakan tercapai atau gagal dengan satu
angka, dan selama ini kami melakukan persis itu.

### Ukuran yang goyah dan ukuran yang tenang

Pada enam benih yang sama, uang yang diambil pelaku hati hati bergerak dari
Rp 275 juta sampai Rp 475 juta, dengan ragam relatif 0,175. T6 ragamnya
0,350, dua kali lipatnya.

Sebabnya ada pada rumusnya. T6 dihitung dari keuntungan maksimum satu berkas,
jadi ia bergantung pada satu klaim di seluruh himpunan uji. Uang yang diambil
menjumlahkan ratusan berkas.

Kalau target ketahanan ditulis ulang suatu hari, ia harus memakai ukuran yang
menjumlahkan, bukan yang mengambil maksimum, dan harus dilaporkan sebagai
sebaran atas beberapa dunia, bukan satu angka.

### Penjaganya dipasang

Sebuah penataan gaya menggeser angka ketahanan yang kami laporkan sampai dua
kali lipat, dan tidak ada satu pun uji yang berbunyi. Itu lubang yang lebih
besar daripada A5 sendiri.

Sekarang ada uji yang memakukan sidik dunia pembangkit pada benih tetap:
cacah episode, tarif total, cacah berkas curang, jumlah lama rawat, dan
jumlah diagnosis sekunder. Ia tidak menilai apakah dunianya bagus. Ia
memastikan tidak ada yang menggesernya tanpa sadar, dan kalau memang sengaja
digeser, angkanya harus ikut diperbarui dalam commit yang sama sehingga
terlihat di riwayat. Integrasi berkelanjutan menjalankannya sebelum uji lain.

### A1 dan langit langit mesin pengembangan

Target A1 menyebut lima ratus berkas. Yang pernah selesai dalam satu jalan
seratus dua puluh, dan seluruhnya bersih.

Jalan lima ratus dicoba tiga kali dan dihentikan penjaga memori tiga kali.
Sebabnya bukan pengukurannya melainkan mesin ini: model bahasanya menuntut
dua setengah gigabita dan keadaan datanya harus hidup bersamaan, sedangkan
yang bebas tinggal dua gigabita.

Pengukurannya lalu dibuat menyambung. Hasil tiap berkas ditulis begitu
selesai, dan jalan berikutnya melewati yang sudah ada. Hasilnya sama dengan
sekali jalan, karena tiap berkas berdiri sendiri dan modelnya bersuhu nol.

Sesudah beberapa jendela ditutup, lima ratusnya selesai. Empat jalan
bersambung, satu jalan terakhir menyelesaikan tiga ratus dua sisanya.

Lima ratus dari lima ratus berkas disusun agen. Nol yang mundur ke versi
aturan, nol angka tak bersumber, nol cacat pemeriksaan dalam. Rp 49,77 per
berkas, 317 token keluaran, 13,1 detik per berkas.

Gerbang layak kirim ditera pada dua ratus lima puluh berkas dan meloloskan
seluruh dua ratus lima puluh berkas penilaian, tidak satu pun bercacat.
Dengan cacah kalibrasi sebesar itu janjinya berdiri jauh di atas batas
lima puluh sembilan yang dituntut Clopper-Pearson.

**A1 tercapai pada ukurannya sendiri.** Yang menahannya selama beberapa jam
memori mesin, bukan kode, dan itu tercatat di sini supaya jelas bahwa yang
diperbaiki cara menjalankannya, bukan cara mengukurnya.

### Alasannya benar, penaksirnya yang tidak

Memilih keuntungan maksimum sebagai ukuran bukan kelalaian. Alasannya
ditulis sejak awal di adversarial.py, dan alasannya masih berdiri: yang
menentukan bukan berapa persen pelaku tertangkap melainkan berapa besar
yang masih bisa diambil pelaku terbaik. Sistem pengawasan yang baik tidak
menangkap semua orang, ia membuat kecurangan tidak sepadan.

Yang tidak pernah ditanyakan: seberapa teliti maksimum itu bisa ditaksir
dari satu dunia. Jawabannya tidak teliti sama sekali. Maksimum atas beberapa
ratus klaim bergantung pada satu klaim, dan satu klaim berpindah setiap kali
dunianya berganti.

Gagasan yang sama bisa ditulis dengan penaksir yang menjumlahkan. Ukurlah
seluruh uang yang masih bisa diambil pelaku yang memeriksa sebelum
bertindak, lalu bandingkan dengan yang diambil pelaku yang tidak peduli
tertangkap. Satu berkas terbaik tidak lagi menentukan angkanya.

Pada enam dunia yang sama:

| | tengah | rentang | ragam relatif |
|---|---|---|---|
| keuntungan maksimum satu berkas | 0,327 | 0,180 sampai 0,550 | 0,350 |
| penyusutan seluruh uang | 0,752 | 0,721 sampai 0,858 | 0,063 |

Lima setengah kali lebih tenang, dan artinya bisa dibaca satu kalimat.
Pelaku yang sabar mengambil sekitar seperempat dari yang diambil pelaku
yang nekat.

**A5 tetap gagal, dan angka 0,75 di atas bukan penggantinya.** Mengganti
target yang gagal dengan ukuran baru yang kebetulan lulus adalah memeriksa
pekerjaan sendiri. Yang boleh dilakukan cuma mencatatnya sebagai garis dasar
hari ini, supaya target ketahanan berikutnya ditulis di atas penaksir yang
bisa dipercaya, dengan ambang yang ditetapkan sebelum diukur.

### Keenam agen dijalankan sekali jalan, dan yang ketiga jatuh

Tiap agen punya ujinya sendiri dan tiap uji lulus. Yang tidak pernah ada
satu jalan yang menjalankan keenamnya pada keadaan yang sama dengan model
bahasa yang benar benar menyala. Uji memakai penutur bernaskah, dan penutur
bernaskah membuktikan penjaganya benar tanpa membuktikan modelnya patuh.

Jalan pertama meloloskan keenamnya, dan itu justru tandanya pemeriksaannya
terlalu longgar. Agen Sanggah dinyatakan lulus karena ada kode yang terbaca,
padahal suratnya menyebut dua pemeriksaan yang dilampirkan dan agennya cuma
menemukan satu.

Diperketat jadi menuntut keduanya, agennya gagal. Sebabnya ketemu di
keluaran mentah model. Ia memilih trombosit dengan benar, lalu mengutip
suratnya sebagai "hemoglobin dan tromb-than". Kata karangan itu tidak ada di
surat, jadi penjaga kutipan membuang kodenya.

Penjaganya benar. Yang hilang bacaan yang benar, bukan karangan.

### Model memilih, katalog membuktikan

Perbaikannya menambah jalan kedua yang tidak lebih longgar. Kalau kutipan
model tidak berakar di surat, kodenya masih bisa masuk asalkan nama katalog
pemeriksaan itu memang ada di surat. Yang berganti pembuktinya, dari kutipan
model ke nama katalog. Yang memilih kodenya tetap model.

Pembagian itu yang membuatnya tetap aman. Surat percobaannya menyebut
kreatinin justru untuk bilang pemeriksaan itu tidak dikerjakan. Pencocokan
kata sendirian memetakannya, model menolaknya, dan karena yang memilih tetap
model, kreatinin tetap tidak masuk meski namanya ada di surat.

Sesudah perbaikan, tolok ukur dua puluh empat surat tetap sempurna pada
ingatan dan ketepatan, dan kode yang dibuang penjaga kutipan turun jadi nol.
Alasan yang tercetak menyebut kutipan model tidak terbaca, supaya
verifikator tahu mana yang dibuktikan kutipan dan mana yang dibuktikan nama.

### Agennya sampai ke tangan pengunjung

Peragaan membaca Supabase, bukan peladen Python, karena tidak ada mesin yang
menyalakan model bahasa dua puluh empat jam. Akibatnya selama ini seluruh
berkas perkara di sana versi aturan, dan pengunjung tidak pernah melihat satu
pun keluaran agen.

Enam puluh berkas dengan selisih terbesar sekarang disusun Agen Berkas di
mesin ini, lengkap dengan jejak alat dan sidik rantainya, lalu disimpan apa
adanya. Layar klaim menyebut siapa yang menyusunnya, dan sidik rantainya
tercetak di bawah naskah supaya bisa dicocokkan.

Jalan pertamanya salah dunia. Pemuatnya memakai 1500 peserta 2 tahun,
sedangkan peragaannya dibangun dari 8000 peserta 3 tahun, jadi berkasnya
tersimpan untuk nomor klaim yang tidak ada di sana. Layar klaimnya menjawab
"K00000401 tidak ada" ketika dibuka sebagai pengunjung, dan itu yang
menemukannya. Bukan uji, lagi lagi.

Barisnya dihapus, parameternya disamakan, dan penjaganya sekarang menanyakan
lebih dulu apakah nomor yang disusun ada di tabel peragaan. Kalau tidak,
skripnya berhenti tanpa menulis apa pun.

### A5 versi baru, ambang didaftarkan lebih dulu lalu diuji di luar sampel

Ambangnya ditulis ke rencana dan disimpan ke riwayat pukul 17.54, dan angka
pertamanya baru muncul sesudah itu. Urutan itu yang membuat hasilnya berarti,
dan commit-nya bisa diperiksa siapa pun.

Yang didaftarkan: nilai tengah penyusutan uang sekurangnya 0,50 pada enam
benih, dengan yang terkecil sekurangnya 0,40. Angka 0,50 bukan angka baru,
ia batas "turun setengah" yang sudah ditulis rencana ini sejak awal untuk
A5. Yang berganti penaksirnya.

Benihnya tiga belas sampai delapan belas, dan keenamnya belum pernah dipakai
di proyek ini. Garis dasar yang sudah ada diukur pada tujuh sampai dua belas.

Hasilnya: terkecil 0,571, tengah 0,745, terbesar 0,830, simpangan baku
0,088. Kedua ambangnya terlampaui.

Pada enam dunia yang sama, T6 lama memberi tengah 0,208 dan terkecil nol,
dengan dua dari enam melewati 0,40. Ragam relatifnya 0,799 melawan 0,121
pada penaksir baru. Itu memperkuat temuan sebelumnya, bukan membantahnya.

### Apa yang boleh dan tidak boleh disimpulkan dari situ

Boleh: pengawasan ini menyusutkan uang yang bisa diambil pelaku yang sabar
sampai sekitar tiga perempat dari yang diambil pelaku yang nekat, dan
angkanya bertahan pada enam dunia yang tidak dipakai memilih ambangnya.

Tidak boleh: menyebut A5 tercapai. Target itu berbunyi T6 naik ke empat
puluh persen, dan T6 pada enam dunia ini tengahnya dua puluh persen. Ia
tetap gagal, dan barisnya di papan skor tetap gagal.

Yang perlu ditulis terang terangan tentang batas pendaftaran ini. Ia
menutup satu celah, yaitu menggeser ambang sesudah melihat hasil. Ia tidak
menutup celah yang lain, yaitu memilih ukuran sesudah tahu ukuran lama tidak
menolong. Ukurannya kami pilih sendiri, sesudah tahu T6 goyah, dan garis
dasarnya sudah kami lihat sebelum ambangnya ditetapkan.

Jadi yang berdiri di sini satu ukuran yang lebih layak dipercaya, beserta
angkanya di luar sampel. Sebutan target baru saya tahan sampai ada pihak
yang tidak ikut mengukur yang menuliskannya.

### Agen yang benar benar dipakai pengunjung, dan dua cacat yang cuma model lain bisa temukan

Sampai hari ini yang dilihat pengunjung keluaran agen yang disimpan lebih
dulu. Sekarang satu agen benar benar bekerja saat itu juga, di situs publik,
tanpa mesin yang menyala dua puluh empat jam.

Agen Sanggah yang bisa begitu, dan alasannya struktural. Ia satu satunya
agen yang tidak butuh keadaan data maupun penebak terlatih. Yang
diperlukannya surat dari pengunjung, katalog pemeriksaan, dan satu model.
Ketiganya muat di fungsi tanpa peladen.

Penyedianya Groq, gratis tanpa kartu, dan modelnya gpt-oss-120b. Pilihan itu
diukur bukan ditebak. Qwen di sana berpikir dulu sebelum menjawab, tiga kali
lebih lambat dan lebih sering kehilangan pemeriksaan kedua pada satu surat.

Cerebras dicoba lebih dulu dan menolak dengan kuota habis. Halaman harganya
menyebut lima dolar kredit percobaan, sedangkan blog yang saya pakai riset
menyebut sejuta token per hari. Blognya salah, dan saya sempat meneruskan
angka itu sebelum memeriksanya ke sumber resmi.

### Model yang berbeda memunculkan cacat yang model lama sembunyikan

Angka pertama lewat Groq 21 dari 24 surat, di bawah model setempat yang 24
dari 24. Sebabnya bukan modelnya.

Yang pertama batas laju. Dua puluh empat surat terkirim dalam sebelas detik,
jauh di atas jatah per menit, dan yang tertolak dihitung sebagai gagal
membaca. Sekarang penutur mengulang dengan jeda bertahap, dan jedanya
diambil dari kepala Retry-After kalau penyedianya mengirimkannya. Tanpa itu,
pengunjung kedua yang menekan tombol pada menit yang sama akan mendapat
kegagalan diam diam.

Yang kedua penjaga kutipan kami sendiri. Ia menuntut kutipan sekurangnya dua
kata, dan model awan mengutip "HbA1c" sebagai satu kata. Kutipan itu bukti
terkuat yang bisa ada, dan penjaganya membuangnya.

Syarat dua kata itu memang sewenang wenang sejak awal. Yang menjaganya
syarat berikutnya, bahwa sekurangnya satu kata harus di luar daftar kata
umum, dan syarat itu sudah cukup sendiri. Model setempat tidak pernah
mengutip satu kata, jadi cacat itu tidur selama dua puluh empat surat, dua
puluh sembilan uji, dan satu pemeriksaan enam agen.

Sesudah keduanya diperbaiki, model awan dan model setempat sama sama 24 dari
24 dengan ingatan dan ketepatan penuh.

### Agen kedua hidup di situs, dan tiga hal yang cuma kelihatan sesudah dipasang

Agen Berkas sekarang ikut bekerja saat itu juga di situs publik. Yang
menghalanginya selama ini bukan modelnya melainkan alatnya. Alat agen
membaca seluruh episode di dalam memori, dan proses sebesar itu tidak muat
di fungsi tanpa peladen.

Yang dikerjakan memindahkan sumber angkanya, bukan menulis ulang alatnya.
Empat dari lima alat sekarang membaca tabel. Yang kelima menuntut penebak
tarif terlatih, dan ia menolak dengan keterangan. Jawaban keempatnya sudah
diadu medan demi medan dengan jawaban versi memori, karena satu medan yang
berbeda mengubah apa yang dilihat model dan membuat angka yang sudah diukur
pada lima ratus berkas tidak berlaku lagi.

Lapisan agennya disalin apa adanya ke sebelah fungsinya, dan yang diubah
cuma bentuk impornya. Ujinya menghasilkan ulang lalu membandingkan bita demi
bita, memeriksa rantai impornya tertutup, dan memastikan tidak ada pustaka
berat yang menyelinap ikut. Ketiganya gagal dengan cara yang berbeda, dan
tidak ada satu pun yang bisa menangkap ketiganya.

**Jatah gratisnya diukur, dan ia mengikat.** Groq memberi seribu permintaan
per hari. Yang lebih mengikat delapan ribu token per menit, sedangkan satu
berkas perkara memakai sekitar tujuh ribu.

Artinya kira kira satu berkas per menit. Pengunjung kedua pada menit yang
sama mendapat berkas versi aturan, dan halamannya menyebut sebabnya. Itu
bukan kegagalan yang disembunyikan, melainkan batas yang ditulis apa adanya.

**Nama alat yang salah satu huruf membatalkan seluruh berkas.** Penyedianya
memeriksa nama alat di pihak mereka. Model memanggil hitungan_pengandaian,
nama yang tidak ada, dan seluruh gilirannya ditolak dengan empat ratus.

Penyelia di sini sudah tahu cara menanganinya sejak awal. Alat yang tidak
ada dikembalikan sebagai keterangan, dan model membetulkan namanya pada
giliran berikutnya. Penolakan itu tidak pernah sampai ke sana. Sekarang ia
diterjemahkan balik jadi giliran biasa, supaya penjaga yang sudah ada
mengerjakan tugas yang memang tugasnya.

Yang membuatnya ketahuan bukan uji melainkan isi penolakannya. Sebelumnya
yang tercatat cuma nomornya, dan empat ratus bisa berarti alat salah bentuk,
pesan salah urutan, atau model tidak ada. Nomor saja tidak bisa dibedakan
siapa pun.

**Berkas perkara tanpa satu pun angka lolos semua pemeriksaan.** Ini yang
paling mahal dari ketiganya, dan ia cuma kelihatan dengan membuka halamannya
sebagai pengunjung.

Pada berkas K00001283, model memanggil alat yang pasti ditolak jalur ini.
Gilirannya habis untuk satu penolakan, lalu ia menulis bahwa nilai yang
diajukan tidak tersedia, nilai yang didukung bukti tidak tersedia, dan
selisihnya tidak tersedia. Alat yang menghitung tidak pernah ia panggil.

Berkas itu lolos A1, karena tidak ada angka yang bisa tidak bersumber. Ia
lolos pemeriksaan dalam, karena tidak ada ikatan yang bisa keliru. Ia lolos
pemeriksaan bagian, karena tiap kata wajib memang disebut. Tiap penjaga
bekerja persis seperti seharusnya, dan yang keluar tetap dokumen yang tidak
berisi apa apa.

Dua hal diperbaiki. Alat yang tidak bisa dilayani berhenti ditawarkan ke
model, karena alat yang ditawarkan tapi pasti ditolak menyesatkan, bukan
sekadar sia sia. Dan berkas yang menyebut kurang dari tiga angka sekarang
ditolak, dengan ambang yang sama persis dengan yang sudah dipakai menghitung
keyakinan.

Pelajaran yang lebih umum dari ketiganya sama. Penjaga di sini dibangun
untuk menangkap yang salah, dan tidak satu pun dibangun untuk menangkap yang
kosong. Kalimat yang tidak menyebut apa apa tidak punya apa apa yang bisa
dituduh.

**Gerbangnya belum berlaku untuk model awan.** Ambang layak kirim ditera
pada dua ratus lima puluh berkas susunan model setempat, dan model yang
berbeda memberi sebaran yang berbeda.

Maka berkas dari model awan keluar tanpa keadaan, dan fungsinya menyebut
gerbangnya kosong. Itu jawaban yang benar, bukan pekerjaan yang belum
selesai. Menerakan ulang menuntut ratusan berkas, dan pada jatah per menit
di atas itu berarti berjam jam serta hampir seluruh jatah harian.

Yang perlu dicatat tentang harganya. Ambang hasil tera pada model setempat
angkanya nol, karena tidak ada satu pun cacat pada separuh kalibrasinya.
Gerbang dengan ambang nol meluluskan semuanya. Jadi jarak antara gerbang
kosong dan gerbang tertera, pada keadaan sekarang, tidak mengubah satu
berkas pun.
