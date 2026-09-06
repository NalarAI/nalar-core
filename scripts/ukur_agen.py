"""Mengukur lapisan agen dengan model bahasa sungguhan, bukan penutur tiruan.

Uji di tests/test_agen_dua.py memakai penutur bernaskah, dan itu memang
tugasnya: memastikan lingkaran, penyelia, dan penjaganya benar sebelum satu
bobot pun dipasang. Yang tidak bisa dijawab uji itu satu pertanyaan, dan
justru pertanyaan yang menentukan: apakah model berbobot terbuka yang muat
di dalam pusat data benar benar patuh.

Skrip ini yang menjawabnya. Yang dilaporkan empat angka yang bisa salah.

A1, cacah angka pada berkas perkara yang tidak berasal dari pemanggilan
alat. Ambangnya nol, dan nol yang dimaksud benar benar nol.

Laju mundur, bagian berkas yang gagal disusun agen sehingga keluar versi
aturan. Ini bukan kegagalan sistem, tapi kalau angkanya tinggi berarti
lapisan agennya belum menghemat pekerjaan siapa pun.

Cacat pemeriksaan dalam, dipakai menera gerbang layak kirim. Separuh berkas
dipakai menera, separuh sisanya dipakai menilai, dan yang dilaporkan hasil
pada separuh yang tidak dipakai menera.

A7, biaya token per berkas, dibanding ongkos periksa manual Rp 750 ribu.

Butuh peladen model setempat yang bicara dengan tata cara OpenAI. Contoh
yang dipakai mengembangkan ini Ollama dengan Qwen3 4B:

    ollama pull qwen3:4b
    ollama create nalar-qwen3-4b -f peladen/Modelfile.qwen3-4b
    python scripts/ukur_agen.py --n 40

Jalankan:
    python scripts/ukur_agen.py [--n 40] [--model qwen3:4b] [--delta 0.05]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

# Baris demi baris, bukan ditahan sampai selesai. Sekali jalan bisa makan
# puluhan menit, dan laporan yang baru muncul di akhir tidak bisa dipakai
# memutuskan apakah jalannya perlu dihentikan lebih awal.
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar.agen import Gerbang, PenuturSetempat, susun_agen, tera  # noqa: E402
from nalar.api.keadaan import Keadaan  # noqa: E402


def ukur(n: int, model: str, alamat: str | None, delta: float) -> dict:
    penutur = PenuturSetempat(alamat=alamat, model=model)
    if not penutur.hidup():
        print(f"Peladen model tidak menyala di {penutur.alamat}.")
        print("Nyalakan lebih dulu, misalnya dengan: ollama serve")
        sys.exit(2)

    print(f"Model {penutur.model} di {penutur.alamat}")
    print("Menyiapkan keadaan, ini memakan waktu sekitar satu menit.")
    K = Keadaan(n_peserta=1500, tahun=2, seed=7, n_fktp=90, n_fkrtl=24)
    K.bangun(alpha=0.02)
    urut = [K.id_klaim(int(i)) for i in K.urutan[:n]]
    print(f"{len(urut)} berkas, urut dari selisih terbesar.\n")

    baris = []
    t0 = time.time()
    for k, id_berkas in enumerate(urut, 1):
        mulai = time.time()
        h = susun_agen(K, id_berkas, penutur=penutur, dalam=True)
        detik = time.time() - mulai
        d = h.get("dalam") or {"lulus": True, "cacat": []}
        baris.append(
            {
                "id": id_berkas,
                "sumber": h["sumber"],
                "sebab_mundur": h["sebab_mundur"],
                "skor": h["skor"],
                "cacat": d["cacat"],
                # Cacat yang menjatuhkan berkas di saringan cepat. Tanpa
                # ini laporan hanya bilang berapa yang mundur, dan tidak
                # bilang kenapa, sehingga tidak ada yang bisa diperbaiki.
                "cacat_saringan": h["cacat"],
                "n_cacat": len(d["cacat"]),
                "a1": [c for c in d["cacat"] if c.get("jenis") == "a1"],
                "biaya_rp": h["penyelia"]["biaya_rp"],
                "token_masuk": h["penyelia"]["token_masuk"],
                "token_keluar": h["penyelia"]["token_keluar"],
                "panggilan_alat": h["penyelia"]["panggilan_alat"],
                "detik": round(detik, 2),
                "n_kata": len(h["teks"].split()),
            }
        )
        tanda = "agen  " if h["sumber"] == "agen" else "aturan"
        catatan = "bersih" if not d["cacat"] else f"{len(d['cacat'])} cacat"
        print(
            f"  {k:3d}/{len(urut)}  {id_berkas}  {tanda}  {catatan:10s} "
            f"Rp {h['penyelia']['biaya_rp']:7.2f}  {detik:5.1f}s"
        )

    return {
        "model": penutur.model,
        "n": len(urut),
        "delta": delta,
        "detik_total": round(time.time() - t0, 1),
        "baris": baris,
    }


def laporkan(hasil: dict) -> None:
    baris = hasil["baris"]
    n = len(baris)
    agen = [b for b in baris if b["sumber"] == "agen"]
    mundur = [b for b in baris if b["sumber"] == "aturan"]

    print("\n" + "=" * 68)
    print(f"Model {hasil['model']}, {n} berkas, {hasil['detik_total']:.0f} detik")
    print("=" * 68)

    n_a1 = sum(len(b["a1"]) for b in agen)
    print(f"\nA1  angka tak bersumber pada berkas susunan agen : {n_a1}")
    print(f"    berkas yang disusun agen                     : {len(agen)}/{n}")
    print(f"    berkas yang mundur ke versi aturan           : {len(mundur)}/{n}")

    sebab: dict[str, int] = {}
    for b in mundur:
        kunci = b["sebab_mundur"].split(":")[0]
        for c in b.get("cacat_saringan") or []:
            kunci = f"{kunci}, {c['jenis']}"
            break
        sebab[kunci] = sebab.get(kunci, 0) + 1
    for s, c in sorted(sebab.items(), key=lambda x: -x[1]):
        print(f"      {c:3d}  {s}")

    if agen:
        rp = sum(b["biaya_rp"] for b in agen) / len(agen)
        tk = sum(b["token_keluar"] for b in agen) / len(agen)
        detik = sum(b["detik"] for b in agen) / len(agen)
        print(f"\nA7  biaya rata rata per berkas                   : Rp {rp:.2f}")
        print(f"    bagian dari ongkos periksa Rp 750 ribu       : {rp / 750000:.5%}")
        print(f"    token keluaran rata rata                     : {tk:.0f}")
        print(f"    lama rata rata                               : {detik:.1f} detik")

    # Gerbang ditera pada separuh pertama, dinilai pada separuh kedua. Menera
    # dan menilai pada berkas yang sama akan melaporkan angka yang lebih
    # bagus daripada yang akan terjadi, dan itu bentuk kebohongan yang paling
    # mudah dilakukan tanpa sengaja.
    kal = agen[: len(agen) // 2]
    nilai = agen[len(agen) // 2 :]
    if len(kal) >= 8 and nilai:
        t = tera(
            [b["skor"] for b in kal],
            [b["n_cacat"] > 0 for b in kal],
            delta=hasil["delta"],
        )
        g = Gerbang(ambang=t["ambang"], delta=hasil["delta"], n_kalibrasi=t["n"])
        kirim = [b for b in nilai if g.putuskan(b["skor"]) == "layak_kirim"]
        cacat_kirim = sum(1 for b in kirim if b["n_cacat"] > 0)
        print(f"\nGerbang layak kirim, delta {hasil['delta']}")
        print(f"    ambang hasil tera                            : {t['ambang']}")
        print(f"    ditera pada                                  : {len(kal)} berkas")
        print(f"    dinilai pada                                 : {len(nilai)} berkas")
        print(f"    yang layak kirim                             : {len(kirim)}")
        print(f"    di antaranya bercacat                        : {cacat_kirim}")
        hasil["gerbang"] = {**t, "n_nilai": len(nilai), "cacat_kirim": cacat_kirim}

    jenis: dict[str, int] = {}
    for b in agen:
        for c in b["cacat"]:
            jenis[c["jenis"]] = jenis.get(c["jenis"], 0) + 1
    if jenis:
        print("\nCacat pemeriksaan dalam, menurut jenis")
        for j, c in sorted(jenis.items(), key=lambda x: -x[1]):
            print(f"      {c:3d}  {j}")
    else:
        print("\nTidak ada cacat pemeriksaan dalam pada berkas susunan agen.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--model", default=os.environ.get("NALAR_MODEL", "nalar-qwen3-4b"))
    p.add_argument("--alamat", default=os.environ.get("NALAR_MODEL_URL"))
    p.add_argument("--delta", type=float, default=0.05)
    p.add_argument("--keluar", default="runs/ukur_agen.json")
    a = p.parse_args()

    hasil = ukur(a.n, a.model, a.alamat, a.delta)
    laporkan(hasil)

    os.makedirs(os.path.dirname(a.keluar) or ".", exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)
    print(f"\nRinciannya di {a.keluar}")


if __name__ == "__main__":
    main()
