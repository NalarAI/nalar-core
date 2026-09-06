"""Agen Pola: dibangunkan peristiwa, bukan oleh orang yang membuka halaman.

Sistem sekarang menunggu dibuka. Titik perubahan pola sudah dihitung sejak
lama dan tampil di halaman analitik, tapi tidak ada yang membangunkan siapa
pun ketika sebuah faskes bergeser. Kalau tidak ada yang membuka halaman itu
bulan ini, pergeserannya tidak diketahui bulan ini.

Survei tujuh dimensi atas agen kesehatan mencatat sekitar 92 persen sistem
yang ditinjau tidak punya pengaktifan oleh peristiwa. Agen ini mengisi lubang
itu.

Yang membedakannya dari laporan biasa satu hal saja, dan bukan
kecanggihannya. Laporan menyusun daftar terurut dan menyerahkan pemilihan
kepada pembacanya. Agen ini memilih sendiri, memakai aturan yang ditetapkan
lebih dulu, lalu membuka perkara hanya untuk yang melewatinya. Kalau tidak
ada yang melewati, ia diam. Agen yang selalu punya sesuatu untuk dilaporkan
akan berhenti dibaca dalam sebulan.

Dan yang memilih harus menghitung berapa banyak yang ia uji. Uji titik
perubahan dijalankan pada tiap faskes yang klaimnya cukup banyak, jadi
seratus faskes berarti seratus uji. Pada ambang lima persen tanpa koreksi,
lima di antaranya akan lolos karena undian. Halaman analitik kami sendiri
menampilkan daftar seperti itu, dan pada data peragaan tujuh faskes lolos
dari seratus empat yang diuji. Lima dari tujuh itu diperkirakan undian.

Maka ambangnya dikendalikan Benjamini-Hochberg, bukan angka tetap. Pada data
peragaan hasilnya nol perkara, dan nol itu jawaban yang benar.

Yang dilaporkannya tiga hal yang bisa ditindaklanjuti: tanggalnya, besar
pergeserannya, dan berkas mana yang menyumbang. Bukan skor, bukan peringkat.
Verifikator tidak bisa mengerjakan apa pun dengan peringkat.

Satu hal yang tidak dikerjakan agen ini: menyimpulkan sebab. Faskes bisa
bergeser karena berganti dokter, membuka layanan baru, atau kedatangan wabah.
Menyebut pergeseran sebagai kecurigaan berarti menuduh berdasarkan sesuatu
yang punya banyak sebab wajar.
"""

from __future__ import annotations

import time

import numpy as np

from .jejak import Jejak

# Ambang yang menentukan sebuah pergeseran layak dibukakan perkara. Ditulis
# di sini, sebelum satu perkara pun dibuka, supaya tidak digeser belakangan
# mengikuti hasil yang kebetulan menarik.
#
# FDR, bukan nilai p apa adanya, dan ini yang paling penting di berkas ini.
# Uji titik perubahan dijalankan pada tiap faskes yang klaimnya cukup banyak,
# jadi seratus faskes berarti seratus uji. Pada ambang lima persen tanpa
# koreksi, lima di antaranya akan lolos karena undian, bukan karena bergeser.
# Daftar yang menampilkan mereka sebagai temuan sedang menampilkan derau.
MINIMAL_KLAIM = 60
MINIMAL_GESER_RP = 0
FDR = 0.10


def benjamini_hochberg(p: list[float], fdr: float) -> float:
    """Nilai p terbesar yang masih lolos kendali laju penemuan palsu.

    Mengembalikan nol kalau tidak ada satu pun yang lolos, artinya seluruh
    pergeseran yang terlihat sepadan dengan yang muncul dari undian.

    Dipilih Benjamini-Hochberg, bukan Bonferroni, karena yang ingin dijaga
    porsi perkara yang salah dibuka, bukan peluang satu pun salah dibuka.
    Verifikator bisa menerima satu dari sepuluh perkara ternyata tidak
    berisi. Yang tidak bisa diterima sembilan dari sepuluh.
    """
    n = len(p)
    if n == 0:
        return 0.0
    urut = sorted(p)
    lolos = 0.0
    for k, nilai in enumerate(urut, start=1):
        if nilai <= fdr * k / n:
            lolos = nilai
    return lolos


def _berkas_penyumbang(episodes, selisih, kunci, hari_ganti, atas=5):
    """Berkas sesudah tanggal pergeseran, terurut dari selisih terbesar."""
    keluar = []
    for i, r in enumerate(episodes):
        if (int(r["f_jenis"]), int(r["faskes"])) != kunci:
            continue
        if int(r["hari"]) < int(hari_ganti):
            continue
        keluar.append((float(selisih[i]), i))
    keluar.sort(reverse=True)
    return [i for _, i in keluar[:atas]]


def jalankan(
    keadaan,
    fdr: float = FDR,
    minimal_klaim: int = MINIMAL_KLAIM,
    minimal_geser_rp: int = MINIMAL_GESER_RP,
) -> dict:
    """Perkara yang layak dibuka, atau daftar kosong beserta alasannya.

    Daftar kosong adalah keluaran yang sah dan yang paling sering benar.
    """
    from ..profil import perubahan_faskes

    jejak = Jejak(perkara="pola")
    t0 = time.time()

    selisih = np.asarray(keadaan.selisih, dtype=np.float64)
    titik = perubahan_faskes(
        keadaan.episodes,
        selisih,
        minimal_klaim=minimal_klaim,
        peringkat=False,
        per_pasien=False,
    )
    jejak.tambah(
        "perubahan_faskes",
        {"minimal_klaim": minimal_klaim},
        {"n_faskes_diuji": len(titik)},
        0.0,
    )

    # perubahan_faskes mengembalikan peta berkunci (jenis, nomor) faskes,
    # bukan daftar. Kuncinya dipakai apa adanya untuk mengumpulkan berkas
    # penyumbang, jadi tidak ada nama yang perlu diurai kembali jadi kunci.
    per_faskes: dict[tuple, list[int]] = {}
    for i, r in enumerate(keadaan.episodes):
        per_faskes.setdefault((int(r["f_jenis"]), int(r["faskes"])), []).append(i)

    # Ambang p dihitung dari seluruh uji yang dijalankan, bukan ditetapkan
    # angka tetap. Menetapkannya tetap berarti mengabaikan berapa banyak
    # faskes yang diuji, dan jumlah itu yang menentukan berapa banyak lolos
    # karena undian.
    semua_p = [float(v["p"]) for v in titik.values()]
    batas_p = benjamini_hochberg(semua_p, fdr)
    tanpa_koreksi = sum(1 for x in semua_p if x <= 0.05)
    jejak.tambah(
        "benjamini_hochberg",
        {"fdr": fdr, "n_uji": len(semua_p)},
        {"batas_p": batas_p, "lolos_tanpa_koreksi": tanpa_koreksi},
        0.0,
    )

    perkara = []
    for kunci, t in titik.items():
        geser = float(t["rata_sesudah"]) - float(t["rata_sebelum"])
        if batas_p <= 0 or float(t["p"]) > batas_p or geser < minimal_geser_rp:
            continue
        pos = per_faskes.get(kunci, [])
        if not pos:
            continue
        contoh = keadaan.episodes[pos[0]]
        idx = _berkas_penyumbang(keadaan.episodes, selisih, kunci, t["hari_ganti"])
        perkara.append(
            {
                "faskes": keadaan.nama_faskes(contoh),
                "kelas_faskes": contoh["f_kelas"],
                "hari_ganti": int(t["hari_ganti"]),
                "rata_sebelum_rp": round(float(t["rata_sebelum"])),
                "rata_sesudah_rp": round(float(t["rata_sesudah"])),
                "geser_rp": round(geser),
                "p": float(t["p"]),
                "n_klaim": len(pos),
                "n_sesudah": int(t["n_sesudah"]),
                "berkas_penyumbang": [keadaan.id_klaim(i) for i in idx],
                "catatan": (
                    "Pergeseran punya banyak sebab wajar, termasuk berganti "
                    "dokter, membuka layanan baru, dan perubahan bauran "
                    "pasien. Yang diminta pemeriksaan, bukan kesimpulan."
                ),
            }
        )

    perkara.sort(key=lambda x: -x["geser_rp"])
    jejak.tambah(
        "susun_perkara",
        {"batas_p": batas_p, "minimal_geser_rp": minimal_geser_rp},
        {"n_perkara": len(perkara)},
        0.0,
    )

    if perkara:
        sebab = ""
    elif not titik:
        sebab = (
            "Tidak ada faskes yang klaimnya cukup banyak untuk diuji pada periode ini."
        )
    else:
        sebab = (
            f"{len(titik)} faskes diuji, dan {tanpa_koreksi} di antaranya "
            "lolos pada ambang lima persen. Sesudah dikoreksi terhadap "
            "banyaknya uji, tidak ada yang tersisa. Pergeseran yang terlihat "
            "sepadan dengan yang muncul dari undian."
        )

    return {
        "n_faskes_diuji": len(titik),
        "n_perkara": len(perkara),
        "n_lolos_tanpa_koreksi": tanpa_koreksi,
        "sebab_kosong": sebab,
        "perkara": perkara,
        "ambang": {
            "fdr": fdr,
            "batas_p": batas_p,
            "minimal_klaim": minimal_klaim,
            "minimal_geser_rp": minimal_geser_rp,
        },
        "detik": round(time.time() - t0, 2),
        "jejak": jejak,
        "ringkas_jejak": jejak.ringkas(),
    }
