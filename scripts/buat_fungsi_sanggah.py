"""Menghasilkan fungsi tanpa peladen untuk Agen Sanggah, dari sumber aslinya.

Agen Sanggah satu satunya agen yang tidak butuh keadaan data maupun penebak
terlatih. Yang diperlukannya surat dari pengguna, katalog pemeriksaan, dan
satu model bahasa. Ketiganya muat di fungsi tanpa peladen, jadi ia bisa
hidup di situs peragaan tanpa mesin yang menyala dua puluh empat jam.

Yang berbahaya dari itu satu hal: berkasnya jadi salinan kedua dari logika
yang sudah ada di sini, dan salinan kedua selalu menyimpang. Proyek ini
sudah pernah kena, dan yang menyimpang diam diam selalu ketahuan belakangan.

Maka berkasnya tidak ditulis tangan. Ia dihasilkan dari definisi yang sama
yang dipakai peladen dan uji, dan tests/test_fungsi.py menghasilkannya ulang
lalu membandingkannya bita demi bita. Menyunting berkas hasil akan
menjatuhkan uji itu.

Jalankan:
    python scripts/buat_fungsi_sanggah.py
    python scripts/buat_fungsi_sanggah.py --periksa
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar.agen.sanggah import ARAHAN_SURAT, SEBUTAN, UMUM  # noqa: E402
from nalar.katalog import PEMERIKSAAN  # noqa: E402

TUJUAN = os.path.join(
    os.path.dirname(__file__), "..", "..", "nalar-web", "api", "sanggah.py"
)

KEPALA = '''"""Agen Sanggah sebagai fungsi tanpa peladen. BERKAS INI DIHASILKAN.

Jangan disunting tangan. Sumbernya nalar-core/src/nalar/agen/sanggah.py, dan
berkas ini dihasilkan scripts/buat_fungsi_sanggah.py. Uji di nalar-core
menghasilkannya ulang lalu membandingkannya, jadi suntingan tangan akan
menjatuhkan uji itu.

Yang dikerjakannya sama persis dengan jalur model di peladen. Model memilih
kode pemeriksaan yang menurut surat memang dilampirkan, tiap kode membawa
kutipan, dan kutipan yang katanya tidak ada di surat membuang kodenya. Kalau
kutipannya rusak tapi nama katalognya ada di surat, kodenya tetap masuk
dengan nama katalog sebagai pembuktinya.

Yang tidak dikerjakannya menghitung ulang selisih. Itu tugas penebak tarif,
dan penebak tarif tidak muat di sini. Antarmuka yang memanggil fungsi ini
sudah punya daftar pengandaian dari basis data, jadi pengurangannya
dikerjakan di sana dengan angka yang sudah dihitung model.

Kunci modelnya dibaca dari lingkungan, dan tanpa kunci fungsi ini menjawab
bahwa tidak ada model yang tersedia. Jawaban itu sah, dan antarmukanya jatuh
ke pencocokan nama di peramban.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

ALAMAT = os.environ.get("NALAR_MODEL_URL", "https://api.cerebras.ai/v1")
MODEL = os.environ.get("NALAR_MODEL", "qwen-3.8-27b")
KUNCI = os.environ.get("NALAR_MODEL_KEY", "")
TENGGAT = float(os.environ.get("NALAR_MODEL_TENGGAT", "25"))
'''

EKOR = '''

def _bersih(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def alasan_kata(kode: str, nama: str, teks: str) -> str:
    """Alasan berbasis kata untuk satu kode, atau kosong kalau tidak ada."""
    for sebut in SEBUTAN.get(kode, ()):
        if re.search(rf"\\b{re.escape(sebut)}\\b", teks):
            return f"surat menyebut {sebut}"
    kata = [k for k in _bersih(nama).split() if k and k not in UMUM]
    if kata and all(re.search(rf"\\b{re.escape(k)}\\b", teks) for k in kata):
        return f"surat menyebut {nama.lower()}"
    if re.search(rf"\\b{kode.lower()}\\b", teks):
        return f"surat menyebut kode {kode}"
    return ""


def berakar(kutipan: str, kata_surat: set) -> bool:
    """Tiap kata pada kutipan ada di surat, dan sekurangnya satu berarti."""
    kata = [k for k in _bersih(kutipan).split() if k]
    if len(kata) < 2 or not all(k in kata_surat for k in kata):
        return False
    return any(k not in UMUM for k in kata)


def mirip_nama(kutipan: str, kata_surat: set, kode: str) -> bool:
    """Kata tak dikenal pada kutipan mirip nama pemeriksaan itu sendiri."""
    sebut = [PEMERIKSAAN[kode].lower(), kode.lower(), *SEBUTAN.get(kode, ())]
    awalan = {_bersih(x).replace(" ", "")[:4] for x in sebut if len(_bersih(x)) >= 4}
    for k in _bersih(kutipan).split():
        if k in kata_surat or len(k) < 4:
            continue
        if any(k.startswith(a) or a.startswith(k[:4]) for a in awalan if a):
            return True
    return False


def skema() -> list:
    return [
        {
            "name": "catat_pemeriksaan",
            "description": (
                "Daftar pemeriksaan yang menurut surat sudah dikerjakan "
                "atau dilampirkan, beserta potongan kalimat dasarnya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pemeriksaan": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "kode": {"type": "string", "enum": sorted(PEMERIKSAAN)},
                                "kutipan": {
                                    "type": "string",
                                    "description": (
                                        "Potongan kalimat dari surat, "
                                        "disalin apa adanya."
                                    ),
                                },
                            },
                            "required": ["kode", "kutipan"],
                        },
                    }
                },
                "required": ["pemeriksaan"],
            },
        }
    ]


def daftar_kode() -> str:
    return "\\n".join(f"  {k}  {n}" for k, n in PEMERIKSAAN.items())


def tanya_model(surat: str) -> list:
    """Satu giliran ke model, kembalikan daftar kode dan kutipannya."""
    badan = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": ARAHAN.format(daftar=daftar_kode())},
            {"role": "user", "content": surat},
        ],
        "temperature": 0,
        "tools": [{"type": "function", "function": a} for a in skema()],
    }
    req = urllib.request.Request(
        f"{ALAMAT}/chat/completions",
        data=json.dumps(badan, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KUNCI}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TENGGAT) as r:
        jawab = json.loads(r.read().decode("utf-8"))
    pesan = jawab["choices"][0]["message"]
    butir = []
    for p in pesan.get("tool_calls") or []:
        f = p.get("function") or {}
        mentah = f.get("arguments") or "{}"
        try:
            arg = json.loads(mentah) if isinstance(mentah, str) else dict(mentah)
        except json.JSONDecodeError:
            continue
        isi = arg.get("pemeriksaan") or []
        if isinstance(isi, list):
            butir.extend(x for x in isi if isinstance(x, dict))
    return butir


def petakan(surat: str) -> dict:
    """Pemetaan susunan model, beserta yang dibuang penjaganya."""
    if not KUNCI:
        return {"cara": "tidak ada model", "dipetakan": [], "dibuang": []}
    try:
        butir = tanya_model(surat)
    except (urllib.error.URLError, OSError, TimeoutError, KeyError, IndexError) as e:
        return {"cara": "model tidak menjawab", "dipetakan": [], "dibuang": [],
                "keterangan": str(e)[:120]}

    kata_surat = set(_bersih(surat).split())
    keluar, dibuang, sudah = [], [], set()
    for x in butir:
        kode = str(x.get("kode", "")).strip().upper()
        kutipan = str(x.get("kutipan", "")).strip()
        if kode not in PEMERIKSAAN:
            dibuang.append({"kode": kode, "sebab": "kode di luar katalog"})
            continue
        if kode in sudah:
            continue
        alasan = f'surat menyebut "{kutipan}"'
        if not berakar(kutipan, kata_surat):
            kata = alasan_kata(kode, PEMERIKSAAN[kode], " ".join(kata_surat))
            if not (kata and mirip_nama(kutipan, kata_surat, kode)):
                dibuang.append({"kode": kode, "sebab": "kutipannya tidak ada di surat"})
                continue
            alasan = kata + ", kutipan model tidak terbaca"
        sudah.add(kode)
        keluar.append({"kode": kode, "nama": PEMERIKSAAN[kode], "alasan": alasan})
    return {"cara": "model", "dipetakan": keluar, "dibuang": dibuang}


class handler(BaseHTTPRequestHandler):
    def _jawab(self, kode: int, badan: dict) -> None:
        isi = json.dumps(badan, ensure_ascii=False).encode("utf-8")
        self.send_response(kode)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        self.wfile.write(isi)

    def do_OPTIONS(self):  # noqa: N802
        self._jawab(200, {})

    def do_POST(self):  # noqa: N802
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except (ValueError, json.JSONDecodeError):
            return self._jawab(400, {"galat": "badan bukan JSON"})
        surat = str(data.get("isi") or "").strip()
        if not surat:
            return self._jawab(422, {"galat": "isi surat kosong"})
        if len(surat) > 8000:
            return self._jawab(422, {"galat": "surat terlalu panjang"})
        self._jawab(200, petakan(surat))
'''


def bangun() -> str:
    bagian = [KEPALA]
    bagian.append("\nARAHAN = " + json.dumps(ARAHAN_SURAT, ensure_ascii=False) + "\n")
    nama = {k: v[0] for k, v in PEMERIKSAAN.items()}
    bagian.append(
        "\nPEMERIKSAAN = " + json.dumps(nama, ensure_ascii=False, indent=4) + "\n"
    )
    bagian.append(
        "\nSEBUTAN = "
        + json.dumps(
            {k: list(v) for k, v in SEBUTAN.items()}, ensure_ascii=False, indent=4
        )
        + "\n"
    )
    bagian.append(
        "\nUMUM = set(" + json.dumps(sorted(UMUM), ensure_ascii=False, indent=4) + ")\n"
    )
    bagian.append(EKOR)
    return "".join(bagian)


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--periksa", action="store_true", help="Bandingkan, jangan tulis.")
    p.add_argument("--keluar", default=TUJUAN)
    a = p.parse_args()

    isi = bangun()
    if a.periksa:
        if not os.path.exists(a.keluar):
            print(f"{a.keluar} belum ada.")
            return 1
        with open(a.keluar, encoding="utf-8") as f:
            punya = f.read()
        if punya != isi:
            print(f"{a.keluar} berbeda dari yang dihasilkan sumbernya.")
            print("Jalankan scripts/buat_fungsi_sanggah.py untuk memperbaruinya.")
            return 1
        print(f"{a.keluar} sama dengan sumbernya.")
        return 0

    os.makedirs(os.path.dirname(a.keluar), exist_ok=True)
    with open(a.keluar, "w", encoding="utf-8", newline="\n") as f:
        f.write(isi)
    print(f"{a.keluar} ditulis, {len(isi.splitlines())} baris")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
