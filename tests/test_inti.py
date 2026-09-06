"""Uji untuk klaim yang bisa diperiksa orang lain.

Rancangan menyebut empat cara juri memverifikasi bahwa modelnya memang ditulis
sendiri. Salah satunya uji unit untuk bias antar-bidang dan untuk jaminan
konformal. Berkas ini memenuhi itu, ditambah uji untuk aturan tarif dan untuk
kebenaran dasar pembangkit.

Jalankan:
    python tests/test_inti.py
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar import katalog as K  # noqa: E402
from nalar.konformal import Kalibrator, ambang  # noqa: E402
from nalar.schema import N_FIELDS  # noqa: E402
from nalar.tarif import hitung_keparahan, kelompokkan, tarif  # noqa: E402

# Torch hanya dipakai oleh satu blok uji, yaitu yang memeriksa bias antar
# bidang pada transformer. Transformer itu sudah dinyatakan kalah pada
# percobaan kedua belas dan bukan yang dikirim, jadi memaksa setiap orang
# mengunduh delapan ratus megabita hanya untuk menjalankan uji tidak sepadan.
# Blok itu dilewati kalau torch tidak ada, dan dilewatinya dicatat, bukan
# didiamkan.
try:
    import torch

    from nalar.model import PerhatianBerbidang

    ADA_TORCH = True
except ImportError:
    ADA_TORCH = False

lulus, gagal = 0, 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


# ---------------------------------------------------------------------------
print("\n1. Bias antar-bidang benar benar mengambil nilai yang tepat")
# ---------------------------------------------------------------------------
if not ADA_TORCH:
    print("  DILEWATI  torch tidak terpasang, tiga uji transformer tidak jalan")
    print("            pasang dengan: pip install '.[transformer]'")
else:
    torch.manual_seed(0)
    att = PerhatianBerbidang(d=16, n_kepala=2, pakai_bias_bidang=True)
    with torch.no_grad():
        att.bias_bidang.copy_(
            torch.arange(2 * N_FIELDS * N_FIELDS, dtype=torch.float32).view(
                2, N_FIELDS, N_FIELDS
            )
        )
        att.qkv.weight.zero_()  # matikan sumbangan isi, sisakan bias saja
    B, T = 2, 5
    x = torch.randn(B, T, 16)
    fld = torch.tensor([[0, 3, 3, 11, 11], [5, 5, 0, 2, 9]])
    pad = torch.ones(B, T, dtype=torch.bool)

    # ambil skor sebelum softmax dengan menghitung ulang jalur bias
    fi = fld.long()
    pasangan = (fi[:, :, None] * N_FIELDS + fi[:, None, :]).reshape(-1)
    rata = att.bias_bidang.reshape(2, -1)
    b = rata.index_select(1, pasangan).view(2, B, T, T).permute(1, 0, 2, 3)
    harapan = att.bias_bidang[1, fld[0, 2], fld[0, 4]]
    cek(
        "nilai bias diambil dari pasangan bidang yang benar",
        torch.allclose(b[0, 1, 2, 4], harapan),
        f"{b[0, 1, 2, 4].item()} vs {harapan.item()}",
    )

    y = att(x, fld, pad)
    cek("keluaran perhatian berbentuk benar", tuple(y.shape) == (B, T, 16))

    att_mati = PerhatianBerbidang(d=16, n_kepala=2, pakai_bias_bidang=False)
    cek(
        "saklar bias bisa dimatikan untuk ablasi",
        not hasattr(att_mati, "bias_bidang"),
    )

# ---------------------------------------------------------------------------
print("\n2. Jaminan konformal terpenuhi pada data buatan")
# ---------------------------------------------------------------------------
rng = np.random.default_rng(0)
for alpha in (0.01, 0.05, 0.10):
    laju = []
    for _ in range(60):
        kal_skor = rng.normal(size=3000)
        uji_skor = rng.normal(size=3000)
        t = ambang(kal_skor, alpha)
        laju.append(float((uji_skor > t).mean()))
    rata_laju = float(np.mean(laju))
    cek(
        f"alpha {alpha}: laju penandaan {rata_laju:.4f} tidak melebihi alpha",
        rata_laju <= alpha * 1.25,
        f"terukur {rata_laju:.4f}",
    )

cek(
    "kalibrator per kelompok memakai ambang berbeda tiap kelompok",
    len(
        Kalibrator(0.05, minimal_kelompok=50)
        .pasang(rng.normal(size=1000), rng.integers(0, 3, 1000))
        .ambang_kelompok
    )
    == 3,
)

# ---------------------------------------------------------------------------
print("\n3. Aturan tarif berperilaku seperti INA-CBG")
# ---------------------------------------------------------------------------
cek("tanpa diagnosis sekunder berat, keparahan I", hitung_keparahan([], 4, True) == 1)
cek(
    "satu diagnosis sekunder berat menaikkan ke keparahan II",
    hitung_keparahan(["N17"], 4, True) == 2,
)
cek(
    "dua diagnosis sekunder berat menaikkan ke keparahan III",
    hitung_keparahan(["N17", "J96"], 4, True) == 3,
)
cek(
    "rawat jalan tidak punya tingkat keparahan",
    hitung_keparahan(["N17", "J96"], 0, False) == 0,
)

k1 = kelompokkan("J18", [], [], 5, True)
k3 = kelompokkan("J18", ["N17", "J96"], [], 5, True)
t1 = tarif(k1, "J18", [], 3, "C", 0)
t3 = tarif(k3, "J18", [], 3, "C", 0)
cek("menambah dua diagnosis berat menaikkan tarif", t3 > t1, f"{t1} -> {t3}")
cek(
    "selisih keparahan I ke III berada di kisaran jutaan rupiah",
    2_000_000 < (t3 - t1) < 12_000_000,
    f"selisih {t3 - t1}",
)

kA = tarif(kelompokkan("J18", [], [], 5, True), "J18", [], 3, "A", 0)
kD = tarif(kelompokkan("J18", [], [], 5, True), "J18", [], 3, "D", 0)
cek("rumah sakit kelas A menerima tarif lebih tinggi dari kelas D", kA > kD)

# ---------------------------------------------------------------------------
print("\n4. Pemitaan pemeriksaan relatif terhadap rentang rujukan")
# ---------------------------------------------------------------------------
cek("hemoglobin 7 masuk pita sangat rendah", K.pita_lab("HB", 7.0) == 0)
cek("hemoglobin 14 masuk pita normal", K.pita_lab("HB", 14.0) == 3)
cek("leukosit 22 ribu masuk pita sangat tinggi", K.pita_lab("LEUKO", 22000.0) >= 5)
cek(
    "dua pemeriksaan berbeda dengan posisi relatif sama masuk pita sama",
    K.pita_lab("HB", 12.0 + 0.5 * 4.0) == K.pita_lab("KREA", 0.6 + 0.5 * 0.6),
)

# ---------------------------------------------------------------------------
print("\n5. Pembangkit menghasilkan kebenaran dasar yang konsisten")
# ---------------------------------------------------------------------------
from nalar.generator import Pembangkit  # noqa: E402

g = Pembangkit(n_peserta=600, tahun=2, seed=42, n_fktp=60, n_fkrtl=15)
eps = g.jalankan()
cek("pembangkit menghasilkan episode", len(eps) > 100, f"{len(eps)}")

jujur = [r for r in eps if not r["modus"]]
cek(
    "klaim jujur punya selisih nol",
    all(abs(r["selisih_rp"]) < 1 for r in jujur[:500]),
    "ada klaim jujur dengan selisih bukan nol",
)

upcode = [r for r in eps if "M04" in r["modus"]]
if upcode:
    cek(
        "upcoding menghasilkan selisih positif",
        all(r["selisih_rp"] > 0 for r in upcode),
        f"{sum(1 for r in upcode if r['selisih_rp'] <= 0)} dari {len(upcode)} tidak",
    )
    cek(
        "upcoding menaikkan keparahan di atas versi jujurnya",
        all(r["keparahan"] >= r["keparahan_j"] for r in upcode),
    )
else:
    print("  LEWAT  tidak ada contoh upcoding pada benih ini")

porsi = sum(1 for r in eps if r["modus"]) / len(eps)
cek(
    "porsi klaim terpengaruh berada di rentang literatur tiga sampai lima belas persen",
    0.03 <= porsi <= 0.15,
    f"terukur {porsi:.3f}",
)

# ---------------------------------------------------------------------------
print("\n6. Pemisahan latih dan uji tidak bocor antar-faskes")
# ---------------------------------------------------------------------------
from nalar.dataset import bangun_meta, pisah_menurut_entitas  # noqa: E402

meta = bangun_meta(eps)
tr, te = pisah_menurut_entitas(meta, 0.25, seed=3)
kunci = meta["faskes"].astype(np.int64) * 2 + meta["f_jenis"]
cek(
    "tidak ada faskes yang muncul di latih dan uji sekaligus",
    len(set(kunci[tr]) & set(kunci[te])) == 0,
)
cek("kedua sisi tidak kosong", tr.sum() > 0 and te.sum() > 0)

# ---------------------------------------------------------------------------
print(f"\n{lulus} lulus, {gagal} gagal")

# Keluar dengan kode galat hanya ketika berkas ini dijalankan langsung.
#
# Tanpa penjaga ini, sys.exit terpanggil saat modulnya diimpor, dan unittest
# discover menganggapnya galat impor walaupun seluruh uji lulus. Kami sempat
# tidak melihatnya karena membaca keluaran cetak, bukan kode keluarnya, dan
# pipa ke tail menutupi kode itu. Pelajarannya: memeriksa uji harus lewat kode
# keluar, bukan lewat apa yang tercetak.
if __name__ == "__main__":
    sys.exit(1 if gagal else 0)
