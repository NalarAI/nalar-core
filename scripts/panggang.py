"""Memanggang jawaban peladen jadi berkas statis.

Kenapa ini ada, dan kenapa bukan sekadar jalan pintas.

Peladen ini melatih modelnya saat menyala. Itu benar untuk penerapan yang
sungguhan, dan buruk untuk peragaan yang harus siap seketika di depan juri.
Jenjang gratis pada layanan mana pun tidur setelah beberapa menit menganggur,
lalu butuh puluhan detik untuk bangun. Peragaan yang gagal karena peladennya
sedang bangun adalah kegagalan yang tidak perlu.

Jadi seluruh jawaban dipanggang lebih dulu. Yang penting, dipanggangnya dengan
memanggil peladen yang sama persis, lewat TestClient, lalu jawabannya disimpan
apa adanya. Tidak ada satu pun logika yang ditulis ulang di tempat lain,
sehingga tidak ada yang bisa menyimpang. Berkas statis ini benar benar
jawaban peladen, bukan tiruannya.

Yang hilang dari cara ini cuma satu, dan disebutkan terus terang: pemakai
hanya bisa memilih dari kombinasi pengaturan yang sudah dipanggang. Peladen
yang hidup menerima nilai apa pun, dan cara menjalankannya satu baris:

    uvicorn nalar.api.main:app

Jalankan:
    python scripts/panggang.py --keluaran ../nalar-web/public/data
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Kombinasi yang dipanggang. Sengaja sedikit dan bulat, supaya penggeser di
# layar terasa seperti pilihan kebijakan, bukan seperti kenop tanpa arti.
ALPHA = [0.005, 0.01, 0.02, 0.05, 0.10]
BIAYA = [250_000, 750_000, 1_500_000]
KAPASITAS = [50, 100, 250, 500]


def kunci(alpha, biaya, kapasitas) -> str:
    return f"{alpha}-{biaya}-{kapasitas}"


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--keluaran", default="runs/panggang")
    p.add_argument("--peserta", type=int, default=8000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--fktp", type=int, default=400)
    p.add_argument("--fkrtl", type=int, default=80)
    a = p.parse_args()

    from fastapi.testclient import TestClient

    from nalar.api import keadaan as _k

    _k.KEADAAN.__init__(
        n_peserta=a.peserta,
        tahun=a.tahun,
        seed=7,
        n_fktp=a.fktp,
        n_fkrtl=a.fkrtl,
    )
    from nalar.api.main import app

    os.makedirs(a.keluaran, exist_ok=True)
    t0 = time.time()

    with TestClient(app) as c:
        print(f"[1] peladen siap dalam {time.time() - t0:.0f} detik")

        ringkas: dict = {}
        antrean: dict = {}
        keadilan: dict = {}
        klaim: dict = {}
        penjelasan: dict = {}

        print("[2] memanggang antrean dan ringkasan")
        total = len(ALPHA) * len(BIAYA) * len(KAPASITAS)
        n = 0
        for al in ALPHA:
            for bi in BIAYA:
                for ka in KAPASITAS:
                    n += 1
                    par = {"alpha": al, "biaya_audit_rp": bi, "kapasitas": ka}
                    ringkas[kunci(al, bi, ka)] = c.get("/ringkas", params=par).json()
                    j = c.get(
                        "/antrean",
                        params={**par, "batas_per_faskes": 40, "porsi_acak": 0.05},
                    ).json()
                    antrean[kunci(al, bi, ka)] = j
                    for b in j["baris"]:
                        klaim.setdefault(b["penilaian"]["id"], b["penilaian"])
                    print(
                        f"    {n}/{total}  alpha {al} biaya {bi} kapasitas {ka}"
                        f"  terisi {j['terisi']}",
                        flush=True,
                    )

        print("[3] memanggang panel keadilan")
        for al in ALPHA:
            keadilan[str(al)] = c.get("/keadilan", params={"alpha": al}).json()

        print("[4] memanggang profil dan titik perubahan")
        profil = c.get("/profil", params={"atas": 25}).json()
        perubahan = {
            u: c.get("/perubahan", params={"batas_p": 0.05, "ukuran": u}).json()
            for u in ("posisi", "rupiah")
        }

        print(f"[5] memanggang penjelasan untuk {len(klaim)} klaim")
        for i, kid in enumerate(klaim, start=1):
            penjelasan[kid] = c.get(f"/klaim/{kid}/penjelasan").json()
            if i % 50 == 0:
                print(f"    {i}/{len(klaim)}", flush=True)

    # Antrean dipecah satu berkas per kombinasi. Disatukan, berkasnya 4,2
    # megabita, dan peramban harus mengunduh enam puluh kombinasi untuk
    # menampilkan satu. Bentuk tiap berkas tetap jawaban peladen apa adanya.
    os.makedirs(os.path.join(a.keluaran, "antrean"), exist_ok=True)
    besar = 0
    for k, v in antrean.items():
        j = os.path.join(a.keluaran, "antrean", f"{k}.json")
        with open(j, "w", encoding="utf-8") as f:
            json.dump(v, f, ensure_ascii=False, separators=(",", ":"))
        besar = max(besar, os.path.getsize(j))
    print(
        f"    antrean/          {len(antrean)} berkas, terbesar {besar / 1024:.1f} KB"
    )

    berkas = {
        "ringkas.json": ringkas,
        "keadilan.json": keadilan,
        "klaim.json": klaim,
        "penjelasan.json": penjelasan,
        "profil.json": profil,
        "perubahan.json": perubahan,
        "pilihan.json": {
            "alpha": ALPHA,
            "biaya_audit_rp": BIAYA,
            "kapasitas": KAPASITAS,
            "batas_per_faskes": 40,
            "porsi_acak": 0.05,
            "catatan": (
                "Jawaban ini dipanggang dari peladen yang sama, lewat "
                "TestClient, lalu disimpan apa adanya. Yang hilang hanya "
                "kebebasan memilih nilai di luar daftar ini. Peladen yang "
                "hidup menerima nilai apa pun: uvicorn nalar.api.main:app"
            ),
        },
    }

    print("[6] menulis")
    for nama, isi in berkas.items():
        jalur = os.path.join(a.keluaran, nama)
        with open(jalur, "w", encoding="utf-8") as f:
            json.dump(isi, f, ensure_ascii=False, separators=(",", ":"))
        kb = os.path.getsize(jalur) / 1024
        print(f"    {nama:18s} {kb:9.1f} KB")

    print(f"\nselesai dalam {time.time() - t0:.0f} detik, ke {a.keluaran}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
