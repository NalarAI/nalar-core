"""Mengadu Agen Sanggah versi model bahasa dengan versi pencocokan kata.

Berkas sanggah.py sejak awal menjanjikan satu hal: pencocokan kata jadi
garis dasarnya, model bahasa dipasang di atasnya, dan kalau model tidak
menang ia dicabut. Skrip ini yang menagih janji itu.

Suratnya ditulis lebih dulu, sebelum kedua cara dijalankan, dan tidak
disunting sesudah hasilnya terlihat. Itu syarat yang gampang dilanggar
tanpa ketahuan siapa pun, jadi ditulis di sini supaya bisa ditagih.

Yang diukur tiga.

Ingatan, bagian pemeriksaan yang memang disebut surat dan berhasil
ditemukan. Ketepatan, bagian kode yang ditemukan dan memang benar. Dan
surat yang seluruh isinya betul, tanpa satu kode pun lebih atau kurang.

Ketepatan lebih berat daripada ingatan di sini. Kode yang salah dipetakan
akan diteruskan ke skor_ulang, dan selisih yang turun karena bukti yang
tidak pernah ada adalah kerugian yang tidak terlihat siapa pun.

Jalankan:
    python scripts/ukur_sanggah.py [--model nalar-qwen3-4b]
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

from nalar.agen import PenuturSetempat, petakan_bukti, petakan_bukti_model  # noqa: E402
from nalar.agen.penutur import GalatPenutur  # noqa: E402

# Dua puluh empat surat, ditulis sekali, dengan isinya ditetapkan lebih
# dulu. Bentuknya meniru surat balasan rumah sakit yang sebenarnya: ada yang
# menyebut nama katalog persis, ada yang memakai sebutan sehari hari, ada
# yang menyebut pemeriksaan justru untuk bilang ia tidak dikerjakan.
SURAT: list[tuple[str, set[str]]] = [
    (
        "Bersama ini kami lampirkan hasil laboratorium pasien, hemoglobin "
        "8,2 g/dL dan trombosit 95.000. Mohon berkas ditinjau ulang.",
        {"HB", "TROMB"},
    ),
    (
        "Terlampir hasil pemeriksaan fungsi ginjal berupa ureum dan "
        "kreatinin atas nama pasien tersebut di atas.",
        {"UR", "KREA"},
    ),
    (
        "Pasien menjalani analisis gas darah pada hari perawatan kedua, "
        "hasilnya kami sertakan pada lampiran.",
        {"AGD"},
    ),
    (
        "Hasil urinalisis pasien terlampir bersama surat ini.",
        {"URIN"},
    ),
    (
        "Perlu kami sampaikan bahwa pemeriksaan trombosit tidak dilakukan "
        "pada pasien ini karena kondisi klinis tidak menuntutnya.",
        set(),
    ),
    (
        "Kami lampirkan hasil SGOT dan SGPT untuk menunjang diagnosis "
        "gangguan fungsi hati pada pasien.",
        {"SGOT", "SGPT"},
    ),
    (
        "Terlampir kadar albumin serum pasien 2,1 g/dL, diambil pada hari "
        "kedua perawatan.",
        {"ALB"},
    ),
    (
        "Elektrolit natrium dan kalium diperiksa pada tanggal yang sama "
        "dengan tindakan, hasilnya kami lampirkan.",
        {"NA", "KAL"},
    ),
    (
        "Kami sertakan hasil glukosa darah puasa dan HbA1c sebagai dasar "
        "penegakan diagnosis diabetes melitus.",
        {"GDP", "HBA1C"},
    ),
    (
        "Hasil troponin pasien meningkat, sedangkan CK-MB masih dalam batas "
        "normal. Keduanya terlampir.",
        {"TROP", "CKMB"},
    ),
    (
        "Pemeriksaan laju endap darah dan C-reactive protein mendukung "
        "adanya proses infeksi, hasilnya kami lampirkan.",
        {"LED", "CRP"},
    ),
    (
        "Kami lampirkan hasil prokalsitonin dan laktat yang diambil selama "
        "pasien dirawat di ruang intensif.",
        {"PCT", "LAKTAT"},
    ),
    (
        "Terlampir hasil BTA sputum tiga kali berturut turut, seluruhnya negatif.",
        {"BTA"},
    ),
    (
        "Pemeriksaan Widal dan apusan malaria dikerjakan untuk menyingkirkan "
        "penyebab demam pada pasien ini.",
        {"WIDAL", "MALARIA"},
    ),
    (
        "Kami keberatan atas hasil verifikasi ini dan meminta berkas "
        "ditinjau ulang oleh verifikator yang berbeda.",
        set(),
    ),
    (
        "Hasil waktu protrombin dan APTT terlampir, keduanya diperiksa "
        "sebelum tindakan operasi.",
        {"PT", "APTT"},
    ),
    (
        "Kadar TSH dan free T4 pasien kami lampirkan pada berkas ini.",
        {"TSH", "FT4"},
    ),
    (
        "Terlampir hasil feritin serum dan hematokrit pasien.",
        {"FERITIN", "HT"},
    ),
    (
        "Pasien sempat direncanakan pemeriksaan PSA, namun sampai pasien "
        "pulang pemeriksaan tersebut belum dikerjakan.",
        set(),
    ),
    (
        "Hasil bilirubin total dan kolesterol total kami lampirkan sesuai "
        "permintaan verifikator.",
        {"BIL", "KOL"},
    ),
    (
        "Kami lampirkan hasil pemeriksaan hemoglobin, hematokrit, leukosit, "
        "dan trombosit pasien.",
        {"HB", "HT", "LEUKO", "TROMB"},
    ),
    (
        "Terlampir hasil trigliserida pasien yang diambil pada pagi hari.",
        {"TG"},
    ),
    (
        "Pemeriksaan CD4 dan alfa fetoprotein terlampir sesuai permintaan "
        "dokter penanggung jawab pasien.",
        {"CD4", "AFP"},
    ),
    (
        "Mohon berkas ditinjau ulang. Surat pengantar dan resume medis "
        "pasien terlampir bersama surat ini.",
        set(),
    ),
]


def nilai(temuan: list[set[str]]) -> dict:
    benar = ditemukan = seharusnya = utuh = 0
    for (_, asli), dapat in zip(SURAT, temuan):
        benar += len(asli & dapat)
        ditemukan += len(dapat)
        seharusnya += len(asli)
        utuh += int(asli == dapat)
    return {
        "ingatan": round(benar / seharusnya, 4) if seharusnya else 1.0,
        "ketepatan": round(benar / ditemukan, 4) if ditemukan else 1.0,
        "surat_utuh": utuh,
        "n_surat": len(SURAT),
        "ditemukan": ditemukan,
        "seharusnya": seharusnya,
    }


def jalankan(model: str, alamat: str | None) -> dict:
    kata = [{b["kode"] for b in petakan_bukti(s)} for s, _ in SURAT]

    penutur = PenuturSetempat(alamat=alamat, model=model)
    if not penutur.hidup():
        print(f"Peladen model tidak menyala di {penutur.alamat}.")
        sys.exit(2)
    print(f"Model {penutur.model} di {penutur.alamat}, {len(SURAT)} surat.\n")

    hasil_model = []
    n_dibuang = 0
    t0 = time.time()
    for k, (s, asli) in enumerate(SURAT, 1):
        try:
            peta, dibuang = petakan_bukti_model(s, penutur)
        except GalatPenutur as e:
            print(f"  {k:2d}  model tidak menjawab: {e}")
            peta, dibuang = [], []
        n_dibuang += len(dibuang)
        dapat = {b["kode"] for b in peta}
        hasil_model.append(dapat)
        tanda = "sama " if dapat == kata[k - 1] else "beda "
        betul = "benar" if dapat == asli else "salah"
        print(
            f"  {k:2d}  {tanda}{betul}  kata={sorted(kata[k - 1])} "
            f"model={sorted(dapat)} asli={sorted(asli)}"
        )
    detik = time.time() - t0

    return {
        "model": penutur.model,
        "kata": nilai(kata),
        "model_bahasa": nilai(hasil_model),
        "dibuang_penjaga": n_dibuang,
        "detik": round(detik, 1),
        "detik_per_surat": round(detik / len(SURAT), 2),
    }


def lapor(h: dict) -> None:
    print("\n" + "=" * 68)
    print(f"Agen Sanggah, {h['kata']['n_surat']} surat, {h['detik']} detik")
    print("=" * 68 + "\n")
    print(f"{'':22}{'pencocokan kata':>18}{'model bahasa':>18}")
    for nama, kunci in (
        ("ingatan", "ingatan"),
        ("ketepatan", "ketepatan"),
    ):
        print(f"  {nama:20}{h['kata'][kunci]:>18.3f}{h['model_bahasa'][kunci]:>18.3f}")
    print(
        f"  {'surat utuh benar':20}"
        f"{h['kata']['surat_utuh']:>15}/{h['kata']['n_surat']}"
        f"{h['model_bahasa']['surat_utuh']:>15}/{h['kata']['n_surat']}"
    )
    print(f"\n  kode dibuang penjaga kutipan  : {h['dibuang_penjaga']}")
    print(f"  lama per surat                : {h['detik_per_surat']} detik")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.environ.get("NALAR_MODEL", "nalar-qwen3-4b"))
    p.add_argument("--alamat", default=os.environ.get("NALAR_MODEL_URL"))
    p.add_argument("--keluar", default="runs/ukur_sanggah.json")
    a = p.parse_args()

    h = jalankan(a.model, a.alamat)
    lapor(h)
    os.makedirs(os.path.dirname(a.keluar), exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)
    print(f"\nRinciannya di {a.keluar}")
