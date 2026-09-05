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
