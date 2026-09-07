"""Menghasilkan fungsi tanpa peladen untuk Agen Berkas, dari sumber aslinya.

Agen Sanggah muat di satu berkas karena yang diperlukannya cuma surat,
katalog, dan satu model. Agen Berkas tidak begitu. Ia memanggil alat,
mencatat jejak, mengisi lubang, memeriksa tiap angkanya, lalu menghitung
keyakinan. Lima belas modul, dan menyalinnya jadi satu berkas berarti
menabrakkan nama yang kebetulan sama tanpa ada yang tahu.

Maka yang disalin modulnya, apa adanya, ke dalam satu paket di sebelah
fungsinya. Satu satunya yang diubah bentuk impornya, dari dua titik jadi
satu titik, karena paketnya jadi datar. Selebihnya bita demi bita sama
dengan yang dipakai peladen dan uji.

Dua modul diperlakukan lain, dan keduanya ditulis di sini.

tarif_resmi berisi tujuh puluh tujuh ribu baris lampiran Permenkes. Ia tidak
ikut, karena alat yang memakainya sudah diganti versi basis data. Yang ikut
pengganti yang menolak dengan keterangan, supaya kalau suatu hari ada jalur
yang memanggilnya, yang terjadi penolakan yang terbaca, bukan angka karangan.

Gerbang layak kirim ikut sebagai angka hasil tera, dan angkanya dikunci pada
model yang dipakai menera. Ambang gerbang menjanjikan sesuatu tentang
sebaran berkas perkara, dan model yang berbeda memberi sebaran yang berbeda.
Memakai ambang satu model untuk model lain berarti menjanjikan yang tidak
pernah diukur.

Jalankan:
    python scripts/buat_fungsi_perkara.py
    python scripts/buat_fungsi_perkara.py --periksa
"""

from __future__ import annotations

import argparse
import json
import os

AKAR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SUMBER = os.path.join(AKAR, "src", "nalar")
TUJUAN = os.path.abspath(os.path.join(AKAR, "..", "nalar-web", "api"))

# Urutannya urutan ketergantungan, dari yang tidak bergantung apa apa sampai
# yang bergantung semuanya. Bukan keharusan Python, tapi ia membuat rantai
# impornya bisa dibaca dari daftar ini saja.
MODUL = [
    ("pembulatan.py", "pembulatan.py"),
    ("katalog.py", "katalog.py"),
    ("agen/jejak.py", "jejak.py"),
    ("agen/aturan.py", "aturan.py"),
    ("agen/periksa.py", "periksa.py"),
    ("agen/dalam.py", "dalam.py"),
    ("agen/gerbang.py", "gerbang.py"),
    ("agen/isian.py", "isian.py"),
    ("agen/penutur.py", "penutur.py"),
    ("agen/alat.py", "alat.py"),
    ("agen/alat_db.py", "alat_db.py"),
    ("agen/penyelia.py", "penyelia.py"),
    ("agen/perkara.py", "perkara.py"),
    ("agen/berkas.py", "berkas.py"),
]

BANNER = """# BERKAS INI DIHASILKAN, JANGAN DISUNTING TANGAN.
#
# Sumbernya nalar-core/src/nalar/{asal}, dan berkas ini dihasilkan
# scripts/buat_fungsi_perkara.py. Uji di nalar-core menghasilkannya ulang
# lalu membandingkannya bita demi bita, jadi suntingan tangan akan
# menjatuhkan uji itu.
"""

AWALAN_PAKET = '''"""Salinan lapisan agen NALAR, dipakai fungsi di sebelahnya.

Seluruh isi paket ini dihasilkan scripts/buat_fungsi_perkara.py di
nalar-core. Jangan disunting tangan, karena uji di sana membandingkannya
bita demi bita dengan yang dihasilkan sumbernya.

Paketnya datar, sementara di nalar-core modul agen ada satu tingkat di
bawah. Itu satu satunya perbedaan bentuk, dan ia yang membuat impor dua
titik jadi satu titik.
"""
'''

TARIF_TIRUAN = '''"""Pengganti tabel tarif resmi. Menolak, bukan menjawab.

Lampiran Permenkes yang asli tujuh puluh tujuh ribu baris, dan membawanya
ke dalam fungsi tanpa peladen berarti memperlambat tiap pemanggilan dingin
demi berkas yang tidak pernah dibaca di jalur ini.

Alat yang memakainya sudah diganti versi basis data di alat_db.py, jadi
modul ini tidak pernah tersentuh. Ia tetap ada supaya kalau suatu hari ada
jalur yang memanggilnya, yang terjadi penolakan yang terbaca di jejak
audit, bukan angka yang dikarang.
"""

from __future__ import annotations


def tarif_resmi(kode, kelas_rawat, kelas_rs, regional, kepemilikan="PEMERINTAH"):
    raise RuntimeError(
        "tabel tarif resmi tidak ikut ke fungsi tanpa peladen. "
        "Yang dipakai di sini tabel nalar.tarif lewat alat_db.py."
    )
'''


def gerbang_tertera() -> dict:
    """Ambang hasil tera, dibaca dari keluaran pengukuran, bukan ditulis ulang.

    Kuncinya nama model. Berkas perkara dari model yang tidak ada di sini
    keluar tanpa keadaan, dan itu jawaban yang benar: gerbangnya memang
    belum pernah ditera untuk model itu.
    """
    keluar = {}
    for nama, jalur in (
        ("nalar-qwen3-4b", "runs/ukur_agen_4b_500.json"),
        ("openai/gpt-oss-120b", "runs/ukur_agen_groq_250.json"),
    ):
        p = os.path.join(AKAR, jalur)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        g = d.get("gerbang") or {}
        if "ambang" not in g:
            continue
        keluar[nama] = {
            "ambang": g["ambang"],
            "delta": g.get("delta", d.get("delta", 0.05)),
            "n_kalibrasi": g.get("n", 0),
            "diukur_pada": d.get("n", 0),
        }
    return keluar


HANDLER = '''"""Agen Berkas sebagai fungsi tanpa peladen. BERKAS INI DIHASILKAN.

Jangan disunting tangan. Sumbernya nalar-core/src/nalar/agen/berkas.py
beserta lapisan yang dipakainya, dan berkas ini dihasilkan
scripts/buat_fungsi_perkara.py. Uji di nalar-core menghasilkannya ulang lalu
membandingkannya, jadi suntingan tangan akan menjatuhkan uji itu.

Yang dikerjakannya lingkaran agen yang sama dengan di peladen. Model memilih
alat, alatnya menjawab dari basis data, tiap jawaban masuk rantai jejak, lalu
tiap angka pada kalimatnya dicocokkan ke angka yang pernah dikembalikan alat.
Angka yang tidak berasal dari alat mana pun membatalkan kalimatnya, dan yang
keluar berkas perkara versi aturan.

Satu hal berbeda dari peladen, dan bedanya di sumber angkanya saja. Alat di
sini membaca tabel, bukan keadaan data di memori. Keduanya sudah diadu medan
demi medan di nalar-core/tests/test_alat_db.py.

Satu alat tidak ikut. skor_ulang menuntut penebak tarif terlatih, dan
penebak tidak muat di sini. Ia menolak dengan keterangan, dan penolakan itu
masuk jejak seperti penolakan alat lainnya.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _nalar.alat import GalatAlat  # noqa: E402
from _nalar.alat_db import PerkakasBasisData, SumberBasisData  # noqa: E402
from _nalar.berkas import jalankan  # noqa: E402
from _nalar.gerbang import Gerbang  # noqa: E402
from _nalar.jejak import Jejak  # noqa: E402
from _nalar.penutur import PenuturSetempat  # noqa: E402
from _nalar.penyelia import Anggaran  # noqa: E402

ALAMAT = os.environ.get("NALAR_MODEL_URL") or "https://api.groq.com/openai/v1"
MODEL = os.environ.get("NALAR_MODEL") or "openai/gpt-oss-120b"
KUNCI = os.environ.get("NALAR_MODEL_KEY", "")

# Peubah situs dipakai kalau yang khusus peladen tidak ada. Situsnya sudah
# punya keduanya, jadi fungsi ini hidup tanpa penyetelan tambahan, dan ia
# pasti membaca basis data yang sama dengan yang dibaca halamannya.
DB_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or ""
DB_KUNCI = os.environ.get("SUPABASE_ANON") or os.environ.get("VITE_SUPABASE_KEY") or ""

# Sama dengan yang dipakai peragaan. Penanda menahan diri bergantung padanya,
# karena ambang tiap kelompok sebaya dihitung per alpha.
ALPHA = 0.02

# Anggaran dipendekkan dari yang di peladen. Fungsi tanpa peladen punya batas
# waktu keras, dan lingkaran yang terpotong di tengah tidak mengembalikan apa
# apa. Yang dipilih anggaran yang selesai lebih dulu daripada batas itu, jadi
# yang keluar tetap berkas perkara, meski berkas perkara versi aturan.
ANGGARAN = Anggaran(giliran=6, panggilan=10, rp=500.0, detik=38.0)
TENGGAT_MODEL = 18.0

# Satu percobaan, tanpa pengulangan. Penyedia awan menolak permintaan yang
# melampaui laju, dan pengulangan berarti menunggu sampai setengah menit.
# Di sini menunggu selama itu lebih buruk daripada mundur ke versi aturan,
# karena yang menunggu orang yang sedang menatap layar. Yang mundur tetap
# mendapat berkas perkara utuh, cuma disusun aturan bukan model, dan
# jawabannya menyebutkan itu.
COBA_MODEL = 1

GERBANG = {gerbang}


def _pabrik(sumber):
    return lambda jejak: PerkakasBasisData(sumber, jejak)


def _menahan(sumber, kid: str) -> bool:
    """Penanda menahan diri untuk satu berkas, dibaca dari tabel penandaan.

    Ia tidak bisa dihitung ulang di sini, karena yang menghitungnya ambang
    kelompok sebaya, dan ambang itu menuntut seluruh episode. Kalau barisnya
    tidak ada, yang dipakai False, dan itu pilihan yang menaikkan keyakinan.
    Karena itu ketiadaannya ikut dilaporkan pada jawaban.
    """
    q = urllib.parse.quote(kid)
    r = sumber.satu(
        f"penandaan?klaim_id=eq.{{q}}&alpha=eq.{{ALPHA}}&select=menahan_diri"
    )
    return bool(r["menahan_diri"]) if r else False


def _baris_jejak(jejak: Jejak) -> list:
    return [
        {{
            "urut": c.urut,
            "alat": c.alat,
            "argumen": c.argumen,
            "ms": c.ms,
            "galat": c.galat,
            "sidik": c.sidik,
        }}
        for c in jejak.catatan
    ]


def susun_berkas(kid: str) -> tuple:
    """Berkas perkara untuk satu nomor, beserta kode jawaban yang pantas.

    Tiga kegagalan yang berbeda dibedakan di sini, karena yang membacanya
    perlu tahu mana yang bisa ia perbaiki sendiri. Nomor berkas yang tidak
    ada di peragaan bisa diperbaiki dengan mengetik nomor lain. Basis data
    yang tidak menjawab tidak bisa diperbaiki pembacanya. Fungsi yang belum
    disetel bukan urusan pembacanya sama sekali.

    Semuanya pernah dijawab lima ratus, dan lima ratus berarti kesalahan
    peladen. Nomor yang salah ketik bukan kesalahan peladen.
    """
    if not (DB_URL and DB_KUNCI):
        return 503, {{"galat": "alamat basis data belum disetel pada fungsi ini"}}

    sumber = SumberBasisData(DB_URL, DB_KUNCI)
    # Diperiksa lebih dulu, bukan ditunggu sampai alatnya menolak di tengah
    # lingkaran. Penolakan di tengah lingkaran sudah terlanjur memakai
    # giliran model, dan giliran itu dibayar dari jatah yang terbatas.
    try:
        if not sumber.satu(
            f"berkas?id=eq.{{urllib.parse.quote(kid)}}&select=id"
        ):
            return 404, {{"galat": f"berkas {{kid}} tidak ada pada peragaan ini"}}
    except GalatAlat as e:
        return 502, {{"galat": str(e)}}
    penutur = PenuturSetempat(
        alamat=ALAMAT,
        model=MODEL,
        kunci=KUNCI,
        tenggat_detik=TENGGAT_MODEL,
        n_coba=COBA_MODEL,
    )

    t = GERBANG.get(MODEL)
    gerbang = (
        Gerbang(ambang=t["ambang"], delta=t["delta"], n_kalibrasi=t["n_kalibrasi"])
        if t
        else None
    )

    h = jalankan(
        None,
        kid,
        penutur=penutur,
        anggaran=ANGGARAN,
        gerbang=gerbang,
        perkakas=_pabrik(sumber),
        menahan=_menahan(sumber, kid),
    )

    keluar = {{
        "id": h["id"],
        "teks": h["teks"],
        "sumber": h["sumber"],
        "sebab_mundur": h["sebab_mundur"],
        "cacat": h["cacat"],
        "n_diperbaiki": h["n_diperbaiki"],
        "a1": h["a1"],
        "skor": h["skor"],
        "keadaan": h["keadaan"],
        "model": MODEL,
        "ringkas_jejak": h["ringkas_jejak"],
        "jejak": _baris_jejak(h["jejak"]),
        "penyelia": h["penyelia"],
    }}
    # Gerbang yang belum ditera untuk model ini disebut apa adanya, bukan
    # disembunyikan di balik keadaan yang terdengar pasti.
    if not t:
        keluar["gerbang"] = None
    else:
        keluar["gerbang"] = {{
            "ambang": t["ambang"],
            "delta": t["delta"],
            "n_kalibrasi": t["n_kalibrasi"],
            "diukur_pada": t["diukur_pada"],
        }}
    return 200, keluar


class handler(BaseHTTPRequestHandler):
    def _jawab(self, kode: int, badan: dict) -> None:
        isi = json.dumps(badan, ensure_ascii=False).encode("utf-8")
        self.send_response(kode)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        self.wfile.write(isi)

    def do_OPTIONS(self):  # noqa: N802
        self._jawab(200, {{}})

    def _kerjakan(self, kid: str) -> None:
        kid = kid.strip()
        # Nomor berkas masuk ke penyaring PostgREST, jadi bentuknya dibatasi
        # di sini, bukan dipercaya. Yang sah huruf K dan delapan angka.
        if not (len(kid) == 9 and kid[0] == "K" and kid[1:].isdigit()):
            salah = {{"galat": "nomor berkas tidak berbentuk K00000000"}}
            return self._jawab(422, salah)
        try:
            kode, badan = susun_berkas(kid)
            self._jawab(kode, badan)
        except Exception as e:  # noqa: BLE001
            self._jawab(500, {{"galat": f"{{type(e).__name__}}: {{e}}"}})

    def do_GET(self):  # noqa: N802
        q = urllib.parse.urlparse(self.path).query
        self._kerjakan(urllib.parse.parse_qs(q).get("id", [""])[0])

    def do_POST(self):  # noqa: N802
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n).decode("utf-8")) if n else {{}}
        except (ValueError, json.JSONDecodeError):
            return self._jawab(400, {{"galat": "badan bukan JSON"}})
        self._kerjakan(str(data.get("id") or ""))
'''


def salin(asal: str) -> str:
    with open(os.path.join(SUMBER, asal), encoding="utf-8") as f:
        isi = f.read()
    # Satu aturan, dipakai seragam. Paket tujuannya datar, jadi impor yang
    # naik satu tingkat jadi impor sesama modul.
    isi = isi.replace("from ..", "from .")
    return BANNER.format(asal=asal) + "\n" + isi


def bangun() -> dict[str, str]:
    """Seluruh berkas yang dihasilkan, dari jalur nisbi ke isinya."""
    keluar = {"_nalar/__init__.py": AWALAN_PAKET}
    for asal, nama in MODUL:
        keluar[f"_nalar/{nama}"] = salin(asal)
    keluar["_nalar/tarif_resmi.py"] = (
        BANNER.format(asal="(tidak ada, modul ini pengganti)") + "\n" + TARIF_TIRUAN
    )
    keluar["perkara.py"] = HANDLER.format(
        gerbang=json.dumps(gerbang_tertera(), ensure_ascii=False, indent=4)
    )
    return keluar


def utama() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--periksa", action="store_true", help="Bandingkan, jangan tulis.")
    p.add_argument("--keluar", default=TUJUAN)
    a = p.parse_args()

    berkas = bangun()

    if a.periksa:
        beda = []
        for nama, isi in berkas.items():
            jalur = os.path.join(a.keluar, nama)
            if not os.path.exists(jalur):
                beda.append(f"{nama} belum ada")
                continue
            with open(jalur, encoding="utf-8") as f:
                if f.read() != isi:
                    beda.append(f"{nama} berbeda dari sumbernya")
        if beda:
            for b in beda:
                print(b)
            print("Jalankan scripts/buat_fungsi_perkara.py untuk memperbaruinya.")
            return 1
        print(f"{len(berkas)} berkas sama dengan sumbernya.")
        return 0

    for nama, isi in berkas.items():
        jalur = os.path.join(a.keluar, nama)
        os.makedirs(os.path.dirname(jalur), exist_ok=True)
        with open(jalur, "w", encoding="utf-8", newline="\n") as f:
            f.write(isi)
    n = sum(len(i.splitlines()) for i in berkas.values())
    print(f"{len(berkas)} berkas ditulis ke {a.keluar}, {n} baris")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
