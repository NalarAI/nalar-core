"""Membulatkan empat angka berkas sehingga seluruh pengurangannya cocok.

Selisih dihitung dalam pecahan, lalu dibulatkan ke rupiah penuh untuk
ditampilkan. Kalau tiap bagian dibulatkan sendiri sendiri, jumlah bagian
yang dibulatkan tidak selalu sama dengan pembulatan jumlahnya. Bedanya satu
rupiah, dan satu rupiah itu tidak penting sama sekali bagi penilaiannya.

Yang penting akibatnya di layar. Berkas perkara menulis nilai diajukan,
nilai yang didukung bukti, dan selisihnya pada satu kalimat. Verifikator
yang mengurangkan dua angka pertama dan mendapat angka ketiga yang berbeda
akan berhenti mempercayai seluruh suratnya, dan ia benar berhenti. Angka
yang tidak bisa dikurangkan adalah angka yang tidak bisa dipertanggungjawabkan.

Diukur pada empat ratus berkas, tiga puluh dua di antaranya meleset satu
rupiah sebelum berkas ini ada. Uji peladen sebelumnya memeriksa tiga berkas
saja, dan ketiganya kebetulan cocok.

Maka pembulatannya dikerjakan satu kali di sini, dan seluruh angka turunan
disusun dari empat angka yang sudah dibulatkan itu, bukan dibulatkan sendiri
sendiri. Dengan begitu tiap pasangan angka yang muncul bersama di layar
pasti cocok pengurangannya.
"""

from __future__ import annotations


def bulat_berkas(
    tarif_ditagihkan: float,
    tarif_didukung_bukti: float,
    barang_ditagihkan: float,
    barang_wajar: float,
) -> dict[str, int]:
    """Empat angka berkas beserta seluruh turunannya, dalam rupiah penuh."""
    a = round(float(tarif_ditagihkan))
    b = round(float(tarif_didukung_bukti))
    c = round(float(barang_ditagihkan))
    d = round(float(barang_wajar))
    mentah = (a + c) - (b + d)
    return {
        "tarif_ditagihkan_rp": a,
        "tarif_didukung_bukti_rp": b,
        "barang_ditagihkan_rp": c,
        "barang_wajar_rp": d,
        "total_diajukan_rp": a + c,
        "total_didukung_bukti_rp": b + d,
        "selisih_tarif_rp": a - b,
        "selisih_barang_rp": c - d,
        # Dijepit di nol, mengikuti penebak. Berkas yang ditagihkan lebih
        # kecil daripada yang didukung bukti bukan temuan, dan menampilkannya
        # sebagai selisih negatif akan memasukkannya ke daftar periksa dari
        # arah yang salah.
        "selisih_rp": max(0, mentah),
        # Nilai sebelum dijepit. Yang menyusun kalimat perlu tahu bedanya,
        # karena kalimat "diajukan X, didukung bukti Y, selisih nol" tidak
        # bisa dikurangkan dan pembacanya berhak curiga.
        "selisih_mentah_rp": mentah,
    }
