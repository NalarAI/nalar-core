"""Gerbang layak kirim, ambangnya ditera bukan ditetapkan dengan perasaan.

Menambah lapisan agen berarti menambah dua sumber pergeseran: dokumen yang
diambil bisa tidak sesuai, dan alat yang dipanggil bisa memberi keluaran yang
tidak andal. Kendali risiko konformal untuk rantai alat menangani keduanya
sekaligus, dengan menyusun keputusan yang tetap sahih meski keduanya
bergeser, memakai himpunan kalibrasi yang dipisahkan lebih dulu.

Bentuknya di sini begini. Tiap berkas perkara keluar dengan satu keadaan,
layak kirim atau perlu dibaca manusia dulu. Ambang keadaan itu ditera pada
himpunan kalibrasi, dan yang dijanjikannya bisa dituliskan sebagai satu
kalimat yang bisa salah: dengan keyakinan sembilan puluh lima persen, dari
seratus berkas paling banyak lima keluar membawa cacat.

Bentuk baku kendali risiko konformal menjanjikan yang lebih lemah, yaitu
rata rata atas seluruh himpunan kalibrasi yang mungkin. Perbedaannya bukan
soal kerapian: janji atas rata rata berarti kira kira separuh pemasangan
akan melewati batasnya tanpa ada yang tahu pemasangan mana. Yang dipakai di
sini batas selang kepercayaan, yang berlaku pada pemasangan yang ini.
Harganya ambang yang lebih ketat, dan harga itu memang pantas dibayar.

Kenapa gerbangnya perlu ditera, bukan cukup disaring.

Versi pertama menjawab: karena pemeriksaan yang teliti terlalu mahal untuk
tiap berkas. Jawaban itu salah, dan salahnya ketahuan sesudah diukur.
Pemeriksaan terteliti yang kami punya berharga satu milidetik per berkas,
jadi ia sekarang jalan pada semuanya, dan kelas cacat yang dulu diserahkan
ke gerbang ini disaring habis sebelum sampai ke sini.

Jawaban yang benar lebih sempit dan lebih jujur. Ada cacat yang tidak bisa
diperiksa mesin berapa pun murahnya: apakah modus yang dipilih masuk akal
bagi berkas ini, apakah kalimatnya terbaca oleh orang klaim, apakah yang
ditekankan memang yang penting. Tidak ada regex untuk itu.

Gerbang ini menjaga yang tersisa itu. Keyakinan yang murah dipakai
memperkirakan berapa besar peluang sebuah berkas membawa cacat yang cuma
manusia bisa lihat, dan berkas yang peluangnya terlalu besar dikirim ke meja
manusia alih alih ke faskes.

Jaminannya berlaku selama berkas baru berasal dari sebaran yang sama dengan
himpunan kalibrasi. Ketika tarif berubah, teranya harus diulang, dan itu
tugas Agen Aturan.
"""

from __future__ import annotations

from dataclasses import dataclass


def skor_keyakinan(
    jejak_ringkas: dict,
    a1: dict,
    n_kata: int,
    n_kata_dasar: int,
    menahan_diri: bool,
) -> float:
    """Keyakinan atas satu berkas perkara, dihitung tanpa melihat cacatnya.

    Rumusnya tetap dan ditulis di sini, bukan dicocokkan ke data. Rumus yang
    dicocokkan ke himpunan kalibrasi akan memakai informasi yang seharusnya
    dipakai untuk menera, dan jaminannya bocor.

    Yang menurunkan keyakinan semuanya tanda bahwa agen sedang bekerja jauh
    dari pijakannya: alat yang menolak, berkas yang memang ditahan sistem,
    angka yang hanya cocok sesudah dibulatkan, dan kalimat yang jauh lebih
    panjang daripada versi aturannya.
    """
    s = 1.0

    n_galat = int(jejak_ringkas.get("n_galat", 0))
    s -= 0.15 * n_galat

    # Berkas yang ditahan sistem berarti kelompok sebayanya tidak punya
    # cukup pembanding. Agen yang tetap menulis surat di atasnya berpijak
    # pada dasar yang sistemnya sendiri sudah bilang tipis.
    if menahan_diri:
        s -= 0.30

    n_angka = max(1, int(a1.get("n_angka_diperiksa", 0)))
    if n_angka < 3:
        # Berkas perkara tanpa angka bukan berkas perkara. Kalimat yang
        # tidak menyebut besaran tidak bisa dibantah faskes, dan yang tidak
        # bisa dibantah tidak layak dikirim.
        s -= 0.25

    if n_kata_dasar > 0:
        lebih = n_kata / n_kata_dasar
        if lebih > 1.6:
            s -= min(0.30, 0.15 * (lebih - 1.6))
        if lebih < 0.5:
            s -= 0.20

    return max(0.0, min(1.0, s))


def batas_cacat(n: int, delta: float, keyakinan: float) -> int:
    """Cacah cacat terbanyak yang masih boleh lolos, pada n berkas kalibrasi.

    Yang dipakai batas atas Clopper-Pearson, dihitung terbalik. Batas atas
    untuk k cacat dari n berkas berada di bawah delta persis ketika peluang
    melihat paling banyak k cacat, seandainya laju sebenarnya delta, sudah
    lebih kecil daripada peluang jaminannya meleset. Membaliknya begitu
    membuat seluruh perhitungan selesai dalam satu lintasan, dan itu penting
    karena teranya dijalankan ulang tiap kali tarif berubah.

    Pilihan memakai batas selang kepercayaan, bukan kendali risiko konformal
    yang menjanjikan rata rata saja, disengaja. Janji atas rata rata artinya
    kira kira separuh pemasangan akan melewati delta tanpa ada yang tahu.
    NALAR menjual janji yang bisa diuji, dan janji yang hanya berlaku pada
    rata rata pemasangan tidak bisa diuji pada pemasangan yang ini.
    """
    import math

    if n <= 0:
        return -1
    gagal = 1.0 - keyakinan
    kumulatif = 0.0
    batas = -1
    for k in range(n + 1):
        log_p = (
            math.lgamma(n + 1)
            - math.lgamma(k + 1)
            - math.lgamma(n - k + 1)
            + k * math.log(delta)
            + (n - k) * math.log1p(-delta)
        )
        kumulatif += math.exp(log_p)
        if kumulatif <= gagal:
            batas = k
        else:
            break
    return batas


def tera(
    skor: list[float],
    cacat: list[bool],
    delta: float = 0.05,
    keyakinan: float = 0.95,
) -> dict:
    """Ambang terendah yang masih menjaga laju berkas cacat terkirim.

    Yang dijanjikan bisa ditulis sebagai satu kalimat yang bisa salah: dengan
    keyakinan sekian, dari seratus berkas paling banyak delta ratus keluar
    membawa cacat. Berkas yang ditahan tidak dihitung merugikan, karena
    memang ada manusia yang membacanya.

    Ambangnya ditelusuri dari yang paling ketat ke yang paling longgar, dan
    berhenti pada pelanggaran pertama. Urutan itu bagian dari jaminannya,
    bukan sekadar cara mencari: pengujian berurut yang arahnya ditetapkan
    lebih dulu tidak menuntut koreksi berganda, sedangkan menelusuri seluruh
    ambang lalu memilih yang terbaik akan menuntutnya.
    """
    n = len(skor)
    if n == 0:
        return {
            "ambang": 1.0,
            "n": 0,
            "risiko": 0.0,
            "terkirim": 0.0,
            "delta": delta,
            "keyakinan": keyakinan,
            "batas_cacat": -1,
        }

    batas = batas_cacat(n, delta, keyakinan)
    calon = sorted({round(s, 4) for s in skor} | {0.0, 1.0})
    pilih = 1.1  # di atas seluruh keyakinan, artinya tidak ada yang dikirim
    catatan = []
    for lam in reversed(calon):
        k = sum(1 for s, c in zip(skor, cacat) if s >= lam and c)
        catatan.append({"ambang": lam, "cacat": k, "batas": batas})
        if k > batas:
            break
        pilih = lam

    k = sum(1 for s, c in zip(skor, cacat) if s >= pilih and c)
    dikirim = sum(1 for s in skor if s >= pilih)
    return {
        "ambang": pilih,
        "n": n,
        "delta": delta,
        "keyakinan": keyakinan,
        "batas_cacat": batas,
        "cacat_lolos": k,
        "risiko": round(k / n, 4),
        "terkirim": round(dikirim / n, 4),
        "cacat_pada_terkirim": round(k / dikirim if dikirim else 0.0, 4),
        "kurva": catatan,
    }


@dataclass
class Gerbang:
    """Ambang hasil tera, beserta cara memakainya pada berkas baru."""

    ambang: float
    delta: float
    n_kalibrasi: int

    def putuskan(self, skor: float) -> str:
        return "layak_kirim" if skor >= self.ambang else "perlu_dibaca_manusia"

    def ringkas(self) -> dict:
        return {
            "ambang": self.ambang,
            "delta": self.delta,
            "n_kalibrasi": self.n_kalibrasi,
        }
