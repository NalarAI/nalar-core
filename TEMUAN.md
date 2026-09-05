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
