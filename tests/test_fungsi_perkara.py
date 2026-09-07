"""Paket agen yang disalin ke fungsi tanpa peladen harus sama dan tertutup.

Tiga hal diperiksa di sini, dan ketiganya menangkap kegagalan yang berbeda.

Pertama, tiap berkas sama bita demi bita dengan yang dihasilkan sumbernya.
Itu menangkap suntingan tangan pada salinan, yang selalu menggoda karena
salinannya kelihatan seperti kode biasa.

Kedua, rantai impornya tertutup. Tiap modul yang disebut ada di dalam paket
yang sama. Modul yang hilang tidak akan ketahuan dari perbandingan bita,
karena kedua sisi sama sama tidak menyebutnya, dan yang terjadi kegagalan
pemanggilan dingin di produksi.

Ketiga, tidak ada satu pun yang menarik pustaka berat. numpy dan sklearn
menambah puluhan megabita, dan fungsi tanpa peladen menghitung tiap megabita
sebagai lama pemanggilan dingin. Yang satu ini gampang bocor: cukup satu
impor baru di nalar-core, dan salinannya ikut membawanya tanpa ada yang
melihat.

Modelnya tidak dipanggil dan basis datanya tidak disentuh. Yang diuji
bentuknya, dan bentuknya bisa diperiksa tanpa jaringan.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys

AKAR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API = os.path.join(AKAR, "..", "nalar-web", "api")
PAKET = os.path.join(API, "_nalar")

lulus = gagal = 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


print("\n1. Berkas hasil sama dengan sumbernya")
if not os.path.isdir(API):
    print("         DILEWATI, nalar-web tidak ada di sebelah repositori ini")
    print(f"\n{lulus} lulus, {gagal} gagal")
    sys.exit(0)

r = subprocess.run(
    [
        sys.executable,
        os.path.join(AKAR, "scripts", "buat_fungsi_perkara.py"),
        "--periksa",
    ],
    capture_output=True,
    text=True,
)
cek(
    "hasilnya sama dengan yang dihasilkan sumbernya",
    r.returncode == 0,
    r.stdout.strip(),
)

print("\n2. Rantai impornya tertutup di dalam paket")
ada = {n[:-3] for n in os.listdir(PAKET) if n.endswith(".py") and n != "__init__.py"}
cek("paketnya berisi modul", len(ada) >= 10, str(len(ada)))

hilang = []
berat = []
PUSTAKA_BERAT = {"numpy", "sklearn", "pandas", "scipy", "torch", "matplotlib"}

for nama in sorted(ada) + ["__init__"]:
    jalur = os.path.join(PAKET, nama + ".py")
    with open(jalur, encoding="utf-8") as f:
        pohon = ast.parse(f.read(), filename=jalur)
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ImportFrom):
            # Impor nisbi satu titik menunjuk sesama modul di paket ini.
            if simpul.level == 1:
                # "from . import aturan" tidak punya module, namanya di names.
                sebut = (
                    [simpul.module] if simpul.module else [a.name for a in simpul.names]
                )
                for s in sebut:
                    if s not in ada:
                        hilang.append(f"{nama} menyebut {s}")
            elif simpul.level > 1:
                hilang.append(f"{nama} naik {simpul.level} tingkat, paketnya datar")
            elif simpul.module and simpul.module.split(".")[0] in PUSTAKA_BERAT:
                berat.append(f"{nama} menarik {simpul.module}")
        elif isinstance(simpul, ast.Import):
            for a in simpul.names:
                if a.name.split(".")[0] in PUSTAKA_BERAT:
                    berat.append(f"{nama} menarik {a.name}")

cek("tiap modul yang disebut ada di paketnya", not hilang, "; ".join(hilang[:3]))

print("\n3. Tidak ada pustaka berat yang ikut")
cek("tidak ada numpy, sklearn, dan sejenisnya", not berat, "; ".join(berat[:3]))

print("\n4. Penanganya bisa dibaca tanpa lingkungan apa pun")
jalur = os.path.join(API, "perkara.py")
with open(jalur, encoding="utf-8") as f:
    isi = f.read()
pohon = ast.parse(isi, filename=jalur)
nama_atas = {
    t.id
    for s in pohon.body
    if isinstance(s, ast.Assign)
    for t in s.targets
    if isinstance(t, ast.Name)
}
cek("gerbang teranya ikut sebagai angka", "GERBANG" in nama_atas)
cek("alamat model bisa diganti lewat lingkungan", 'os.environ.get("NALAR_MODEL' in isi)
cek(
    "nomor berkas disaring sebelum masuk penyaring basis data",
    "kid[1:].isdigit()" in isi,
)
kelas = [s.name for s in pohon.body if isinstance(s, ast.ClassDef)]
cek("penanganya bernama handler", "handler" in kelas, str(kelas))

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
