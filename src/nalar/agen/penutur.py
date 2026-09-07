"""Sambungan ke model bahasa, beserta penutur tiruan yang dipakai menguji.

Model bahasanya berbobot terbuka dan berjalan di dalam pusat data. Itu bukan
pilihan gaya. Aturan lomba melarang data peserta JKN yang nyata keluar tanpa
izin, dan rancangan NALAR sejak awal menolak mengirim isi berkas ke luar.
Maka yang disambung di sini peladen setempat yang bicara dengan tata cara
OpenAI, bukan layanan berbayar di luar.

Tiga hal yang sengaja dibuat begini.

Tidak ada pustaka tambahan. Yang dipakai urllib bawaan Python. Menambah
ketergantungan yang harus ikut lolos pemeriksaan keamanan BPJS bukan harga
yang pantas untuk satu permintaan HTTP.

Penutur tiruan bukan tempelan untuk uji. Ia bentuk baku yang dipakai ketika
tidak ada model yang menyala, dan seluruh lapisan agen tetap bisa dijalankan
tanpa satu pun bobot terpasang. Yang keluar tetap berkas perkara versi
aturan, dan itu memang yang dijanjikan rencana.

Cacah token dicatat tiap balasan, karena target A7 mengikat: biaya token per
berkas harus di bawah Rp 500, dibanding ongkos periksa manual Rp 750 ribu.
Yang tidak dihitung tidak bisa dijaga.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

# Harga acuan sewa GPU, bukan harga jual layanan. Sebuah RTX 4090 setara
# disewa sekitar Rp 6.000 per jam, dan model 4B berbobot 4 bit di atasnya
# mengeluarkan sekitar 60 token per detik pada satu aliran. Itu jatuh di
# sekitar Rp 0,028 per token keluaran. Angka ini dipakai menghitung A7 dan
# ditulis di sini supaya bisa dibantah, bukan disembunyikan di dalam kode.
RP_PER_TOKEN_KELUAR = 0.028
RP_PER_TOKEN_MASUK = 0.0047


class GalatPenutur(Exception):
    """Model bahasa tidak bisa dihubungi, atau menjawab di luar bentuk."""


@dataclass
class Balasan:
    """Satu giliran jawaban model: bicara, atau memanggil alat."""

    teks: str = ""
    panggilan: list[dict] = field(default_factory=list)
    token_masuk: int = 0
    token_keluar: int = 0

    @property
    def memanggil(self) -> bool:
        return bool(self.panggilan)

    def biaya_rp(self) -> float:
        return (
            self.token_masuk * RP_PER_TOKEN_MASUK
            + self.token_keluar * RP_PER_TOKEN_KELUAR
        )


class Penutur:
    """Bentuk yang harus dipenuhi apa pun yang menggantikan model bahasa."""

    nama = "dasar"

    def balas(self, pesan: list[dict], alat: list[dict]) -> Balasan:
        raise NotImplementedError

    def hidup(self) -> bool:
        return False


class PenuturTiruan(Penutur):
    """Penutur bernaskah. Tidak menebak apa pun, hanya mengulang yang ditulis.

    Dipakai untuk dua hal. Menguji bahwa lingkaran pemanggilan alat, anggaran,
    dan penjaganya bekerja tanpa perlu bobot model terpasang. Dan menguji
    bahwa penjaganya memang menangkap, dengan sengaja memberi naskah yang
    mengarang angka.
    """

    nama = "tiruan"

    def __init__(self, naskah: list[Balasan]):
        self.naskah = list(naskah)
        self.giliran = 0

    def balas(self, pesan: list[dict], alat: list[dict]) -> Balasan:
        if self.giliran >= len(self.naskah):
            raise GalatPenutur("naskah penutur tiruan habis")
        b = self.naskah[self.giliran]
        self.giliran += 1
        return b

    def hidup(self) -> bool:
        return True


def _isi_galat(e: urllib.error.HTTPError) -> str:
    """Isi penolakan penyedia, dibaca sekali karena badannya sekali pakai."""
    with contextlib.suppress(OSError):
        return e.read().decode("utf-8", "replace").strip()
    return ""


def _sebab(e: urllib.error.HTTPError, isi: str) -> str:
    """Keterangan penolakan beserta isinya, bukan cuma nomornya.

    Penyedia model menolak dengan nomor yang sama untuk sebab yang jauh
    berbeda. Empat ratus bisa berarti alatnya salah bentuk, pesannya salah
    urutan, atau modelnya tidak ada. Nomornya saja tidak bisa dibedakan
    siapa pun, dan yang membacanya nanti orang yang tidak sedang menatap
    kode ini.

    Isinya dipotong, karena yang berguna kalimat pertamanya dan yang
    berikutnya cuma memanjangkan catatan.
    """
    potong = isi[:300].strip()
    return f"peladen model tidak menjawab: {e}{', ' + potong if potong else ''}"


def _harian(isi: str) -> bool:
    """Penolakan ini karena jatah harian, bukan karena ramai semenit.

    Penyedia memakai nomor yang sama untuk keduanya, dan bedanya cuma ada di
    isi pesannya. Yang membedakan bukan kerapian: yang ramai semenit pulih
    dalam hitungan detik dan pantas ditunggu, yang habis harian pulih dalam
    hitungan jam dan menunggunya membuang seluruh anggaran waktu.
    """
    r = isi.lower()
    return "tokens per day" in r or "(tpd)" in r


def _panggilan_tertolak(isi: str) -> list[dict] | None:
    """Panggilan alat yang ditolak penyedia sebelum sampai ke penyelia.

    Sebagian penyedia memeriksa nama alat di pihak mereka. Nama yang tidak
    ada membuat seluruh giliran ditolak, jadi penyelia di sini tidak pernah
    melihatnya. Padahal penyelia sudah tahu cara menanganinya: alat yang
    tidak ada dikembalikan sebagai keterangan, dan model membetulkan
    namanya pada giliran berikutnya.

    Tanpa terjemahan ini, satu huruf yang salah pada nama alat membatalkan
    seluruh berkas dan yang keluar versi aturan. Itu terlalu mahal untuk
    kesalahan yang model sendiri bisa perbaiki kalau diberi tahu.

    Yang hilang dari terjemahan ini cuma hitungan tokennya, karena penyedia
    tidak melaporkannya pada giliran yang ditolak. Biaya giliran itu jadi
    tercatat nol, dan laporan biaya sedikit lebih rendah dari yang benar.
    """
    try:
        d = json.loads(isi)
    except (ValueError, json.JSONDecodeError):
        return None
    galat = d.get("error") if isinstance(d, dict) else None
    if not isinstance(galat, dict) or galat.get("code") != "tool_use_failed":
        return None
    naskah = galat.get("failed_generation")
    if not isinstance(naskah, str):
        return None
    try:
        g = json.loads(naskah)
    except (ValueError, json.JSONDecodeError):
        return None
    daftar = g if isinstance(g, list) else [g]
    keluar = []
    for c in daftar:
        if not isinstance(c, dict) or not isinstance(c.get("name"), str):
            continue
        arg = c.get("arguments")
        if isinstance(arg, str):
            try:
                arg = json.loads(arg)
            except (ValueError, json.JSONDecodeError):
                arg = {}
        keluar.append(
            {"nama": c["name"], "argumen": arg if isinstance(arg, dict) else {}}
        )
    return keluar or None


class PenuturSetempat(Penutur):
    """Peladen model berbobot terbuka di dalam jaringan, tata cara OpenAI.

    Cocok untuk Ollama, llama.cpp server, maupun vLLM. Yang dipakai hanya
    bagian yang ketiganya sama, jadi menukar mesinnya tidak menyentuh kode
    ini sama sekali.
    """

    nama = "setempat"

    def __init__(
        self,
        alamat: str | None = None,
        model: str | None = None,
        kunci: str | None = None,
        suhu: float = 0.0,
        tenggat_detik: float = 600.0,
        n_coba: int = 3,
    ):
        self.alamat = (
            alamat or os.environ.get("NALAR_MODEL_URL") or "http://127.0.0.1:11434/v1"
        ).rstrip("/")
        self.model = model or os.environ.get("NALAR_MODEL") or "nalar-qwen3-4b"
        # Kunci untuk penyedia awan. Kosong untuk model setempat, dan
        # kosong berarti kepala Authorization tidak dikirim sama sekali.
        self.kunci = kunci or os.environ.get("NALAR_MODEL_KEY") or ""
        # Suhu nol. Yang dinilai dari model ini ketaatannya memanggil alat
        # yang benar, bukan keragaman kalimatnya.
        #
        # Suhu nol tidak membuat jawabannya sama persis tiap kali. Itu sudah
        # diukur di sini: satu berkas yang disusun dua kali keluar dengan
        # kalimat yang berbeda dan angka yang sama. Yang menjamin angkanya
        # bukan suhu, melainkan jejak audit dan pemeriksaan A1.
        self.suhu = suhu
        self.tenggat = tenggat_detik
        # Berapa kali permintaan yang ditolak karena laju diulang. Tiga untuk
        # pengukuran berkelompok, tempat menunggu lebih murah daripada
        # kehilangan berkas. Satu untuk melayani permintaan orang, tempat
        # menunggu tiga puluh detik lebih buruk daripada jawaban versi
        # aturan yang keluar sekarang.
        self.n_coba = max(1, int(n_coba))

    def hidup(self) -> bool:
        # Penyedia awan tidak perlu ditanya. Kuncinya ada berarti alamatnya
        # penyedia, dan penyedia tidak mati diam diam seperti peladen di
        # mesin sendiri. Menanyakannya memakan satu permintaan dari jatah
        # harian untuk tiap berkas, dan tanyanya bisa gagal karena
        # pemanggilan dingin yang lambat, bukan karena modelnya mati.
        #
        # Kunci yang salah tetap ketahuan, cuma satu langkah lebih lambat:
        # permintaan sungguhannya ditolak, dan penolakannya masuk sebab
        # mundur dengan keterangan dari penyedianya sendiri. Itu keterangan
        # yang lebih berguna daripada "tidak ada model yang menyala".
        if self.kunci:
            return True
        try:
            permintaan = urllib.request.Request(
                f"{self.alamat}/models",
                headers={
                    "User-Agent": "nalar/1.0",
                    **({"Authorization": f"Bearer {self.kunci}"} if self.kunci else {}),
                },
            )
            with urllib.request.urlopen(permintaan, timeout=3) as r:
                return r.status == 200
        except (urllib.error.URLError, OSError, TimeoutError):
            return False

    def balas(self, pesan: list[dict], alat: list[dict]) -> Balasan:
        badan = {
            "model": self.model,
            "messages": pesan,
            "temperature": self.suhu,
            "tools": [{"type": "function", "function": a} for a in alat],
        }
        permintaan = urllib.request.Request(
            f"{self.alamat}/chat/completions",
            data=json.dumps(badan, ensure_ascii=False).encode("utf-8"),
            # Penanda agen pengguna wajib ada. Ollama tidak peduli, tapi
            # penyedia awan yang berdiri di belakang Cloudflare menolak
            # bawaan urllib dengan galat 1010 yang tidak menyebut sebab.
            headers={
                "Content-Type": "application/json",
                "User-Agent": "nalar/1.0",
                **({"Authorization": f"Bearer {self.kunci}"} if self.kunci else {}),
            },
            method="POST",
        )
        # Penyedia awan membatasi laju, dan batasnya kena bahkan pada
        # pemakaian sepi karena yang dihitung token per menit bukan
        # permintaan per menit. Tanpa percobaan ulang, pengunjung kedua
        # yang menekan tombol pada menit yang sama mendapat kegagalan.
        #
        # Yang ditunggu diambil dari kepala Retry-After kalau ada, karena
        # menebak sendiri berarti menunggu terlalu lama atau terlalu
        # sebentar, dan yang terlalu sebentar kena lagi.
        for percobaan in range(self.n_coba):
            try:
                with urllib.request.urlopen(permintaan, timeout=self.tenggat) as r:
                    jawab = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                isi = _isi_galat(e)
                # Nama alat yang tidak ada bukan alasan membatalkan berkas.
                # Ia dikembalikan sebagai giliran biasa, dan penyelia yang
                # menolaknya dengan keterangan seperti penolakan alat lain.
                tertolak = _panggilan_tertolak(isi) if e.code == 400 else None
                if tertolak:
                    return Balasan(panggilan=tertolak)
                # Menunggu menolong untuk batas per menit, dan tidak pernah
                # menolong untuk jatah harian. Jatah harian pulih dalam
                # hitungan jam, sedangkan yang menunggu di sini fungsi yang
                # punya batas waktu satu menit. Yang benar pindah ke model
                # berikutnya pada rantai, dan itu terjadi kalau kita menyerah
                # sekarang juga.
                if e.code != 429 or _harian(isi) or percobaan == self.n_coba - 1:
                    raise GalatPenutur(_sebab(e, isi)) from None
                tunggu = e.headers.get("Retry-After")
                try:
                    jeda = min(float(tunggu), 20.0) if tunggu else 0.0
                except ValueError:
                    jeda = 0.0
                time.sleep(jeda or 2.0 * (percobaan + 1))
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                raise GalatPenutur(f"peladen model tidak menjawab: {e}") from None
            except json.JSONDecodeError:
                raise GalatPenutur("jawaban peladen bukan JSON") from None

        try:
            pesan_balik = jawab["choices"][0]["message"]
        except (KeyError, IndexError):
            raise GalatPenutur("jawaban peladen tidak punya choices") from None

        pakai = jawab.get("usage") or {}
        panggilan = []
        for p in pesan_balik.get("tool_calls") or []:
            f = p.get("function") or {}
            mentah = f.get("arguments") or "{}"
            try:
                arg = json.loads(mentah) if isinstance(mentah, str) else dict(mentah)
            except json.JSONDecodeError:
                # Argumen yang tidak bisa dibaca bukan alasan berhenti. Ia
                # dilewatkan apa adanya supaya alatnya sendiri yang menolak,
                # dan penolakan itu ikut tercatat di jejak.
                arg = {"__tak_terbaca__": mentah}
            panggilan.append(
                {"nama": f.get("name", ""), "argumen": arg, "id": p.get("id", "")}
            )

        return Balasan(
            teks=(pesan_balik.get("content") or "").strip(),
            panggilan=panggilan,
            token_masuk=int(pakai.get("prompt_tokens") or 0),
            token_keluar=int(pakai.get("completion_tokens") or 0),
        )


class PenuturBerantai(Penutur):
    """Beberapa penutur, dicoba berurutan sampai ada yang menjawab.

    Alasannya jatah, bukan mutu. Penyedia gratis membatasi token per hari
    untuk tiap model, dan batas itu yang paling dulu kena. Dua ratus ribu
    token sehari, sedangkan satu berkas perkara memakai sekitar enam ribu,
    jadi yang muat kira kira tiga puluh berkas sehari. Model kedua punya
    jatahnya sendiri, dan merangkainya menambah jatah itu tanpa membayar.

    Batas ini tidak kelihatan dari kepala jawaban. x-ratelimit hanya
    menyebut permintaan per hari dan token per menit, sedangkan yang
    mengikat token per hari. Ia baru ketahuan dari isi penolakannya, dan
    isi penolakan itu baru ikut tercatat sesudah kami menambahkannya.

    Urutannya urutan mutu, bukan urutan jatah. Yang pertama yang terbaik
    menurut pengukuran, dan yang berikutnya dipakai cuma ketika yang
    pertama kehabisan. Berkas susunan model mana pun tetap melewati penjaga
    yang sama, jadi yang lolos tetap yang lolos.

    Yang menjawab diingat. Giliran berikutnya mulai dari dia, supaya tidak
    ada permintaan yang terbuang menanyai penutur yang sudah diketahui
    kehabisan.
    """

    nama = "berantai"

    def __init__(self, daftar: list[Penutur]):
        self.daftar = [p for p in daftar if p is not None]
        self.mulai = 0

    @property
    def model(self) -> str:
        """Nama model yang terakhir menjawab, bukan yang pertama didaftar."""
        if not self.daftar:
            return ""
        return getattr(self.daftar[self.mulai], "model", "")

    def hidup(self) -> bool:
        return any(p.hidup() for p in self.daftar)

    def balas(self, pesan: list[dict], alat: list[dict]) -> Balasan:
        if not self.daftar:
            raise GalatPenutur("rantai penutur kosong")
        galat = None
        n = len(self.daftar)
        for k in range(n):
            i = (self.mulai + k) % n
            try:
                b = self.daftar[i].balas(pesan, alat)
                self.mulai = i
                return b
            except GalatPenutur as e:
                galat = e
        raise galat


def penutur_baku() -> Penutur:
    """Penutur setempat kalau menyala, kalau tidak penutur yang tidak bicara.

    Yang dikembalikan ketika tidak ada model menyala bukan galat, melainkan
    penutur yang selalu menolak. Lapisan di atasnya menerjemahkan penolakan
    itu jadi berkas perkara versi aturan, dan itu memang keluaran yang sah.
    """
    p = PenuturSetempat()
    return p if p.hidup() else Penutur()
