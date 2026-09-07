"""Fungsi tanpa peladen harus sama dengan sumbernya, dan berperilaku sama.

Dua hal yang berbeda diperiksa di sini, dan keduanya perlu.

Pertama, berkasnya sama bita demi bita dengan yang dihasilkan sumbernya.
Itu menangkap suntingan tangan pada berkas hasil.

Kedua, penjaganya berperilaku sama dengan jalur model di peladen. Itu
menangkap kesalahan pada penghasilnya sendiri, yang tidak akan ketahuan
dari perbandingan bita karena keduanya salah dengan cara yang sama.

Modelnya tidak dipanggil. Yang diuji penjaganya, dan penjaganya bekerja
pada keluaran model apa pun, jadi keluarannya disodorkan langsung.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

AKAR = os.path.join(os.path.dirname(__file__), "..")
FUNGSI = os.path.join(AKAR, "..", "nalar-web", "api", "sanggah.py")

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
if not os.path.exists(FUNGSI):
    print("         DILEWATI, nalar-web tidak ada di sebelah repositori ini")
    print(f"\n{lulus} lulus, {gagal} gagal")
    sys.exit(0)

r = subprocess.run(
    [
        sys.executable,
        os.path.join(AKAR, "scripts", "buat_fungsi_sanggah.py"),
        "--periksa",
    ],
    capture_output=True,
    text=True,
)
cek("berkas hasil tidak menyimpang dari sumbernya", r.returncode == 0, r.stdout[-200:])

spec = importlib.util.spec_from_file_location("fungsi_sanggah", FUNGSI)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

SURAT = (
    "Bersama ini kami lampirkan hasil pemeriksaan hemoglobin dan trombosit "
    "atas nama pasien tersebut. Pemeriksaan kreatinin tidak dilakukan."
)


def jalankan(butir):
    """Sodorkan keluaran model apa adanya, lalu jalankan penjaganya."""
    m.tanya_model = lambda _surat: butir
    m.KUNCI = "pura pura ada"
    return m.petakan(SURAT)


print("\n2. Penjaganya berperilaku seperti di peladen")

h = jalankan(
    [
        {"kode": "HB", "kutipan": "hasil pemeriksaan hemoglobin"},
        {"kode": "TROMB", "kutipan": "hemoglobin dan trombosit"},
    ]
)
cek(
    "kutipan yang berakar diterima",
    [b["kode"] for b in h["dipetakan"]] == ["HB", "TROMB"] and not h["dibuang"],
    str(h),
)

h = jalankan([{"kode": "KREA", "kutipan": "hasil kreatinin terlampir"}])
cek(
    "kutipan yang mengarang membuang kodenya",
    h["dipetakan"] == [] and h["dibuang"][0]["kode"] == "KREA",
    str(h),
)

# Ini kasus yang menjatuhkan pemeriksaan enam agen kemarin. Model memilih
# trombosit dengan benar lalu mengutipnya sebagai "tromb-than".
h = jalankan([{"kode": "TROMB", "kutipan": "hemoglobin dan tromb-than"}])
cek(
    "kutipan rusak diselamatkan nama katalog",
    [b["kode"] for b in h["dipetakan"]] == ["TROMB"]
    and "kutipan model tidak terbaca" in h["dipetakan"][0]["alasan"],
    str(h),
)

h = jalankan([{"kode": "XYZ", "kutipan": "hemoglobin dan trombosit"}])
cek(
    "kode di luar katalog dibuang",
    h["dipetakan"] == [] and h["dibuang"][0]["sebab"] == "kode di luar katalog",
    str(h),
)

# Yang memilih kodenya tetap model. Pencocokan kata sendirian akan
# memetakan kreatinin, karena namanya memang ada di surat.
h = jalankan([{"kode": "HB", "kutipan": "hasil pemeriksaan hemoglobin"}])
cek(
    "kreatinin yang tidak dipilih model tidak masuk sendiri",
    [b["kode"] for b in h["dipetakan"]] == ["HB"],
    str(h),
)

print("\n3. Tanpa kunci model, jawabannya sah dan bukan galat")
m.KUNCI = ""
h = m.petakan(SURAT)
cek(
    "tanpa kunci menjawab tidak ada model",
    h["cara"] == "tidak ada model" and h["dipetakan"] == [],
    str(h),
)

print("\n4. Katalognya utuh")
cek(
    "seluruh kode katalog ikut terbawa",
    len(m.PEMERIKSAAN) == 35 and "TROMB" in m.PEMERIKSAAN,
    str(len(m.PEMERIKSAAN)),
)
cek(
    "skema alatnya menjepit kodenya",
    len(
        m.skema()[0]["parameters"]["properties"]["pemeriksaan"]["items"]["properties"][
            "kode"
        ]["enum"]
    )
    == 35,
)

print(f"\n{lulus} lulus, {gagal} gagal")
sys.exit(1 if gagal else 0)
