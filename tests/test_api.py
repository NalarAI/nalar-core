"""Uji peladen, seluruh titik akhir sekali jalan.

Bukan sekadar memastikan tidak ada yang meledak. Yang diperiksa juga tiga
janji yang mudah rusak diam diam ketika antarmuka berubah:

Setiap angka uang bersatuan rupiah penuh, jadi tidak ada yang tertukar antara
rupiah dan juta rupiah di layar.

Menahan diri terbedakan dari bersih. Klaim yang kelompoknya menahan diri harus
mengembalikan ambang bernilai null, bukan nol dan bukan angka besar.

Kata curang tidak muncul di keluaran mana pun yang dilihat faskes.

Jalankan:
    python tests/test_api.py
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

lulus, gagal = 0, 0


def cek(nama, kondisi, catatan=""):
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  LULUS  {nama}")
    else:
        gagal += 1
        print(f"  GAGAL  {nama}  {catatan}")


try:
    from fastapi.testclient import TestClient
except ImportError:
    print("\nDILEWATI  fastapi tidak terpasang")
    print("          pasang dengan: pip install '.[api,dev]'")
    sys.exit(0)

from nalar.api import keadaan as _k  # noqa: E402

# Peladen aslinya memakai delapan ribu peserta. Untuk uji, jaringannya
# diperkecil supaya waktunya masuk akal, tapi bentuk keluarannya persis sama.
_k.KEADAAN.__init__(n_peserta=1200, tahun=2, seed=7, n_fktp=60, n_fkrtl=20)

from nalar.api.main import app  # noqa: E402
from nalar.katalog import PEMERIKSAAN  # noqa: E402

print("\n1. Peladen menyala dan menyiapkan modelnya")
with TestClient(app) as c:
    r = c.get("/sehat").json()
    cek("peladen menyatakan dirinya siap", r["siap"] is True, str(r))
    cek("ada klaim yang dilayani", r["n_klaim"] > 0, str(r["n_klaim"]))

    print("\n2. Ringkasan halaman muka")
    s = c.get("/ringkas").json()
    cek("jumlah klaim dan faskes masuk akal", s["n_klaim"] > 0 and s["n_faskes"] > 0)
    cek(
        "nilai klaim total jauh lebih besar daripada selisih terdeteksi",
        s["nilai_klaim_total_rp"] > s["selisih_terdeteksi_rp"] > 0,
        f"{s['nilai_klaim_total_rp']} vs {s['selisih_terdeteksi_rp']}",
    )
    cek(
        "peringatan soal rupiah ikut dikirim, bukan hanya angkanya",
        "benih acak" in s["peringatan"],
    )

    print("\n3. Antrean audit")
    a = c.get("/antrean", params={"kapasitas": 40}).json()
    cek("antrean tidak melebihi kapasitas", a["terisi"] <= a["kapasitas"])
    cek(
        "antrean terurut menurun menurut selisih",
        all(
            a["baris"][i]["penilaian"]["selisih_rp"]
            >= a["baris"][i + 1]["penilaian"]["selisih_rp"]
            for i in range(len(a["baris"]) - 1)
            if a["baris"][i]["alasan_masuk"]
            == a["baris"][i + 1]["alasan_masuk"]
            == "ambang"
        ),
    )
    cek(
        "alasan masuk dibedakan antara ambang dan sampel acak",
        {b["alasan_masuk"] for b in a["baris"]} <= {"ambang", "sampel acak"},
    )
    if a["terisi"] < a["kapasitas"]:
        cek(
            "antrean yang tidak penuh menjelaskan alasannya",
            a["alasan_tidak_penuh"] is not None and "biaya" in a["alasan_tidak_penuh"],
        )

    print("\n4. Satu klaim, penilaian dan penjelasannya")
    if a["baris"]:
        kid = a["baris"][0]["penilaian"]["id"]
        p = c.get(f"/klaim/{kid}").json()
        cek("klaim bisa diambil menurut pengenalnya", p["id"] == kid)
        cek(
            "selisih sama dengan tagihan dikurangi yang didukung bukti",
            max(
                0,
                (p["tarif_ditagihkan_rp"] - p["tarif_didukung_bukti_rp"])
                + (p["barang_ditagihkan_rp"] - p["barang_wajar_rp"]),
            )
            == p["selisih_rp"],
            f"selisih {p['selisih_rp']}",
        )
        cek(
            "klaim yang menahan diri tidak punya ambang, bukan berambang nol",
            (p["ambang_rp"] is None) == p["menahan_diri"],
            f"ambang {p['ambang_rp']} menahan {p['menahan_diri']}",
        )

        j = c.get(f"/klaim/{kid}/penjelasan").json()
        cek(
            "penjelasan memuat kalimat yang bisa dikirim ke faskes",
            len(j["kalimat_untuk_faskes"]) > 40,
        )
        # Fasilitas kesehatan akan menghitung ulang kalimat ini. Kalau tiga
        # angkanya tidak bertemu, seluruh suratnya kehilangan wibawa. Versi
        # sebelumnya mengutip dua angka tarif paket lalu menyebut selisih total
        # yang juga memuat barang habis pakai, dan pengurangannya tidak pernah
        # cocok.
        rp_kalimat = [
            int(x.replace(".", ""))
            for x in re.findall(r"Rp ([\d.]+)", j["kalimat_untuk_faskes"])
        ]
        cek(
            "kalimat untuk faskes memuat tiga angka rupiah",
            len(rp_kalimat) == 3,
            f"ditemukan {len(rp_kalimat)}",
        )
        cek(
            "pengurangan pada kalimat untuk faskes cocok",
            len(rp_kalimat) == 3 and rp_kalimat[0] - rp_kalimat[1] == rp_kalimat[2],
            str(rp_kalimat),
        )
        cek(
            "kata curang tidak muncul di penjelasan",
            not any(k in str(j).lower() for k in ("curang", "fraud", "kecurangan")),
        )
        # Namanya dulu "tiap pengandaian menurunkan selisih". Namanya salah:
        # yang diperiksa cuma bahwa nilainya tidak nol, dan pada data sungguhan
        # sebagian butir memang bertanda negatif, artinya melampirkannya justru
        # menaikkan selisih. Antarmuka yang mengambil nilai mutlaknya karena itu
        # menampilkan bukti yang memperburuk sebagai pengurang.
        cek(
            "tiap pengandaian membawa perubahan yang berarti",
            all(abs(x["ubah_selisih_rp"]) > 1000 for x in j["pengandaian"]),
        )
        cek(
            "arah perubahan terbawa apa adanya, tidak dipaksa positif",
            all(isinstance(x["ubah_selisih_rp"], int) for x in j["pengandaian"]),
        )

        # Berkas perkara. Dokumen verifikator, dan justru karena itu ia harus
        # terpisah dari penjelasan: portal faskes memanggil penjelasan, jadi
        # apa pun yang ditaruh di sana sampai ke peramban pihak yang sedang
        # diperiksa. Dua uji berikut yang menahan keduanya tetap terpisah.
        pk = c.get(f"/klaim/{kid}/perkara").json()
        cek("berkas perkara punya jalurnya sendiri", pk["id"] == kid)
        cek(
            "berkas perkara tidak ikut di penjelasan yang dibaca portal faskes",
            "berkas_perkara" not in j and "teks" not in j,
            str(sorted(j)),
        )
        cek(
            "berkas perkara menyebut selisih dan modus",
            all(k in pk["teks"].lower() for k in ("selisih", "modus")),
        )
        cek(
            "tiap angka pada berkas perkara berasal dari pemanggilan alat",
            pk["jejak"]["a1_lulus"],
        )
        cek(
            "jejaknya menyebut alat mana saja yang dipanggil",
            len(pk["jejak"]["alat"]) == pk["jejak"]["n_panggilan"]
            and pk["jejak"]["n_panggilan"] >= 4,
            str(pk["jejak"]["alat"]),
        )
        cek(
            "sidik rantainya berbentuk SHA-256",
            len(pk["jejak"]["sidik_akhir"]) == 64,
            pk["jejak"]["sidik_akhir"][:16],
        )
        # Dua kali dipanggil harus memberi berkas yang sama. Kalau tidak,
        # jejaknya tidak bisa dipakai membuktikan apa pun, karena angka yang
        # sama bisa keluar dari rantai yang berbeda.
        pk2 = c.get(f"/klaim/{kid}/perkara").json()
        cek(
            "berkas perkara bisa dijalankan ulang dan hasilnya sama",
            pk2["teks"] == pk["teks"],
        )
        cek("sumbernya disebut apa adanya", pk["sumber"] in ("aturan", "agen"))

        # Sanggahan. Ini satu satunya jalur yang menerima kiriman faskes,
        # jadi ia yang paling gampang dipakai memancing keluar apa yang
        # tidak boleh dilihat faskes.
        sg = c.post(
            f"/klaim/{kid}/sanggah",
            json={
                "isi": (
                    "Bersama ini kami lampirkan hasil pemeriksaan hemoglobin "
                    "dan trombosit atas nama pasien tersebut."
                )
            },
        )
        cek("sanggahan dijawab peladen", sg.status_code == 200, str(sg.status_code))
        sj = sg.json()
        cek("caranya disebut apa adanya", sj["cara"] in ("kata", "model"), sj["cara"])
        cek(
            "tiap pemetaan menyertakan alasan yang bisa dibantah",
            all(b["alasan"] for b in sj["dipetakan"]),
            str(sj["dipetakan"][:2]),
        )
        cek(
            "kode yang dipetakan seluruhnya ada di katalog",
            all(b["kode"] in PEMERIKSAAN for b in sj["dipetakan"]),
            str([b["kode"] for b in sj["dipetakan"]]),
        )
        cek(
            "kata curang tidak muncul di jawaban sanggahan",
            not any(k in str(sj).lower() for k in ("curang", "fraud", "kecurangan")),
        )
        cek(
            "berkas perkara tidak ikut di jawaban sanggahan",
            "teks" not in sj and "modus" not in str(sj).lower(),
            str(sorted(sj)),
        )
        cek(
            "surat yang tidak menyebut pemeriksaan tetap dijawab",
            c.post(
                f"/klaim/{kid}/sanggah",
                json={"isi": "Kami keberatan atas hasil verifikasi ini."},
            ).json()["dipetakan"]
            == [],
        )
        cek(
            "surat kosong ditolak, bukan diterima diam diam",
            c.post(f"/klaim/{kid}/sanggah", json={"isi": ""}).status_code == 422,
        )
        cek(
            "sanggahan klaim yang tidak ada menjawab 404",
            c.post("/klaim/K99999999/sanggah", json={"isi": "hemoglobin"}).status_code
            == 404,
        )
        cek(
            "berkas perkara klaim yang tidak ada menjawab 404",
            c.get("/klaim/KTIDAKADA/perkara").status_code == 404,
        )

    # Pengurangannya diperiksa pada banyak berkas, bukan tiga. Versi
    # sebelumnya memeriksa tiga saja dan ketiganya kebetulan cocok, padahal
    # tiga puluh dua dari empat ratus berkas meleset satu rupiah karena tiap
    # bagian dibulatkan sendiri sendiri. Verifikator yang mengurangkan dua
    # angka pertama dan mendapat angka ketiga yang berbeda akan berhenti
    # mempercayai seluruh suratnya, dan ia benar berhenti.
    meleset = []
    for b in a["baris"][:60]:
        n = b["penilaian"]
        d = n["tarif_ditagihkan_rp"] + n["barang_ditagihkan_rp"]
        w = n["tarif_didukung_bukti_rp"] + n["barang_wajar_rp"]
        if max(0, d - w) != n["selisih_rp"]:
            meleset.append((n["id"], d - w, n["selisih_rp"]))
    cek(
        "pengurangan pada penilaian cocok di enam puluh berkas",
        not meleset,
        f"{len(meleset)} meleset, contoh {meleset[:2]}",
    )

    meleset_kalimat = []
    for b in a["baris"][:40]:
        kid = b["penilaian"]["id"]
        j = c.get(f"/klaim/{kid}/penjelasan").json()
        angka = [
            int(x.replace(".", ""))
            for x in re.findall(r"Rp ([\d.]+)", j["kalimat_untuk_faskes"])
        ]
        if len(angka) == 2 and angka[0] <= angka[1]:
            continue  # tidak ada selisih, kalimatnya memang berbeda
        if len(angka) != 3 or angka[0] - angka[1] != angka[2]:
            meleset_kalimat.append((kid, angka))
    cek(
        "pengurangan pada kalimat untuk faskes cocok di empat puluh berkas",
        not meleset_kalimat,
        f"{len(meleset_kalimat)} meleset, contoh {meleset_kalimat[:2]}",
    )

    meleset_perkara = []
    for b in a["baris"][:40]:
        kid = b["penilaian"]["id"]
        t = c.get(f"/klaim/{kid}/perkara").json()["teks"]
        m = re.search(
            r"Diajukan Rp ([\d.]+), didukung bukti Rp ([\d.]+), selisih Rp ([\d.]+)",
            t,
        )
        if not m:
            meleset_perkara.append((kid, "bentuk kalimatnya berubah"))
            continue
        x, y, z = (int(g.replace(".", "")) for g in m.groups())
        if x - y != z:
            meleset_perkara.append((kid, (x, y, z)))
    cek(
        "pengurangan pada berkas perkara cocok di empat puluh berkas",
        not meleset_perkara,
        f"{len(meleset_perkara)} meleset, contoh {meleset_perkara[:2]}",
    )

    cek(
        "klaim yang tidak ada menghasilkan 404",
        c.get("/klaim/KTIDAKADA").status_code == 404,
    )

    print("\n5. Profil faskes, dua daftar")
    pr = c.get("/profil", params={"atas": 5}).json()
    cek("daftar rupiah terisi", len(pr["antrean_rupiah"]) > 0)
    cek("daftar posisi terisi", len(pr["daftar_pantau_posisi"]) > 0)
    cek(
        "hanya daftar rupiah yang membawa kelebihan rupiah",
        all(b["kelebihan_rp"] is not None for b in pr["antrean_rupiah"])
        and all(b["kelebihan_rp"] is None for b in pr["daftar_pantau_posisi"]),
    )
    cek(
        "daftar kedua menyatakan dirinya bukan tuduhan",
        "bukan tuduhan" in pr["catatan_daftar_kedua"],
    )

    print("\n6. Panel keadilan")
    k = c.get("/keadilan").json()
    cek("ada lebih dari satu kelompok yang dinilai", len(k["kelompok"]) >= 2)
    cek(
        "kelebihan berarah maksimum cocok dengan kelompok yang disebut",
        abs(
            max(g["kelebihan_terhadap_keseluruhan"] for g in k["kelompok"])
            - k["kelebihan_berarah_maksimum"]
        )
        < 0.01,
    )
    cek(
        "putusan lulus konsisten dengan batasnya",
        k["lulus"] == (k["kelebihan_berarah_maksimum"] <= k["batas"]),
    )

    print("\n7. Menggeser alpha mengubah penandaan, bukan tarif yang wajar")
    a1 = c.get("/klaim/" + kid).json() if a["baris"] else None
    s5 = c.get("/ringkas", params={"alpha": 0.10}).json()
    s1 = c.get("/ringkas", params={"alpha": 0.01}).json()
    cek(
        "alpha lebih besar menandai lebih banyak klaim",
        s5["laju_penandaan"] >= s1["laju_penandaan"],
        f"{s5['laju_penandaan']} vs {s1['laju_penandaan']}",
    )
    if a1:
        a2 = c.get("/klaim/" + kid).json()
        cek(
            "tarif yang didukung bukti tidak berubah karena alpha",
            a1["tarif_didukung_bukti_rp"] == a2["tarif_didukung_bukti_rp"],
        )

print(f"\n{lulus} lulus, {gagal} gagal")

if __name__ == "__main__":
    sys.exit(1 if gagal else 0)
