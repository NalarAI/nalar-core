"""Ekstraksi tabel tarif INA-CBG resmi dari lampiran Permenkes 3/2023.

Ini yang menggantikan tabel tarif buatan sendiri di tarif.py. Rancangan
menyebut ini sebagai risiko R3, yaitu risiko dengan dampak tertinggi, karena
tanpa tabel tarif resmi seluruh keluaran model kehilangan satuan rupiahnya.

Struktur di dalam PDF:

    TARIF INA-CBG REGIONAL <n>
    RUMAH SAKIT KELAS <A|B|C|D> <PEMERINTAH|SWASTA>
    <RAWAT INAP|RAWAT JALAN>
    NO | KODE INA-CBG | DESKRIPSI | TARIF KELAS 3 | TARIF KELAS 2 | TARIF KELAS 1

Rawat jalan hanya punya satu kolom tarif, bukan tiga.

Satu jebakan yang memakan waktu. Nilai tarif kadang berdiri sendiri satu baris,
kadang menempel di belakang deskripsi, dan keduanya muncul di dokumen yang
sama. Versi pertama pengekstraksi ini mengambil nomor urut sebagai tarif karena
mencari baris yang seluruhnya berupa angka. Yang benar, cari pola angka di
dalam isi baris, dan haruskan ada titik ribuan supaya nomor urut tidak ikut.

Jalankan:
    python scripts/ekstrak_tarif.py
Keluaran:
    data/processed/tarif_inacbg.csv
    data/processed/tarif_inacbg_ringkas.json
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import fitz  # PyMuPDF

AKAR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF = os.path.join(AKAR, "data", "raw", "permenkes3_2023.pdf")
KELUAR = os.path.join(AKAR, "data", "processed")

POLA_KODE = re.compile(r"^([A-Z])-(\d)-(\d{2})-(I{1,3}|0)$")
# Nilai tarif selalu memakai titik ribuan. Mengharuskan minimal satu kelompok
# titik membuat nomor urut, yang berupa angka polos, tidak ikut tertangkap.
POLA_UANG = re.compile(r"\d{1,3}(?:\.\d{3})+")
POLA_REGIONAL = re.compile(r"REGIONAL\s+(\d)")
POLA_KELAS_RS = re.compile(r"RUMAH SAKIT KELAS\s+([ABCD])")
POLA_MILIK = re.compile(r"\b(PEMERINTAH|SWASTA)\b")


def ekstrak(pdf_path: str = PDF):
    d = fitz.open(pdf_path)
    baris = []
    regional = kelas_rs = milik = rawat = None

    for i in range(d.page_count):
        teks = d[i].get_text()
        m = POLA_REGIONAL.search(teks)
        if m:
            regional = int(m.group(1))
        m = POLA_KELAS_RS.search(teks)
        if m:
            kelas_rs = m.group(1)
        m = POLA_MILIK.search(teks)
        if m:
            milik = m.group(1)
        if "RAWAT INAP" in teks:
            rawat = "INAP"
        elif "RAWAT JALAN" in teks:
            rawat = "JALAN"
        if regional is None or kelas_rs is None:
            continue

        potong = [x.strip() for x in teks.split("\n")]
        j = 0
        while j < len(potong):
            mk = POLA_KODE.match(potong[j])
            if not mk:
                j += 1
                continue
            kode = potong[j]

            nilai: list[int] = []
            desk_bagian: list[str] = []
            k = j + 1
            while k < len(potong) and len(nilai) < 3:
                s = potong[k]
                if POLA_KODE.match(s):
                    break
                temuan = POLA_UANG.findall(s)
                if temuan:
                    nilai.extend(int(x.replace(".", "")) for x in temuan)
                    sisa = POLA_UANG.sub(" ", s).strip()
                    if sisa and not sisa.isdigit():
                        desk_bagian.append(sisa)
                elif s and not s.isdigit() and not nilai:
                    desk_bagian.append(s)
                k += 1

            if not nilai:
                j += 1
                continue
            nilai = nilai[:3]
            deskripsi = re.sub(r"\s+", " ", " ".join(desk_bagian)).strip()[:160]

            baris.append(
                dict(
                    kode=kode,
                    cmg=mk.group(1),
                    tipe=int(mk.group(2)),
                    nomor=int(mk.group(3)),
                    keparahan=mk.group(4),
                    deskripsi=deskripsi,
                    regional=regional,
                    kelas_rs=kelas_rs,
                    kepemilikan=milik or "PEMERINTAH",
                    rawat=rawat or "INAP",
                    tarif_kelas3=nilai[0],
                    tarif_kelas2=nilai[1] if len(nilai) > 1 else nilai[0],
                    tarif_kelas1=nilai[2] if len(nilai) > 2 else nilai[0],
                )
            )
            j = max(k, j + 1)
    return baris


def main():
    if not os.path.exists(PDF):
        print(f"Berkas tidak ada: {PDF}")
        print(
            "Unduh dulu dari https://luk.staff.ugm.ac.id/atur/"
            "Permenkes3-2023StandarTarif.pdf"
        )
        return 1

    baris = ekstrak()
    os.makedirs(KELUAR, exist_ok=True)
    csv_path = os.path.join(KELUAR, "tarif_inacbg.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(baris[0].keys()))
        w.writeheader()
        w.writerows(baris)

    kode_unik = sorted({b["kode"] for b in baris})
    ringkas = {
        "sumber": "Lampiran Permenkes Nomor 3 Tahun 2023",
        "n_baris": len(baris),
        "n_kode_unik": len(kode_unik),
        "cmg": sorted({b["cmg"] for b in baris}),
        "regional": sorted({b["regional"] for b in baris}),
        "kelas_rs": sorted({b["kelas_rs"] for b in baris}),
        "kepemilikan": sorted({b["kepemilikan"] for b in baris}),
        "rawat": sorted({b["rawat"] for b in baris}),
        "tarif_terendah": min(b["tarif_kelas3"] for b in baris),
        "tarif_tertinggi": max(b["tarif_kelas1"] for b in baris),
    }
    with open(
        os.path.join(KELUAR, "tarif_inacbg_ringkas.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(ringkas, f, indent=1, ensure_ascii=False)

    print(f"{len(baris)} baris tarif, {len(kode_unik)} kode unik")
    print(f"CMG: {''.join(ringkas['cmg'])}")
    print(
        f"regional {ringkas['regional']}, kelas RS {ringkas['kelas_rs']}, "
        f"kepemilikan {ringkas['kepemilikan']}"
    )
    print(
        f"rentang tarif Rp {ringkas['tarif_terendah']:,} sampai "
        f"Rp {ringkas['tarif_tertinggi']:,}"
    )
    print(f"ditulis ke {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
