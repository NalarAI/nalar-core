"""Rujukan aturan yang bisa dicari, beserta jangkauan NALAR atas tiap modus.

Isinya ditulis sebagai modul Python, bukan berkas data di folder terpisah,
dan itu keputusan sadar. Tabel tarif pernah ditaruh di folder data, jalurnya
dihitung relatif terhadap akar repositori, dan ketika paketnya dipasang
berkasnya tidak ditemukan sehingga seluruh alur diam diam jatuh ke tarif
tebakan. Isi yang kecil seperti ini lebih aman tinggal di dalam modul.

Yang paling berharga di berkas ini bukan uraian modusnya, melainkan kolom
jangkauan. Dua puluh modus didaftar penyelenggara lomba, dan NALAR jujurnya
hanya menyentuh sebagian. Menuliskan yang tidak tersentuh bukan kelemahan
proposal, itu peta pekerjaan berikutnya: modus yang butuh kaitan antar berkas
adalah alasan Agen Pola ada.

Satu batasan yang perlu dibaca pelan. Lama rawat, kelas rawat, dan hasil
laboratorium adalah penciri yang masuk ke penebak. Menaikkannya menaikkan
pula tarif yang dianggap wajar, jadi selisihnya justru mengecil. Modus yang
bekerja dengan memanipulasi ketiganya berada di titik buta penebak normatif,
dan itu tertulis apa adanya di bawah.
"""

from __future__ import annotations

import re

SUMBER_MODUS = (
    "Panduan Peserta Healthkathon 2026, "
    "kategori Efisiensi Risiko pada Fasilitas Kesehatan"
)

# jangkauan: "penuh", "sebagian", atau "belum"
MODUS = [
    {
        "kode": "M01",
        "judul": "Penyalahgunaan dana kapitasi dan nonkapitasi",
        "isi": (
            "Dana kapitasi atau nonkapitasi FKTP milik pemerintah dipakai tidak "
            "sesuai peruntukan."
        ),
        "jangkauan": "belum",
        "sebab": (
            "Kapitasi dibayar per peserta per bulan, bukan per berkas, jadi tidak ada "
            "selisih tarif per berkas yang bisa dihitung."
        ),
    },
    {
        "kode": "M02",
        "judul": "Manipulasi klaim nonkapitasi",
        "isi": "Klaim nonkapitasi dimanipulasi nilainya.",
        "jangkauan": "sebagian",
        "sebab": (
            "Klaim nonkapitasi punya tarif per tindakan, jadi selisih terhadap bukti "
            "terbaca. Yang tidak terbaca manipulasi pada berkas yang buktinya ikut "
            "dipalsukan."
        ),
    },
    {
        "kode": "M03",
        "judul": "Rujukan tidak sesuai ketentuan",
        "isi": "Pasien dirujuk tidak sesuai ketentuan peraturan.",
        "jangkauan": "sebagian",
        "sebab": (
            "Status rujukan ikut jadi penciri, jadi pola rujukan yang menyimpang dari "
            "sebayanya terlihat pada profil faskes. Kesesuaian klinisnya tidak "
            "dinilai."
        ),
    },
    {
        "kode": "M04",
        "judul": "Manipulasi diagnosis atau tindakan, upcoding",
        "isi": "Diagnosis atau tindakan dipalsukan untuk menaikkan besaran klaim.",
        "jangkauan": "penuh",
        "sebab": (
            "Ini sasaran utama. Diagnosis sekunder sengaja dibuang dari penciri, jadi "
            "menambahnya menaikkan tarif yang ditagih tanpa menaikkan tarif yang "
            "dianggap wajar."
        ),
    },
    {
        "kode": "M05",
        "judul": "Cloning, penjiplakan klaim",
        "isi": "Klaim disusun dengan menyalin klaim atau rekam medis pasien lain.",
        "jangkauan": "belum",
        "sebab": (
            "Penilaian berjalan per berkas. Menemukan salinan menuntut perbandingan "
            "antar berkas, dan itu pekerjaan Agen Pola."
        ),
    },
    {
        "kode": "M06",
        "judul": "Phantom billing, klaim palsu",
        "isi": "Klaim atas layanan yang tidak pernah diberikan kepada pasien.",
        "jangkauan": "sebagian",
        "sebab": (
            "Layanan yang tidak diberikan biasanya tidak meninggalkan bukti "
            "penyertanya, jadi selisihnya besar. Yang lolos adalah berkas yang "
            "buktinya ikut dikarang lengkap."
        ),
    },
    {
        "kode": "M07",
        "judul": "Inflated bills, penggelembungan tagihan",
        "isi": (
            "Biaya obat atau alat kesehatan ditagihkan lebih besar daripada biaya "
            "sebenarnya."
        ),
        "jangkauan": "penuh",
        "sebab": (
            "Nilai barang habis pakai ditebak model terpisah, jadi selisih barang "
            "dihitung sendiri dan tidak tertutup selisih tarif paket."
        ),
    },
    {
        "kode": "M08",
        "judul": "Pemecahan episode tidak sesuai ketentuan",
        "isi": (
            "Episode pelayanan dipecah sesuai indikasi medis tetapi tidak sesuai "
            "ketentuan peraturan."
        ),
        "jangkauan": "belum",
        "sebab": (
            "Butuh melihat beberapa berkas pasien yang sama berdekatan waktunya "
            "sebagai satu kesatuan."
        ),
    },
    {
        "kode": "M09",
        "judul": "Services unbundling",
        "isi": (
            "Dua diagnosis atau prosedur yang seharusnya satu paket ditagihkan "
            "terpisah."
        ),
        "jangkauan": "belum",
        "sebab": "Sama seperti pemecahan episode, menuntut kaitan antar berkas.",
    },
    {
        "kode": "M10",
        "judul": "Self-referral, rujukan semu",
        "isi": (
            "Klaim akibat rujukan ke rumah sakit atau dokter tertentu tanpa alasan "
            "keterbatasan fasilitas."
        ),
        "jangkauan": "belum",
        "sebab": (
            "Menuntut struktur jaringan rujukan antar faskes, bukan isi satu berkas."
        ),
    },
    {
        "kode": "M11",
        "judul": "Repeat billing, klaim berulang",
        "isi": (
            "Klaim diulang pada kasus yang sama yang sudah ditagihkan dan dibayarkan."
        ),
        "jangkauan": "belum",
        "sebab": "Menuntut pencocokan antar berkas dan antar periode.",
    },
    {
        "kode": "M12",
        "judul": "Prolonged length of stay",
        "isi": (
            "Klaim membesar karena hari rawat diperpanjang bukan atas indikasi medis."
        ),
        "jangkauan": "belum",
        "sebab": (
            "Titik buta. Lama rawat adalah penciri yang masuk ke penebak, jadi "
            "memperpanjangnya menaikkan pula tarif yang dianggap wajar dan selisihnya "
            "justru mengecil."
        ),
    },
    {
        "kode": "M13",
        "judul": "Manipulasi kelas perawatan",
        "isi": "Kelas perawatan dimanipulasi sehingga klaimnya tidak sesuai.",
        "jangkauan": "belum",
        "sebab": "Titik buta yang sama. Kelas rawat ikut jadi penciri penebak.",
    },
    {
        "kode": "M14",
        "judul": "Menagihkan tindakan yang tidak dilakukan",
        "isi": "Klaim atas diagnosis atau tindakan yang tidak dilaksanakan.",
        "jangkauan": "sebagian",
        "sebab": (
            "Tindakan yang tidak dilakukan tidak meninggalkan bukti penyertanya, jadi "
            "tarif yang ditagih melampaui yang didukung bukti."
        ),
    },
    {
        "kode": "M15",
        "judul": "Tindakan pengobatan tidak sesuai indikasi medis",
        "isi": "Klaim atas tindakan pengobatan yang tidak sesuai indikasi medis.",
        "jangkauan": "belum",
        "sebab": (
            "Kesesuaian indikasi adalah penilaian klinis, bukan kewajaran nilai. "
            "NALAR tidak menilai kelayakan tindakan."
        ),
    },
    {
        "kode": "M16",
        "judul": "Readmisi, admisi berulang",
        "isi": (
            "Satu episode diklaim lebih dari satu kali seolah lebih dari satu episode."
        ),
        "jangkauan": "belum",
        "sebab": "Menuntut kaitan antar berkas pada pasien yang sama.",
    },
    {
        "kode": "M17",
        "judul": "Klaim fiktif obat, alkes, atau tindakan",
        "isi": (
            "Obat, alat kesehatan, atau tindakan ditagihkan tetapi tidak diberikan "
            "kepada pasien."
        ),
        "jangkauan": "penuh",
        "sebab": (
            "Nilai barang yang wajar ditebak dari bukti pada berkas, jadi tagihan "
            "barang yang tidak berdasar terlihat sebagai selisih barang."
        ),
    },
    {
        "kode": "M18",
        "judul": "Pengurangan jumlah obat",
        "isi": (
            "Jumlah obat yang diserahkan ke pasien dikurangi tetapi ditagihkan sesuai "
            "resep."
        ),
        "jangkauan": "belum",
        "sebab": (
            "Yang terbaca hanya yang ditagihkan. Selisih antara yang diserahkan dan "
            "yang ditagihkan menuntut data penyerahan obat."
        ),
    },
    {
        "kode": "M19",
        "judul": "Inflated bills pada obat dan alkes",
        "isi": "Biaya obat atau alkes ditagihkan lebih besar dari biaya sebenarnya.",
        "jangkauan": "penuh",
        "sebab": "Sama dengan M07, dihitung penebak nilai barang.",
    },
    {
        "kode": "M20",
        "judul": "Manipulasi hasil pemeriksaan",
        "isi": "Hasil pemeriksaan dimanipulasi untuk memenuhi syarat penagihan.",
        "jangkauan": "belum",
        "sebab": (
            "Titik buta. Hasil laboratorium adalah penciri penebak, jadi "
            "memanipulasinya menggeser tarif yang dianggap wajar ke arah yang sama."
        ),
    },
]

DASAR = [
    {
        "kode": "D01",
        "judul": "Dasar tarif INA-CBG",
        "isi": (
            "Besaran tarif tiap kelompok INA-CBG ditetapkan menurut kode kelompok, "
            "kelas rawat, kelas rumah sakit, regional, dan kepemilikan. NALAR memakai "
            "76.970 baris untuk 885 kode."
        ),
        "sumber": "Lampiran Peraturan Menteri Kesehatan Nomor 3 Tahun 2023",
    },
    {
        "kode": "D02",
        "judul": "Pencegahan dan penanganan kecurangan JKN",
        "isi": (
            "Pencegahan kecurangan diselenggarakan bersama oleh BPJS Kesehatan, "
            "Kementerian Kesehatan, dan pemerintah daerah, dengan tim yang dibentuk "
            "sampai tingkat kabupaten dan kota."
        ),
        "sumber": "Peraturan Menteri Kesehatan Nomor 16 Tahun 2019",
    },
    {
        "kode": "D03",
        "judul": "Larangan memakai data peserta yang nyata",
        "isi": (
            "Peserta lomba dilarang memakai, mengakses, mengolah, atau "
            "menyebarluaskan data peserta JKN yang bersifat nyata tanpa izin "
            "tertulis, dan diwajibkan memakai data simulasi."
        ),
        "sumber": "Panduan Peserta Healthkathon 2026 pasal kerahasiaan",
    },
    {
        "kode": "D04",
        "judul": "Batas keputusan sistem",
        "isi": (
            "NALAR memberi urutan prioritas pemeriksaan. Keputusan menyetujui, "
            "meminta kelengkapan, atau meneruskan ke unit yang berwenang "
            "menanganinya diambil verifikator, bukan sistem ini."
        ),
        "sumber": "Rancangan NALAR bagian batas dan ketentuan layanan",
    },
]


def _kata(teks: str) -> set[str]:
    return {k for k in re.findall(r"[a-z0-9]+", teks.lower()) if len(k) > 2}


def _entri() -> list[dict]:
    keluar = []
    for m in MODUS:
        keluar.append(
            {
                "kode": m["kode"],
                "judul": m["judul"],
                "isi": m["isi"],
                "jangkauan": m["jangkauan"],
                "sebab": m["sebab"],
                "sumber": SUMBER_MODUS,
            }
        )
    for d in DASAR:
        keluar.append({**d, "jangkauan": None, "sebab": None})
    return keluar


def cari(pertanyaan: str, atas: int = 3) -> list[dict]:
    """Entri aturan yang paling cocok dengan sebuah pertanyaan.

    Pencocokannya berbasis kata, bukan sematan makna, dan itu disengaja pada
    tahap ini. Model sematan menambah satu ketergantungan yang harus ikut
    dipasang di dalam jaringan BPJS, sedangkan korpusnya baru dua puluh empat
    entri. Menaikkannya jadi pencarian bermakna baru berguna setelah korpusnya
    memuat naskah peraturan selengkapnya.
    """
    q = _kata(pertanyaan)
    if not q:
        return []
    nilai = []
    for e in _entri():
        k = _kata(f"{e['judul']} {e['isi']} {e.get('sebab') or ''}")
        tumpang = len(q & k)
        if tumpang:
            nilai.append((tumpang / len(q | k), tumpang, e))
    nilai.sort(key=lambda x: (-x[0], -x[1], x[2]["kode"]))
    return [e for _, _, e in nilai[:atas]]


def jangkauan() -> dict:
    """Berapa modus yang tersentuh penuh, sebagian, dan belum sama sekali."""
    h = {"penuh": 0, "sebagian": 0, "belum": 0}
    for m in MODUS:
        h[m["jangkauan"]] += 1
    return h
