"""Gelanggang: menjalankan satu siasat terhadap detektor yang benar benar dikirim.

Yang diukur bukan berapa persen pelaku tertangkap. Ukuran itu terdengar bagus
dan menyesatkan, karena pelaku yang mengambil sedikit dari banyak berkas bisa
tertangkap delapan puluh persen dan tetap pulang membawa lebih banyak uang
daripada pelaku yang tertangkap nol persen.

Yang diukur uang yang lolos. Sistem pengawasan yang baik tidak menangkap semua
orang, ia membuat kecurangan tidak sepadan.

Empat hal yang dijaga di sini, dan keempatnya pernah jadi cara menipu diri
sendiri pada percobaan sebelumnya.

Berkas aslinya tidak pernah disentuh. Tiap siasat bekerja pada salinan, jadi
siasat kedua menghadapi himpunan yang sama persis dengan siasat pertama.

Ambangnya diambil sebelum serangan, bukan sesudah. Ambang yang dihitung ulang
pada berkas yang sudah diserang akan bergeser mengikuti serangannya, dan
pelakunya akan terlihat lebih sering tertangkap daripada yang sebenarnya.

Pelakunya diberi akses penuh ke skor detektor. Itu asumsi terburuk dan
disengaja. Rumah sakit yang benar benar ingin menghindari sistem akan mencoba
sampai tahu apa yang lolos, dan mengukur seolah mereka buta akan memberi angka
yang terlalu bagus.

Siasat baru harus menang pada himpunan yang tidak dipakai menemukannya.
Siasat yang cuma menang di tempat ia ditemukan bukan temuan, itu kebetulan.
"""

from __future__ import annotations

import numpy as np

from .siasat import cocok_sasaran, periksa, pilih, varian


def _lantai_biaya(biaya_audit_rp: int) -> int:
    """Selisih terkecil yang masih pantas diperiksa.

    Berkas yang selisihnya di bawah ini tidak pernah masuk antrean, sekalipun
    tertandai, karena memeriksanya lebih mahal daripada yang bisa
    diselamatkan. Pelaku yang tahu angka ini punya tempat sembunyi yang tidak
    bisa ditutup dengan model yang lebih pintar.
    """
    return int(biaya_audit_rp)


def jalankan(
    episodes: list[dict],
    idx,
    penskor,
    ambang,
    tahan,
    siasat: dict,
    biaya_audit_rp: int = 750_000,
    maks_klaim: int = 400,
) -> dict:
    """Ukur satu siasat pada satu himpunan berkas.

    penskor  fungsi yang menerima daftar berkas dan mengembalikan selisihnya
    ambang   ambang penandaan per berkas, dihitung sebelum serangan
    tahan    penanda kelompok yang menahan diri, per berkas
    """
    periksa(siasat)
    gerakan = siasat["gerakan"]
    sasaran = siasat.get("sasaran") or {"jenis": "semua_rawat_inap"}
    cara = siasat.get("pilihan") or {"jenis": "paling_untung"}

    calon = [int(i) for i in idx if episodes[int(i)]["rawat_inap"]][:maks_klaim]
    if not calon:
        return {"nama": siasat["nama"], "galat": "tidak ada berkas rawat inap"}

    asli = [episodes[i] for i in calon]
    skor_asli = np.asarray(penskor(asli), dtype=np.float64)

    # Sasaran disaring memakai selisih sebelum serangan, bukan sesudah.
    sasar = [
        pos
        for pos, i in enumerate(calon)
        if cocok_sasaran(episodes[i], sasaran, bool(tahan[i]), float(skor_asli[pos]))
    ]
    if not sasar:
        return {
            "nama": siasat["nama"],
            "n_sasaran": 0,
            "diambil_rp": 0,
            "lolos_rp": 0,
            "maks_per_klaim_rp": 0,
            "porsi_tertangkap": None,
            "catatan": "tidak ada berkas yang cocok dengan sasarannya",
        }

    lantai = _lantai_biaya(biaya_audit_rp)

    # Seluruh varian dari seluruh berkas disusun lebih dulu, lalu diberi skor
    # sekali jalan. Memanggil penebak per berkas membuat satu siasat memakan
    # ratusan panggilan, dan agen menjalankan puluhan siasat.
    semua, batas = [], []
    for pos in sasar:
        v = varian(episodes[calon[pos]], gerakan)
        batas.append((pos, len(semua), len(semua) + len(v)))
        semua.extend(v)
    if not semua:
        return {"nama": siasat["nama"], "n_sasaran": len(sasar), "diambil_rp": 0}

    skor_semua = np.asarray(penskor(semua), dtype=np.float64)

    diambil, lolos, per_klaim, per_klaim_lolos = 0.0, 0.0, [], []
    n_tertangkap = 0

    for pos, a, b in batas:
        i = calon[pos]
        r = episodes[i]
        vs = semua[a:b]
        untung = np.array(
            [
                float(v["tarif"] - r["tarif"])
                + float(v.get("tagih_bhp", 0) - r.get("tagih_bhp", 0))
                for v in vs
            ],
            dtype=np.float64,
        )
        skor = skor_semua[a:b]
        k = pilih(cara, untung, skor, float(skor_asli[pos]), float(ambang[i]))
        if k is None or untung[k] <= 0:
            continue

        diambil += float(untung[k])
        per_klaim.append(float(untung[k]))

        # Tertangkap berarti dua duanya: skornya melewati ambang, dan
        # selisihnya cukup besar untuk pantas diperiksa. Berkas yang tertandai
        # tapi nilainya di bawah lantai biaya tidak pernah dibuka siapa pun,
        # dan menghitungnya sebagai tertangkap akan melaporkan pengawasan yang
        # tidak pernah terjadi.
        ketahuan = bool(skor[k] > ambang[i]) and float(skor[k]) >= lantai
        if ketahuan:
            n_tertangkap += 1
        else:
            lolos += float(untung[k])
            per_klaim_lolos.append(float(untung[k]))

    n = len(per_klaim)
    return {
        "nama": siasat["nama"],
        "n_sasaran": len(sasar),
        "n_diserang": n,
        "diambil_rp": round(diambil),
        "lolos_rp": round(lolos),
        "maks_per_klaim_rp": round(max(per_klaim)) if per_klaim else 0,
        # Yang terbesar di antara yang benar benar lolos. Ini ukuran T6 yang
        # sebenarnya: berapa besar keuntungan yang masih bisa diambil pelaku
        # tanpa tertangkap. Yang terbesar termasuk yang tertangkap tidak
        # menjawab pertanyaan itu, karena yang tertangkap tidak jadi uang.
        "maks_lolos_rp": round(max(per_klaim_lolos)) if per_klaim_lolos else 0,
        "rerata_per_klaim_rp": round(diambil / n) if n else 0,
        "porsi_tertangkap": round(n_tertangkap / n, 4) if n else None,
    }


# Tiga pelaku yang sudah ada, ditulis ulang dalam bahasa siasat. Angkanya
# harus sama dengan yang dilaporkan percobaan sebelumnya, dan itu diperiksa
# di uji. Tanpa ini, siasat baru tidak punya pembanding yang jujur.
BAKU = [
    {
        "nama": "serakah",
        "sasaran": {"jenis": "semua_rawat_inap"},
        "gerakan": [{"jenis": "tambah_diagnosis"}],
        "pilihan": {"jenis": "paling_untung"},
    },
    {
        "nama": "hati hati",
        "sasaran": {"jenis": "semua_rawat_inap"},
        "gerakan": [{"jenis": "tambah_diagnosis"}],
        "pilihan": {"jenis": "aman_di_bawah_ambang"},
    },
    {
        "nama": "menyebar",
        "sasaran": {"jenis": "semua_rawat_inap"},
        "gerakan": [{"jenis": "tambah_diagnosis"}],
        "pilihan": {"jenis": "kenaikan_skor_terkecil"},
    },
]


def garis_dasar(episodes, idx, penskor, ambang, tahan, **kw) -> dict:
    """Hasil ketiga pelaku baku. Ini yang harus dikalahkan siasat baru."""
    hasil = [jalankan(episodes, idx, penskor, ambang, tahan, s, **kw) for s in BAKU]
    terbaik = max(hasil, key=lambda h: h.get("lolos_rp", 0))
    return {
        "baris": hasil,
        "lolos_terbaik_rp": terbaik.get("lolos_rp", 0),
        # Kedua ukuran diambil dari pelaku terbaik menurut ukurannya
        # masing masing, bukan dari satu pelaku saja. Siasat baru harus
        # mengalahkan yang terbaik pada ukuran yang ia klaim, bukan
        # mengalahkan pelaku yang kebetulan lemah pada ukuran itu.
        "maks_lolos_terbaik_rp": max(h.get("maks_lolos_rp", 0) for h in hasil),
        "nama_terbaik": terbaik.get("nama", ""),
    }
