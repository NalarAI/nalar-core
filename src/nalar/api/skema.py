"""Bentuk masukan dan keluaran API. Ini kontraknya.

Ditulis lebih dulu, sebelum satu baris antarmuka dibuat, supaya model dan
website bisa dikerjakan tanpa saling menunggu.

Tiga aturan yang mengikat seluruh berkas ini.

Setiap angka uang berakhiran `_rp` dan bersatuan rupiah penuh, bukan ribuan
dan bukan pecahan. Tidak ada skor tanpa satuan yang keluar dari sini, karena
skor tanpa satuan tidak bisa dibawa ke rapat.

Kata curang, fraud, dan kecurangan tidak muncul di nama bidang mana pun. Yang
dikirim sistem ini permintaan konfirmasi, bukan vonis, dan penamaan yang
salah akan membocorkan sikap yang salah ke seluruh antarmuka.

Menahan diri adalah keadaan tersendiri, bukan ambang bernilai tak hingga yang
disamarkan. Faskes yang datanya belum cukup untuk dinilai harus terlihat
berbeda dari faskes yang sudah dinilai dan bersih.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Pengaturan(BaseModel):
    """Parameter kebijakan yang boleh digeser pemakai di layar."""

    alpha: float = Field(
        0.02,
        ge=0.001,
        le=0.2,
        description="Porsi klaim bersih yang boleh ikut tertandai. Ini janji "
        "yang dipegang faskes, bukan sekadar setelan.",
    )
    biaya_audit_rp: int = Field(
        750_000,
        ge=0,
        description="Ongkos memeriksa satu berkas. Angka kebijakan yang harus "
        "diisi BPJS, bukan yang kami tetapkan.",
    )
    kapasitas: int = Field(
        1000,
        ge=1,
        le=100_000,
        description="Berapa berkas yang sanggup diperiksa pada periode ini.",
    )
    batas_per_faskes: int | None = Field(
        40,
        ge=1,
        description="Batas berkas per faskes, supaya satu faskes tidak "
        "menghabiskan seluruh anggaran pemeriksaan.",
    )
    porsi_acak: float = Field(
        0.05,
        ge=0.0,
        le=0.5,
        description="Porsi antrean yang diisi sampel acak. Ini yang membuat "
        "faskes yang sistemnya menahan diri tetap terperiksa, dan "
        "yang membuat pelaku tidak bisa memastikan dirinya aman.",
    )


class Penilaian(BaseModel):
    """Hasil untuk satu klaim."""

    id: str
    faskes: str
    kelas_faskes: str
    daerah_tertinggal: bool
    hari: int
    rawat_inap: bool
    kelompok_tarif: str

    tarif_ditagihkan_rp: int
    tarif_didukung_bukti_rp: int
    barang_ditagihkan_rp: int
    barang_wajar_rp: int
    selisih_rp: int

    ambang_rp: int | None = Field(
        None, description="Null berarti kelompoknya menahan diri."
    )
    ditandai: bool
    menahan_diri: bool
    posisi_terhadap_garis: float = Field(
        description="Nol berarti persis sebesar yang didukung bukti, satu "
        "berarti persis di ambang. Ini yang menjawab faskes yang "
        "menagih tepat di bawah garis dan tidak pernah "
        "melewatinya."
    )


class Pengandaian(BaseModel):
    """Satu bukti yang tidak ada di berkas, beserta akibatnya bila ada.

    Nilainya selisih sekarang dikurangi selisih seandainya bukti itu ada.
    Positif berarti bukti menurunkan selisih, negatif berarti menaikkannya.
    Keduanya dikirim apa adanya, karena antarmuka yang mengambil nilai
    mutlaknya akan menampilkan bukti yang memperburuk sebagai pengurang.
    """

    kode: str
    nama: str
    ubah_selisih_rp: int


class Jejak(BaseModel):
    """Ringkasan jejak pemanggilan alat yang menyusun sebuah berkas perkara.

    Yang disimpan bukan isi hasilnya, melainkan alat mana yang dipanggil dan
    sidik rantainya. Rantai sidik itu yang membuat satu baris tidak bisa
    disunting tanpa merusak seluruh baris sesudahnya, dan itu yang bisa
    ditunjukkan ketika fasilitas kesehatan menanyakan asal sebuah angka.
    """

    n_panggilan: int
    alat: list[str]
    sidik_akhir: str
    a1_lulus: bool = Field(
        description="Tidak ada angka pada berkas perkara yang tidak berasal "
        "dari pemanggilan alat."
    )


class Penjelasan(BaseModel):
    """Penjelasan satu klaim, dalam bentuk yang bisa dibantah."""

    id: str
    tarif_ditagihkan_rp: int
    tarif_didukung_bukti_rp: int
    selisih_rp: int
    pengandaian: list[Pengandaian]
    status: str = Field(description="Kalimat yang boleh dikirim ke faskes apa adanya.")
    kalimat_untuk_faskes: str


class Perkara(BaseModel):
    """Berkas perkara satu klaim. Dokumen verifikator, bukan surat untuk faskes.

    Dipisahkan dari Penjelasan dengan sengaja, dan pemisahannya bukan soal
    kerapian. Portal fasilitas kesehatan memanggil Penjelasan, jadi apa pun
    yang ditaruh di sana sampai ke peramban pihak yang sedang diperiksa,
    sekalipun antarmukanya tidak menampilkannya. Berkas perkara menyebut
    modus kecurangan yang paling dekat dengan bentuk selisihnya, dan itu
    keterangan untuk yang memeriksa, bukan untuk yang diperiksa.
    """

    id: str
    teks: str = Field(
        description="Bukti pada berkas, tarif resmi yang berlaku, dan modus "
        "yang paling dekat beserta jangkauan NALAR atasnya."
    )
    sumber: str = Field(
        description="aturan, atau agen. Versi aturan deterministik dan tidak "
        "menuntut model bahasa menyala."
    )
    jejak: Jejak


class PerkaraPola(BaseModel):
    """Satu perkara yang dibuka Agen Pola karena polanya bergeser.

    Bedanya dengan baris tabel titik perubahan bukan isinya, melainkan siapa
    yang memilih. Tabel menyusun daftar terurut dan menyerahkan pemilihan
    kepada pembacanya. Perkara ini sudah melewati ambang yang ditetapkan
    sebelum satu perkara pun dibuka, dan membawa nomor berkas yang menyumbang
    sehingga bisa langsung dibuka.
    """

    faskes: str
    kelas_faskes: str
    hari_ganti: int
    rata_sebelum_rp: int
    rata_sesudah_rp: int
    geser_rp: int
    p: float
    n_klaim: int
    n_sesudah: int
    berkas_penyumbang: list[str]
    catatan: str = Field(
        description="Pergeseran punya banyak sebab wajar. Yang diminta "
        "pemeriksaan, bukan kesimpulan."
    )


class LaporanPola(BaseModel):
    """Keluaran Agen Pola. Daftar kosong adalah jawaban yang sah.

    Ambang p tidak ditetapkan angka tetap, melainkan dikendalikan terhadap
    banyaknya faskes yang diuji. Seratus faskes berarti seratus uji, dan pada
    ambang lima persen tanpa koreksi lima di antaranya lolos karena undian.
    """

    n_faskes_diuji: int
    n_perkara: int
    n_lolos_tanpa_koreksi: int = Field(
        description="Berapa yang akan lolos pada ambang lima persen tanpa "
        "koreksi. Selisihnya dengan n_perkara adalah yang diperkirakan undian."
    )
    sebab_kosong: str = Field(
        description="Kenapa tidak ada perkara yang dibuka. Kosong ketika ada."
    )
    perkara: list[PerkaraPola]
    fdr: float
    batas_p: float
    minimal_klaim: int
    minimal_geser_rp: int


class BarisAntrean(BaseModel):
    peringkat: int
    penilaian: Penilaian
    alasan_masuk: str = Field(
        description="ambang, atau sampel acak. Dibedakan supaya pemeriksa "
        "tahu mana yang datang dari kecurigaan dan mana yang "
        "datang dari undian."
    )


class Antrean(BaseModel):
    kapasitas: int
    terisi: int
    alasan_tidak_penuh: str | None
    rupiah_ditemukan_rp: int
    biaya_audit_rp: int
    rasio_pengembalian: float
    baris: list[BarisAntrean]


class BarisProfil(BaseModel):
    faskes: str
    kelas_faskes: str
    n_klaim: int
    kelompok_sebaya: str
    rata_kelompok: float
    rata_faskes_setelah_disusutkan: float
    skor_baku: float
    kelebihan_rp: int | None = Field(
        None, description="Hanya terisi pada daftar rupiah."
    )


class ProfilGanda(BaseModel):
    """Dua daftar yang saling melengkapi, bukan saling mengganti."""

    antrean_rupiah: list[BarisProfil]
    daftar_pantau_posisi: list[BarisProfil]
    catatan_daftar_kedua: str


class KelompokKeadilan(BaseModel):
    kelompok: str
    n_klaim: int
    n_ditandai: int
    laju_penandaan: float
    kelebihan_terhadap_keseluruhan: float
    porsi_menahan_diri: float


class Keadilan(BaseModel):
    """Panel yang membuat sistem mengawasi dirinya sendiri di depan pemakai."""

    alpha: float
    laju_keseluruhan: float
    kelompok: list[KelompokKeadilan]
    rasio_simetris: float
    kelebihan_berarah_maksimum: float
    kelompok_paling_sering_ditandai: str
    batas: float = 2.0
    lulus: bool


class TitikPerubahan(BaseModel):
    faskes: str
    kelas_faskes: str
    n_klaim: int
    hari_ganti: int
    rata_sebelum: float
    rata_sesudah: float
    p: float


class Ringkas(BaseModel):
    """Angka untuk halaman muka."""

    n_klaim: int
    n_faskes: int
    rentang_hari: int
    nilai_klaim_total_rp: int
    selisih_terdeteksi_rp: int
    n_ditandai: int
    n_menahan_diri: int
    laju_penandaan: float
    rasio_pengembalian: float
    peringatan: str = Field(
        description="Kalimat yang wajib ikut setiap kali angka rupiah "
        "dikutip, karena rupiah bergeser antar benih acak."
    )


class Surat(BaseModel):
    """Lampiran keterangan dari faskes, dalam bentuk kalimat biasa."""

    isi: str = Field(
        min_length=1,
        max_length=8000,
        description="Isi surat atau catatan yang dikirim faskes.",
    )


class BuktiTerbaca(BaseModel):
    kode: str
    nama: str
    alasan: str


class Sanggahan(BaseModel):
    """Yang boleh dilihat faskes atas suratnya sendiri.

    Yang tidak ada di sini berkas perkara dan daftar modus. Faskes berhak
    tahu pemeriksaan mana yang terbaca dan berapa selisihnya berubah, dan
    tidak berhak tahu dugaan apa yang sedang diperiksa atas dirinya.
    """

    id: str
    cara: str = Field(
        description="model kalau dibaca model bahasa, kata kalau pencocokan kata."
    )
    dipetakan: list[BuktiTerbaca]
    sudah_ada: list[str]
    selisih_semula_rp: int | None = None
    selisih_sesudah_rp: int | None = None
    turun_rp: int | None = None
    keterangan: str = ""
