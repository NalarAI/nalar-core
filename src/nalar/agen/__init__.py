"""Lapisan agen NALAR: alat, jejak audit, penyelia, dan dua agen pertama.

Urutan pembangunannya disengaja, dan tertulis di nalar-docs/RENCANA-AGENTIK.md
bagian delapan. Lapisan alat beserta jejak auditnya dibangun lebih dulu tanpa
model bahasa sama sekali, penyusun berbasis aturan memakai keduanya, dan
hasilnya jadi garis dasar yang harus dikalahkan agen mana pun sesudahnya.

Tahap dua menambah Agen Berkas dan Agen Sanggah, dan menambah Agen Penyelia
bersamaan, karena tanpa pemutus rantai dan anggaran token tahap dua tidak
boleh menyentuh siapa pun.

Satu aturan berlaku di seluruh berkas di sini. Model bahasa tidak pernah
menentukan sebuah berkas ditandai atau tidak, dan tidak pernah menyebut angka
rupiah yang tidak berasal dari pemanggilan alat. Yang pertama dijaga dengan
tidak memberinya satu pun alat yang bisa menulis. Yang kedua dijaga penjaga
di periksa.py, dan diukur pada tiap berkas sebelum apa pun keluar.
"""

from .alat import Alat, GalatAlat, Perkakas
from .berkas import jalankan as susun_agen
from .dalam import kumpulkan_fakta, periksa_cepat, periksa_dalam
from .gerbang import Gerbang, skor_keyakinan, tera
from .isian import isi_lubang, susun_isian
from .jejak import Jejak
from .penutur import Balasan, GalatPenutur, Penutur, PenuturSetempat, PenuturTiruan
from .penyelia import Anggaran, Penyelia, RantaiDiputus
from .periksa import angka_tak_bersumber, periksa_a1
from .perkara import susun
from .pola import jalankan as awasi_pola
from .sanggah import jalankan as baca_sanggahan
from .sanggah import petakan_bukti, petakan_bukti_model
from .terbitan import jalankan as tanggapi_terbitan

__all__ = [
    "Alat",
    "Anggaran",
    "Balasan",
    "GalatAlat",
    "GalatPenutur",
    "Gerbang",
    "Jejak",
    "Penutur",
    "PenuturSetempat",
    "PenuturTiruan",
    "Penyelia",
    "Perkakas",
    "RantaiDiputus",
    "angka_tak_bersumber",
    "awasi_pola",
    "baca_sanggahan",
    "isi_lubang",
    "kumpulkan_fakta",
    "periksa_a1",
    "periksa_cepat",
    "periksa_dalam",
    "petakan_bukti",
    "petakan_bukti_model",
    "skor_keyakinan",
    "susun",
    "susun_agen",
    "susun_isian",
    "tanggapi_terbitan",
    "tera",
]
