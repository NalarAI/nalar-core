"""Menaruh berkas perkara susunan agen ke basis data peragaan.

Peragaan yang dilihat pengunjung membaca Supabase, bukan peladen Python,
karena tidak ada mesin yang menyalakan model bahasa dua puluh empat jam.
Akibatnya seluruh berkas perkara di sana versi aturan, dan pengunjung tidak
pernah melihat satu pun keluaran agen.

Skrip ini menutup jarak itu tanpa berbohong. Berkas perkaranya benar benar
disusun Agen Berkas dengan model berbobot terbuka di mesin ini, lengkap
dengan jejak alat dan sidik rantainya, lalu disimpan apa adanya. Yang
dilihat pengunjung keluaran agen sungguhan, cuma disusunnya lebih dulu.

Medan sumber pada tabelnya menyebut mana yang mana, dan layar klaim
menampilkannya. Berkas yang jatuh di saringan tetap tersimpan sebagai versi
aturan, karena itu memang keluaran yang sah.

Yang dipilih berkas dengan selisih terbesar, karena itu yang paling dulu
dibuka pengunjung pada antrean.

Jalankan:
    python scripts/muat_perkara_agen.py --n 60
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# muat_db yang menyetel aliran keluaran, dan menyetelnya dua kali menutup
# yang pertama. Berkas ini menumpang punyanya.

from muat_db import Db, baca_env  # noqa: E402
from nalar.agen import PenuturSetempat, susun_agen  # noqa: E402
from nalar.api.keadaan import Keadaan  # noqa: E402


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    # Angka angka ini harus sama persis dengan scripts/muat_db.py. Dunia yang
    # berbeda menghasilkan nomor berkas yang berbeda, dan barisnya akan
    # tersimpan sebagai berkas perkara untuk klaim yang tidak ada di peragaan.
    # Itu benar benar terjadi sekali, dan penjaga di bawah yang menangkapnya.
    p.add_argument("--n", type=int, default=60)
    p.add_argument("--peserta", type=int, default=8000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--fktp", type=int, default=400)
    p.add_argument("--fkrtl", type=int, default=80)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--model", default=os.environ.get("NALAR_MODEL", "nalar-qwen3-4b"))
    p.add_argument("--kirim", action="store_true", help="Tulis ke basis data.")
    a = p.parse_args()

    penutur = PenuturSetempat(model=a.model)
    if not penutur.hidup():
        print(f"Peladen model tidak menyala di {penutur.alamat}.")
        return 2

    print("Menyiapkan keadaan, sekitar satu menit.")
    K = Keadaan(
        n_peserta=a.peserta,
        tahun=a.tahun,
        seed=a.benih,
        n_fktp=a.fktp,
        n_fkrtl=a.fkrtl,
    )
    K.bangun(alpha=0.02)
    urut = [K.id_klaim(int(i)) for i in K.urutan[: a.n]]
    print(f"{len(urut)} berkas, urut dari selisih terbesar.\n")

    baris, n_agen = [], 0
    t0 = time.time()
    for k, kid in enumerate(urut, 1):
        h = susun_agen(K, kid, penutur=penutur)
        r = h["ringkas_jejak"]
        agen = h["sumber"] == "agen"
        n_agen += int(agen)
        baris.append(
            {
                "klaim_id": kid,
                "teks": h["teks"],
                "sumber": h["sumber"],
                "n_panggilan": r["n_panggilan"],
                "alat": r["alat"],
                "sidik_akhir": r["sidik_akhir"],
                "a1_lulus": bool(h["a1"]["lulus"]),
            }
        )
        print(
            f"  {k:3d}/{len(urut)}  {kid}  {h['sumber']:6s}  "
            f"{r['n_panggilan']} alat  {h['sebab_mundur'][:40]}"
        )

    print(f"\n{n_agen}/{len(urut)} disusun agen, {time.time() - t0:.0f} detik")

    if not a.kirim:
        print("Tidak dikirim. Tambahkan --kirim untuk menulis ke basis data.")
        return 0

    url, kunci = baca_env()
    db = Db(url, kunci)

    # Penjaga dunia. Tiap klaim peragaan sudah punya barisnya sendiri di
    # tabel ini, dimuat scripts/muat_db.py. Kalau nomor yang kita susun tidak
    # ada di sana, dunianya beda, dan menulis tetap akan menaruh berkas
    # perkara untuk klaim yang tidak pernah bisa dibuka pengunjung.
    daftar = ",".join(b["klaim_id"] for b in baris)
    ada = json.loads(
        db._panggil("GET", f"perkara?klaim_id=in.({daftar})&select=klaim_id").decode()
    )
    punya = {r["klaim_id"] for r in ada}
    hilang = [b["klaim_id"] for b in baris if b["klaim_id"] not in punya]
    if hilang:
        print(
            f"Berhenti. {len(hilang)} nomor tidak ada di basis data peragaan, "
            f"contohnya {hilang[:3]}."
        )
        print("Samakan --peserta, --tahun, --fktp, dan --fkrtl dengan muat_db.py.")
        return 2
    # Kunci utamanya klaim_id, jadi baris lama ditimpa. Yang ditimpa versi
    # aturan berkas yang sama, dan versi aturan bisa dibuat ulang kapan saja
    # tanpa model bahasa.
    db._panggil(
        "POST",
        "perkara",
        baris,
        {"Prefer": "resolution=merge-duplicates,return=minimal"},
    )
    print(f"{len(baris)} baris ditulis ke nalar.perkara")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
