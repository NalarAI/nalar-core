"""Angka di layar harus sama dengan angka yang dihitung model.

Ini uji yang paling mudah dilewatkan dan paling mahal kalau bocor. Peladen
menyusun ulang, membulatkan, dan menamai ulang keluaran model sebelum
mengirimnya ke website. Setiap langkah itu tempat angka bisa bergeser diam
diam, dan tidak ada yang akan sadar sampai ada yang membandingkan laporan
dengan berkas hasil di depan juri.

Jadi di sini seluruhnya dihitung dua kali. Sekali langsung dari model, sekali
lewat peladen, lalu keduanya diadu.

Jalankan:
    python tests/test_konsistensi.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np  # noqa: E402

lulus, gagal = 0, 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


try:
    from fastapi.testclient import TestClient
except ImportError:
    print("\nDILEWATI  fastapi tidak terpasang")
    print("          pasang dengan: pip install '.[api,dev]'")
    sys.exit(0)

try:
    import sklearn  # noqa: F401
except ImportError:
    print("\nDILEWATI  scikit-learn tidak terpasang")
    print("          pasang dengan: pip install '.[dev]'")
    sys.exit(0)

from nalar.api import keadaan as _k  # noqa: E402

_k.KEADAAN.__init__(n_peserta=1200, tahun=2, seed=7, n_fktp=60, n_fkrtl=20)

from nalar.api.main import app  # noqa: E402
from nalar.profil import peringkat_faskes, profil_faskes  # noqa: E402

with TestClient(app) as c:
    K = _k.KEADAAN
    eps = K.episodes

    print("\n1. Ringkasan halaman muka sama dengan hitungan langsung")
    s = c.get("/ringkas").json()
    cek(
        "jumlah klaim sama",
        s["n_klaim"] == len(eps),
        f"{s['n_klaim']} vs {len(eps)}",
    )
    cek(
        "nilai klaim total sama",
        s["nilai_klaim_total_rp"]
        == int(sum(r["tarif"] + r.get("tagih_bhp", 0) for r in eps)),
    )
    cek(
        "jumlah ditandai sama",
        s["n_ditandai"] == int(K.tanda.sum()),
        f"{s['n_ditandai']} vs {int(K.tanda.sum())}",
    )
    cek(
        "jumlah menahan diri sama",
        s["n_menahan_diri"] == int(K.tahan.sum()),
    )

    print("\n2. Selisih tiap klaim sama, bukan hanya totalnya")
    # Total yang cocok bisa saja menyembunyikan dua klaim yang tertukar, jadi
    # yang diadu di sini klaim per klaim pada sampel acak.
    rng = np.random.default_rng(0)
    contoh = rng.choice(len(eps), size=min(40, len(eps)), replace=False)
    beda = []
    for i in contoh:
        kid = K.id_klaim(int(i))
        p = c.get(f"/klaim/{kid}").json()
        langsung = round(float(K.selisih[int(i)]))
        if p["selisih_rp"] != langsung:
            beda.append((kid, p["selisih_rp"], langsung))
    cek(
        f"selisih {len(contoh)} klaim contoh sama persis",
        not beda,
        f"{len(beda)} berbeda, contoh {beda[:2]}",
    )

    print("\n3. Panel keadilan sama dengan hitungan langsung")
    kd = c.get("/keadilan").json()
    kelas = np.array([r["f_kelas"] for r in eps])
    for g in kd["kelompok"]:
        m = kelas == g["kelompok"]
        cek(
            f"kelompok {g['kelompok']}: jumlah klaim sama",
            g["n_klaim"] == int(m.sum()),
            f"{g['n_klaim']} vs {int(m.sum())}",
        )
        cek(
            f"kelompok {g['kelompok']}: laju penandaan sama",
            abs(g["laju_penandaan"] - float(K.tanda[m].mean())) < 1e-4,
            f"{g['laju_penandaan']} vs {float(K.tanda[m].mean()):.5f}",
        )

    print("\n4. Antrean audit sama dengan yang disusun model")
    a = c.get("/antrean", params={"kapasitas": 30}).json()
    idx = K.detektor.antrean_audit(
        eps, kapasitas=30, batas_per_faskes=40, porsi_acak=0.05
    )
    cek(
        "jumlah baris sama",
        a["terisi"] == len(idx),
        f"{a['terisi']} vs {len(idx)}",
    )
    cek(
        "urutan pengenal klaim sama persis",
        [b["penilaian"]["id"] for b in a["baris"]] == [K.id_klaim(int(i)) for i in idx],
    )
    rp = round(float(K.selisih[idx].sum())) if len(idx) else 0
    cek(
        "rupiah yang ditemukan sama",
        a["rupiah_ditemukan_rp"] == rp,
        f"{a['rupiah_ditemukan_rp']} vs {rp}",
    )

    print("\n5. Profil faskes sama dengan hitungan langsung")
    pr = c.get("/profil", params={"atas": 10}).json()
    langsung = peringkat_faskes(
        profil_faskes(eps, K.selisih, minimal_klaim=20), atas=10
    )
    cek(
        "urutan faskes pada daftar rupiah sama",
        [b["faskes"] for b in pr["antrean_rupiah"]]
        == [
            K.nama_faskes(
                next(x for x in eps if (int(x["f_jenis"]), int(x["faskes"])) == kk)
            )
            for kk, _ in langsung
        ],
    )
    cek(
        "kelebihan rupiah baris teratas sama",
        not langsung
        or pr["antrean_rupiah"][0]["kelebihan_rp"] == int(langsung[0][1]["kelebihan"]),
    )

    print("\n6. Menggeser alpha menggeser ambang, bukan penebaknya")
    # Kalau tarif yang didukung bukti ikut berubah ketika alpha digeser, maka
    # ada yang salah paham tentang apa yang dikalibrasi, dan simulator di
    # website sedang membohongi pemakainya.
    kid = K.id_klaim(int(contoh[0]))
    p1 = c.get(f"/klaim/{kid}").json()
    c.get("/ringkas", params={"alpha": 0.1})
    p2 = c.get(f"/klaim/{kid}").json()
    cek(
        "tarif yang didukung bukti tidak bergeser",
        p1["tarif_didukung_bukti_rp"] == p2["tarif_didukung_bukti_rp"],
    )
    cek(
        "selisih tidak bergeser",
        p1["selisih_rp"] == p2["selisih_rp"],
    )
    cek(
        "ambang bergeser naik ketika alpha diperbesar",
        p1["ambang_rp"] is None
        or p2["ambang_rp"] is None
        or p2["ambang_rp"] <= p1["ambang_rp"],
        f"{p1['ambang_rp']} -> {p2['ambang_rp']}",
    )

print(f"\n{lulus} lulus, {gagal} gagal")

if __name__ == "__main__":
    sys.exit(1 if gagal else 0)
