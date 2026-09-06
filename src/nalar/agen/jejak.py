"""Jejak pemanggilan alat, ditulis sekali dan tidak bisa diubah diam diam.

Ini dibangun lebih dulu, sebelum ada satu pun agen, dan itu disengaja. Jejak
audit yang ditambahkan sesudah sistemnya jalan selalu bocor: selalu ada satu
jalur yang lupa dicatat, dan yang lupa dicatat itu yang justru ditanyakan
belakangan.

Tiap catatan menyimpan nama alat, argumennya, sidik hasilnya, lama
pemanggilannya, dan sidik catatan sebelumnya. Rantai sidik itu yang membuat
satu baris tidak bisa disunting tanpa merusak seluruh baris sesudahnya.

Yang tidak disimpan: isi hasil selengkapnya. Yang perlu diaudit adalah bahwa
sebuah angka benar berasal dari alat, bukan seluruh isi rekam medis ikut
menumpuk di berkas catatan. Maka yang disimpan sidik hasilnya, ditambah
himpunan angka yang muncul di dalamnya, karena himpunan angka itulah yang
dipakai memeriksa tidak ada angka karangan pada surat ke fasilitas kesehatan.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

AWAL = "0" * 64


def _kanonik(o) -> str:
    """JSON yang urutannya tetap, supaya sidiknya bisa dihitung ulang."""
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sidik(teks: str) -> str:
    return hashlib.sha256(teks.encode("utf-8")).hexdigest()


def angka_di(o) -> set[float]:
    """Seluruh angka yang muncul pada sebuah hasil alat, sedalam apa pun.

    Dipakai memeriksa bahwa tiap angka pada teks yang disusun agen benar
    benar berasal dari alat. Bilangan bulat dan pecahan disimpan sebagai
    pecahan supaya perbandingannya tidak bergantung pada tipe.
    """
    keluar: set[float] = set()

    def telusuri(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            keluar.add(float(x))
        elif isinstance(x, dict):
            for v in x.values():
                telusuri(v)
        elif isinstance(x, (list, tuple, set)):
            for v in x:
                telusuri(v)

    telusuri(o)
    return keluar


@dataclass
class Catatan:
    urut: int
    waktu: float
    alat: str
    argumen: dict
    sidik_hasil: str
    angka: list[float]
    ms: float
    galat: str | None
    induk: str
    sidik: str = ""

    def tanpa_sidik(self) -> dict:
        d = self.__dict__.copy()
        d.pop("sidik")
        return d


@dataclass
class Jejak:
    """Rantai catatan pemanggilan alat untuk satu berkas perkara."""

    perkara: str
    catatan: list[Catatan] = field(default_factory=list)

    def tambah(
        self,
        alat: str,
        argumen: dict,
        hasil,
        ms: float,
        galat: str | None = None,
    ) -> Catatan:
        induk = self.catatan[-1].sidik if self.catatan else AWAL
        c = Catatan(
            urut=len(self.catatan) + 1,
            waktu=time.time(),
            alat=alat,
            argumen=argumen,
            sidik_hasil=_sidik(_kanonik(hasil)) if galat is None else "",
            angka=sorted(angka_di(hasil)) if galat is None else [],
            ms=round(ms, 3),
            galat=galat,
            induk=induk,
        )
        c.sidik = _sidik(induk + _kanonik(c.tanpa_sidik()))
        self.catatan.append(c)
        return c

    def angka_terkumpul(self) -> set[float]:
        """Seluruh angka yang pernah dikembalikan alat pada perkara ini."""
        keluar: set[float] = set()
        for c in self.catatan:
            keluar.update(c.angka)
        return keluar

    def periksa_rantai(self) -> tuple[bool, str]:
        """Rantai sidiknya utuh atau tidak, beserta baris pertama yang rusak."""
        induk = AWAL
        for c in self.catatan:
            if c.induk != induk:
                return False, f"induk baris {c.urut} tidak cocok"
            if c.sidik != _sidik(induk + _kanonik(c.tanpa_sidik())):
                return False, f"sidik baris {c.urut} tidak cocok"
            induk = c.sidik
        return True, ""

    def ke_jsonl(self) -> str:
        return "\n".join(
            _kanonik({"perkara": self.perkara, **c.__dict__}) for c in self.catatan
        )

    def ringkas(self) -> dict:
        return {
            "perkara": self.perkara,
            "n_panggilan": len(self.catatan),
            "alat": [c.alat for c in self.catatan],
            "ms_total": round(sum(c.ms for c in self.catatan), 3),
            "n_galat": sum(1 for c in self.catatan if c.galat),
            "sidik_akhir": self.catatan[-1].sidik if self.catatan else AWAL,
        }
