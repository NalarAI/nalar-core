"""Agen Lawan melawan detektor yang benar benar dikirim.

Menjawab satu pertanyaan yang tidak bisa dijawab pengujian sebelumnya: apakah
ada siasat penghindaran yang tidak terpikir oleh kami. Ketiga pelaku yang
dipakai mengukur T6 kami tulis sendiri, dan ketiganya memakai satu modus saja.
Menulis pelaku keempat buatan sendiri hanya memindahkan batasnya.

Tiga hal diadu, dan urutannya penting.

Pertama, tiga pelaku baku. Ini yang dipakai melaporkan T6 selama ini, ditulis
ulang dalam bahasa siasat supaya bisa diadu setara.

Kedua, pencarian menyeluruh tanpa model bahasa. Ruang siasatnya kecil dan bisa
ditelusuri habis, dan hasilnya jadi garis dasar kedua. Agen yang tidak
mengalahkan pencarian biasa tidak sedang merancang apa pun.

Ketiga, Agen Lawan. Model bahasa membaca uraian cara kerja detektor, tanpa
satu pun angka dari berkas, lalu menyusun siasat.

Yang dilaporkan siasat yang menang di dua himpunan sekaligus: himpunan tempat
ia ditemukan, dan himpunan yang tidak pernah dilihat selama pencarian. Menang
di satu himpunan saja tidak dihitung.

Jalankan:
    python scripts/agen_lawan.py [--peserta 20000] [--model nalar-qwen3-4b]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np  # noqa: E402

from nalar.agen import lawan  # noqa: E402
from nalar.agen.penutur import PenuturSetempat  # noqa: E402
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402
from nalar.detektor import Detektor  # noqa: E402
from nalar.generator import Pembangkit  # noqa: E402


def jt(x) -> str:
    return f"{(x or 0) / 1e6:8.1f} jt"


def siapkan(n_peserta: int, tahun: int, seed: int):
    print("[1] membangkitkan data dan melatih detektor yang dikirim")
    t = time.time()
    g = Pembangkit(n_peserta=n_peserta, tahun=tahun, seed=seed, n_fktp=900, n_fkrtl=150)
    eps = g.jalankan()
    meta = bangun_meta(eps)
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=seed)
    itr, ite = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    rng = np.random.default_rng(seed)
    rng.shuffle(itr)
    nk = min(20000, len(itr) // 3)
    det = Detektor(alpha=0.02, seed=seed)
    det.latih([eps[i] for i in itr[nk:]]).kalibrasi([eps[i] for i in itr[:nk]])
    print(f"    {len(eps)} episode, {len(ite)} masuk uji, {time.time() - t:.0f} detik")

    # Ambang dan keadaan menahan diri diambil sekali, sebelum satu serangan
    # pun. Menghitungnya ulang pada berkas yang sudah diserang akan
    # menggeser ambangnya mengikuti serangan, dan pelakunya akan terlihat
    # lebih sering tertangkap daripada yang sebenarnya.
    amb = np.full(len(eps), np.inf)
    tahan = np.ones(len(eps), dtype=bool)
    a_te, t_te = det.ambang_untuk([eps[i] for i in ite])
    amb[ite] = a_te
    tahan[ite] = t_te

    def penskor(daftar):
        return det.skor(daftar)["selisih"]

    # Himpunan uji dibelah dua menurut faskes, bukan menurut berkas. Membelah
    # menurut berkas akan menaruh berkas dari rumah sakit yang sama di kedua
    # sisi, dan siasat yang cuma cocok untuk satu rumah sakit akan terlihat
    # sahih di sisi seberang.
    faskes = np.array([(int(eps[i]["f_jenis"]), int(eps[i]["faskes"])) for i in ite])
    kunci = np.array([hash(tuple(x)) % 2 for x in faskes])
    temu = ite[kunci == 0]
    sahih = ite[kunci == 1]
    print(f"    penemuan {len(temu)} berkas, pengesahan {len(sahih)} berkas")
    return eps, temu, sahih, penskor, amb, tahan


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=20000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument("--klaim", type=int, default=400)
    p.add_argument("--cari", type=int, default=120)
    p.add_argument("--giliran", type=int, default=12)
    p.add_argument("--model", default=os.environ.get("NALAR_MODEL", "nalar-qwen3-4b"))
    p.add_argument("--keluar", default="runs/agen_lawan.json")
    a = p.parse_args()

    eps, temu, sahih, penskor, amb, tahan = siapkan(a.peserta, a.tahun, a.benih)
    g = lawan.Gelanggang(eps, temu, sahih, penskor, amb, tahan, maks_klaim=a.klaim)

    print("\n[2] tiga pelaku baku, yang dipakai melaporkan T6 selama ini")
    for b in g.dasar_temu["baris"]:
        print(
            f"    {b['nama']:10s} diserang {b.get('n_diserang', 0):4d}  "
            f"diambil {jt(b.get('diambil_rp'))}  lolos {jt(b.get('lolos_rp'))}  "
            f"maks {jt(b.get('maks_per_klaim_rp'))}  "
            f"tertangkap {b.get('porsi_tertangkap')}"
        )
    print(
        f"    terbaik {g.dasar_temu['nama_terbaik']}, "
        f"lolos {jt(g.dasar_temu['lolos_terbaik_rp'])}"
    )

    print(f"\n[3] pencarian menyeluruh tanpa model bahasa, {a.cari} siasat")
    t = time.time()
    cari = lawan.cari_menyeluruh(g, batas=a.cari)
    print(f"    selesai dalam {time.time() - t:.0f} detik")
    for b in cari[:5]:
        s = b["siasat"]
        print(
            f"    {s['nama']:8s} {s['sasaran']['jenis']:22s} "
            f"{'+'.join(x['jenis'] for x in s['gerakan']):42s} "
            f"{s['pilihan']['jenis']:28s} lolos {jt(b['temu'].get('lolos_rp'))}"
        )
    menang_cari = [b for b in cari if b["temu"].get("mengalahkan_garis_dasar")]
    sah_cari, teduh_cari = [], []
    for b in cari:
        h = g.sahihkan(b["siasat"])
        satu = {"siasat": b["siasat"], "temu": b["temu"], "sahih": h}
        if lawan.bertahan(b["temu"], h):
            sah_cari.append(satu)
        elif lawan.tak_pernah_tertangkap(b["temu"], h):
            teduh_cari.append(satu)
    sah_cari = lawan.sisakan_yang_berbeda(sah_cari)
    teduh_cari = lawan.sisakan_yang_berbeda(teduh_cari)
    print(
        f"    {len(menang_cari)} mengalahkan garis dasar di himpunan penemuan, "
        f"{len(sah_cari)} bertahan di himpunan pengesahan"
    )

    print("\n[4] Agen Lawan")
    penutur = PenuturSetempat(model=a.model)
    if not penutur.hidup():
        print(f"    peladen model tidak menyala di {penutur.alamat}, dilewati")
        hasil_agen = {"sumber": "model mati", "temuan": [], "dicoba": 0}
    else:
        t = time.time()
        hasil_agen = lawan.jalankan(g, penutur=penutur, n_giliran=a.giliran)
        print(
            f"    {hasil_agen.get('dicoba', 0)} siasat dicoba dalam "
            f"{time.time() - t:.0f} detik, "
            f"biaya Rp {hasil_agen.get('penyelia', {}).get('biaya_rp', 0):.2f}"
        )
        if hasil_agen.get("sebab_berhenti"):
            print(f"    berhenti karena: {hasil_agen['sebab_berhenti']}")
        for b in hasil_agen.get("temuan", [])[:5]:
            s = b["siasat"]
            print(
                f"    {s['nama'][:22]:22s} "
                f"{'+'.join(x['jenis'] for x in s['gerakan']):42s} "
                f"lolos {jt(b['sahih'].get('lolos_rp'))} pada pengesahan"
            )

    print("\n[5] menilai target A4")
    # A4 berbunyi sekurangnya tiga siasat penghindaran baru yang bisa
    # diulang. Yang dihitung siasat yang mengalahkan garis dasar di kedua
    # himpunan sekaligus, dan yang tandanya berbeda satu sama lain.
    baru = lawan.sisakan_yang_berbeda(sah_cari + hasil_agen.get("temuan", []))
    print(
        f"    siasat yang tidak pernah tertangkap sama sekali: {len(teduh_cari)}"
        "  (dilaporkan terpisah, tidak dihitung A4)"
    )
    for b in teduh_cari[:4]:
        s2 = b["siasat"]
        print(
            f"      {s2['sasaran']['jenis']:22s} "
            f"{'+'.join(x['jenis'] for x in s2['gerakan']):40s} "
            f"lolos {jt(b['sahih'].get('lolos_rp'))}"
        )
    print(f"    siasat baru yang bertahan di dua himpunan: {len(baru)}")
    print(f"    A4 tercapai: {len(baru) >= 3}")
    for b in baru[:6]:
        s = b["siasat"]
        lebih = b["sahih"].get("lebih_jumlah_rp", 0)
        print(
            f"      {s['nama'][:20]:20s} lolos {jt(b['sahih'].get('lolos_rp'))} "
            f"lebih {jt(lebih)} jumlah, {jt(b['sahih'].get('lebih_maks_rp', 0))} maks"
        )

    catatan = {
        "pengaturan": vars(a),
        "garis_dasar_penemuan": g.dasar_temu,
        "garis_dasar_pengesahan": g.dasar_sahih,
        "pencarian": [{"siasat": b["siasat"], "temu": b["temu"]} for b in cari[:20]],
        "agen": hasil_agen,
        "siasat_baru": baru,
        "tak_pernah_tertangkap": teduh_cari,
        "A4": {"n": len(baru), "batas": 3, "lulus": len(baru) >= 3},
    }
    os.makedirs(os.path.dirname(a.keluar) or ".", exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(catatan, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nRinciannya di {a.keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
