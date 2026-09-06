"""Peladen penilaian klaim.

Menyajikan detektor lewat HTTP supaya website bisa memakainya. Seluruh data
yang dilayani buatan, dan tidak ada satu pun klaim peserta JKN yang sungguhan.

Jalankan:
    uvicorn nalar.api.main:app --reload
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..agen import susun
from ..profil import peringkat_faskes, perubahan_faskes, profil_faskes
from .keadaan import KEADAAN, PERINGATAN_RUPIAH
from .skema import (
    Antrean,
    BarisAntrean,
    BarisProfil,
    Jejak,
    Keadilan,
    KelompokKeadilan,
    Pengandaian,
    Penilaian,
    Penjelasan,
    Perkara,
    ProfilGanda,
    Ringkas,
    TitikPerubahan,
)


@asynccontextmanager
async def daur_hidup(_: FastAPI):
    """Bangun keadaan sekali saat peladen menyala.

    Memakai lifespan, bukan on_event, karena on_event sudah usang dan
    peringatannya akan muncul di log setiap kali peladen dinyalakan.
    """
    t = time.time()
    KEADAAN.bangun()
    print(
        f"[nalar] siap dalam {time.time() - t:.1f} detik, {len(KEADAAN.episodes)} klaim"
    )
    yield


app = FastAPI(
    lifespan=daur_hidup,
    title="NALAR",
    version="0.1.0",
    description=(
        "Menghitung berapa rupiah dari sebuah tagihan klaim JKN yang tidak "
        "didukung buktinya sendiri, tanpa satu pun contoh kecurangan "
        "berlabel.\n\n"
        "Seluruh data yang dilayani peladen ini buatan. Tidak ada klaim "
        "peserta JKN yang sungguhan, sesuai ketentuan lomba."
    ),
)

# Website peraga dilayani dari asal yang berbeda. Untuk peragaan ini dibuka
# lebar, dan itu harus diperketat sebelum menyentuh data sungguhan.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _pastikan_siap() -> None:
    if not KEADAAN.siap:
        raise HTTPException(503, "model masih disiapkan, coba beberapa detik lagi")


def _penilaian(i: int) -> Penilaian:
    r = KEADAAN.episodes[i]
    s = KEADAAN.skor
    tahan = bool(KEADAAN.tahan[i])
    return Penilaian(
        id=KEADAAN.id_klaim(i),
        faskes=KEADAAN.nama_faskes(r),
        kelas_faskes=r["f_kelas"],
        daerah_tertinggal=bool(r["f_dtpk"]),
        hari=int(r["hari"]),
        rawat_inap=bool(r["rawat_inap"]),
        kelompok_tarif=r["cbg"],
        tarif_ditagihkan_rp=int(r["tarif"]),
        tarif_didukung_bukti_rp=round(float(s["harapan_tarif"][i])),
        barang_ditagihkan_rp=int(r.get("tagih_bhp", 0)),
        barang_wajar_rp=round(float(s["harapan_tagihan"][i])),
        selisih_rp=round(float(KEADAAN.selisih[i])),
        ambang_rp=None if tahan else round(float(KEADAAN.ambang[i])),
        ditandai=bool(KEADAAN.tanda[i]),
        menahan_diri=tahan,
        posisi_terhadap_garis=round(float(KEADAAN.posisi[i]), 4),
    )


@app.get("/", summary="Keterangan singkat")
def akar() -> dict:
    return {
        "nama": "NALAR",
        "siap": KEADAAN.siap,
        "data": "buatan, tidak ada klaim peserta JKN yang sungguhan",
        "dokumentasi": "/docs",
    }


@app.get("/sehat", summary="Kesiapan peladen")
def sehat() -> dict:
    return {
        "siap": KEADAAN.siap,
        "n_klaim": len(KEADAAN.episodes) if KEADAAN.siap else 0,
    }


@app.get("/ringkas", response_model=Ringkas, summary="Angka untuk halaman muka")
def ringkas(
    alpha: float = Query(0.02, ge=0.001, le=0.2),
    biaya_audit_rp: int = Query(750_000, ge=0),
    kapasitas: int = Query(1000, ge=1),
) -> Ringkas:
    _pastikan_siap()
    KEADAAN.set_alpha(alpha)
    eps = KEADAAN.episodes
    det = KEADAAN.detektor
    det.biaya_audit_rp = biaya_audit_rp
    antre = det.antrean_audit(
        eps, kapasitas=kapasitas, batas_per_faskes=40, porsi_acak=0.05
    )
    rp = float(KEADAAN.selisih[antre].sum()) if len(antre) else 0.0
    biaya = biaya_audit_rp * len(antre)
    faskes = {(int(r["f_jenis"]), int(r["faskes"])) for r in eps}
    return Ringkas(
        n_klaim=len(eps),
        n_faskes=len(faskes),
        rentang_hari=KEADAAN.n_hari,
        nilai_klaim_total_rp=int(sum(r["tarif"] + r.get("tagih_bhp", 0) for r in eps)),
        selisih_terdeteksi_rp=round(float(KEADAAN.selisih.sum())),
        n_ditandai=int(KEADAAN.tanda.sum()),
        n_menahan_diri=int(KEADAAN.tahan.sum()),
        laju_penandaan=round(float(KEADAAN.tanda.mean()), 5),
        rasio_pengembalian=round(rp / max(biaya, 1), 2),
        peringatan=PERINGATAN_RUPIAH,
    )


@app.get("/antrean", response_model=Antrean, summary="Antrean audit sadar biaya")
def antrean(
    alpha: float = Query(0.02, ge=0.001, le=0.2),
    biaya_audit_rp: int = Query(750_000, ge=0),
    kapasitas: int = Query(100, ge=1, le=5000),
    batas_per_faskes: int | None = Query(40, ge=1),
    porsi_acak: float = Query(0.05, ge=0.0, le=0.5),
) -> Antrean:
    _pastikan_siap()
    KEADAAN.set_alpha(alpha)
    det = KEADAAN.detektor
    det.biaya_audit_rp = biaya_audit_rp
    idx = det.antrean_audit(
        KEADAAN.episodes,
        kapasitas=kapasitas,
        batas_per_faskes=batas_per_faskes,
        porsi_acak=porsi_acak,
    )
    baris = []
    for peringkat, i in enumerate(idx, start=1):
        i = int(i)
        alasan = "ambang" if KEADAAN.tanda[i] else "sampel acak"
        baris.append(
            BarisAntrean(
                peringkat=peringkat, penilaian=_penilaian(i), alasan_masuk=alasan
            )
        )
    rp = float(KEADAAN.selisih[idx].sum()) if len(idx) else 0.0
    biaya = biaya_audit_rp * len(idx)
    kurang = len(idx) < kapasitas
    return Antrean(
        kapasitas=kapasitas,
        terisi=len(idx),
        alasan_tidak_penuh=(
            "Sisanya tidak diisi karena selisihnya lebih kecil daripada biaya "
            "memeriksanya. Tidak mengisi antrean adalah perilaku yang benar, "
            "bukan kekurangan."
            if kurang
            else None
        ),
        rupiah_ditemukan_rp=round(rp),
        biaya_audit_rp=int(biaya),
        rasio_pengembalian=round(rp / max(biaya, 1), 2),
        baris=baris,
    )


@app.get("/klaim/{kid}", response_model=Penilaian, summary="Penilaian satu klaim")
def klaim(kid: str) -> Penilaian:
    _pastikan_siap()
    try:
        return _penilaian(KEADAAN.indeks_dari_id(kid))
    except KeyError:
        raise HTTPException(404, f"klaim {kid} tidak ada") from None


@app.get(
    "/klaim/{kid}/penjelasan",
    response_model=Penjelasan,
    summary="Penjelasan yang bisa dibantah",
)
def penjelasan(kid: str) -> Penjelasan:
    _pastikan_siap()
    try:
        i = KEADAAN.indeks_dari_id(kid)
    except KeyError:
        raise HTTPException(404, f"klaim {kid} tidak ada") from None

    j = KEADAAN.detektor.jelaskan(KEADAAN.episodes, i)
    a = j["angka"]
    pengandaian = [
        Pengandaian(
            kode=b["bukti"],
            nama=KEADAAN.nama_bukti(b["bukti"]),
            ubah_selisih_rp=int(b["perubahan_selisih_rp"]),
        )
        for b in j["bukti_yang_bila_ada_akan_mengubah_penilaian"]
    ]
    selisih = int(a["selisih_rp"])

    def rp(n: int) -> str:
        # Pemisah ribuan Indonesia memakai titik. Sebelumnya seluruh koma pada
        # kalimat ikut diganti titik, sehingga kalimatnya patah di tengah.
        # Sekarang yang diubah hanya angkanya.
        return "Rp " + f"{int(n):,}".replace(",", ".")

    # Kalimatnya menyebut nilai berkas utuh, bukan bagian tarif paketnya saja.
    #
    # Selisih menjumlahkan selisih tarif paket dan selisih barang habis pakai.
    # Versi sebelumnya mengutip dua angka tarif lalu menyebut selisih total, dan
    # pengurangannya tidak pernah cocok. Fasilitas kesehatan yang menghitung
    # ulang akan menemukan angka yang tidak bertemu, dan itu alasan yang sah
    # untuk tidak mempercayai seluruh suratnya.
    diajukan = int(a["tarif_ditagihkan"]) + int(a["tagihan_barang_ditagihkan"])
    wajar = int(a["tarif_didukung_bukti"]) + int(a["tagihan_barang_wajar"])
    kalimat = (
        f"Nilai yang diajukan {rp(diajukan)}, sedangkan yang didukung bukti "
        f"pada berkas ini {rp(wajar)}. Selisih {rp(selisih)}, mencakup tarif "
        "paket dan barang habis pakai. Mohon melengkapi bukti berikut bila "
        "tersedia, atau menyampaikan alasan klinisnya."
    )
    return Penjelasan(
        id=kid,
        tarif_ditagihkan_rp=int(a["tarif_ditagihkan"]),
        tarif_didukung_bukti_rp=int(a["tarif_didukung_bukti"]),
        selisih_rp=selisih,
        pengandaian=pengandaian,
        status=j["status"],
        kalimat_untuk_faskes=kalimat,
    )


@app.get(
    "/klaim/{kid}/perkara",
    response_model=Perkara,
    summary="Berkas perkara untuk verifikator",
)
def perkara(kid: str) -> Perkara:
    """Berkas perkara satu klaim, disusun lapisan agen.

    Yang dilayani versi aturan: deterministik, tidak menuntut model bahasa
    menyala, dan bisa dijalankan ulang oleh siapa pun yang punya kodenya.
    Ketika ada model berbobot terbuka di dalam pusat data, Agen Berkas
    menggantikannya, dan yang jatuh di saringan tetap keluar sebagai versi
    ini.

    Sengaja terpisah dari penjelasan. Portal fasilitas kesehatan memanggil
    penjelasan, jadi apa pun yang ditaruh di sana sampai ke peramban pihak
    yang sedang diperiksa. Berkas perkara menyebut modus yang paling dekat
    dengan bentuk selisihnya, dan itu keterangan untuk yang memeriksa.
    """
    _pastikan_siap()
    try:
        KEADAAN.indeks_dari_id(kid)
    except KeyError:
        raise HTTPException(404, f"klaim {kid} tidak ada") from None

    p = susun(KEADAAN, kid)
    r = p["ringkas_jejak"]
    return Perkara(
        id=kid,
        teks=p["teks"],
        sumber="aturan",
        jejak=Jejak(
            n_panggilan=r["n_panggilan"],
            alat=r["alat"],
            sidik_akhir=r["sidik_akhir"],
            a1_lulus=bool(p["a1"]["lulus"]),
        ),
    )


def _baris_profil(kunci, v, pakai_kelebihan: bool) -> BarisProfil:
    r = next(
        x for x in KEADAAN.episodes if (int(x["f_jenis"]), int(x["faskes"])) == kunci
    )
    return BarisProfil(
        faskes=KEADAAN.nama_faskes(r),
        kelas_faskes=r["f_kelas"],
        n_klaim=v["n"],
        kelompok_sebaya=v["sebaya"],
        rata_kelompok=float(v["rata_sebaya"]),
        rata_faskes_setelah_disusutkan=float(v["rata_susut"]),
        skor_baku=float(v["z"]),
        kelebihan_rp=int(v["kelebihan"]) if pakai_kelebihan else None,
    )


@app.get(
    "/profil",
    response_model=ProfilGanda,
    summary="Dua daftar faskes yang saling melengkapi",
)
def profil(atas: int = Query(25, ge=1, le=200)) -> ProfilGanda:
    _pastikan_siap()
    eps = KEADAAN.episodes
    rp = profil_faskes(eps, KEADAAN.selisih, minimal_klaim=20)
    ps = profil_faskes(eps, KEADAAN.posisi, minimal_klaim=20)
    return ProfilGanda(
        antrean_rupiah=[
            _baris_profil(k, v, True) for k, v in peringkat_faskes(rp, atas=atas)
        ],
        daftar_pantau_posisi=[
            _baris_profil(k, v, False) for k, v in peringkat_faskes(ps, atas=atas)
        ],
        catatan_daftar_kedua=(
            "Daftar kedua bukan tuduhan. Ia menandai faskes yang pola "
            "penagihannya menempel pada batas, yang bisa berarti pengodean "
            "yang rapi dan bisa berarti sesuatu yang lain. Yang dituntut "
            "darinya penjelasan, bukan pengembalian."
        ),
    )


@app.get(
    "/keadilan",
    response_model=Keadilan,
    summary="Panel yang membuat sistem mengawasi dirinya sendiri",
)
def keadilan(alpha: float = Query(0.02, ge=0.001, le=0.2)) -> Keadilan:
    _pastikan_siap()
    KEADAAN.set_alpha(alpha)
    kelas = np.array([r["f_kelas"] for r in KEADAAN.episodes])
    tanda = KEADAAN.tanda
    tahan = KEADAAN.tahan
    lk = float(tanda.mean())

    baris, laju = [], []
    for k in ("FKTP", "A", "B", "C", "D"):
        m = kelas == k
        if m.sum() < 30:
            continue
        v = float(tanda[m].mean())
        laju.append(v)
        baris.append(
            KelompokKeadilan(
                kelompok=k,
                n_klaim=int(m.sum()),
                n_ditandai=int(tanda[m].sum()),
                laju_penandaan=round(v, 5),
                kelebihan_terhadap_keseluruhan=round(v / max(lk, 1e-9), 3),
                porsi_menahan_diri=round(float(tahan[m].mean()), 4),
            )
        )
    if not laju:
        raise HTTPException(500, "tidak ada kelompok yang cukup besar dinilai")
    tertinggi = max(baris, key=lambda b: b.laju_penandaan)
    return Keadilan(
        alpha=alpha,
        laju_keseluruhan=round(lk, 5),
        kelompok=baris,
        rasio_simetris=round(max(laju) / max(min(laju), 1e-9), 3),
        kelebihan_berarah_maksimum=round(max(laju) / max(lk, 1e-9), 3),
        kelompok_paling_sering_ditandai=tertinggi.kelompok,
        lulus=bool(max(laju) / max(lk, 1e-9) <= 2.0),
    )


@app.get(
    "/perubahan",
    response_model=list[TitikPerubahan],
    summary="Faskes yang perilakunya bergeser sepanjang waktu",
)
def perubahan(
    batas_p: float = Query(0.05, ge=0.001, le=0.5),
    ukuran: str = Query("posisi", pattern="^(posisi|rupiah)$"),
) -> list[TitikPerubahan]:
    _pastikan_siap()
    nilai = KEADAAN.posisi if ukuran == "posisi" else KEADAAN.selisih
    hasil = perubahan_faskes(
        KEADAAN.episodes, nilai, minimal_klaim=60, n_acak=200, seed=7
    )
    keluar = []
    for kunci, v in sorted(hasil.items(), key=lambda kv: kv[1]["p"]):
        if v["p"] > batas_p:
            continue
        r = next(
            x
            for x in KEADAAN.episodes
            if (int(x["f_jenis"]), int(x["faskes"])) == kunci
        )
        keluar.append(
            TitikPerubahan(
                faskes=KEADAAN.nama_faskes(r),
                kelas_faskes=r["f_kelas"],
                n_klaim=v["n_sebelum"] + v["n_sesudah"],
                hari_ganti=v["hari_ganti"],
                rata_sebelum=float(v["rata_sebelum"]),
                rata_sesudah=float(v["rata_sesudah"]),
                p=v["p"],
            )
        )
    return keluar
