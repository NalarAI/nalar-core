"""Menulis hasil model ke Postgres.

Ini bentuk yang dipakai di produksi. Model dilatih di luar jalur permintaan,
hasilnya masuk basis data, lalu aplikasi membaca dari sana. Melatih model
setiap kali ada permintaan bukan arsitektur, itu demo yang kebetulan jalan.

Yang ditulis adalah jawaban API itu sendiri, diambil lewat TestClient, jadi
tidak ada logika yang ditulis ulang di SQL maupun di frontend. Kalau kontrak
API berubah, isi tabel ikut berubah, dan tidak ada tempat lain yang perlu
disentuh.

Butuh kunci service_role, karena aplikasi memang tidak punya hak tulis sama
sekali. Ambil dari rahasia/gh.env atau lewat environment.

Jalankan:
    python scripts/muat_db.py
    python scripts/muat_db.py --kosongkan
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

ALPHA = [0.005, 0.01, 0.02, 0.05, 0.10]
BIAYA = [250_000, 750_000, 1_500_000]
KAPASITAS = [50, 100, 250, 500]


def baca_env() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL")
    kunci = os.environ.get("SUPABASE_SERVICE")
    if not (url and kunci):
        jalur = os.path.join(os.path.dirname(__file__), "..", "..", "rahasia", "gh.env")
        if os.path.exists(jalur):
            with open(jalur, encoding="utf-8") as f:
                for baris in f:
                    if "=" not in baris:
                        continue
                    k, _, v = baris.strip().partition("=")
                    if k == "SUPABASE_URL" and not url:
                        url = v
                    if k == "SUPABASE_SERVICE" and not kunci:
                        kunci = v
    if not (url and kunci):
        raise SystemExit(
            "SUPABASE_URL dan SUPABASE_SERVICE tidak ditemukan. "
            "Isi lewat environment atau rahasia/gh.env"
        )
    return url.rstrip("/"), kunci


class Db:
    def __init__(self, url: str, kunci: str):
        self.url = url
        self.kunci = kunci

    def _panggil(self, metode: str, jalur: str, badan=None, tambahan=None):
        data = json.dumps(badan).encode() if badan is not None else None
        req = urllib.request.Request(
            f"{self.url}/rest/v1/{jalur}", data=data, method=metode
        )
        req.add_header("apikey", self.kunci)
        req.add_header("Authorization", f"Bearer {self.kunci}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept-Profile", "nalar")
        req.add_header("Content-Profile", "nalar")
        req.add_header("Prefer", "return=minimal")
        for k, v in (tambahan or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            raise SystemExit(
                f"{metode} {jalur} gagal {e.code}: {e.read().decode()[:400]}"
            ) from None

    def kosongkan(self):
        # Urutan penghapusannya terikat kunci asing, jadi urutannya tinggal di
        # basis data lewat TRUNCATE CASCADE. Menyimpan urutan itu di sini
        # berarti menyimpan pengetahuan skema di dua tempat.
        self._panggil("POST", "rpc/kosongkan", {})

    def sisipkan(self, tabel: str, baris: list[dict], per_batch: int = 500):
        for i in range(0, len(baris), per_batch):
            self._panggil("POST", tabel, baris[i : i + per_batch])


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--peserta", type=int, default=8000)
    p.add_argument("--tahun", type=int, default=3)
    p.add_argument("--fktp", type=int, default=400)
    p.add_argument("--fkrtl", type=int, default=80)
    p.add_argument("--benih", type=int, default=7)
    p.add_argument(
        "--kosongkan", action="store_true", help="hapus isi tabel dulu sebelum menulis"
    )
    a = p.parse_args()

    url, kunci = baca_env()
    db = Db(url, kunci)

    from fastapi.testclient import TestClient

    from nalar.api import keadaan as _k

    _k.KEADAAN.__init__(
        n_peserta=a.peserta,
        tahun=a.tahun,
        seed=a.benih,
        n_fktp=a.fktp,
        n_fkrtl=a.fkrtl,
    )
    from nalar.api.main import app

    t0 = time.time()
    if a.kosongkan:
        print("[0] mengosongkan tabel")
        db.kosongkan()

    with TestClient(app) as c:
        print(f"[1] model siap dalam {time.time() - t0:.0f} detik")

        klaim: dict[str, dict] = {}
        antrean_baris: list[dict] = []
        antrean_ringkas: list[dict] = []
        ringkas: list[dict] = []

        print("[2] menghitung antrean untuk seluruh kombinasi pengaturan")
        total = len(ALPHA) * len(BIAYA) * len(KAPASITAS)
        n = 0
        for al in ALPHA:
            for bi in BIAYA:
                for ka in KAPASITAS:
                    n += 1
                    par = {"alpha": al, "biaya_audit_rp": bi, "kapasitas": ka}
                    r = c.get("/ringkas", params=par).json()
                    ringkas.append(
                        {
                            "alpha": al,
                            "biaya_audit_rp": bi,
                            "kapasitas": ka,
                            "n_klaim": r["n_klaim"],
                            "n_faskes": r["n_faskes"],
                            "rentang_hari": r["rentang_hari"],
                            "nilai_klaim_total_rp": r["nilai_klaim_total_rp"],
                            "selisih_terdeteksi_rp": r["selisih_terdeteksi_rp"],
                            "n_ditandai": r["n_ditandai"],
                            "n_menahan_diri": r["n_menahan_diri"],
                            "laju_penandaan": r["laju_penandaan"],
                            "rasio_pengembalian": r["rasio_pengembalian"],
                        }
                    )
                    q = c.get(
                        "/antrean",
                        params={**par, "batas_per_faskes": 40, "porsi_acak": 0.05},
                    ).json()
                    antrean_ringkas.append(
                        {
                            "alpha": al,
                            "biaya_audit_rp": bi,
                            "kapasitas": ka,
                            "terisi": q["terisi"],
                            "rupiah_ditemukan_rp": q["rupiah_ditemukan_rp"],
                            "biaya_total_rp": q["biaya_audit_rp"],
                            "rasio_pengembalian": q["rasio_pengembalian"],
                            "alasan_tidak_penuh": q["alasan_tidak_penuh"],
                        }
                    )
                    for b in q["baris"]:
                        pn = b["penilaian"]
                        klaim.setdefault(pn["id"], pn)
                        antrean_baris.append(
                            {
                                "alpha": al,
                                "biaya_audit_rp": bi,
                                "kapasitas": ka,
                                "peringkat": b["peringkat"],
                                "klaim_id": pn["id"],
                                "alasan_masuk": b["alasan_masuk"],
                            }
                        )
                    if n % 10 == 0 or n == total:
                        print(f"    {n}/{total}", flush=True)

        print(f"[3] menyiapkan {len(klaim)} klaim dan penandaannya")
        baris_klaim = [
            {
                "id": k["id"],
                "faskes": k["faskes"],
                "kelas_faskes": k["kelas_faskes"],
                "daerah_tertinggal": k["daerah_tertinggal"],
                "hari": k["hari"],
                "rawat_inap": k["rawat_inap"],
                "kelompok_tarif": k["kelompok_tarif"],
                "tarif_ditagihkan_rp": k["tarif_ditagihkan_rp"],
                "tarif_didukung_bukti_rp": k["tarif_didukung_bukti_rp"],
                "barang_ditagihkan_rp": k["barang_ditagihkan_rp"],
                "barang_wajar_rp": k["barang_wajar_rp"],
                "selisih_rp": k["selisih_rp"],
                "posisi_terhadap_garis": k["posisi_terhadap_garis"],
            }
            for k in klaim.values()
        ]

        # Penandaan bergantung alpha, jadi tiap klaim diminta ulang untuk tiap
        # alpha. Ini yang membuat tabelnya jujur: klaim tidak berubah, hanya
        # penilaian ambangnya.
        penandaan: list[dict] = []
        for al in ALPHA:
            c.get(
                "/ringkas",
                params={"alpha": al, "biaya_audit_rp": 750000, "kapasitas": 100},
            )
            for kid in klaim:
                pn = c.get(f"/klaim/{kid}").json()
                penandaan.append(
                    {
                        "alpha": al,
                        "klaim_id": kid,
                        "ambang_rp": pn["ambang_rp"],
                        "ditandai": pn["ditandai"],
                        "menahan_diri": pn["menahan_diri"],
                    }
                )
            print(f"    penandaan alpha {al} selesai", flush=True)

        print("[4] penjelasan dan bukti pendukung")
        penjelasan: list[dict] = []
        pengandaian: list[dict] = []
        for i, kid in enumerate(klaim, start=1):
            j = c.get(f"/klaim/{kid}/penjelasan").json()
            penjelasan.append(
                {
                    "klaim_id": kid,
                    "status": j["status"],
                    "kalimat_untuk_faskes": j["kalimat_untuk_faskes"],
                }
            )
            for u, b in enumerate(j["pengandaian"]):
                pengandaian.append(
                    {
                        "klaim_id": kid,
                        "urutan": u,
                        "kode": b["kode"],
                        "nama": b["nama"],
                        "ubah_selisih_rp": b["ubah_selisih_rp"],
                    }
                )
            if i % 100 == 0:
                print(f"    {i}/{len(klaim)}", flush=True)

        print("[5] keadilan, profil, dan titik perubahan")
        keadilan: list[dict] = []
        for al in ALPHA:
            kd = c.get("/keadilan", params={"alpha": al}).json()
            for g in kd["kelompok"]:
                keadilan.append(
                    {
                        "alpha": al,
                        "kelompok": g["kelompok"],
                        "n_klaim": g["n_klaim"],
                        "n_ditandai": g["n_ditandai"],
                        "laju_penandaan": g["laju_penandaan"],
                        "kelebihan": g["kelebihan_terhadap_keseluruhan"],
                        "porsi_menahan_diri": g["porsi_menahan_diri"],
                    }
                )

        pr = c.get("/profil", params={"atas": 25}).json()
        profil: list[dict] = []
        for daftar, kunci_daftar in (
            ("rupiah", "antrean_rupiah"),
            ("posisi", "daftar_pantau_posisi"),
        ):
            for i, b in enumerate(pr[kunci_daftar], start=1):
                profil.append(
                    {
                        "daftar": daftar,
                        "peringkat": i,
                        "faskes": b["faskes"],
                        "kelas_faskes": b["kelas_faskes"],
                        "n_klaim": b["n_klaim"],
                        "kelompok_sebaya": b["kelompok_sebaya"],
                        "rata_kelompok": b["rata_kelompok"],
                        "rata_susut": b["rata_faskes_setelah_disusutkan"],
                        "skor_baku": b["skor_baku"],
                        "kelebihan_rp": b["kelebihan_rp"],
                    }
                )

        perubahan: list[dict] = []
        for u in ("posisi", "rupiah"):
            for t in c.get("/perubahan", params={"batas_p": 0.05, "ukuran": u}).json():
                perubahan.append(
                    {
                        "ukuran": u,
                        "faskes": t["faskes"],
                        "kelas_faskes": t["kelas_faskes"],
                        "n_klaim": t["n_klaim"],
                        "hari_ganti": t["hari_ganti"],
                        "rata_sebelum": t["rata_sebelum"],
                        "rata_sesudah": t["rata_sesudah"],
                        "p": t["p"],
                    }
                )

    pilihan = (
        [{"jenis": "alpha", "nilai": v, "urutan": i} for i, v in enumerate(ALPHA)]
        + [
            {"jenis": "biaya_audit_rp", "nilai": v, "urutan": i}
            for i, v in enumerate(BIAYA)
        ]
        + [
            {"jenis": "kapasitas", "nilai": v, "urutan": i}
            for i, v in enumerate(KAPASITAS)
        ]
    )

    print("[6] menulis ke Postgres")
    urutan_tulis = [
        ("klaim", baris_klaim),
        ("penandaan", penandaan),
        ("ringkas", ringkas),
        ("antrean_ringkas", antrean_ringkas),
        ("antrean", antrean_baris),
        ("keadilan", keadilan),
        ("profil_faskes", profil),
        ("perubahan", perubahan),
        ("penjelasan", penjelasan),
        ("pengandaian", pengandaian),
        ("pilihan", pilihan),
        (
            "terbitan",
            [
                {
                    "id": 1,
                    "versi_model": "0.1.0",
                    "benih": a.benih,
                    "n_peserta": a.peserta,
                    "tahun": a.tahun,
                    "catatan": "Seluruh isi tabel ini berasal dari data buatan. "
                    "Tidak ada klaim peserta JKN yang sungguhan.",
                }
            ],
        ),
    ]
    for nama, baris in urutan_tulis:
        db.sisipkan(nama, baris)
        print(f"    {nama:18s} {len(baris):6d} baris")

    print(f"\nselesai dalam {time.time() - t0:.0f} detik")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
