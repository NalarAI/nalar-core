"""Alat yang membaca basis data harus menjawab sama dengan yang di memori.

Ini uji yang menuntut basis data hidup, jadi ia dilewati kalau kuncinya
tidak ada di lingkungan. Integrasi berkelanjutan tidak punya kuncinya, dan
itu memang benar: kunci layanan tidak boleh ada di sana.

Yang diperiksa kesamaan jawaban medan demi medan, bukan kesamaan bentuk.
Satu medan yang berbeda mengubah apa yang dilihat model, dan seluruh angka
yang sudah diukur pada lima ratus berkas jadi tidak berlaku lagi.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

lulus = gagal = 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


def baca_env() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL")
    kunci = os.environ.get("SUPABASE_SERVICE")
    if not (url and kunci):
        jalur = os.path.join(os.path.dirname(__file__), "..", "..", "rahasia", "gh.env")
        if os.path.exists(jalur):
            with open(jalur, encoding="utf-8") as f:
                for baris in f:
                    k, _, v = baris.strip().partition("=")
                    if k == "SUPABASE_URL" and not url:
                        url = v
                    if k == "SUPABASE_SERVICE" and not kunci:
                        kunci = v
    return url or "", kunci or ""


URL, KUNCI = baca_env()
if not (URL and KUNCI):
    print("\nDILEWATI, tidak ada kunci basis data di lingkungan ini")
    print("\n0 lulus, 0 gagal")
    sys.exit(0)

from nalar.agen.alat import Perkakas  # noqa: E402
from nalar.agen.alat_db import PerkakasBasisData, SumberBasisData  # noqa: E402
from nalar.agen.jejak import Jejak  # noqa: E402
from nalar.api.keadaan import Keadaan  # noqa: E402


def ambil(jalur: str):
    r = urllib.request.Request(f"{URL.rstrip('/')}/rest/v1/{jalur}", method="GET")
    for k, v in (
        ("apikey", KUNCI),
        ("Authorization", f"Bearer {KUNCI}"),
        ("Accept-Profile", "nalar"),
    ):
        r.add_header(k, v)
    with urllib.request.urlopen(r, timeout=30) as h:
        return json.load(h)


print("\n1. Menyiapkan keadaan peragaan")
# Angka angka ini harus sama dengan scripts/muat_db.py. Dunia yang berbeda
# memberi nomor berkas yang sama untuk klaim yang berbeda, dan bedanya tidak
# akan terlihat sampai ada yang membandingkan isinya.
K = Keadaan(n_peserta=8000, tahun=3, seed=7, n_fktp=400, n_fkrtl=80)
K.bangun(alpha=0.02)
ids = [r["klaim_id"] for r in ambil("perkara?select=klaim_id&limit=6")]
cek("ada berkas yang bisa diuji", len(ids) >= 3, str(len(ids)))

sumber = SumberBasisData(URL, KUNCI)
pm = Perkakas(K, Jejak(perkara="memori"))
pd = PerkakasBasisData(sumber, Jejak(perkara="basisdata"))

print("\n2. ambil_berkas menjawab sama")
beda_semua = []
for kid in ids:
    a = pm.panggil("ambil_berkas", id=kid)
    b = pd.panggil("ambil_berkas", id=kid)
    beda = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    if beda:
        beda_semua.append((kid, beda, {k: (a.get(k), b.get(k)) for k in beda}))
cek(
    f"{len(ids)} berkas sama medan demi medan",
    not beda_semua,
    str(beda_semua[:2]),
)

print("\n3. hitung_pengandaian menjawab sama")
beda_semua = []
for kid in ids:
    a = pm.panggil("hitung_pengandaian", id=kid)
    b = pd.panggil("hitung_pengandaian", id=kid)
    beda = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    if beda:
        beda_semua.append((kid, beda))
cek(
    f"{len(ids)} pengandaian sama medan demi medan",
    not beda_semua,
    str(beda_semua[:2]),
)

print("\n4. cari_tarif menjawab sama")
beda_semua = []
for kid in ids:
    r = pm.panggil("ambil_berkas", id=kid)
    arg = dict(
        kode=r["kelompok_tarif"],
        kelas_rawat=r["kelas_rawat"],
        kelas_rs=r["kelas_faskes"],
        regional=r["regional"],
    )
    try:
        a = pm.panggil("cari_tarif", **arg)
    except Exception:  # noqa: BLE001
        continue
    b = pd.panggil("cari_tarif", **arg)
    if a != b:
        beda_semua.append((kid, a, b))
cek("tarif yang dijawab sama", not beda_semua, str(beda_semua[:1]))

print("\n5. skor_ulang menolak dengan keterangan, bukan mengarang")
try:
    pd.panggil("skor_ulang", id=ids[0], bukti_tambahan=["HB"])
    cek("skor_ulang menolak", False, "justru menjawab")
except Exception as e:  # noqa: BLE001
    cek("skor_ulang menolak dengan sebab", "penebak tarif" in str(e), str(e)[:80])

print("\n6. Jejaknya tetap tercatat pada jalur basis data")
cek(
    "tiap pemanggilan masuk jejak",
    pd.jejak.ringkas()["n_panggilan"] >= len(ids) * 2,
    str(pd.jejak.ringkas()["n_panggilan"]),
)
cek("sidik rantainya berbentuk SHA-256", len(pd.jejak.ringkas()["sidik_akhir"]) == 64)

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
