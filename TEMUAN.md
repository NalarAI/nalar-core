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
